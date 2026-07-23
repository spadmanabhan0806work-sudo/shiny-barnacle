from __future__ import annotations

import io
import json
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import (
    BatchUploadModel,
    CallRecordingModel,
    IntentExtractionModel,
    ReviewQueueItemModel,
    TranscriptModel,
)


class ExportResultsUseCase:
    """Export batch call results as JSON or Excel."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_batch(self, batch_id: UUID) -> BatchUploadModel | None:
        result = await self._session.execute(
            select(BatchUploadModel).where(BatchUploadModel.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def build_records(self, batch: BatchUploadModel) -> list[dict]:
        records: list[dict] = []
        for call_id_str in batch.call_ids:
            call_id = UUID(str(call_id_str))
            call_result = await self._session.execute(
                select(CallRecordingModel).where(CallRecordingModel.id == call_id)
            )
            call = call_result.scalar_one_or_none()
            if call is None:
                continue

            transcript_result = await self._session.execute(
                select(TranscriptModel).where(TranscriptModel.call_id == call_id)
            )
            transcript = transcript_result.scalar_one_or_none()

            extraction_result = await self._session.execute(
                select(IntentExtractionModel)
                .where(IntentExtractionModel.call_id == call_id)
                .order_by(IntentExtractionModel.id.desc())
            )
            extraction = extraction_result.scalars().first()

            intent_fields: dict | None = None
            review_status: str | None = None
            if extraction:
                intent_fields = {
                    "side": extraction.side,
                    "stock_symbol": extraction.stock_symbol,
                    "quantity": extraction.quantity,
                    "price": float(extraction.price),
                    "exchange": extraction.exchange,
                    "confidence": extraction.confidence,
                    "prompt_version": extraction.prompt_version,
                    "llm_provider": extraction.llm_provider,
                }
                review_result = await self._session.execute(
                    select(ReviewQueueItemModel).where(
                        ReviewQueueItemModel.extraction_id == extraction.id
                    )
                )
                review = review_result.scalar_one_or_none()
                if review and review.corrected_fields:
                    intent_fields.update(review.corrected_fields)
                    review_status = review.status

            records.append(
                {
                    "call_id": str(call.id),
                    "status": call.status,
                    "detected_language": call.detected_language,
                    "duration_sec": call.duration_sec,
                    "transcript": transcript.full_text if transcript else None,
                    "intent": intent_fields,
                    "review_status": review_status,
                }
            )
        return records

    async def export_json(self, batch_id: UUID) -> tuple[bytes, str]:
        batch = await self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch not found: {batch_id}")
        records = await self.build_records(batch)
        payload = {
            "batch_id": str(batch.id),
            "tenant_id": batch.tenant_id,
            "total": len(records),
            "results": records,
        }
        content = json.dumps(payload, indent=2).encode("utf-8")
        filename = f"operyx-batch-{batch_id}.json"
        return content, filename

    async def export_excel(self, batch_id: UUID) -> tuple[bytes, str]:
        batch = await self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch not found: {batch_id}")
        records = await self.build_records(batch)

        wb = Workbook()
        ws = wb.active
        ws.title = "Results"
        headers = [
            "call_id",
            "status",
            "detected_language",
            "duration_sec",
            "transcript",
            "side",
            "stock_symbol",
            "quantity",
            "price",
            "exchange",
            "confidence",
            "prompt_version",
            "review_status",
        ]
        ws.append(headers)

        for record in records:
            intent = record.get("intent") or {}
            ws.append(
                [
                    record["call_id"],
                    record["status"],
                    record.get("detected_language"),
                    record.get("duration_sec"),
                    record.get("transcript"),
                    intent.get("side"),
                    intent.get("stock_symbol"),
                    intent.get("quantity"),
                    intent.get("price"),
                    intent.get("exchange"),
                    intent.get("confidence"),
                    intent.get("prompt_version"),
                    record.get("review_status"),
                ]
            )

        buffer = io.BytesIO()
        wb.save(buffer)
        filename = f"operyx-batch-{batch_id}.xlsx"
        return buffer.getvalue(), filename

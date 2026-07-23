from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.annotation import Annotation, AnnotationStatus, GroundTruth
from src.domain.entities.call_recording import CallRecording, CallStatus
from src.domain.entities.evaluation_run import EvaluationRun
from src.domain.entities.intent_extraction import IntentExtraction
from src.domain.entities.review_queue_item import ReviewQueueItem, ReviewStatus
from src.domain.entities.transcript import Transcript, TranscriptSegment
from src.domain.repositories.annotation_repository import AnnotationRepository
from src.domain.repositories.audit_log_repository import AuditLogRepository, AuditLogEntry
from src.domain.repositories.batch_upload_repository import BatchUploadRepository, BatchUpload
from src.domain.repositories.call_recording_repository import CallRecordingRepository
from src.domain.repositories.evaluation_run_repository import EvaluationRunRepository
from src.domain.repositories.intent_extraction_repository import IntentExtractionRepository
from src.domain.repositories.review_queue_repository import ReviewQueueRepository
from src.domain.repositories.transcript_repository import TranscriptRepository
from src.infrastructure.persistence.models import (
    AnnotationModel,
    AuditLogModel,
    BatchUploadModel,
    CallRecordingModel,
    EvaluationRunModel,
    IntentExtractionModel,
    ReviewQueueItemModel,
    TranscriptModel,
)


class SqlAlchemyCallRecordingRepository(CallRecordingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: CallRecordingModel) -> CallRecording:
        return CallRecording(
            id=model.id,
            tenant_id=model.tenant_id,
            storage_key=model.storage_key,
            status=CallStatus(model.status),
            detected_language=model.detected_language,
            duration_sec=model.duration_sec,
            created_at=model.created_at,
        )

    def _to_model(self, entity: CallRecording) -> CallRecordingModel:
        return CallRecordingModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            storage_key=entity.storage_key,
            status=entity.status.value,
            detected_language=entity.detected_language,
            duration_sec=entity.duration_sec,
            created_at=entity.created_at,
        )

    async def create(self, recording: CallRecording) -> CallRecording:
        model = self._to_model(recording)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, call_id: UUID) -> CallRecording | None:
        result = await self._session.execute(
            select(CallRecordingModel).where(CallRecordingModel.id == call_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        *,
        status: CallStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CallRecording]:
        query = select(CallRecordingModel).order_by(CallRecordingModel.created_at.desc())
        if status:
            query = query.where(CallRecordingModel.status == status.value)
        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, recording: CallRecording) -> CallRecording:
        result = await self._session.execute(
            select(CallRecordingModel).where(CallRecordingModel.id == recording.id)
        )
        model = result.scalar_one()
        model.status = recording.status.value
        model.detected_language = recording.detected_language
        model.duration_sec = recording.duration_sec
        await self._session.flush()
        return self._to_entity(model)


class SqlAlchemyAnnotationRepository(AnnotationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: AnnotationModel) -> Annotation:
        gt = model.ground_truth
        return Annotation(
            id=model.id,
            call_id=model.call_id,
            annotator_id=model.annotator_id,
            ground_truth=GroundTruth(
                side=gt["side"],
                stock_symbol=gt["stock_symbol"],
                quantity=gt["quantity"],
                price=float(gt["price"]),
                exchange=gt["exchange"],
            ),
            status=AnnotationStatus(model.status),
        )

    def _to_model(self, entity: Annotation) -> AnnotationModel:
        return AnnotationModel(
            id=entity.id,
            call_id=entity.call_id,
            annotator_id=entity.annotator_id,
            ground_truth={
                "side": entity.ground_truth.side,
                "stock_symbol": entity.ground_truth.stock_symbol,
                "quantity": entity.ground_truth.quantity,
                "price": entity.ground_truth.price,
                "exchange": entity.ground_truth.exchange,
            },
            status=entity.status.value,
        )

    async def create(self, annotation: Annotation) -> Annotation:
        model = self._to_model(annotation)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_call_id(self, call_id: UUID) -> Annotation | None:
        result = await self._session.execute(
            select(AnnotationModel).where(AnnotationModel.call_id == call_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, annotation: Annotation) -> Annotation:
        result = await self._session.execute(
            select(AnnotationModel).where(AnnotationModel.id == annotation.id)
        )
        model = result.scalar_one()
        model.ground_truth = {
            "side": annotation.ground_truth.side,
            "stock_symbol": annotation.ground_truth.stock_symbol,
            "quantity": annotation.ground_truth.quantity,
            "price": annotation.ground_truth.price,
            "exchange": annotation.ground_truth.exchange,
        }
        model.status = annotation.status.value
        await self._session.flush()
        return self._to_entity(model)

    async def list_all(self, *, limit: int = 1000, offset: int = 0) -> list[Annotation]:
        result = await self._session.execute(
            select(AnnotationModel).limit(limit).offset(offset)
        )
        return [self._to_entity(m) for m in result.scalars().all()]


class SqlAlchemyTranscriptRepository(TranscriptRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _segments_to_json(self, segments: list[TranscriptSegment]) -> list[dict]:
        return [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text,
                "confidence": s.confidence,
            }
            for s in segments
        ]

    def _segments_from_json(self, data: list[dict] | None) -> list[TranscriptSegment]:
        if not data:
            return []
        return [
            TranscriptSegment(
                start=item.get("start", 0.0),
                end=item.get("end", 0.0),
                text=item.get("text", ""),
                confidence=item.get("confidence"),
            )
            for item in data
        ]

    def _to_entity(self, model: TranscriptModel) -> Transcript:
        return Transcript(
            id=model.id,
            call_id=model.call_id,
            full_text=model.full_text,
            segments=self._segments_from_json(model.segments),
            stt_provider=model.stt_provider,
            stt_model=model.stt_model,
        )

    def _to_model(self, entity: Transcript) -> TranscriptModel:
        return TranscriptModel(
            id=entity.id,
            call_id=entity.call_id,
            full_text=entity.full_text,
            segments=self._segments_to_json(entity.segments),
            stt_provider=entity.stt_provider,
            stt_model=entity.stt_model,
        )

    async def create(self, transcript: Transcript) -> Transcript:
        model = self._to_model(transcript)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_call_id(self, call_id: UUID) -> Transcript | None:
        result = await self._session.execute(
            select(TranscriptModel).where(TranscriptModel.call_id == call_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, transcript: Transcript) -> Transcript:
        result = await self._session.execute(
            select(TranscriptModel).where(TranscriptModel.id == transcript.id)
        )
        model = result.scalar_one()
        model.full_text = transcript.full_text
        model.segments = self._segments_to_json(transcript.segments)
        model.stt_provider = transcript.stt_provider
        model.stt_model = transcript.stt_model
        await self._session.flush()
        return self._to_entity(model)


class SqlAlchemyIntentExtractionRepository(IntentExtractionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: IntentExtractionModel) -> IntentExtraction:
        return IntentExtraction(
            id=model.id,
            call_id=model.call_id,
            side=model.side,
            stock_symbol=model.stock_symbol,
            quantity=model.quantity,
            price=float(model.price),
            exchange=model.exchange,
            confidence=model.confidence,
            prompt_version=model.prompt_version,
            llm_provider=model.llm_provider,
            raw_llm_output=model.raw_llm_output,
        )

    def _to_model(self, entity: IntentExtraction) -> IntentExtractionModel:
        return IntentExtractionModel(
            id=entity.id,
            call_id=entity.call_id,
            side=entity.side,
            stock_symbol=entity.stock_symbol,
            quantity=entity.quantity,
            price=entity.price,
            exchange=entity.exchange,
            confidence=entity.confidence,
            prompt_version=entity.prompt_version,
            llm_provider=entity.llm_provider,
            raw_llm_output=entity.raw_llm_output,
        )

    async def create(self, extraction: IntentExtraction) -> IntentExtraction:
        model = self._to_model(extraction)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_call_id(self, call_id: UUID) -> IntentExtraction | None:
        result = await self._session.execute(
            select(IntentExtractionModel)
            .where(IntentExtractionModel.call_id == call_id)
            .order_by(IntentExtractionModel.id.desc())
        )
        model = result.scalars().first()
        return self._to_entity(model) if model else None

    async def get_by_id(self, extraction_id: UUID) -> IntentExtraction | None:
        result = await self._session.execute(
            select(IntentExtractionModel).where(IntentExtractionModel.id == extraction_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, extraction: IntentExtraction) -> IntentExtraction:
        result = await self._session.execute(
            select(IntentExtractionModel).where(IntentExtractionModel.id == extraction.id)
        )
        model = result.scalar_one()
        model.side = extraction.side
        model.stock_symbol = extraction.stock_symbol
        model.quantity = extraction.quantity
        model.price = extraction.price
        model.exchange = extraction.exchange
        model.confidence = extraction.confidence
        model.prompt_version = extraction.prompt_version
        model.llm_provider = extraction.llm_provider
        model.raw_llm_output = extraction.raw_llm_output
        await self._session.flush()
        return self._to_entity(model)


class SqlAlchemyReviewQueueRepository(ReviewQueueRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: ReviewQueueItemModel) -> ReviewQueueItem:
        return ReviewQueueItem(
            id=model.id,
            extraction_id=model.extraction_id,
            status=ReviewStatus(model.status),
            corrected_fields=model.corrected_fields,
            reviewer_id=model.reviewer_id,
        )

    def _to_model(self, entity: ReviewQueueItem) -> ReviewQueueItemModel:
        return ReviewQueueItemModel(
            id=entity.id,
            extraction_id=entity.extraction_id,
            status=entity.status.value,
            corrected_fields=entity.corrected_fields,
            reviewer_id=entity.reviewer_id,
        )

    async def create(self, item: ReviewQueueItem) -> ReviewQueueItem:
        model = self._to_model(item)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, item_id: UUID) -> ReviewQueueItem | None:
        result = await self._session.execute(
            select(ReviewQueueItemModel).where(ReviewQueueItemModel.id == item_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_extraction_id(self, extraction_id: UUID) -> ReviewQueueItem | None:
        result = await self._session.execute(
            select(ReviewQueueItemModel).where(
                ReviewQueueItemModel.extraction_id == extraction_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_pending(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewQueueItem]:
        result = await self._session.execute(
            select(ReviewQueueItemModel)
            .where(ReviewQueueItemModel.status == ReviewStatus.PENDING.value)
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, item: ReviewQueueItem) -> ReviewQueueItem:
        result = await self._session.execute(
            select(ReviewQueueItemModel).where(ReviewQueueItemModel.id == item.id)
        )
        model = result.scalar_one()
        model.status = item.status.value
        model.corrected_fields = item.corrected_fields
        model.reviewer_id = item.reviewer_id
        await self._session.flush()
        return self._to_entity(model)


class SqlAlchemyEvaluationRunRepository(EvaluationRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: EvaluationRunModel) -> EvaluationRun:
        return EvaluationRun(
            id=model.id,
            prompt_version=model.prompt_version,
            stt_provider=model.stt_provider,
            llm_provider=model.llm_provider,
            aggregate_metrics=model.aggregate_metrics,
            ran_at=model.ran_at,
        )

    def _to_model(self, entity: EvaluationRun) -> EvaluationRunModel:
        return EvaluationRunModel(
            id=entity.id,
            prompt_version=entity.prompt_version,
            stt_provider=entity.stt_provider,
            llm_provider=entity.llm_provider,
            aggregate_metrics=entity.aggregate_metrics,
            ran_at=entity.ran_at,
        )

    async def create(self, run: EvaluationRun) -> EvaluationRun:
        model = self._to_model(run)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, run_id: UUID) -> EvaluationRun | None:
        result = await self._session.execute(
            select(EvaluationRunModel).where(EvaluationRunModel.id == run_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[EvaluationRun]:
        result = await self._session.execute(
            select(EvaluationRunModel)
            .order_by(EvaluationRunModel.ran_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(m) for m in result.scalars().all()]


class SqlAlchemyBatchUploadRepository(BatchUploadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: BatchUploadModel) -> BatchUpload:
        call_ids = [uuid.UUID(str(cid)) for cid in (model.call_ids or [])]
        return BatchUpload(
            id=model.id,
            tenant_id=model.tenant_id,
            call_ids=call_ids,
            created_at=model.created_at,
        )

    async def create(self, *, tenant_id: str, call_ids: list[uuid.UUID]) -> BatchUpload:
        model = BatchUploadModel(
            tenant_id=tenant_id,
            call_ids=[str(cid) for cid in call_ids],
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, batch_id: uuid.UUID) -> BatchUpload | None:
        result = await self._session.execute(
            select(BatchUploadModel).where(BatchUploadModel.id == batch_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: AuditLogModel) -> AuditLogEntry:
        return AuditLogEntry(
            id=model.id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            action=model.action,
            actor_id=model.actor_id,
            changes=model.changes,
            created_at=model.created_at,
        )

    async def create(
        self,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_id: str,
        changes: dict | None = None,
    ) -> AuditLogEntry:
        model = AuditLogModel(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            actor_id=actor_id,
            changes=changes,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

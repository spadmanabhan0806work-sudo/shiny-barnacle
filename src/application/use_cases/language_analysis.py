from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.language_detector import detect_language
from src.domain.value_objects.language import Language
from src.infrastructure.persistence.models import (
    BatchUploadModel,
    CallRecordingModel,
    TranscriptModel,
)

_REPORT_BUCKETS = ("hi", "en", "ml", "gu", "mixed", "other")
_LOW_CONFIDENCE_THRESHOLD = 0.6


@dataclass
class CallLanguageDetail:
    call_id: str
    detected_language: str
    transcript_language: str
    bucket: str
    avg_segment_confidence: float | None
    needs_review: bool
    review_reasons: list[str] = field(default_factory=list)


@dataclass
class LanguageAnalysisReport:
    batch_id: str | None
    generated_at: str
    total_calls: int
    processed_calls: int
    distribution: dict[str, int]
    needs_review: list[CallLanguageDetail]
    calls: list[CallLanguageDetail]

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "generated_at": self.generated_at,
            "total_calls": self.total_calls,
            "processed_calls": self.processed_calls,
            "distribution": self.distribution,
            "needs_review_count": len(self.needs_review),
            "needs_review": [
                {
                    "call_id": c.call_id,
                    "detected_language": c.detected_language,
                    "transcript_language": c.transcript_language,
                    "bucket": c.bucket,
                    "avg_segment_confidence": c.avg_segment_confidence,
                    "review_reasons": c.review_reasons,
                }
                for c in self.needs_review
            ],
            "calls": [
                {
                    "call_id": c.call_id,
                    "detected_language": c.detected_language,
                    "transcript_language": c.transcript_language,
                    "bucket": c.bucket,
                    "avg_segment_confidence": c.avg_segment_confidence,
                    "needs_review": c.needs_review,
                    "review_reasons": c.review_reasons,
                }
                for c in self.calls
            ],
        }


def bucket_language(code: str) -> str:
    if code in _REPORT_BUCKETS:
        return code
    if code == Language.UNKNOWN.value:
        return "other"
    return "other"


def _avg_segment_confidence(segments: list | None) -> float | None:
    if not segments:
        return None
    scores = [
        float(item["confidence"])
        for item in segments
        if isinstance(item, dict) and item.get("confidence") is not None
    ]
    if not scores:
        return None
    return sum(scores) / len(scores)


class LanguageAnalysisUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        *,
        batch_id: UUID | None = None,
        call_ids: list[UUID] | None = None,
    ) -> LanguageAnalysisReport:
        target_ids = await self._resolve_call_ids(batch_id, call_ids)
        distribution = {bucket: 0 for bucket in _REPORT_BUCKETS}
        details: list[CallLanguageDetail] = []
        processed = 0

        for call_id in target_ids:
            detail = await self._analyze_call(call_id)
            if detail is None:
                continue
            processed += 1
            distribution[detail.bucket] = distribution.get(detail.bucket, 0) + 1
            details.append(detail)

        needs_review = [d for d in details if d.needs_review]
        return LanguageAnalysisReport(
            batch_id=str(batch_id) if batch_id else None,
            generated_at=datetime.now(UTC).isoformat(),
            total_calls=len(target_ids),
            processed_calls=processed,
            distribution=distribution,
            needs_review=needs_review,
            calls=details,
        )

    async def _resolve_call_ids(
        self,
        batch_id: UUID | None,
        call_ids: list[UUID] | None,
    ) -> list[UUID]:
        if call_ids:
            return call_ids
        if batch_id is None:
            raise ValueError("batch_id or call_ids is required")

        result = await self._session.execute(
            select(BatchUploadModel).where(BatchUploadModel.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if batch is None:
            raise ValueError(f"Batch not found: {batch_id}")
        return [UUID(str(cid)) for cid in batch.call_ids]

    async def _analyze_call(self, call_id: UUID) -> CallLanguageDetail | None:
        call_result = await self._session.execute(
            select(CallRecordingModel).where(CallRecordingModel.id == call_id)
        )
        call = call_result.scalar_one_or_none()
        if call is None:
            return None

        transcript_result = await self._session.execute(
            select(TranscriptModel).where(TranscriptModel.call_id == call_id)
        )
        transcript = transcript_result.scalar_one_or_none()

        transcript_text = transcript.full_text if transcript else ""
        transcript_language = detect_language(transcript_text)
        stored_language = call.detected_language or transcript_language
        bucket = bucket_language(stored_language)
        avg_conf = _avg_segment_confidence(transcript.segments if transcript else None)

        review_reasons: list[str] = []
        if stored_language == Language.UNKNOWN.value:
            review_reasons.append("unknown_language")
        if not transcript_text.strip():
            review_reasons.append("empty_transcript")
        if avg_conf is not None and avg_conf < _LOW_CONFIDENCE_THRESHOLD:
            review_reasons.append("low_stt_confidence")
        if call.status == "failed":
            review_reasons.append("processing_failed")

        return CallLanguageDetail(
            call_id=str(call_id),
            detected_language=stored_language,
            transcript_language=transcript_language,
            bucket=bucket,
            avg_segment_confidence=avg_conf,
            needs_review=bool(review_reasons),
            review_reasons=review_reasons,
        )


async def write_language_report(
    session: AsyncSession,
    output_path: Path,
    *,
    batch_id: UUID | None = None,
    call_ids: list[UUID] | None = None,
) -> LanguageAnalysisReport:
    use_case = LanguageAnalysisUseCase(session)
    report = await use_case.execute(batch_id=batch_id, call_ids=call_ids)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report

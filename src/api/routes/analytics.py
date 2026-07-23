from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.models import CallRecordingModel, IntentExtractionModel

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ConfidenceBucket(BaseModel):
    range: str
    count: int


class LanguageBreakdown(BaseModel):
    language: str
    count: int


class VolumeStats(BaseModel):
    total_calls: int
    by_status: dict[str, int]


class AnalyticsResponse(BaseModel):
    volume: VolumeStats
    confidence_distribution: list[ConfidenceBucket]
    language_breakdown: list[LanguageBreakdown]
    avg_confidence: float | None = None


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsResponse:
    total_result = await session.execute(select(func.count()).select_from(CallRecordingModel))
    total_calls = total_result.scalar() or 0

    status_result = await session.execute(
        select(CallRecordingModel.status, func.count()).group_by(CallRecordingModel.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    lang_result = await session.execute(
        select(CallRecordingModel.detected_language, func.count())
        .where(CallRecordingModel.detected_language.isnot(None))
        .group_by(CallRecordingModel.detected_language)
        .order_by(func.count().desc())
    )
    language_breakdown = [
        LanguageBreakdown(language=row[0] or "unknown", count=row[1])
        for row in lang_result.all()
    ]

    extraction_result = await session.execute(select(IntentExtractionModel.confidence))
    confidences = [row[0] for row in extraction_result.all()]

    buckets = [
        ("0.0-0.5", 0),
        ("0.5-0.7", 0),
        ("0.7-0.85", 0),
        ("0.85-1.0", 0),
    ]
    for conf in confidences:
        if conf < 0.5:
            buckets[0] = (buckets[0][0], buckets[0][1] + 1)
        elif conf < 0.7:
            buckets[1] = (buckets[1][0], buckets[1][1] + 1)
        elif conf < 0.85:
            buckets[2] = (buckets[2][0], buckets[2][1] + 1)
        else:
            buckets[3] = (buckets[3][0], buckets[3][1] + 1)

    avg_confidence = sum(confidences) / len(confidences) if confidences else None

    return AnalyticsResponse(
        volume=VolumeStats(total_calls=total_calls, by_status=by_status),
        confidence_distribution=[
            ConfidenceBucket(range=label, count=count) for label, count in buckets
        ],
        language_breakdown=language_breakdown,
        avg_confidence=avg_confidence,
    )

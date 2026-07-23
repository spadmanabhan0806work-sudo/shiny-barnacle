from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.models import (
    CallRecordingModel,
    IntentExtractionModel,
    ReviewQueueItemModel,
)
from src.infrastructure.persistence.repositories import (
    SqlAlchemyIntentExtractionRepository,
    SqlAlchemyReviewQueueRepository,
)
from src.api.middleware.audit import audit_extraction_change, audit_review_change

router = APIRouter(prefix="/reviews", tags=["reviews"])


class IntentSummary(BaseModel):
    id: UUID
    call_id: UUID
    side: str
    stock_symbol: str
    quantity: int
    price: float
    exchange: str
    confidence: float
    prompt_version: str
    llm_provider: str


class ReviewItemResponse(BaseModel):
    id: UUID
    extraction_id: UUID
    status: str
    corrected_fields: dict | None = None
    reviewer_id: str | None = None
    intent: IntentSummary | None = None


class ReviewListResponse(BaseModel):
    reviews: list[ReviewItemResponse]
    total: int


class ReviewUpdateRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|correct)$")
    reviewer_id: str = "operator"
    corrected_fields: dict | None = None


async def _build_review_response(
    session: AsyncSession,
    item_id: UUID,
) -> ReviewItemResponse | None:
    result = await session.execute(
        select(ReviewQueueItemModel).where(ReviewQueueItemModel.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None

    extraction_result = await session.execute(
        select(IntentExtractionModel).where(IntentExtractionModel.id == item.extraction_id)
    )
    extraction = extraction_result.scalar_one_or_none()

    intent = None
    if extraction:
        intent = IntentSummary(
            id=extraction.id,
            call_id=extraction.call_id,
            side=extraction.side,
            stock_symbol=extraction.stock_symbol,
            quantity=extraction.quantity,
            price=float(extraction.price),
            exchange=extraction.exchange,
            confidence=extraction.confidence,
            prompt_version=extraction.prompt_version,
            llm_provider=extraction.llm_provider,
        )

    return ReviewItemResponse(
        id=item.id,
        extraction_id=item.extraction_id,
        status=item.status,
        corrected_fields=item.corrected_fields,
        reviewer_id=item.reviewer_id,
        intent=intent,
    )


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    session: AsyncSession = Depends(get_db_session),
    status: str = "pending",
    limit: int = 100,
    offset: int = 0,
) -> ReviewListResponse:
    query = select(ReviewQueueItemModel).limit(limit).offset(offset)
    if status:
        query = query.where(ReviewQueueItemModel.status == status)
    result = await session.execute(query)
    items = result.scalars().all()

    reviews: list[ReviewItemResponse] = []
    for item in items:
        review = await _build_review_response(session, item.id)
        if review:
            reviews.append(review)

    return ReviewListResponse(reviews=reviews, total=len(reviews))


@router.patch("/{review_id}", response_model=ReviewItemResponse)
async def update_review(
    review_id: UUID,
    body: ReviewUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ReviewItemResponse:
    review_repo = SqlAlchemyReviewQueueRepository(session)
    intent_repo = SqlAlchemyIntentExtractionRepository(session)

    item = await review_repo.get_by_id(review_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Review not found: {review_id}")

    extraction = await intent_repo.get_by_id(item.extraction_id)
    if extraction is None:
        raise HTTPException(status_code=404, detail="Extraction not found for review")

    if body.action == "approve":
        item.approve(body.reviewer_id)
        await audit_review_change(
            session, request, review_id=review_id, action="approve",
            changes={"reviewer_id": body.reviewer_id},
        )
    elif body.action == "correct":
        if not body.corrected_fields:
            raise HTTPException(status_code=400, detail="corrected_fields required for correct action")
        item.correct(body.reviewer_id, body.corrected_fields)
        if "side" in body.corrected_fields:
            extraction.side = str(body.corrected_fields["side"]).upper()
        if "stock_symbol" in body.corrected_fields:
            extraction.stock_symbol = str(body.corrected_fields["stock_symbol"]).upper()
        if "quantity" in body.corrected_fields:
            extraction.quantity = int(body.corrected_fields["quantity"])
        if "price" in body.corrected_fields:
            extraction.price = float(body.corrected_fields["price"])
        if "exchange" in body.corrected_fields:
            extraction.exchange = str(body.corrected_fields["exchange"]).upper()
        await intent_repo.update(extraction)
        await audit_review_change(
            session, request, review_id=review_id, action="correct",
            changes=body.corrected_fields,
        )
        await audit_extraction_change(
            session, request, extraction_id=extraction.id, action="correct",
            changes=body.corrected_fields,
        )

    await review_repo.update(item)

    call_result = await session.execute(
        select(CallRecordingModel).where(CallRecordingModel.id == extraction.call_id)
    )
    call_model = call_result.scalar_one_or_none()
    if call_model and call_model.status == "review_required":
        call_model.status = "completed"
        await session.flush()

    response = await _build_review_response(session, review_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Review not found after update")
    return response

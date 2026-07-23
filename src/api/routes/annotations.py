from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases import CreateAnnotationUseCase, GetAnnotationUseCase
from src.domain.entities.annotation import Annotation
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import (
    SqlAlchemyAnnotationRepository,
    SqlAlchemyCallRecordingRepository,
)

router = APIRouter(prefix="/annotations", tags=["annotations"])


class GroundTruthDTO(BaseModel):
    side: str = Field(..., pattern="^(BUY|SELL)$")
    stock_symbol: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    exchange: str = Field(..., pattern="^(NSE|BSE)$")


class CreateAnnotationRequest(BaseModel):
    call_id: UUID
    annotator_id: str
    ground_truth: GroundTruthDTO


class AnnotationResponse(BaseModel):
    id: UUID
    call_id: UUID
    annotator_id: str
    ground_truth: GroundTruthDTO
    status: str

    @classmethod
    def from_entity(cls, annotation: Annotation) -> "AnnotationResponse":
        gt = annotation.ground_truth
        return cls(
            id=annotation.id,
            call_id=annotation.call_id,
            annotator_id=annotation.annotator_id,
            ground_truth=GroundTruthDTO(
                side=gt.side,
                stock_symbol=gt.stock_symbol,
                quantity=gt.quantity,
                price=gt.price,
                exchange=gt.exchange,
            ),
            status=annotation.status.value,
        )


@router.post("", response_model=AnnotationResponse, status_code=201)
async def create_annotation(
    request: CreateAnnotationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AnnotationResponse:
    use_case = CreateAnnotationUseCase(
        SqlAlchemyAnnotationRepository(session),
        SqlAlchemyCallRecordingRepository(session),
    )
    try:
        annotation = await use_case.execute(
            call_id=request.call_id,
            annotator_id=request.annotator_id,
            ground_truth=request.ground_truth.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnnotationResponse.from_entity(annotation)


@router.get("/{call_id}", response_model=AnnotationResponse)
async def get_annotation(
    call_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> AnnotationResponse:
    use_case = GetAnnotationUseCase(SqlAlchemyAnnotationRepository(session))
    annotation = await use_case.execute(call_id)
    if annotation is None:
        raise HTTPException(status_code=404, detail=f"Annotation not found for call {call_id}")
    return AnnotationResponse.from_entity(annotation)

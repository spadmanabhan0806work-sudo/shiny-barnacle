from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.run_evaluation import RunEvaluationUseCase
from src.domain.entities.evaluation_run import EvaluationRun
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import (
    SqlAlchemyAnnotationRepository,
    SqlAlchemyEvaluationRunRepository,
    SqlAlchemyIntentExtractionRepository,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


class RunEvaluationRequest(BaseModel):
    dataset_path: str | None = None
    use_db_annotations: bool = True
    prompt_version: str | None = None
    stt_provider: str | None = None
    llm_provider: str | None = None


class EvaluationRunResponse(BaseModel):
    id: UUID
    prompt_version: str
    stt_provider: str
    llm_provider: str
    aggregate_metrics: dict | None
    ran_at: str
    report_path: str | None = None

    @classmethod
    def from_entity(cls, run: EvaluationRun) -> "EvaluationRunResponse":
        return cls(
            id=run.id,
            prompt_version=run.prompt_version,
            stt_provider=run.stt_provider,
            llm_provider=run.llm_provider,
            aggregate_metrics=run.aggregate_metrics,
            ran_at=run.ran_at.isoformat(),
            report_path=f"eval/reports/output/{run.id}.html",
        )


class EvaluationListResponse(BaseModel):
    evaluations: list[EvaluationRunResponse]
    total: int


@router.post("", response_model=EvaluationRunResponse, status_code=201)
async def create_evaluation(
    body: RunEvaluationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> EvaluationRunResponse:
    settings = get_settings()
    use_case = RunEvaluationUseCase(
        SqlAlchemyEvaluationRunRepository(session),
        SqlAlchemyAnnotationRepository(session),
        SqlAlchemyIntentExtractionRepository(session),
        settings,
    )
    try:
        run = await use_case.execute(
            dataset_path=body.dataset_path,
            use_db_annotations=body.use_db_annotations,
            prompt_version=body.prompt_version,
            stt_provider=body.stt_provider,
            llm_provider=body.llm_provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EvaluationRunResponse.from_entity(run)


@router.get("/{evaluation_id}", response_model=EvaluationRunResponse)
async def get_evaluation(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> EvaluationRunResponse:
    repo = SqlAlchemyEvaluationRunRepository(session)
    run = await repo.get_by_id(evaluation_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Evaluation not found: {evaluation_id}")
    return EvaluationRunResponse.from_entity(run)


@router.get("", response_model=EvaluationListResponse)
async def list_evaluations(
    session: AsyncSession = Depends(get_db_session),
    limit: int = 100,
    offset: int = 0,
) -> EvaluationListResponse:
    repo = SqlAlchemyEvaluationRunRepository(session)
    runs = await repo.list_all(limit=limit, offset=offset)
    return EvaluationListResponse(
        evaluations=[EvaluationRunResponse.from_entity(r) for r in runs],
        total=len(runs),
    )

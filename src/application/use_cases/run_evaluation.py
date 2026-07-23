from __future__ import annotations

from pathlib import Path

from eval.runners.benchmark_runner import BenchmarkPair, BenchmarkRunner
from src.domain.entities.evaluation_run import EvaluationRun
from src.domain.repositories.annotation_repository import AnnotationRepository
from src.domain.repositories.evaluation_run_repository import EvaluationRunRepository
from src.domain.repositories.intent_extraction_repository import IntentExtractionRepository
from src.infrastructure.config.settings import Settings


class RunEvaluationUseCase:
    """Run benchmark comparing predictions against gold annotations."""

    def __init__(
        self,
        evaluation_repo: EvaluationRunRepository,
        annotation_repo: AnnotationRepository,
        intent_repo: IntentExtractionRepository,
        settings: Settings,
        reports_dir: Path | None = None,
    ) -> None:
        self._evaluation_repo = evaluation_repo
        self._annotation_repo = annotation_repo
        self._intent_repo = intent_repo
        self._settings = settings
        self._runner = BenchmarkRunner(reports_dir=reports_dir)

    async def execute(
        self,
        *,
        dataset_path: str | None = None,
        use_db_annotations: bool = True,
        prompt_version: str | None = None,
        stt_provider: str | None = None,
        llm_provider: str | None = None,
    ) -> EvaluationRun:
        prompt_version = prompt_version or self._settings.get(
            "prompts.active_version", "v1.0.0"
        )
        stt_provider = stt_provider or self._settings.stt_provider
        llm_provider = llm_provider or self._settings.llm_provider

        if dataset_path:
            result = self._runner.run_from_dataset(
                Path(dataset_path),
                prompt_version=prompt_version,
                stt_provider=stt_provider,
                llm_provider=llm_provider,
            )
        elif use_db_annotations:
            pairs = await self._pairs_from_db()
            if not pairs:
                raise ValueError("No annotation/extraction pairs found in database")
            result = self._runner.run_from_pairs(
                pairs,
                dataset_name="db_annotations",
                prompt_version=prompt_version,
                stt_provider=stt_provider,
                llm_provider=llm_provider,
            )
        else:
            raise ValueError("Provide dataset_path or enable use_db_annotations")

        run = EvaluationRun(
            id=result.run_id,
            prompt_version=prompt_version,
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            aggregate_metrics=result.to_dict()["aggregate_metrics"],
            ran_at=result.ran_at,
        )
        return await self._evaluation_repo.create(run)

    async def _pairs_from_db(self) -> list[BenchmarkPair]:
        pairs: list[BenchmarkPair] = []
        annotations = await self._annotation_repo.list_all()
        for annotation in annotations:
            extraction = await self._intent_repo.get_by_call_id(annotation.call_id)
            if extraction is None:
                continue
            pairs.append(
                BenchmarkPair(
                    call_id=annotation.call_id,
                    ground_truth={
                        "side": annotation.ground_truth.side,
                        "stock_symbol": annotation.ground_truth.stock_symbol,
                        "quantity": annotation.ground_truth.quantity,
                        "price": annotation.ground_truth.price,
                        "exchange": annotation.ground_truth.exchange,
                    },
                    prediction={
                        "side": extraction.side,
                        "stock_symbol": extraction.stock_symbol,
                        "quantity": extraction.quantity,
                        "price": float(extraction.price),
                        "exchange": extraction.exchange,
                    },
                )
            )
        return pairs

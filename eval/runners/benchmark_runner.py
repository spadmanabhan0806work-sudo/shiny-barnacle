from __future__ import annotations

from pathlib import Path
from uuid import UUID

from eval.datasets.loader import GoldDataset
from eval.metrics.field_scorers import FIELD_NAMES, compare_fields, score_all_fields
from eval.reports.html_report import write_html_report
from eval.runners.models import BenchmarkPair, BenchmarkResult


def load_gold_dataset(path: Path) -> GoldDataset:
    return GoldDataset.from_path(path)


class BenchmarkRunner:
    """Compare predictions against gold annotations and compute field metrics."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self._reports_dir = reports_dir or Path("eval/reports/output")

    def run_from_pairs(
        self,
        pairs: list[BenchmarkPair],
        *,
        dataset_name: str,
        prompt_version: str,
        stt_provider: str,
        llm_provider: str,
        run_id: UUID | None = None,
        write_report: bool = True,
    ) -> BenchmarkResult:
        from uuid import uuid4

        scored_pairs = [(p.ground_truth, p.prediction) for p in pairs]
        field_metrics = score_all_fields(scored_pairs)

        per_call = []
        all_fields_correct = 0
        for pair in pairs:
            comparison = compare_fields(pair.ground_truth, pair.prediction)
            if all(comparison.matches.values()):
                all_fields_correct += 1
            per_call.append(
                {
                    "call_id": str(pair.call_id) if pair.call_id else None,
                    "ground_truth": pair.ground_truth,
                    "prediction": pair.prediction,
                    "matches": comparison.matches,
                }
            )

        total = len(pairs)
        summary = {
            "total": total,
            "matched_all_fields": all_fields_correct,
            "macro_accuracy": sum(m.accuracy for m in field_metrics.values()) / len(FIELD_NAMES)
            if FIELD_NAMES
            else 0.0,
        }

        result = BenchmarkResult(
            run_id=run_id or uuid4(),
            dataset_name=dataset_name,
            prompt_version=prompt_version,
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            field_metrics=field_metrics,
            per_call=per_call,
            summary=summary,
        )

        if write_report:
            self._reports_dir.mkdir(parents=True, exist_ok=True)
            write_html_report(result, self._reports_dir / f"{result.run_id}.html")

        return result

    def run_from_dataset(
        self,
        dataset_path: Path,
        *,
        prompt_version: str,
        stt_provider: str,
        llm_provider: str,
        run_id: UUID | None = None,
    ) -> BenchmarkResult:
        dataset = load_gold_dataset(dataset_path)
        pairs = []
        for entry in dataset.entries:
            if entry.prediction is None:
                raise ValueError(
                    f"Dataset entry {entry.call_id} missing prediction; "
                    "use run_from_db_pairs for live extractions."
                )
            pairs.append(
                BenchmarkPair(
                    call_id=entry.call_id,
                    ground_truth=entry.ground_truth,
                    prediction=entry.prediction,
                )
            )
        return self.run_from_pairs(
            pairs,
            dataset_name=dataset.name,
            prompt_version=prompt_version,
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            run_id=run_id,
        )

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass
class BenchmarkPair:
    call_id: UUID | None
    ground_truth: dict
    prediction: dict


@dataclass
class BenchmarkResult:
    run_id: UUID
    dataset_name: str
    prompt_version: str
    stt_provider: str
    llm_provider: str
    field_metrics: dict
    per_call: list[dict]
    summary: dict
    ran_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "id": str(self.run_id),
            "dataset_name": self.dataset_name,
            "prompt_version": self.prompt_version,
            "stt_provider": self.stt_provider,
            "llm_provider": self.llm_provider,
            "aggregate_metrics": {
                "fields": {
                    name: {
                        "accuracy": m.accuracy,
                        "precision": m.precision,
                        "recall": m.recall,
                        "f1": m.f1,
                        "correct": m.correct,
                        "total": m.total,
                    }
                    for name, m in self.field_metrics.items()
                },
                "per_call": self.per_call,
                "summary": self.summary,
            },
            "ran_at": self.ran_at.isoformat(),
        }

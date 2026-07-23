from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class EvaluationRun:
    prompt_version: str
    stt_provider: str
    llm_provider: str
    aggregate_metrics: dict | None = None
    id: UUID = field(default_factory=uuid4)
    ran_at: datetime = field(default_factory=lambda: datetime.now(UTC))

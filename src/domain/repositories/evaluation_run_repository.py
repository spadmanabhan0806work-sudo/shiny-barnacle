from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.evaluation_run import EvaluationRun


class EvaluationRunRepository(ABC):
    @abstractmethod
    async def create(self, run: EvaluationRun) -> EvaluationRun:
        ...

    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> EvaluationRun | None:
        ...

    @abstractmethod
    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[EvaluationRun]:
        ...

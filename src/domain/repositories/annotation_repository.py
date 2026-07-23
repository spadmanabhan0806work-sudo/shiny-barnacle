from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.annotation import Annotation


class AnnotationRepository(ABC):
    @abstractmethod
    async def create(self, annotation: Annotation) -> Annotation:
        ...

    @abstractmethod
    async def get_by_call_id(self, call_id: UUID) -> Annotation | None:
        ...

    @abstractmethod
    async def update(self, annotation: Annotation) -> Annotation:
        ...

    @abstractmethod
    async def list_all(self, *, limit: int = 1000, offset: int = 0) -> list[Annotation]:
        ...

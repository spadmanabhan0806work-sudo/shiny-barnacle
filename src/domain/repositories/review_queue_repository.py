from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.review_queue_item import ReviewQueueItem


class ReviewQueueRepository(ABC):
    @abstractmethod
    async def create(self, item: ReviewQueueItem) -> ReviewQueueItem:
        ...

    @abstractmethod
    async def get_by_id(self, item_id: UUID) -> ReviewQueueItem | None:
        ...

    @abstractmethod
    async def get_by_extraction_id(self, extraction_id: UUID) -> ReviewQueueItem | None:
        ...

    @abstractmethod
    async def list_pending(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewQueueItem]:
        ...

    @abstractmethod
    async def update(self, item: ReviewQueueItem) -> ReviewQueueItem:
        ...

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.intent_extraction import IntentExtraction


class IntentExtractionRepository(ABC):
    @abstractmethod
    async def create(self, extraction: IntentExtraction) -> IntentExtraction:
        ...

    @abstractmethod
    async def get_by_call_id(self, call_id: UUID) -> IntentExtraction | None:
        ...

    @abstractmethod
    async def get_by_id(self, extraction_id: UUID) -> IntentExtraction | None:
        ...

    @abstractmethod
    async def update(self, extraction: IntentExtraction) -> IntentExtraction:
        ...

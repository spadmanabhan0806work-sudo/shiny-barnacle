from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.transcript import Transcript


class TranscriptRepository(ABC):
    @abstractmethod
    async def create(self, transcript: Transcript) -> Transcript:
        ...

    @abstractmethod
    async def get_by_call_id(self, call_id: UUID) -> Transcript | None:
        ...

    @abstractmethod
    async def update(self, transcript: Transcript) -> Transcript:
        ...

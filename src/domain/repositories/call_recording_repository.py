from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.call_recording import CallRecording, CallStatus


class CallRecordingRepository(ABC):
    @abstractmethod
    async def create(self, recording: CallRecording) -> CallRecording:
        ...

    @abstractmethod
    async def get_by_id(self, call_id: UUID) -> CallRecording | None:
        ...

    @abstractmethod
    async def list_all(
        self,
        *,
        status: CallStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CallRecording]:
        ...

    @abstractmethod
    async def update(self, recording: CallRecording) -> CallRecording:
        ...

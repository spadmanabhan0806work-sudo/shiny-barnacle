from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BatchUpload:
    id: uuid.UUID
    tenant_id: str
    call_ids: list[uuid.UUID]
    created_at: datetime | None = None


class BatchUploadRepository(ABC):
    @abstractmethod
    async def create(self, *, tenant_id: str, call_ids: list[uuid.UUID]) -> BatchUpload:
        ...

    @abstractmethod
    async def get_by_id(self, batch_id: uuid.UUID) -> BatchUpload | None:
        ...

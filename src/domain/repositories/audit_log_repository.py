from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AuditLogEntry:
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    actor_id: str
    changes: dict[str, Any] | None
    created_at: datetime | None = None


class AuditLogRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_id: str,
        changes: dict | None = None,
    ) -> AuditLogEntry:
        ...

from __future__ import annotations

import uuid
from typing import Any

from src.domain.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, audit_repo: AuditLogRepository) -> None:
        self._audit_repo = audit_repo

    async def log(
        self,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_id: str = "system",
        changes: dict[str, Any] | None = None,
    ) -> None:
        await self._audit_repo.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            changes=changes,
        )

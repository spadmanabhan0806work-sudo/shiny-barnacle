from __future__ import annotations

from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.audit_service import AuditService
from src.infrastructure.persistence.repositories import SqlAlchemyAuditLogRepository


async def audit_review_change(
    session: AsyncSession,
    request: Request,
    *,
    review_id: UUID,
    action: str,
    changes: dict | None = None,
) -> None:
    user = getattr(request.state, "user", None)
    actor_id = user.user_id if user else "system"
    audit = AuditService(SqlAlchemyAuditLogRepository(session))
    await audit.log(
        entity_type="review",
        entity_id=review_id,
        action=action,
        actor_id=actor_id,
        changes=changes,
    )


async def audit_extraction_change(
    session: AsyncSession,
    request: Request,
    *,
    extraction_id: UUID,
    action: str,
    changes: dict | None = None,
) -> None:
    user = getattr(request.state, "user", None)
    actor_id = user.user_id if user else "system"
    audit = AuditService(SqlAlchemyAuditLogRepository(session))
    await audit.log(
        entity_type="extraction",
        entity_id=extraction_id,
        action=action,
        actor_id=actor_id,
        changes=changes,
    )

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from src.infrastructure.persistence.database import get_session_factory

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    """Readiness probe — checks PostgreSQL connectivity."""
    from fastapi.responses import JSONResponse

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "checks": {"database": "ok"}}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": {"database": f"error: {exc}"}},
        )

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.export_results import ExportResultsUseCase
from src.infrastructure.persistence.database import get_db_session

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{batch_id}")
async def export_batch(
    batch_id: UUID,
    format: str = Query("json", pattern="^(json|xlsx|excel)$"),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    use_case = ExportResultsUseCase(session)

    try:
        if format in ("xlsx", "excel"):
            content, filename = await use_case.export_excel(batch_id)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            content, filename = await use_case.export_json(batch_id)
            media_type = "application/json"
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

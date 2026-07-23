from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import Role
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.models import PromptVersionModel
from src.infrastructure.prompts.prompt_registry import PromptRegistry

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptVersionResponse(BaseModel):
    version: str
    module: str
    system_prompt_hash: str
    is_active: bool
    ab_weight: float


class PromptListResponse(BaseModel):
    prompts: list[PromptVersionResponse]
    active_version: str


class PromptWeightUpdate(BaseModel):
    version: str
    ab_weight: float = Field(ge=0.0, le=1.0)


class SetActivePromptRequest(BaseModel):
    active_version: str | None = None
    weights: list[PromptWeightUpdate] | None = None


def _get_registry() -> PromptRegistry:
    settings = get_settings()
    base_path = Path(settings.get("prompts.base_path", "./prompts"))
    manifest_path = Path(settings.get("prompts.manifest_path", "./prompts/manifest.yaml"))
    return PromptRegistry(base_path, manifest_path)


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    session: AsyncSession = Depends(get_db_session),
) -> PromptListResponse:
    registry = _get_registry()
    active = registry.get_active_version()

    result = await session.execute(select(PromptVersionModel))
    db_versions = {m.version: m for m in result.scalars().all()}

    prompts: list[PromptVersionResponse] = []
    for version in registry.list_versions():
        bundle = registry.load(version)
        db_row = db_versions.get(version)
        prompts.append(
            PromptVersionResponse(
                version=version,
                module=bundle.module,
                system_prompt_hash=bundle.system_hash,
                is_active=db_row.is_active if db_row else version == active,
                ab_weight=db_row.ab_weight if db_row else registry.get_weight(version),
            )
        )

    return PromptListResponse(prompts=prompts, active_version=active)


@router.patch("/active", response_model=PromptListResponse)
async def set_active_prompt(
    body: SetActivePromptRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> PromptListResponse:
    user = getattr(request.state, "user", None)
    if user and not user.has_role(Role.ADMIN):
        raise HTTPException(status_code=403, detail="Requires admin role")

    registry = _get_registry()

    if body.active_version:
        registry.set_active_version(body.active_version)

    if body.weights:
        weight_map = {w.version: w.ab_weight for w in body.weights}
        registry.update_weights(weight_map)

    active = registry.get_active_version()
    manifest = registry.get_manifest()

    for version, meta in manifest.get("versions", {}).items():
        result = await session.execute(
            select(PromptVersionModel).where(PromptVersionModel.version == version)
        )
        row = result.scalar_one_or_none()
        if row is None:
            bundle = registry.load(version)
            row = PromptVersionModel(
                version=version,
                module=manifest.get("module", "call_to_trade"),
                system_prompt_hash=bundle.system_hash,
                is_active=version == active,
                ab_weight=meta.get("weight", 0.0),
            )
            session.add(row)
        else:
            row.is_active = version == active
            row.ab_weight = meta.get("weight", row.ab_weight)
            row.system_prompt_hash = registry.load(version).system_hash

    await session.flush()
    return await list_prompts(session)

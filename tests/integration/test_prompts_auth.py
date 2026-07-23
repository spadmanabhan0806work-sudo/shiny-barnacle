import base64
import json
import os
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.api.middleware.auth import Role, _decode_stub_token, _role_from_claims
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import get_db_session


def _make_token(payload: dict) -> str:
    raw = json.dumps(payload).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def test_decode_stub_token():
    token = _make_token({"sub": "user-1", "roles": ["reviewer"]})
    claims = _decode_stub_token(token)
    assert claims is not None
    assert claims["sub"] == "user-1"


def test_role_from_claims_admin():
    assert _role_from_claims({"roles": ["admin"]}) == Role.ADMIN


def test_role_from_claims_reviewer():
    assert _role_from_claims({"roles": ["reviewer"]}) == Role.REVIEWER


@pytest.mark.asyncio
async def test_auth_blocks_without_token(test_engine):
    get_settings.cache_clear()
    with patch.dict(os.environ, {"AUTH_ENABLED": "true"}):
        get_settings.cache_clear()
        factory = __import__(
            "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
        ).async_sessionmaker(test_engine, expire_on_commit=False)

        async def override_get_db():
            async with factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db_session] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/prompts")
            assert response.status_code == 401

        app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_auth_allows_admin_for_prompts(test_engine):
    get_settings.cache_clear()
    admin_token = _make_token({"sub": "admin-1", "roles": ["admin"]})
    with patch.dict(os.environ, {"AUTH_ENABLED": "true"}):
        get_settings.cache_clear()
        factory = __import__(
            "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
        ).async_sessionmaker(test_engine, expire_on_commit=False)

        async def override_get_db():
            async with factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db_session] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/prompts",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200

        app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_auth_denies_annotator_for_prompts(test_engine):
    get_settings.cache_clear()
    token = _make_token({"sub": "user-1", "roles": ["annotator"]})
    with patch.dict(os.environ, {"AUTH_ENABLED": "true"}):
        get_settings.cache_clear()
        factory = __import__(
            "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
        ).async_sessionmaker(test_engine, expire_on_commit=False)

        async def override_get_db():
            async with factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db_session] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/prompts",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 403

        app.dependency_overrides.clear()
    get_settings.cache_clear()

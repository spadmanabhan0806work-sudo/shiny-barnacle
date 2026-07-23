from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.models import Base


def _sqlite_compat(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()


@pytest.fixture(autouse=True)
def mock_inline_processing():
    """PoC processes calls in-process; mock pipeline during API integration tests."""
    with patch("src.api.routes.calls._process_calls_inline", new_callable=AsyncMock):
        yield


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    event.listen(Base.metadata, "before_create", _sqlite_compat)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    event.remove(Base.metadata, "before_create", _sqlite_compat)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
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
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def call_id(client: AsyncClient) -> uuid.UUID:
    """Upload a test audio file and return the call ID."""
    audio_data = b"RIFF" + b"\x00" * 40
    response = await client.post(
        "/api/v1/calls",
        files={"file": ("test.wav", audio_data, "audio/wav")},
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])

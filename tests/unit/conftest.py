from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import JSON, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.persistence.models import Base


def _sqlite_compat(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()


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

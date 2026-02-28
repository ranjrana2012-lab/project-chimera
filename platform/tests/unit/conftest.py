"""Pytest configuration and fixtures for unit tests."""
import sys
from pathlib import Path
import asyncio
from typing import AsyncGenerator, Generator

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from shared.models import Base
from shared.config import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_engine():
    """Create an async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Create a database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        max_workers=4,
        test_timeout_seconds=60
    )


@pytest.fixture
def redis_client(monkeypatch):
    """Provide a mock Redis client for testing.

    This fixture returns a mock Redis client that can be used in unit tests
    without requiring an actual Redis instance to be running. The mock provides
    basic Redis-like interface methods commonly used in the codebase.

    For integration tests that require real Redis, use a separate fixture
    or configure accordingly.
    """
    from unittest.mock import MagicMock, AsyncMock

    # Create a mock Redis client
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.close = AsyncMock(return_value=None)

    # Make it async context manager compatible
    async def mock_context():
        yield mock_redis

    mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
    mock_redis.__aexit__ = AsyncMock(return_value=None)

    return mock_redis

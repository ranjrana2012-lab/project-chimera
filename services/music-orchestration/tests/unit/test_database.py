import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from music_orchestration.database import get_engine, Base


@pytest.mark.asyncio
async def test_database_connection():
    """Test that database connection can be established"""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute("SELECT 1")
        assert result.scalar() == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_tables_can_be_created():
    """Test that all tables can be created without errors"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

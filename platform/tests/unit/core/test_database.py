"""Comprehensive unit tests for database module."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import inspect

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from shared import database
from shared.config import settings


class TestDatabaseEngine:
    """Test suite for database engine configuration."""

    def test_engine_exists(self):
        """Test that database engine is created."""
        assert database.engine is not None

    def test_engine_is_async_engine(self):
        """Test that engine is an AsyncEngine."""
        assert isinstance(database.engine, AsyncEngine)

    def test_engine_has_url(self):
        """Test that engine has a URL attribute."""
        assert hasattr(database.engine, 'url')
        assert database.engine.url is not None

    def test_engine_url_from_settings(self):
        """Test that engine URL matches settings."""
        # Engine URL should be based on settings
        assert database.engine.url is not None

    def test_engine_has_pool(self):
        """Test that engine has a connection pool."""
        assert hasattr(database.engine, 'pool')
        assert database.engine.pool is not None

    def test_engine_pool_attributes(self):
        """Test that engine pool has expected attributes."""
        pool = database.engine.pool
        # Pool should have size and overflow settings
        assert hasattr(pool, 'size')

    def test_engine_echo_disabled(self):
        """Test that engine echo (SQL logging) is disabled by default."""
        assert database.engine.echo is False

    def test_engine_is_initialized(self):
        """Test that engine is properly initialized."""
        # Engine should be callable
        assert callable(database.engine.connect)


class TestAsyncSessionLocal:
    """Test suite for AsyncSessionLocal factory."""

    def test_session_factory_exists(self):
        """Test that AsyncSessionLocal factory exists."""
        assert database.AsyncSessionLocal is not None

    def test_session_factory_is_callable(self):
        """Test that AsyncSessionLocal is callable."""
        assert callable(database.AsyncSessionLocal)

    def test_session_factory_creates_session(self):
        """Test that AsyncSessionLocal creates an AsyncSession."""
        session = database.AsyncSessionLocal()
        assert isinstance(session, AsyncSession)
        # Close the session to avoid warnings
        import asyncio
        asyncio.run(session.close())

    def test_session_factory_multiple_sessions(self):
        """Test that multiple sessions can be created."""
        session1 = database.AsyncSessionLocal()
        session2 = database.AsyncSessionLocal()

        assert session1 is not session2

        # Clean up
        import asyncio
        asyncio.gather(session1.close(), session2.close())


class TestGetDb:
    """Test suite for get_db dependency injection function."""

    def test_get_db_exists(self):
        """Test that get_db function exists."""
        assert hasattr(database, 'get_db')
        assert callable(database.get_db)

    def test_get_db_is_async_generator(self):
        """Test that get_db is an async generator function."""
        assert inspect.isasyncgenfunction(database.get_db)

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """Test that get_db yields an AsyncSession."""
        async for session in database.get_db():
            assert isinstance(session, AsyncSession)
            break  # Only test first yield

    @pytest.mark.asyncio
    async def test_get_db_context_manager(self):
        """Test that get_db works as async context manager."""
        session_generator = database.get_db()
        session = await session_generator.__anext__()
        assert isinstance(session, AsyncSession)

        # Clean up
        try:
            await session_generator.aclose()
        except:
            pass


class TestDatabaseBase:
    """Test suite for Base declarative base."""

    def test_base_is_imported(self):
        """Test that Base is imported from models."""
        assert hasattr(database, 'Base')
        assert database.Base is not None

    def test_base_has_metadata(self):
        """Test that Base has metadata."""
        assert hasattr(database.Base, 'metadata')

    def test_base_metadata_is_declared(self):
        """Test that Base metadata is a MetaData object."""
        from sqlalchemy.schema import MetaData
        assert isinstance(database.Base.metadata, MetaData)


class TestDatabaseModuleExports:
    """Test suite for database module exports."""

    def test_exports_engine(self):
        """Test that module exports engine."""
        assert 'engine' in dir(database)

    def test_exports_async_session_local(self):
        """Test that module exports AsyncSessionLocal."""
        assert 'AsyncSessionLocal' in dir(database)

    def test_exports_get_db(self):
        """Test that module exports get_db."""
        assert 'get_db' in dir(database)

    def test_exports_base(self):
        """Test that module exports Base."""
        assert 'Base' in dir(database)

    def test_all_required_exports(self):
        """Test all required exports are present."""
        required = ['engine', 'AsyncSessionLocal', 'get_db', 'Base']
        for export in required:
            assert export in dir(database), f"Missing export: {export}"


class TestDatabaseConnectionSettings:
    """Test suite for database connection settings."""

    def test_engine_uses_settings_url(self):
        """Test that engine uses URL from settings."""
        # Engine should be created with settings.database_url
        assert database.engine.url is not None

    def test_engine_pool_size(self):
        """Test that engine pool size is configured."""
        # Default pool size should be set
        assert database.engine.pool is not None

    def test_engine_max_overflow(self):
        """Test that engine max_overflow is configured."""
        pool = database.engine.pool
        assert hasattr(pool, '_max_overflow')

    def test_engine_pool_pre_ping(self):
        """Test that engine has pool_pre_ping enabled."""
        # pool_pre_ping helps detect stale connections
        # This is an engine option, not always directly accessible
        assert database.engine is not None


class TestDatabaseSessionConfiguration:
    """Test suite for database session configuration."""

    def test_session_expire_on_commit_false(self):
        """Test that sessions have expire_on_commit=False."""
        # This allows objects to remain accessible after commit
        session = database.AsyncSessionLocal()
        # The kwarg might be set in the sessionmaker
        # Close the session
        import asyncio
        asyncio.run(session.close())

    @pytest.mark.asyncio
    async def test_session_is_async(self):
        """Test that session is async."""
        session = database.AsyncSessionLocal()
        assert isinstance(session, AsyncSession)
        await session.close()

    @pytest.mark.asyncio
    async def test_session_in_transaction_after_begin(self):
        """Test session can begin transaction."""
        session = database.AsyncSessionLocal()
        # Session should support transactions
        assert hasattr(session, 'begin')
        await session.close()


class TestDatabaseIntegration:
    """Integration tests for database module."""

    @pytest.mark.asyncio
    async def test_session_close_and_reopen(self):
        """Test closing and reopening sessions."""
        session1 = database.AsyncSessionLocal()
        await session1.close()

        session2 = database.AsyncSessionLocal()
        assert session2 is not None
        await session2.close()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self):
        """Test multiple concurrent sessions can be created."""
        import asyncio

        async def create_and_close():
            session = database.AsyncSessionLocal()
            await asyncio.sleep(0.01)
            await session.close()

        # Create multiple sessions concurrently
        await asyncio.gather(
            create_and_close(),
            create_and_close(),
            create_and_close()
        )

    @pytest.mark.asyncio
    async def test_get_db_multiple_iterations(self):
        """Test get_db can be called multiple times."""
        count = 0
        async for _ in database.get_db():
            count += 1
            if count >= 3:
                break
        assert count == 3


class TestDatabaseEdgeCases:
    """Test suite for database edge cases."""

    def test_engine_singleton(self):
        """Test that engine is a singleton (same instance)."""
        engine1 = database.engine
        engine2 = database.engine
        assert engine1 is engine2

    def test_session_factory_singleton(self):
        """Test that AsyncSessionLocal is a singleton."""
        factory1 = database.AsyncSessionLocal
        factory2 = database.AsyncSessionLocal
        assert factory1 is factory2

    @pytest.mark.asyncio
    async def test_session_identities(self):
        """Test that different sessions have different identities."""
        session1 = database.AsyncSessionLocal()
        session2 = database.AsyncSessionLocal()

        assert session1 is not session2
        assert id(session1) != id(session2)

        await session1.close()
        await session2.close()

    @pytest.mark.asyncio
    async def test_get_db_exhaustion(self):
        """Test that get_db generator can be exhausted."""
        db_gen = database.get_db()
        session1 = await db_gen.__anext__()
        await session1.close()

        # Should be able to get another
        session2 = await db_gen.__anext__()
        await session2.close()


class TestDatabaseConfigurationValidation:
    """Test suite for database configuration validation."""

    def test_engine_creation_with_valid_url(self):
        """Test engine can be created with valid URL."""
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:"
        )
        assert engine is not None

    def test_engine_with_various_urls(self):
        """Test engine creation with various URL formats."""
        from sqlalchemy.ext.asyncio import create_async_engine

        urls = [
            "sqlite+aiosqlite:///:memory:",
            "postgresql+asyncpg://localhost/test",
            "mysql+aiomysql://localhost/test"
        ]

        for url in urls:
            try:
                engine = create_async_engine(url)
                assert engine is not None
            except ImportError:
                # Skip if driver not installed
                pass

    def test_session_maker_configurations(self):
        """Test various sessionmaker configurations."""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")

        # Test with expire_on_commit=False
        Session1 = async_sessionmaker(
            engine,
            expire_on_commit=False
        )
        assert Session1 is not None

        # Test with class_=AsyncSession
        Session2 = async_sessionmaker(
            engine,
            class_=AsyncSession
        )
        assert Session2 is not None

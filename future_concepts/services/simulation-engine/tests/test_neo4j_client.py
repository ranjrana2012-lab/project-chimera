"""
Tests for Neo4jClient using mocking to work without actual Neo4j installation.

These tests use mocking to test the Neo4jClient without requiring
a running Neo4j instance or the neo4j Python package.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_neo4j_client_init_raises_without_neo4j():
    """Test that Neo4jClient raises RuntimeError when neo4j module not available."""
    # Mock sys.modules to make neo4j unavailable
    with patch.dict('sys.modules', {'neo4j': None}):
        # Force reimport of the module
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="neo4j module is not available"):
            Neo4jClient("bolt://localhost:7687", "neo4j", "password")


@pytest.mark.asyncio
async def test_neo4j_client_init_with_mock_neo4j():
    """Test Neo4jClient initialization with mocked neo4j module."""
    # Create a mock AsyncGraphDatabase
    mock_db = MagicMock()
    mock_db.AsyncGraphDatabase = MagicMock()
    mock_driver = MagicMock()
    mock_db.AsyncGraphDatabase.driver.return_value = mock_driver

    # Patch the neo4j module
    with patch.dict('sys.modules', {'neo4j': mock_db}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        # Should not raise
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        assert client is not None


@pytest.mark.asyncio
async def test_neo4j_client_create_entity():
    """Test create_entity method with mocked driver."""
    from graph.models import Entity, EntityType

    # Mock the entire neo4j module
    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = AsyncMock()

    # Setup async context manager for session
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = AsyncMock()
    mock_driver.session.return_value = mock_session_context
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        # Create test entity
        entity = Entity(
            id="test_entity",
            type=EntityType.ORGANIZATION,
            attributes={"name": "Test Org"},
            valid_at=datetime.now(timezone.utc)
        )

        # This should not raise
        await client.create_entity(entity)

        # Verify the session was used
        assert mock_driver.session.called
        assert mock_session.run.called


@pytest.mark.asyncio
async def test_neo4j_client_create_relationship():
    """Test create_relationship method with mocked driver."""
    from graph.models import Relationship, RelationType

    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = AsyncMock()
    mock_driver.session.return_value = mock_session_context
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        relationship = Relationship(
            source="entity1",
            target="entity2",
            type=RelationType.KNOWS,
            attributes={"since": "2020"},
            valid_at=datetime.now(timezone.utc)
        )

        await client.create_relationship(relationship)

        assert mock_session.run.called


@pytest.mark.asyncio
async def test_neo4j_client_get_entity_found():
    """Test get_entity when entity exists."""
    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = AsyncMock()
    mock_driver.session.return_value = mock_session_context

    # Create a test entity dict directly
    test_entity_dict = {"id": "test_id", "type": "person", "name": "Test"}

    # Create a mock record that returns the dict when dict(record["e"]) is called
    # Since record["e"] should return something that can be converted to dict,
    # we'll make record["e"] return a plain dict
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: test_entity_dict

    mock_result = AsyncMock()
    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        result = await client.get_entity("test_id")

        assert result is not None
        assert result["id"] == "test_id"
        assert result["type"] == "person"


@pytest.mark.asyncio
async def test_neo4j_client_get_entity_not_found():
    """Test get_entity when entity doesn't exist."""
    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = AsyncMock()
    mock_driver.session.return_value = mock_session_context

    # Mock result with None
    mock_result = AsyncMock()
    mock_result.single.return_value = None
    mock_session.run.return_value = mock_result
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        result = await client.get_entity("nonexistent")

        assert result is None


@pytest.mark.asyncio
async def test_neo4j_client_query_related():
    """Test query_related method."""
    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = AsyncMock()
    mock_driver.session.return_value = mock_session_context

    # Mock result with related entities
    mock_result = AsyncMock()
    mock_result.data.return_value = [
        {"related": {"id": "related1"}},
        {"related": {"id": "related2"}}
    ]
    mock_session.run.return_value = mock_result
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        result = await client.query_related("test_id", depth=2)

        assert len(result) == 2
        assert result[0]["id"] == "related1"


@pytest.mark.asyncio
async def test_neo4j_client_clear_all():
    """Test clear_all method."""
    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = AsyncMock()
    mock_driver.session.return_value = mock_session_context
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        await client.clear_all()

        assert mock_session.run.called


@pytest.mark.asyncio
async def test_neo4j_client_close():
    """Test close method."""
    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_driver = AsyncMock()
    mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver

    with patch.dict('sys.modules', {'neo4j': mock_neo4j}):
        import importlib
        import graph.neo4j_client
        importlib.reload(graph.neo4j_client)

        from graph.neo4j_client import Neo4jClient

        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

        await client.close()

        # Verify driver.close was called
        assert mock_driver.close.called

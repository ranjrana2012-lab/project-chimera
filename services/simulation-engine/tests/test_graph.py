import pytest
from datetime import datetime

# Try to import graph components, skip if dependencies unavailable
try:
    from graph.neo4j_client import Neo4jClient
    from graph.builder import GraphBuilder
    from graph.models import Entity, EntityType
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False


@pytest.fixture
async def neo4j_client():
    """Create a test Neo4j client - skip if Neo4j unavailable."""
    import os

    if not GRAPH_AVAILABLE:
        pytest.skip("Graph dependencies not available")

    # Skip test if Neo4j not available
    if not os.getenv("NEO4J_AVAILABLE"):
        pytest.skip("Neo4j not available for testing")

    uri = os.getenv("TEST_GRAPH_DB_URL", "bolt://localhost:7687")
    user = os.getenv("TEST_GRAPH_DB_USER", "neo4j")
    password = os.getenv("TEST_GRAPH_DB_PASSWORD", "password")

    client = Neo4jClient(uri, user, password)
    await client.clear_all()

    yield client

    await client.clear_all()
    await client.close()


@pytest.mark.asyncio
async def test_create_entity(neo4j_client):
    """Test creating an entity in the graph."""
    if not GRAPH_AVAILABLE:
        pytest.skip("Graph dependencies not available")

    entity = Entity(
        id="test_entity_1",
        type=EntityType.PERSON,
        attributes={"name": "Alice", "role": "test_subject"},
        valid_at=datetime.utcnow()
    )

    await neo4j_client.create_entity(entity)

    retrieved = await neo4j_client.get_entity("test_entity_1")
    assert retrieved is not None
    assert retrieved["id"] == "test_entity_1"
    assert retrieved["type"] == "person"


@pytest.mark.asyncio
async def test_graph_builder(neo4j_client):
    """Test building a graph from documents."""
    if not GRAPH_AVAILABLE:
        pytest.skip("Graph dependencies not available")

    builder = GraphBuilder(neo4j_client)

    documents = [
        "Alice and Bob discussed the new policy.",
        "The policy affects many organizations."
    ]

    result = await builder.build_from_documents(documents)

    assert result["entities"] > 0
    assert result["relationships"] >= 0


@pytest.mark.asyncio
async def test_llm_entity_extraction():
    """Test LLM-based entity extraction."""
    if not GRAPH_AVAILABLE:
        pytest.skip("Graph dependencies not available")

    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()
    text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
    entities = await extractor.extract_entities(text)

    assert len(entities) > 0
    assert any(e.type == EntityType.ORGANIZATION for e in entities)


@pytest.mark.asyncio
async def test_temporal_fact_extraction():
    """Test temporal fact extraction with valid_at/invalid_at."""
    if not GRAPH_AVAILABLE:
        pytest.skip("Graph dependencies not available")

    from graph.llm_extractor import LLMExtractor
    from datetime import datetime

    extractor = LLMExtractor()
    text = "The policy was active from 2020-2023, then repealed."
    facts = await extractor.extract_facts(text)

    assert len(facts) > 0
    assert facts[0].valid_at.year == 2020
    assert facts[0].invalid_at is not None
    assert facts[0].invalid_at.year == 2023

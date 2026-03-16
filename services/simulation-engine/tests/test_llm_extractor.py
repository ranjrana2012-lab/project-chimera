"""
Tests for LLM-based entity and fact extraction.

These tests focus on the LLMExtractor class without requiring Neo4j.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.asyncio
async def test_llm_entity_extraction():
    """Test LLM-based entity extraction."""
    from graph.llm_extractor import LLMExtractor
    from graph.models import EntityType

    extractor = LLMExtractor()
    text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
    entities = await extractor.extract_entities(text)

    assert len(entities) > 0, "Should extract at least one entity"
    assert any(e.type == EntityType.ORGANIZATION for e in entities), "Should extract organizations"
    assert any(e.type == EntityType.PERSON for e in entities), "Should extract persons"
    assert any(e.type == EntityType.LOCATION for e in entities), "Should extract locations"


@pytest.mark.asyncio
async def test_temporal_fact_extraction():
    """Test temporal fact extraction with valid_at/invalid_at."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()
    text = "The policy was active from 2020-2023, then repealed."
    facts = await extractor.extract_facts(text)

    assert len(facts) > 0, "Should extract at least one fact"
    assert facts[0].valid_at.year == 2020, "Valid date should be 2020"
    assert facts[0].invalid_at is not None, "Should have invalid date"
    assert facts[0].invalid_at.year == 2023, "Invalid date should be 2023"


@pytest.mark.asyncio
async def test_llm_extractor_fallback():
    """Test that LLMExtractor falls back gracefully on LLM failure."""
    from graph.llm_extractor import LLMExtractor
    from graph.models import EntityType

    # Create extractor with invalid backend to test fallback
    extractor = LLMExtractor(llm_backend="invalid_backend")
    text = "Test text for fallback."

    # Should not raise exception, should return empty list or fallback result
    try:
        entities = await extractor.extract_entities(text)
        # If it succeeds, verify it returns something reasonable
        assert isinstance(entities, list)
    except Exception as e:
        # If it raises, it should be a handled error
        assert "LLM" in str(e) or "backend" in str(e).lower()


@pytest.mark.asyncio
async def test_extract_entities_with_short_text():
    """Test entity extraction with short text."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()

    # Very short text should return empty list
    entities = await extractor.extract_entities("Hi")
    assert entities == []

    # Empty text should return empty list
    entities = await extractor.extract_entities("")
    assert entities == []

    # None should return empty list
    entities = await extractor.extract_entities(None)
    assert entities == []


@pytest.mark.asyncio
async def test_extract_facts_with_short_text():
    """Test fact extraction with short text."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()

    # Very short text should return empty list
    facts = await extractor.extract_facts("Hi")
    assert facts == []

    # Empty text should return empty list
    facts = await extractor.extract_facts("")
    assert facts == []


@pytest.mark.asyncio
async def test_parse_entities_response_with_json():
    """Test parsing JSON response into entities."""
    from graph.llm_extractor import LLMExtractor
    from graph.models import EntityType

    extractor = LLMExtractor()

    # Test valid JSON response
    json_response = '''[
        {"name": "Apple", "type": "organization", "description": "Tech company"},
        {"name": "Steve Jobs", "type": "person", "description": "Founder"}
    ]'''

    entities = extractor._parse_entities_response(json_response, "test text")

    assert len(entities) == 2
    assert entities[0].type == EntityType.ORGANIZATION
    assert entities[0].attributes["name"] == "Apple"
    assert entities[1].type == EntityType.PERSON
    assert entities[1].attributes["name"] == "Steve Jobs"


@pytest.mark.asyncio
async def test_parse_entities_response_with_markdown():
    """Test parsing JSON response with markdown code blocks."""
    from graph.llm_extractor import LLMExtractor
    from graph.models import EntityType

    extractor = LLMExtractor()

    # Test JSON response with markdown code blocks
    json_response = '''```json
    [
        {"name": "Apple", "type": "organization", "description": "Tech company"}
    ]
    ```'''

    entities = extractor._parse_entities_response(json_response, "test text")

    assert len(entities) == 1
    assert entities[0].type == EntityType.ORGANIZATION


@pytest.mark.asyncio
async def test_parse_facts_response():
    """Test parsing JSON response into facts."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()

    # Test valid JSON response
    json_response = '''[
        {
            "subject": "policy",
            "predicate": "was_active",
            "object": "active",
            "valid_date": "2020-01-01",
            "invalid_date": "2023-12-31"
        }
    ]'''

    facts = extractor._parse_facts_response(json_response, "test text")

    assert len(facts) == 1
    assert facts[0].subject == "policy"
    assert facts[0].predicate == "was_active"
    assert facts[0].object == "active"
    assert facts[0].valid_at.year == 2020
    assert facts[0].invalid_at.year == 2023


@pytest.mark.asyncio
async def test_map_entity_type():
    """Test mapping entity type strings to enums."""
    from graph.llm_extractor import LLMExtractor
    from graph.models import EntityType

    extractor = LLMExtractor()

    assert extractor._map_entity_type("person") == EntityType.PERSON
    assert extractor._map_entity_type("organization") == EntityType.ORGANIZATION
    assert extractor._map_entity_type("location") == EntityType.LOCATION
    assert extractor._map_entity_type("event") == EntityType.EVENT
    assert extractor._map_entity_type("concept") == EntityType.CONCEPT
    assert extractor._map_entity_type("policy") == EntityType.POLICY
    assert extractor._map_entity_type("unknown") == EntityType.CONCEPT  # Default


@pytest.mark.asyncio
async def test_parse_date_various_formats():
    """Test parsing dates from various formats."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()

    # Test datetime object
    dt = datetime(2023, 5, 15, 12, 30)
    assert extractor._parse_date(dt) == dt

    # Test ISO format
    result = extractor._parse_date("2023-05-15")
    assert result.year == 2023
    assert result.month == 5
    assert result.day == 15

    # Test ISO format with time
    result = extractor._parse_date("2023-05-15T12:30:00")
    assert result.year == 2023
    assert result.hour == 12

    # Test unparseable string (should return current time)
    result = extractor._parse_date("invalid_date")
    assert isinstance(result, datetime)


@pytest.mark.asyncio
async def test_fallback_entity_extraction():
    """Test fallback entity extraction using regex."""
    from graph.llm_extractor import LLMExtractor
    from graph.models import EntityType

    extractor = LLMExtractor()

    # Test fallback extraction
    entities = extractor._extract_entities_fallback("Alice and Bob went to New York.")

    assert len(entities) > 0
    assert all(isinstance(e.id, str) for e in entities)
    assert all(isinstance(e.type, EntityType) for e in entities)
    assert all("name" in e.attributes for e in entities)
    assert all(e.attributes.get("source") == "fallback_extraction" for e in entities)


@pytest.mark.asyncio
async def test_fallback_fact_extraction():
    """Test fallback fact extraction using regex."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()

    # Test fallback extraction with years
    facts = extractor._extract_facts_fallback("The policy was active from 2020 to 2023.")

    assert len(facts) > 0
    assert facts[0].subject == "extracted_content"
    assert facts[0].predicate == "contains_temporal_reference"
    # The fallback extracts the first 2-digit year pattern
    assert facts[0].object.startswith("years_")
    assert facts[0].valid_at is not None


@pytest.mark.asyncio
async def test_build_entity_extraction_prompt():
    """Test building entity extraction prompt."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()
    prompt = extractor._build_entity_extraction_prompt("Test text")

    assert "Test text" in prompt
    assert "entities" in prompt.lower()
    assert "json" in prompt.lower()


@pytest.mark.asyncio
async def test_build_fact_extraction_prompt():
    """Test building fact extraction prompt."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()
    prompt = extractor._build_fact_extraction_prompt("Test text")

    assert "Test text" in prompt
    assert "facts" in prompt.lower()
    assert "temporal" in prompt.lower()
    assert "json" in prompt.lower()


@pytest.mark.asyncio
async def test_error_handling_invalid_json():
    """Test error handling for invalid JSON responses."""
    from graph.llm_extractor import LLMExtractor

    extractor = LLMExtractor()

    # Test invalid JSON
    with pytest.raises(ValueError, match="Invalid JSON"):
        extractor._parse_entities_response("not valid json", "test text")

    with pytest.raises(ValueError, match="Invalid JSON"):
        extractor._parse_facts_response("not valid json", "test text")

"""
Pytest configuration and shared fixtures for Project Chimera tests.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient, ASGITransport
from pydantic import RedisDsn

# Add services to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "services"))


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Test configuration values."""
    return {
        "app_name": "project-chimera-test",
        "app_env": "testing",
        "app_debug": True,
        "redis_host": os.getenv("TEST_REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("TEST_REDIS_PORT", "6379")),
        "redis_db": int(os.getenv("TEST_REDIS_DB", "15")),  # Use DB 15 for tests
        "kafka_bootstrap_servers": os.getenv("TEST_KAFKA_SERVERS", "localhost:9092"),
        "kafka_consumer_group": "test-consumer-group",
    }


@pytest.fixture
async def redis_client(test_config: dict) -> AsyncGenerator[aioredis.Redis, None]:
    """Create a Redis client for testing."""
    redis = await aioredis.from_url(
        f"redis://{test_config['redis_host']}:{test_config['redis_port']}/{test_config['redis_db']}",
        encoding="utf-8",
        decode_responses=True,
    )
    yield redis
    await redis.flushdb()  # Clean up test data
    await redis.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(base_url="http://test", timeout=30.0) as client:
        yield client


@pytest.fixture
def mock_llm_response() -> MagicMock:
    """Mock LLM inference response."""
    mock = MagicMock()
    mock.text = "This is a test dialogue response."
    mock.generation_id = "test-gen-123"
    mock.model_used = "test-model"
    mock.tokens_used = 50
    mock.latency_ms = 150
    return mock


@pytest.fixture
def mock_sentiment_response() -> dict:
    """Mock sentiment analysis response."""
    return {
        "sentiment": "positive",
        "confidence": 0.85,
        "emotions": {
            "joy": 0.72,
            "anticipation": 0.45,
            "trust": 0.38,
        },
    }


@pytest.fixture
def mock_caption_response() -> dict:
    """Mock captioning response."""
    return {
        "text": "This is a test caption.",
        "language": "en",
        "confidence": 0.95,
        "timestamp": "2026-02-26T12:00:00Z",
    }


@pytest.fixture
def mock_bsl_gloss_response() -> dict:
    """Mock BSL gloss translation response."""
    return {
        "gloss": "HELLO MY NAME TEST",
        "breakdown": ["HELLO", "MY", "NAME", "TEST"],
        "language": "bsl",
        "confidence": 0.88,
    }


@pytest.fixture
def sample_scene_context() -> dict:
    """Sample scene context for testing."""
    return {
        "scene_id": "scene-001",
        "title": "Opening Monologue",
        "characters": ["PROTAGONIST", "ANTAGONIST"],
        "setting": "A dimly lit room",
        "mood": "tense",
        "current_dialogue": [],
        "stage_directions": ["Lights up slowly"],
    }


@pytest.fixture
def sample_dialogue_context() -> list:
    """Sample dialogue history for testing."""
    return [
        {
            "character": "PROTAGONIST",
            "text": "What do you want from me?",
            "timestamp": "2026-02-26T12:00:00Z",
        },
        {
            "character": "ANTAGONIST",
            "text": "The truth. Nothing more.",
            "timestamp": "2026-02-26T12:00:05Z",
        },
    ]


@pytest.fixture
def sample_sentiment_vector() -> dict:
    """Sample audience sentiment vector for testing."""
    return {
        "overall": "positive",
        "intensity": 0.65,
        "engagement": 0.78,
        "emotional_arc": ["neutral", "curious", "engaged"],
        "social_mentions": 42,
    }


@pytest.fixture
def safety_test_cases() -> dict:
    """Test cases for safety filter."""
    return {
        "safe_content": [
            "The stage lights dimmed slowly.",
            "Hello, how are you today?",
            "The performance begins now.",
        ],
        "blocked_content": [
            "This contains [PROFANITY] content.",
            "Hate speech should be blocked.",
        ],
        "flagged_content": [
            "The character showed intense anger.",
            "A reference to violence was mentioned.",
        ],
    }


@pytest.fixture
def mock_skill_invocation() -> dict:
    """Mock skill invocation request."""
    return {
        "skill_name": "scenespeak",
        "input": {
            "current_scene": {
                "scene_id": "scene-001",
                "title": "Test Scene",
            },
            "dialogue_context": [],
            "sentiment_vector": {"overall": "neutral"},
        },
        "config": {
            "timeout": 3000,
            "retry_policy": {
                "max_retries": 2,
                "backoff": "exponential",
            },
        },
    }


# Test markers configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "load: Load tests")
    config.addinivalue_line("markers", "red_team: Red team / security tests")
    config.addinivalue_line("markers", "accessibility: Accessibility tests")


# Skip tests that require external services if not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests based on availability."""
    skip_requires_kafka = pytest.mark.skip(reason="Kafka not available")
    skip_requires_redis = pytest.mark.skip(reason="Redis not available")

    # Check if services are available
    kafka_available = os.getenv("TEST_KAFKA_AVAILABLE", "false").lower() == "true"
    redis_available = os.getenv("TEST_REDIS_AVAILABLE", "false").lower() == "true"

    for item in items:
        if "kafka" in item.keywords and not kafka_available:
            item.add_marker(skip_requires_kafka)
        if "redis" in item.keywords and not redis_available:
            item.add_marker(skip_requires_redis)

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
def base_urls():
    """Base URLs for all services."""
    return {
        "openclaw": "http://localhost:8000",
        "scenespeak": "http://localhost:8001",
        "captioning": "http://localhost:8002",
        "bsl": "http://localhost:8003",
        "sentiment": "http://localhost:8004",
        "lighting": "http://localhost:8005",
        "safety": "http://localhost:8006",
        "console": "http://localhost:8007"
    }


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
        # Service endpoints for integration tests
        "openclaw_host": os.getenv("OPENCLAW_HOST", "localhost"),
        "openclaw_port": int(os.getenv("OPENCLAW_PORT", "8000")),
        "sentiment_host": os.getenv("SENTIMENT_HOST", "localhost"),
        "sentiment_port": int(os.getenv("SENTIMENT_PORT", "8001")),
        "scenespeak_host": os.getenv("SCENESPEAK_HOST", "localhost"),
        "scenespeak_port": int(os.getenv("SCENESPEAK_PORT", "8002")),
        "safety_host": os.getenv("SAFETY_HOST", "localhost"),
        "safety_port": int(os.getenv("SAFETY_PORT", "8003")),
        "captioning_host": os.getenv("CAPTIONING_HOST", "localhost"),
        "captioning_port": int(os.getenv("CAPTIONING_PORT", "8004")),
        "bsl_host": os.getenv("BSL_HOST", "localhost"),
        "bsl_port": int(os.getenv("BSL_PORT", "8005")),
        "lighting_host": os.getenv("LIGHTING_HOST", "localhost"),
        "lighting_port": int(os.getenv("LIGHTING_PORT", "8006")),
        "console_host": os.getenv("CONSOLE_HOST", "localhost"),
        "console_port": int(os.getenv("CONSOLE_PORT", "8007")),
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
async def async_http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(base_url="http://test", timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def http_client():
    """HTTP client for testing."""
    import requests
    session = requests.Session()
    session.verify = False
    return session


@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for all services to be ready."""
    from fixtures.deployments import K3sHelper
    import time

    print("\nWaiting for services to be ready...")
    services = [
        "openclaw-orchestrator",
        "scenespeak-agent",
        "captioning-agent",
        "bsl-text2gloss-agent",
        "sentiment-agent",
        "lighting-control",
        "safety-filter",
        "operator-console"
    ]

    timeout = 300
    start = time.time()

    while time.time() - start < timeout:
        ready = 0
        for service in services:
            if K3sHelper.wait_for_service_ready(service, timeout=1):
                ready += 1
        if ready == len(services):
            print(f"All {len(services)} services ready!")
            return True
        time.sleep(5)

    raise TimeoutError(f"Services not ready within {timeout}s")


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
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_k8s: Tests requiring kubernetes")
    config.addinivalue_line("markers", "requires_services: Tests requiring deployed services")
    config.addinivalue_line("markers", "load: Load tests")
    config.addinivalue_line("markers", "red_team: Red team / security tests")
    config.addinivalue_line("markers", "accessibility: Accessibility tests")
    config.addinivalue_line("markers", "kafka: Tests requiring Kafka")
    config.addinivalue_line("markers", "redis: Tests requiring Redis")


# Skip tests that require external services if not available
def pytest_collection_modifyitems(config, items):
    """Skip service-dependent tests if services aren't ready."""
    skip_requires_kafka = pytest.mark.skip(reason="Kafka not available")
    skip_requires_redis = pytest.mark.skip(reason="Redis not available")

    # Check if services are available
    kafka_available = os.getenv("TEST_KAFKA_AVAILABLE", "false").lower() == "true"
    redis_available = os.getenv("TEST_REDIS_AVAILABLE", "false").lower() == "true"

    # Check if k8s services are ready (import only when needed to avoid issues)
    services_ready = False
    try:
        from fixtures.deployments import K3sHelper
        services_ready = len(K3sHelper.get_pods()) > 0
    except Exception:
        pass

    for item in items:
        if "kafka" in item.keywords and not kafka_available:
            item.add_marker(skip_requires_kafka)
        if "redis" in item.keywords and not redis_available:
            item.add_marker(skip_requires_redis)
        if item.get_closest_marker("requires_services"):
            if not services_ready:
                item.add_marker(pytest.mark.skip("Services not deployed"))

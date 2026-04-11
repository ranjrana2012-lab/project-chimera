"""Shared fixtures for MVP integration tests."""

import pytest
from typing import Dict
import os


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for services (localhost or Docker network)."""
    return os.getenv("BASE_URL", "http://localhost")


@pytest.fixture(scope="session")
def service_ports() -> Dict[str, int]:
    """Service port mappings for MVP services."""
    return {
        "orchestrator": 8000,
        "scenespeak": 8001,
        "sentiment": 8004,
        "safety": 8005,
        "translation": 8006,
        "console": 8007,
        "hardware": 8008,
        "redis": 6379,
    }


@pytest.fixture
def orchestrator_url(base_url, service_ports) -> str:
    """Base URL for OpenClaw Orchestrator."""
    return f"{base_url}:{service_ports['orchestrator']}"


@pytest.fixture
def scenespeak_url(base_url, service_ports) -> str:
    """Base URL for SceneSpeak Agent."""
    return f"{base_url}:{service_ports['scenespeak']}"


@pytest.fixture
def sentiment_url(base_url, service_ports) -> str:
    """Base URL for Sentiment Agent."""
    return f"{base_url}:{service_ports['sentiment']}"


@pytest.fixture
def safety_url(base_url, service_ports) -> str:
    """Base URL for Safety Filter."""
    return f"{base_url}:{service_ports['safety']}"


@pytest.fixture
def translation_url(base_url, service_ports) -> str:
    """Base URL for Translation Agent."""
    return f"{base_url}:{service_ports['translation']}"


@pytest.fixture
def hardware_url(base_url, service_ports) -> str:
    """Base URL for Hardware Bridge."""
    return f"{base_url}:{service_ports['hardware']}"


@pytest.fixture
def console_url(base_url, service_ports) -> str:
    """Base URL for Operator Console."""
    return f"{base_url}:{service_ports['console']}"


# Test data fixtures
@pytest.fixture
def sample_prompt() -> str:
    """Sample prompt for orchestration tests."""
    return "The hero enters the dark room, drawing their sword."


@pytest.fixture
def sample_positive_text() -> str:
    """Sample text with positive sentiment."""
    return "The audience cheered with joy and excitement!"


@pytest.fixture
def sample_negative_text() -> str:
    """Sample text with negative sentiment."""
    return "The crowd booed angrily at the terrible performance."


@pytest.fixture
def sample_neutral_text() -> str:
    """Sample text with neutral sentiment."""
    return "The actor walked to the center of the stage."

"""
Integration test configuration and fixtures for Project Chimera.

This module provides pytest fixtures for integration testing across all services.
Fixtures handle service discovery, HTTP clients, WebSocket connections, and test data.
"""

import os
import sys
import time
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
import json

import pytest
import pytest_asyncio
from httpx import AsyncClient, ConnectError, TimeoutException
import websockets.asyncio.client
from websockets.exceptions import ConnectionClosed

# Add project root to Python path
_project_root = Path(__file__).parent.parent.parent.absolute()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# Service URLs (adjust for docker-compose or local development)
SERVICE_PORTS = {
    "orchestrator": 8000,
    "scenespeak": 8001,
    "captioning": 8002,
    "bsl": 8003,
    "sentiment": 8004,
    "lighting": 8005,
    "safety": 8005,  # FIXED: Matches docker-compose.yml
    "console": 8007,
}

# Base URL configuration
USE_DOCKER = os.getenv("USE_DOCKER", "true").lower() == "true"
BASE_HOST = "localhost" if not USE_DOCKER else "chimera-{service}"


def get_service_url(service_name: str) -> str:
    """Get the base URL for a service."""
    port = SERVICE_PORTS.get(service_name)
    if USE_DOCKER:
        return f"http://{BASE_HOST.format(service=service_name)}"
    return f"http://localhost:{port}"


def get_service_ws_url(service_name: str) -> str:
    """Get the WebSocket URL for a service."""
    port = SERVICE_PORTS.get(service_name)
    if USE_DOCKER:
        return f"ws://{BASE_HOST.format(service=service_name)}"
    return f"ws://localhost:{port}"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def all_services_running() -> AsyncGenerator[Dict[str, bool], None]:
    """
    Ensure all services are up and running before tests.

    This fixture polls all service health endpoints until they respond
    or timeout is reached. Returns a dict of service status.

    Skip tests if services are not available.
    """
    service_status = {}
    max_retries = 30  # 30 seconds timeout
    retry_interval = 1.0

    async def check_service(service_name: str) -> bool:
        """Check if a single service is healthy."""
        url = get_service_url(service_name)
        health_endpoints = ["/health/live", "/health", "/"]

        for endpoint in health_endpoints:
            try:
                async with AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"{url}{endpoint}")
                    if response.status_code == 200:
                        return True
            except (ConnectError, TimeoutException):
                continue
        return False

    # Wait for all services to be ready
    for attempt in range(max_retries):
        all_ready = True

        for service_name in SERVICE_PORTS.keys():
            if service_name not in service_status or not service_status[service_name]:
                is_healthy = await check_service(service_name)
                service_status[service_name] = is_healthy

                if not is_healthy:
                    all_ready = False

        if all_ready:
            break

        if attempt < max_retries - 1:
            await asyncio.sleep(retry_interval)

    # Log status
    for service, status in service_status.items():
        status_str = "✓" if status else "✗"
        print(f"{status_str} {service}: {'UP' if status else 'DOWN'}")

    # Check if critical services are up
    critical_services = ["orchestrator", "scenespeak", "safety", "console"]
    critical_down = [s for s in critical_services if not service_status.get(s, False)]

    if critical_down:
        pytest.skip(f"Critical services not available: {', '.join(critical_down)}")

    yield service_status


@pytest_asyncio.fixture
async def orchestrator_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client for the orchestrator service.

    Provides an async HTTP client configured for the orchestrator API.
    Skips tests if orchestrator is not available.
    """
    if not all_services_running.get("orchestrator", False):
        pytest.skip("Orchestrator service not available")

    base_url = get_service_url("orchestrator")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def scenespeak_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the SceneSpeak agent service."""
    if not all_services_running.get("scenespeak", False):
        pytest.skip("SceneSpeak agent not available")

    base_url = get_service_url("scenespeak")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def captioning_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the captioning agent service."""
    if not all_services_running.get("captioning", False):
        pytest.skip("Captioning agent not available")

    base_url = get_service_url("captioning")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def bsl_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the BSL agent service."""
    if not all_services_running.get("bsl", False):
        pytest.skip("BSL agent not available")

    base_url = get_service_url("bsl")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def sentiment_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the sentiment agent service."""
    if not all_services_running.get("sentiment", False):
        pytest.skip("Sentiment agent not available")

    base_url = get_service_url("sentiment")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def safety_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the safety filter service."""
    if not all_services_running.get("safety", False):
        pytest.skip("Safety filter not available")

    base_url = get_service_url("safety")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def console_client(all_services_running: Dict[str, bool]) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the operator console service."""
    if not all_services_running.get("console", False):
        pytest.skip("Operator console not available")

    base_url = get_service_url("console")
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def console_websocket(all_services_running: Dict[str, bool]) -> AsyncGenerator[Any, None]:
    """
    WebSocket connection to the operator console.

    Provides an async WebSocket connection for real-time updates.
    """
    if not all_services_running.get("console", False):
        pytest.skip("Operator console not available")

    ws_url = get_service_ws_url("console")
    ws_path = "/ws"

    async with websockets.asyncio.client.connect(f"{ws_url}{ws_path}") as websocket:
        yield websocket


@pytest.fixture
def test_text() -> str:
    """
    Sample text for analysis and processing.

    Provides test dialogue content for various agents.
    """
    return "Hello, welcome to the show! We hope you enjoy tonight's performance."


@pytest.fixture
def test_dialogue_prompt() -> Dict[str, Any]:
    """
    Sample dialogue generation prompt for SceneSpeak.

    Provides a structured prompt for dialogue generation.
    """
    return {
        "prompt": "Generate a dramatic opening line for a play about time travel.",
        "max_tokens": 50,
        "temperature": 0.7,
        "context": {
            "show_id": "test-show-001",
            "scene_number": 1,
            "adapter": "drama"
        }
    }


@pytest.fixture
def test_audio_file() -> Generator[Path, None, None]:
    """
    Sample audio file for captioning tests.

    Creates a temporary WAV file with silence for testing captioning.
    The file is automatically cleaned up after the test.
    """
    # Create a temporary WAV file (1 second of silence)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    # Write a minimal WAV header (44 bytes) for 1 second of silence at 16kHz
    wav_data = b"RIFF" + (36).to_bytes(4, "little") + b"WAVE"
    wav_data += b"fmt " + (16).to_bytes(4, "little")
    wav_data += (1).to_bytes(2, "little")  # PCM
    wav_data += (1).to_bytes(2, "little")  # Mono
    wav_data += (16000).to_bytes(4, "little")  # Sample rate
    wav_data += (32000).to_bytes(4, "little")  # Byte rate
    wav_data += (2).to_bytes(2, "little")  # Block align
    wav_data += (16).to_bytes(2, "little")  # Bits per sample
    wav_data += b"data" + (0).to_bytes(4, "little")

    tmp_path.write_bytes(wav_data)

    yield tmp_path

    # Cleanup
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def test_text_for_translation() -> str:
    """
    Sample English text for BSL translation tests.

    Provides text that exercises the BSL translator.
    """
    return "The time traveler stepped into the machine, ready for adventure."


@pytest.fixture
def safe_content() -> str:
    """Content that should pass all safety filters."""
    return "Welcome to our wonderful show! We hope you have a great time."


@pytest.fixture
def unsafe_content() -> str:
    """Content that should trigger safety filters (mild example)."""
    return "This is a stupid show and I hate it."


@pytest.fixture
def test_show_context() -> Dict[str, Any]:
    """
    Sample show context for testing.

    Provides metadata about a theatrical production.
    """
    return {
        "show_id": "test-show-001",
        "title": "The Time Traveler's Dilemma",
        "scene": 1,
        "act": 1,
        "adapter": "drama",
        "audience_size": 150,
        "venue": "Test Theater"
    }


@pytest.fixture
def test_metrics_data() -> Dict[str, Any]:
    """
    Sample metrics data for testing.

    Provides mock service metrics for console tests.
    """
    return {
        "cpu_percent": 45.2,
        "memory_mb": 512.0,
        "request_rate": 10.5,
        "error_rate": 0.001
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires running services)"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow-running (may take > 5 seconds)"
    )
    config.addinivalue_line(
        "markers",
        "websocket: mark test as using WebSocket connections"
    )
    config.addinivalue_line(
        "markers",
        "requires_docker: mark test as requiring docker-compose services"
    )

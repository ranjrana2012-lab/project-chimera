"""Integration tests for KimiClient vLLM client."""

import os

import pytest
from services.kimi_super_agent.kimi_client import KimiClient


@pytest.fixture
def kimi_client():
    """Create a KimiClient instance for testing."""
    client = KimiClient(
        base_url=os.getenv("KIMI_VLLM_TEST_URL", "http://localhost:8012"),
        model_name=os.getenv("KIMI_MODEL_TEST_NAME", os.getenv("KIMI_MODEL_NAME", "/model")),
        timeout_seconds=int(os.getenv("KIMI_TEST_TIMEOUT", "300")),
    )
    return client


@pytest.mark.asyncio
async def test_kimi_client_generate(kimi_client):
    """Test vLLM client generates response."""
    request = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 8
    }

    response = await kimi_client.generate(request)

    assert "choices" in response
    assert len(response["choices"]) > 0
    assert "content" in response["choices"][0]["message"]


@pytest.mark.asyncio
async def test_kimi_client_health_check(kimi_client):
    """Test vLLM client health check."""
    is_healthy = await kimi_client.health_check()

    # Should return False if service not running
    # Should return True if service is running
    assert isinstance(is_healthy, bool)

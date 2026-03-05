"""
Tests for GLM 4.7 API client with local fallback.

Following TDD methodology, these tests verify:
- GLM API integration with valid API key
- Fallback to local model when API fails
- Proper error handling and logging
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from models import GenerateRequest
from glm_client import GLMClient, DialogueResponse


@pytest.fixture
def client():
    """Create a GLM client with test API key"""
    return GLMClient(api_key="test-key")


@pytest.fixture
def client_no_key():
    """Create a GLM client without API key"""
    return GLMClient(api_key=None)


@pytest.fixture
def request_data():
    """Create a sample generation request"""
    return GenerateRequest(prompt="Hello world")


def test_client_init(client):
    """Test client initialization"""
    assert client.api_key == "test-key"
    assert client.api_base is not None
    assert client.local_model_path is None


def test_client_init_no_key(client_no_key):
    """Test client initialization without API key"""
    assert client_no_key.api_key is None
    assert client_no_key.api_base is not None


@pytest.mark.asyncio
async def test_generate_with_api_key(client):
    """Test generation when API key is available"""
    # Mock the API call
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Generated text"}}],
        "usage": {"total_tokens": 100}
    }
    mock_response.raise_for_status = Mock()

    # Create a mock client context manager
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.generate("Hello", max_tokens=100)

    assert result.text == "Generated text"
    assert result.source == "api"
    assert result.tokens_used == 100
    assert result.model == "glm-4"


@pytest.mark.asyncio
async def test_generate_api_fallback_to_local(client_no_key):
    """Test fallback to local model when API key is not available"""
    # Should use local fallback
    result = await client_no_key.generate("Hello")

    # Will be placeholder until local model is implemented
    assert result.source in ["local", "placeholder"]
    assert "Local model" in result.text


@pytest.mark.asyncio
async def test_generate_api_error_fallback(client):
    """Test fallback to local model when API call fails"""
    # Mock API failure
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("API Error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.generate("Hello")

    # Should fall back to local on API error
    assert result.source in ["local", "placeholder"]


@pytest.mark.asyncio
async def test_local_model_placeholder(client_no_key):
    """Test local model placeholder when model path is not configured"""
    result = await client_no_key.generate("Test prompt")

    assert result.source == "placeholder"
    assert result.model == "local"
    assert result.tokens_used == 0
    assert "model path not configured" in result.text.lower()


def test_dialogue_response_model():
    """Test DialogueResponse dataclass"""
    response = DialogueResponse(
        text="Generated dialogue",
        tokens_used=100,
        model="glm-4",
        source="api",
        duration_ms=500
    )

    assert response.text == "Generated dialogue"
    assert response.tokens_used == 100
    assert response.model == "glm-4"
    assert response.source == "api"
    assert response.duration_ms == 500

"""
Unit tests for Local LLM integration.

Tests for LocalLLMClient including connection handling, generation,
and fallback logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import httpx

from local_llm import LocalLLMClient, LocalLLMResponse, LocalLLM


@pytest.fixture
def mock_httpx_client():
    """Fixture for mocked httpx.AsyncClient."""
    with patch("local_llm.httpx.AsyncClient") as mock:
        client = mock.return_value
        # Make client methods async
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.aclose = AsyncMock()
        yield client


@pytest.fixture
def local_llm_client():
    """Fixture for LocalLLMClient instance."""
    return LocalLLMClient(
        base_url="http://localhost:11434",
        model="llama3.2"
    )


class TestLocalLLMClient:
    """Test suite for LocalLLMClient."""

    @pytest.mark.asyncio
    async def test_connect_success(self, local_llm_client, mock_httpx_client):
        """Test successful connection to Ollama."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "mistral:7b"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        # Connect
        result = await local_llm_client.connect()

        # Assertions
        assert result is True
        assert local_llm_client._connected is True
        assert await local_llm_client.is_available() is True
        assert local_llm_client._available_models == ["llama3.2", "mistral:7b"]

    @pytest.mark.asyncio
    async def test_connect_failure(self, local_llm_client, mock_httpx_client):
        """Test connection failure to Ollama."""
        # Mock connection error
        mock_httpx_client.get.side_effect = httpx.ConnectError("Connection refused")

        # Connect
        result = await local_llm_client.connect()

        # Assertions
        assert result is False
        assert local_llm_client._connected is False
        assert await local_llm_client.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_success(self, local_llm_client, mock_httpx_client):
        """Test successful text generation."""
        # Setup client as connected
        local_llm_client._connected = True
        local_llm_client.client = mock_httpx_client

        # Mock generation response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "Hello, this is a test response.",
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        # Generate
        result = await local_llm_client.generate(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )

        # Assertions
        assert isinstance(result, LocalLLMResponse)
        assert result.text == "Hello, this is a test response."
        assert result.tokens_used == 30
        assert result.model == "llama3.2"
        assert result.source == "local"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_generate_not_connected(self, local_llm_client):
        """Test generation when client is not connected."""
        # Ensure client is not connected
        local_llm_client._connected = False

        # Attempt generation should raise RuntimeError
        with pytest.raises(RuntimeError, match="Not connected to local LLM"):
            await local_llm_client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_http_error(self, local_llm_client, mock_httpx_client):
        """Test generation with HTTP error."""
        # Setup client as connected
        local_llm_client._connected = True
        local_llm_client.client = mock_httpx_client

        # Mock HTTP error
        mock_httpx_client.post.side_effect = httpx.HTTPError("API Error")

        # Attempt generation should raise HTTPError
        with pytest.raises(httpx.HTTPError):
            await local_llm_client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_health_check_connected(self, local_llm_client, mock_httpx_client):
        """Test health check when connected."""
        # Setup client as connected
        local_llm_client._connected = True
        local_llm_client.client = mock_httpx_client

        # Mock tags response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        # Check health
        health = await local_llm_client.health_check()

        # Assertions
        assert health["connected"] is True
        assert health["status"] == "healthy"
        assert health["base_url"] == "http://localhost:11434"
        assert health["model"] == "llama3.2"
        assert health["available_models"] == ["llama3.2"]

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, local_llm_client):
        """Test health check when disconnected."""
        # Ensure client is not connected
        local_llm_client._connected = False

        # Check health
        health = await local_llm_client.health_check()

        # Assertions
        assert health["connected"] is False
        assert health["status"] == "disconnected"
        assert health["available_models"] == []

    @pytest.mark.asyncio
    async def test_get_available_models(self, local_llm_client):
        """Test getting available models."""
        # Setup models
        local_llm_client._connected = True
        local_llm_client._available_models = ["llama3.2", "mistral:7b", "gemma:2b"]

        # Get models
        models = await local_llm_client.get_available_models()

        # Assertions
        assert models == ["llama3.2", "mistral:7b", "gemma:2b"]

    @pytest.mark.asyncio
    async def test_get_available_models_not_connected(self, local_llm_client):
        """Test getting available models when not connected."""
        # Ensure not connected
        local_llm_client._connected = False

        # Get models
        models = await local_llm_client.get_available_models()

        # Assertions
        assert models == []

    @pytest.mark.asyncio
    async def test_ensure_model_available(self, local_llm_client):
        """Test ensuring a model is available."""
        # Setup models
        local_llm_client._connected = True
        local_llm_client._available_models = ["llama3.2", "mistral:7b"]

        # Check for existing model
        assert await local_llm_client.ensure_model("llama3.2") is True

        # Check for non-existing model
        assert await local_llm_client.ensure_model("gemma:2b") is False

    @pytest.mark.asyncio
    async def test_ensure_model_not_connected(self, local_llm_client):
        """Test ensuring model when not connected."""
        # Ensure not connected
        local_llm_client._connected = False

        # Check for model
        assert await local_llm_client.ensure_model("llama3.2") is False

    @pytest.mark.asyncio
    async def test_disconnect(self, local_llm_client, mock_httpx_client):
        """Test disconnecting from local LLM."""
        # Setup as connected
        local_llm_client._connected = True
        local_llm_client.client = mock_httpx_client

        # Disconnect
        await local_llm_client.disconnect()

        # Assertions
        assert local_llm_client._connected is False
        mock_httpx_client.aclose.assert_called_once()


class TestLocalLLMLegacy:
    """Test suite for legacy LocalLLM class."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_httpx_client):
        """Test legacy LocalLLM initialization."""
        # Mock successful connection
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": [{"name": "llama3.2"}]}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        # Initialize
        local_llm = LocalLLM(base_url="http://localhost:11434")
        result = await local_llm.initialize()

        # Assertions
        assert result is True
        assert local_llm._initialized is True

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_httpx_client):
        """Test legacy LocalLLM generate."""
        # Mock successful connection and generation
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2"}],
            "response": "Test response",
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response
        mock_httpx_client.post.return_value = mock_response

        # Initialize and generate
        local_llm = LocalLLM(base_url="http://localhost:11434")
        await local_llm.initialize()
        result = await local_llm.generate("Test prompt", max_tokens=100)

        # Assertions
        assert result["text"] == "Test response"
        assert result["tokens_used"] == 30
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_generate_not_initialized(self):
        """Test legacy LocalLLM generate when not initialized."""
        # Mock connection failure
        with patch("local_llm.httpx.AsyncClient") as mock:
            mock_client = mock.return_value
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            local_llm = LocalLLM(base_url="http://localhost:11434")
            result = await local_llm.generate("Test prompt")

            # Assertions - should return error placeholder
            assert result["text"] == "[Local model not available]"
            assert result["tokens_used"] == 0

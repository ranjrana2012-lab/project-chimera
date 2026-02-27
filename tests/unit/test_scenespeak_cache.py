"""Unit tests for SceneSpeak Response Cache."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

from services.scenespeak_agent.src.core.cache import ResponseCache


@pytest.mark.unit
class TestResponseCache:
    """Test cases for ResponseCache."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis_mock = AsyncMock()
        # Configure the mock to have the necessary methods
        redis_mock.get = AsyncMock()
        redis_mock.setex = AsyncMock()
        redis_mock.keys = AsyncMock()
        redis_mock.delete = AsyncMock()
        return redis_mock

    @pytest.fixture
    def cache(self, mock_redis):
        """Create a ResponseCache instance with mock Redis."""
        return ResponseCache(redis_client=mock_redis, ttl=3600)

    def test_initialization(self, mock_redis):
        """Test cache initialization."""
        cache = ResponseCache(redis_client=mock_redis, ttl=7200)
        assert cache.redis == mock_redis
        assert cache.ttl == 7200

    def test_initialization_default_ttl(self, mock_redis):
        """Test cache initialization with default TTL."""
        cache = ResponseCache(redis_client=mock_redis)
        assert cache.ttl == 3600

    def test_make_key_basic(self, cache):
        """Test cache key generation for basic prompt."""
        prompt = "Generate dialogue for protagonist"
        params = {"temperature": 0.8, "max_tokens": 256}
        key = cache._make_key(prompt, params)

        # Verify key format
        assert key.startswith("chimera:scenespeak:cache:")
        # Verify it's a SHA256 hash (64 hex characters)
        hash_part = key.split(":")[-1]
        assert len(hash_part) == 64
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_make_key_consistency(self, cache):
        """Test that same inputs produce same key."""
        prompt = "Test prompt"
        params = {"temp": 0.5}
        key1 = cache._make_key(prompt, params)
        key2 = cache._make_key(prompt, params)
        assert key1 == key2

    def test_make_key_different_prompts(self, cache):
        """Test that different prompts produce different keys."""
        params = {"temperature": 0.7}
        key1 = cache._make_key("First prompt", params)
        key2 = cache._make_key("Second prompt", params)
        assert key1 != key2

    def test_make_key_different_params(self, cache):
        """Test that different params produce different keys."""
        prompt = "Test prompt"
        key1 = cache._make_key(prompt, {"temperature": 0.7})
        key2 = cache._make_key(prompt, {"temperature": 0.9})
        assert key1 != key2

    def test_make_key_param_order_independence(self, cache):
        """Test that parameter order doesn't affect key."""
        prompt = "Test"
        key1 = cache._make_key(prompt, {"a": 1, "b": 2})
        key2 = cache._make_key(prompt, {"b": 2, "a": 1})
        assert key1 == key2

    def test_make_key_empty_prompt(self, cache):
        """Test key generation with empty prompt."""
        key = cache._make_key("", {})
        assert key.startswith("chimera:scenespeak:cache:")
        assert len(key.split(":")[-1]) == 64

    def test_make_key_complex_params(self, cache):
        """Test key generation with complex parameter structures."""
        prompt = "Complex test"
        params = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "number": 42.5
        }
        key = cache._make_key(prompt, params)
        assert key.startswith("chimera:scenespeak:cache:")
        hash_part = key.split(":")[-1]
        assert len(hash_part) == 64

    @pytest.mark.asyncio
    async def test_get_cached_response(self, cache, mock_redis):
        """Test retrieving a cached response."""
        prompt = "Test prompt"
        params = {"temperature": 0.7}
        cached_data = {"dialogue": "Hello world", "tokens": 5}
        mock_redis.get.return_value = json.dumps(cached_data)

        result = await cache.get(prompt, params)

        # Verify Redis was called with correct key
        expected_key = cache._make_key(prompt, params)
        mock_redis.get.assert_called_once_with(expected_key)
        # Verify result
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_get_no_cache(self, cache, mock_redis):
        """Test getting when response is not cached."""
        prompt = "Uncached prompt"
        params = {}
        mock_redis.get.return_value = None

        result = await cache.get(prompt, params)

        mock_redis.get.assert_called_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_response(self, cache, mock_redis):
        """Test caching a response."""
        prompt = "Test prompt"
        params = {"temperature": 0.7}
        response = {"dialogue": "Response text", "tokens": 10}

        await cache.set(prompt, params, response)

        # Verify Redis was called correctly
        expected_key = cache._make_key(prompt, params)
        mock_redis.setex.assert_called_once_with(
            expected_key,
            3600,
            json.dumps(response)
        )

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, mock_redis):
        """Test caching with custom TTL."""
        cache = ResponseCache(redis_client=mock_redis, ttl=1800)
        prompt = "Test"
        params = {}
        response = {"data": "value"}

        await cache.set(prompt, params, response)

        # Verify TTL is used
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 1800

    @pytest.mark.asyncio
    async def test_set_complex_response(self, cache, mock_redis):
        """Test caching complex response structure."""
        prompt = "Complex"
        params = {}
        response = {
            "dialogue": "Text",
            "metadata": {"model": "test", "timestamp": "2024-01-01"},
            "tokens": 100,
            "confidence": 0.95
        }

        await cache.set(prompt, params, response)

        # Verify JSON serialization
        call_args = mock_redis.setex.call_args
        cached_json = call_args[0][2]
        assert json.loads(cached_json) == response

    @pytest.mark.asyncio
    async def test_set_none_response(self, cache, mock_redis):
        """Test caching None as response."""
        prompt = "Test"
        params = {}
        response = None

        await cache.set(prompt, params, response)

        # Verify None is JSON-serialized
        call_args = mock_redis.setex.call_args
        assert "null" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_clear_no_keys(self, cache, mock_redis):
        """Test clearing cache when no keys exist."""
        mock_redis.keys.return_value = []

        await cache.clear()

        mock_redis.keys.assert_called_once_with("chimera:scenespeak:cache:*")
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_single_key(self, cache, mock_redis):
        """Test clearing cache with one key."""
        mock_redis.keys.return_value = ["chimera:scenespeak:cache:abc123"]
        mock_redis.delete.return_value = 1

        await cache.clear()

        mock_redis.keys.assert_called_once_with("chimera:scenespeak:cache:*")
        mock_redis.delete.assert_called_once_with("chimera:scenespeak:cache:abc123")

    @pytest.mark.asyncio
    async def test_clear_multiple_keys(self, cache, mock_redis):
        """Test clearing cache with multiple keys."""
        keys = [
            "chimera:scenespeak:cache:key1",
            "chimera:scenespeak:cache:key2",
            "chimera:scenespeak:cache:key3"
        ]
        mock_redis.keys.return_value = keys

        await cache.clear()

        # Verify delete was called for each key
        assert mock_redis.delete.call_count == 3
        calls = [call[0][0] for call in mock_redis.delete.call_args_list]
        assert calls == keys

    @pytest.mark.asyncio
    async def test_get_json_decode_error(self, cache, mock_redis):
        """Test get with invalid JSON in cache."""
        prompt = "Test"
        params = {}
        mock_redis.get.return_value = b"invalid json{{{"

        result = await cache.get(prompt, params)

        # Should return None on JSON decode error
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_scenario(self, cache, mock_redis):
        """Test full cache hit scenario."""
        prompt = "Generate response"
        params = {"temperature": 0.8, "max_tokens": 256}
        cached_response = {
            "dialogue": "Cached dialogue",
            "tokens": 42,
            "from_cache": True
        }
        mock_redis.get.return_value = json.dumps(cached_response)

        # First call - cache hit
        result = await cache.get(prompt, params)
        assert result == cached_response
        assert result["from_cache"] is True

    @pytest.mark.asyncio
    async def test_cache_miss_then_set(self, cache, mock_redis):
        """Test cache miss followed by setting the response."""
        prompt = "New prompt"
        params = {"temperature": 0.5}

        # Cache miss
        mock_redis.get.return_value = None
        result = await cache.get(prompt, params)
        assert result is None

        # Set the response
        new_response = {"dialogue": "New dialogue", "tokens": 50}
        await cache.set(prompt, params, new_response)
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_unicode_in_prompt_and_response(self, cache, mock_redis):
        """Test handling of Unicode characters."""
        prompt = "Generate emoji: 🎭 and symbols: ©"
        params = {}
        response = {"dialogue": "Response with 🎭 and ©"}

        await cache.set(prompt, params, response)

        # Verify JSON serialization handles Unicode
        call_args = mock_redis.setex.call_args
        cached_json = call_args[0][2]
        assert json.loads(cached_json) == response

    @pytest.mark.asyncio
    async def test_special_characters_in_params(self, cache, mock_redis):
        """Test key generation with special characters in params."""
        prompt = "Test"
        params = {"special": "!@#$%^&*()[]{}"}

        key = cache._make_key(prompt, params)
        # Key should still be valid (only contains hex after prefix)
        assert key.startswith("chimera:scenespeak:cache:")
        hash_part = key.split(":")[-1]
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_key_deterministic_hash(self, cache):
        """Test that key generation is deterministic."""
        prompt = "Deterministic test"
        params = {"value": 42}

        # Generate key multiple times
        keys = [cache._make_key(prompt, params) for _ in range(10)]

        # All keys should be identical
        assert len(set(keys)) == 1

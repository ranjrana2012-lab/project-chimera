import pytest
from unittest.mock import Mock, AsyncMock

from music_orchestration.cache import CacheManager
from music_orchestration.schemas import MusicRequest, UseCase


@pytest.mark.asyncio
async def test_cache_set_and_get():
    redis_mock = Mock()
    redis_mock.set = AsyncMock()
    redis_mock.get = AsyncMock(return_value=b'{"music_id": "abc-123"}')
    redis_mock.expire = AsyncMock()

    cache = CacheManager(redis_mock)

    await cache.set("test-key", {"music_id": "abc-123"}, ttl=604800)
    result = await cache.get("test-key")

    assert result["music_id"] == "abc-123"
    redis_mock.set.assert_called_once()
    redis_mock.get.assert_called_once()


@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    redis_mock = Mock()
    redis_mock.get = AsyncMock(return_value=None)

    cache = CacheManager(redis_mock)
    result = await cache.get("nonexistent-key")

    assert result is None


@pytest.mark.asyncio
async def test_get_cache_key_from_request():
    redis_mock = Mock()
    cache = CacheManager(redis_mock)

    request = MusicRequest(
        prompt="upbeat electronic",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )

    key = cache.get_cache_key(request)
    assert key == request.cache_key
    assert len(key) == 64  # SHA256 hex length

import json
from typing import Any
from redis.asyncio import Redis
from music_orchestration.schemas import MusicRequest


class CachedAudio(dict):
    """Cached audio metadata"""
    pass


class CacheManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.key_prefix = "music:cache:"
        self.default_ttl = 604800  # 7 days

    def get_cache_key(self, request: MusicRequest) -> str:
        """Get cache key from request"""
        return request.cache_key

    def _prefixed_key(self, cache_key: str) -> str:
        """Add prefix to cache key for Redis storage"""
        return f"{self.key_prefix}{cache_key}"

    async def get(self, cache_key: str) -> CachedAudio | None:
        """Get cached audio if exists"""
        data = await self.redis.get(self._prefixed_key(cache_key))
        if data:
            return CachedAudio(json.loads(data))
        return None

    async def set(
        self,
        cache_key: str,
        audio: dict[str, Any],
        ttl: int | None = None
    ) -> None:
        """Cache audio metadata"""
        ttl = ttl or self.default_ttl
        await self.redis.set(self._prefixed_key(cache_key), json.dumps(audio), ex=ttl)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching pattern"""
        keys = await self.redis.keys(self._prefixed_key(pattern))
        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def get_stats(self) -> dict[str, int]:
        """Get cache statistics"""
        info = await self.redis.info("stats")
        return {
            "keys_count": info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
        }

"""
Request Cache for Project Chimera services.

Redis-based caching for service responses with appropriate TTLs.
Reduces redundant computations and improves response times.

Usage:
    cache = RequestCache()
    result = await cache.get("agent:show123:abc123")
    if result is None:
        result = await compute_expensive_operation()
        await cache.set("agent:show123:abc123", result, ttl=300)
"""

import hashlib
import json
import logging
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache operations."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class RequestCache:
    """
    Redis-based caching for service responses.

    Features:
    - Content-based cache keys (hash of request parameters)
    - Per-agent TTL configuration
    - Cache statistics tracking
    - Graceful degradation on Redis failures
    - Async operations for performance

    Recommended TTLs:
    - Sentiment: 5 minutes (audience mood changes)
    - Translation: 1 hour (content doesn't change)
    - Safety: 10 minutes (safety rules stable)
    - SceneSpeak: No cache (creative generation varies)
    """

    # Default TTLs by agent (in seconds)
    DEFAULT_TTLS: Dict[str, int] = {
        "sentiment": 300,      # 5 minutes
        "translation": 3600,   # 1 hour
        "safety": 600,         # 10 minutes
        "scenespeak": 0,      # No cache (creative)
        "orchestrator": 60,   # 1 minute
    }

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "chimera",
        default_ttl: int = 300,
        enabled: bool = True,
    ):
        """
        Initialize the request cache.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all cache keys
            default_ttl: Default TTL in seconds if agent-specific not found
            enabled: Whether caching is enabled (allows graceful degradation)
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.enabled = enabled
        self._redis: Optional[redis.Redis] = None
        self._stats = CacheStats()

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get or create Redis connection."""
        if not self.enabled:
            return None

        if self._redis is None:
            try:
                self._redis = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._redis.ping()
                logger.info("Connected to Redis for caching")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.enabled = False
                return None

        return self._redis

    def cache_key(
        self,
        agent: str,
        prompt: str,
        show_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a cache key from request parameters.

        The key is a hash of all request parameters to ensure
        identical requests hit the same cache entry.

        Args:
            agent: Agent name (e.g., "sentiment", "translation")
            prompt: The input prompt text
            show_id: Optional show identifier
            **kwargs: Additional parameters to include in hash

        Returns:
            Cache key string
        """
        # Create deterministic hash of all parameters
        key_data = {
            "agent": agent,
            "prompt": prompt,
            "show_id": show_id,
            **kwargs,
        }
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()[:12]

        return f"{self.key_prefix}:{agent}:{show_id or 'default'}:{key_hash}"

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response.

        Args:
            key: Cache key

        Returns:
            Cached response dict, or None if not found
        """
        if not self.enabled:
            return None

        try:
            r = await self._get_redis()
            if r is None:
                return None

            cached = await r.get(key)
            if cached:
                self._stats.hits += 1
                return json.loads(cached)
            else:
                self._stats.misses += 1
                return None
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            self._stats.errors += 1
            return None

    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache a response.

        Args:
            key: Cache key
            value: Response dict to cache
            ttl: Time to live in seconds (uses agent default if None)

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled:
            return False

        if ttl == 0:
            # Explicitly disabled
            return False

        try:
            r = await self._get_redis()
            if r is None:
                return False

            await r.setex(key, ttl or self.default_ttl, json.dumps(value))
            self._stats.sets += 1
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            self._stats.errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a cached response.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False

        try:
            r = await self._get_redis()
            if r is None:
                return False

            result = await r.delete(key)
            self._stats.deletes += 1
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            self._stats.errors += 1
            return False

    async def invalidate_agent(self, agent: str, show_id: Optional[str] = None) -> int:
        """
        Invalidate all cache entries for an agent.

        Args:
            agent: Agent name
            show_id: Optional show ID to narrow scope

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            r = await self._get_redis()
            if r is None:
                return 0

            pattern = f"{self.key_prefix}:{agent}:{show_id or '*'}:*"
            keys = []
            async for key in r.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await r.delete(*keys)
                self._stats.deletes += deleted
                logger.info(f"Invalidated {deleted} cache entries for {agent}")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidation failed for {agent}: {e}")
            self._stats.errors += 1
            return 0

    def get_ttl_for_agent(self, agent: str) -> int:
        """Get the default TTL for an agent."""
        return self.DEFAULT_TTLS.get(agent, self.default_ttl)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# Global cache instance
_global_cache: Optional[RequestCache] = None


def get_global_cache() -> RequestCache:
    """Get or create the global cache instance."""
    global _global_cache
    if _global_cache is None:
        redis_url = "redis://" + redis.__name__
        _global_cache = RequestCache(redis_url=redis_url)
    return _global_cache


async def close_global_cache() -> None:
    """Close the global cache instance."""
    global _global_cache
    if _global_cache is not None:
        await _global_cache.close()
        _global_cache = None


__all__ = [
    "RequestCache",
    "CacheStats",
    "get_global_cache",
    "close_global_cache",
]

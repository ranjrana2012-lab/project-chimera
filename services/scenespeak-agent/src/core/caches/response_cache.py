"""ResponseCache adapter for SceneSpeak Agent."""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from .redis_cache import RedisCache


class ResponseCache:
    """Cache for dialogue generation responses.

    Provides an interface compatible with the task specification
    for caching LLM responses with prompt and parameter-based keys.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 300,
    ):
        """Initialize ResponseCache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            ttl: Default time-to-live for cached items in seconds
        """
        self._redis_cache = RedisCache(
            host=host,
            port=port,
            db=db,
            password=password,
        )
        self.ttl = ttl

    async def connect(self) -> None:
        """Connect to Redis."""
        await self._redis_cache.connect()

    async def get(self, prompt: str, params: dict) -> Optional[dict]:
        """Get cached response for a prompt and parameters.

        Args:
            prompt: The prompt used for generation
            params: Generation parameters (max_tokens, temperature, top_p)

        Returns:
            Cached response dict if found, None otherwise
        """
        key = self._make_key(prompt, params)
        value = await self._redis_cache.get(key)
        return value

    async def set(self, prompt: str, params: dict, response: dict) -> None:
        """Cache a response for a prompt and parameters.

        Args:
            prompt: The prompt used for generation
            params: Generation parameters (max_tokens, temperature, top_p)
            response: The response to cache
        """
        key = self._make_key(prompt, params)
        await self._redis_cache.set(key, response, ttl=self.ttl)

    async def delete(self, prompt: str, params: dict) -> None:
        """Delete cached response for a prompt and parameters.

        Args:
            prompt: The prompt used for generation
            params: Generation parameters
        """
        key = self._make_key(prompt, params)
        await self._redis_cache.delete(key)

    def _make_key(self, prompt: str, params: dict) -> str:
        """Create a cache key from prompt and parameters.

        Args:
            prompt: The prompt
            params: Generation parameters

        Returns:
            A string key suitable for Redis
        """
        import hashlib
        key_data = f"{prompt}:{json.dumps(params, sort_keys=True)}"
        return f"scenespeak:{hashlib.sha256(key_data.encode()).hexdigest()}"

    async def close(self) -> None:
        """Close the cache connection."""
        await self._redis_cache.close()

    @property
    def is_connected(self) -> bool:
        """Check if cache is connected."""
        return self._redis_cache.is_connected

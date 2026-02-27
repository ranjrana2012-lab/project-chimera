"""Response caching layer."""
import hashlib
import json
from typing import Optional, Any
import redis.asyncio as redis


class ResponseCache:
    """Caches LLM responses."""

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl: int = 3600
    ):
        self.redis = redis_client
        self.ttl = ttl

    def _make_key(self, prompt: str, params: dict) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = f"{prompt}:{json.dumps(params, sort_keys=True)}"
        return f"chimera:scenespeak:cache:{hashlib.sha256(key_data.encode()).hexdigest()}"

    async def get(self, prompt: str, params: dict) -> Optional[Any]:
        """Get cached response."""
        key = self._make_key(prompt, params)
        cached = await self.redis.get(key)

        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None

    async def set(self, prompt: str, params: dict, response: Any) -> None:
        """Cache a response."""
        key = self._make_key(prompt, params)
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(response)
        )

    async def clear(self) -> None:
        """Clear all cache."""
        # Delete all keys matching pattern
        for key in await self.redis.keys("chimera:scenespeak:cache:*"):
            await self.redis.delete(key)

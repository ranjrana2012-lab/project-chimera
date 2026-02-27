"""
Redis Cache for SceneSpeak Agent
"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis


class RedisCache:
    """Redis-based cache for dialogue generations."""

    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client: Optional[aioredis.Redis] = None
        self.is_connected = False

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = await aioredis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
            encoding="utf-8",
            decode_responses=True,
        )
        self.is_connected = True

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected:
            return None

        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        if not self.is_connected:
            return

        try:
            await self._client.setex(
                key,
                ttl,
                json.dumps(value),
            )
        except Exception:
            pass

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if not self.is_connected:
            return

        try:
            await self._client.delete(key)
        except Exception:
            pass

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self.is_connected = False

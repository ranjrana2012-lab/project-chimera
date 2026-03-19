# services/nemoclaw-orchestrator/state/store.py
"""Redis-backed state store for show state machine persistence."""
import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisStateStore:
    """Redis-backed store for persisting show state machine data.

    Provides async methods for saving, retrieving, and deleting show state data
    with configurable TTL for automatic cleanup.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "show_state",
        ttl: int = 3600,
    ):
        """Initialize the Redis state store.

        Args:
            redis_client: Optional existing Redis client (for testing)
            url: Redis connection URL (used if redis_client not provided)
            key_prefix: Prefix for Redis keys
            ttl: Time-to-live for state data in seconds (default: 1 hour)
        """
        self._redis = redis_client
        self._url = url
        self.key_prefix = key_prefix
        self.ttl = ttl

    def _make_key(self, show_id: str) -> str:
        """Generate a Redis key for the show state.

        Args:
            show_id: Unique show identifier

        Returns:
            Redis key string
        """
        return f"{self.key_prefix}:{show_id}"

    async def save_state(self, show_id: str, state_data: Dict[str, Any]) -> None:
        """Save show state to Redis.

        Args:
            show_id: Unique show identifier
            state_data: State data dictionary to persist

        Raises:
            Exception: If Redis operation fails
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        key = self._make_key(show_id)
        value = json.dumps(state_data)

        try:
            await self._redis.setex(key, self.ttl, value)
            logger.debug(f"Saved state for show {show_id}")
        except Exception as e:
            logger.error(f"Failed to save state for show {show_id}: {e}")
            raise

    async def get_state(self, show_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve show state from Redis.

        Args:
            show_id: Unique show identifier

        Returns:
            State data dictionary, or None if not found
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        key = self._make_key(show_id)

        try:
            value = await self._redis.get(key)
            if value is None:
                return None

            state_data = json.loads(value)
            logger.debug(f"Retrieved state for show {show_id}")
            return state_data
        except Exception as e:
            logger.error(f"Failed to get state for show {show_id}: {e}")
            raise

    async def delete_state(self, show_id: str) -> int:
        """Delete show state from Redis.

        Args:
            show_id: Unique show identifier

        Returns:
            Number of keys deleted (0 or 1)
        """
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        key = self._make_key(show_id)

        try:
            result = await self._redis.delete(key)
            logger.debug(f"Deleted state for show {show_id}: {result} key(s) removed")
            return result
        except Exception as e:
            logger.error(f"Failed to delete state for show {show_id}: {e}")
            raise

    async def connect(self) -> None:
        """Establish Redis connection.

        Creates a new Redis connection if one wasn't provided at initialization.
        """
        if not self._redis:
            self._redis = await redis.from_url(self._url, decode_responses=True)
            logger.info(f"Connected to Redis at {self._url}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    @property
    def is_connected(self) -> bool:
        """Check if Redis client is connected."""
        return self._redis is not None

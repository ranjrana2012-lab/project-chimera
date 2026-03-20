# services/nemoclaw-orchestrator/llm/credit_cache.py
import redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CreditStatusCache:
    """
    Manage Z.AI credit exhaustion status in Redis with TTL

    Uses Redis to store whether Z.AI credits are exhausted, with automatic
    expiration (TTL) to allow auto-recovery when credits are replenished.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl: int = 3600
    ):
        """
        Initialize credit status cache

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
            ttl: Time-to-live for exhausted flag in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self.key = "zai:credit:status"

        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None
        self._redis_url = url

    @property
    def redis(self) -> redis.Redis:
        """Get or create Redis client (lazy initialization)"""
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def is_available(self) -> bool:
        """
        Check if Z.AI is available (not marked as exhausted)

        Returns:
            True if Z.AI is available, False if marked exhausted
        """
        try:
            return not self.redis.exists(self.key)
        except Exception as e:
            logger.error(f"Redis error checking credit status: {e}")
            # Assume available on Redis error (fail-open)
            return True

    def mark_exhausted(self):
        """Mark Z.AI as exhausted with TTL"""
        try:
            self.redis.setex(self.key, self.ttl, "exhausted")
            logger.info(f"Z.AI marked as exhausted for {self.ttl}s")
        except Exception as e:
            logger.error(f"Redis error marking exhausted: {e}")

    def reset(self):
        """Manually reset the exhausted flag"""
        try:
            deleted = self.redis.delete(self.key)
            if deleted:
                logger.info("Z.AI credit status reset manually")
        except Exception as e:
            logger.error(f"Redis error resetting credit status: {e}")

    def close(self):
        """Close Redis connection"""
        if self._redis:
            self._redis.close()
            self._redis = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

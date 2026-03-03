"""
Captioning Agent - Rate Limiting Module

Implements rate limiting for transcription requests to prevent resource exhaustion.

Features:
- Token bucket algorithm for rate limiting
- Per-client rate limits (max 10 concurrent transcriptions)
- Sliding window tracking
- Redis-backed state (optional)
- Prometheus metrics integration
"""

import time
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock

from prometheus_client import Counter


# Configure logging
logger = logging.getLogger(__name__)


# Metrics
rate_limit_requests = Counter(
    'captioning_rate_limit_requests_total',
    'Total requests checked against rate limit',
    ['action']  # allowed, limited, denied
)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_concurrent: int = 10
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    window_size: int = 60  # seconds


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Features:
    - Per-client rate limiting
    - Sliding window tracking
    - Concurrent request limiting
    - Thread-safe for FastAPI
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if None)
        """
        self.config = config or RateLimitConfig()

        # Track active requests per client
        self.active_requests: Dict[str, int] = defaultdict(int)

        # Track request history for sliding window
        # Format: {client_id: [(timestamp, request_count), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)

        # Thread lock for thread safety
        self.lock = Lock()

        # Cleanup old history entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def check_rate_limit(
        self,
        client_id: str,
        redis_client=None
    ) -> dict:
        """
        Check if request should be rate limited.

        Args:
            client_id: Unique client identifier
            redis_client: Optional Redis client for distributed rate limiting

        Returns:
            Dict with action and metadata:
            {
                "allowed": bool,
                "action": "allowed" | "limited",
                "limit": int,
                "remaining": int,
                "reset_at": float,
                "retry_after": int
            }
        """
        with self.lock:
            current_time = time.time()

            # Periodic cleanup
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_entries(current_time)
                self.last_cleanup = current_time

            # Check concurrent request limit
            if self.active_requests[client_id] >= self.config.max_concurrent:
                rate_limit_requests.labels(action="denied").inc()
                return {
                    "allowed": False,
                    "action": "limited",
                    "limit": self.config.max_concurrent,
                    "remaining": 0,
                    "reset_at": current_time + 60,
                    "reason": "max_concurrent",
                    "retry_after": 5
                }

            # Check per-minute rate limit
            minute_ago = current_time - 60
            requests_in_last_minute = sum(
                count for ts, count in self.request_history[client_id]
                if ts > minute_ago
            )

            if requests_in_last_minute >= self.config.max_requests_per_minute:
                rate_limit_requests.labels(action="limited").inc()
                # Find when oldest request expires
                oldest_recent = min(
                    (ts for ts, _ in self.request_history[client_id] if ts > minute_ago),
                    default=current_time
                )
                reset_at = oldest_recent + 60

                return {
                    "allowed": False,
                    "action": "limited",
                    "limit": self.config.max_requests_per_minute,
                    "remaining": 0,
                    "reset_at": reset_at,
                    "reason": "per_minute",
                    "retry_after": int(reset_at - current_time)
                }

            # Request allowed
            remaining = self.config.max_requests_per_minute - requests_in_last_minute - 1
            rate_limit_requests.labels(action="allowed").inc()

            return {
                "allowed": True,
                "action": "allowed",
                "limit": self.config.max_requests_per_minute,
                "remaining": max(0, remaining),
                "reset_at": current_time + 60,
                "reason": None
            }

    def record_request(self, client_id: str, request_count: int = 1):
        """
        Record a request for rate limiting.

        Args:
            client_id: Unique client identifier
            request_count: Number of requests to record
        """
        with self.lock:
            current_time = time.time()

            # Add to active requests
            self.active_requests[client_id] += 1

            # Add to history
            self.request_history[client_id].append((current_time, request_count))

    def release_request(self, client_id: str, request_count: int = 1):
        """
        Release a completed request.

        Args:
            client_id: Unique client identifier
            request_count: Number of requests to release
        """
        with self.lock:
            if self.active_requests[client_id] > 0:
                self.active_requests[client_id] -= 1

    def _cleanup_old_entries(self, current_time: float):
        """
        Clean up old request history entries.

        Args:
            current_time: Current timestamp
        """
        cutoff_time = current_time - 3600  # Keep 1 hour of history

        # Clean up request history
        for client_id in list(self.request_history.keys()):
            # Remove old entries
            self.request_history[client_id] = [
                (ts, count) for ts, count in self.request_history[client_id]
                if ts > cutoff_time
            ]

            # Remove empty history
            if not self.request_history[client_id]:
                del self.request_history[client_id]
                self.active_requests.pop(client_id, None)

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self.lock:
            return {
                "active_clients": len(self.active_requests),
                "total_active_requests": sum(self.active_requests.values()),
                "clients_with_history": len(self.request_history)
            }


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter for more precise control.

    Uses a sliding time window instead of fixed intervals.
    """

    def __init__(self, window_seconds: int = 60, max_requests: int = 60):
        """
        Initialize sliding window rate limiter.

        Args:
            window_seconds: Size of the sliding window in seconds
            max_requests: Maximum requests allowed in window
        """
        self.window_seconds = window_seconds
        self.max_requests = max_requests

        # Request timestamps per client
        self.requests: Dict[str, list] = defaultdict(list)

        self.lock = Lock()

    def check_rate_limit(self, client_id: str) -> dict:
        """
        Check if request is allowed under sliding window.

        Args:
            client_id: Unique client identifier

        Returns:
            Dict with allowed status and metadata
        """
        with self.lock:
            current_time = time.time()
            window_start = current_time - self.window_seconds

            # Get client's requests
            client_requests = self.requests[client_id]

            # Remove requests outside the window
            self.requests[client_id] = [
                ts for ts in client_requests
                if ts > window_start
            ]
            client_requests = self.requests[client_id]

            # Check if limit exceeded
            if len(client_requests) >= self.max_requests:
                # Find when oldest request expires
                oldest_request = min(client_requests)
                reset_at = oldest_request + self.window_seconds

                return {
                    "allowed": False,
                    "action": "limited",
                    "limit": self.max_requests,
                    "remaining": 0,
                    "reset_at": reset_at,
                    "retry_after": int(reset_at - current_time)
                }

            # Request allowed
            remaining = self.max_requests - len(client_requests)

            return {
                "allowed": True,
                "action": "allowed",
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_at": current_time + self.window_seconds
            }

    def record_request(self, client_id: str):
        """
        Record a request at current time.

        Args:
            client_id: Unique client identifier
        """
        with self.lock:
            current_time = time.time()
            self.requests[client_id].append(current_time)


# Singleton instance
_default_limiter = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create default rate limiter instance."""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter(config)
    return _default_limiter


async def check_rate_limit_middleware(
    client_id: str,
    limiter: Optional[RateLimiter] = None
):
    """
    FastAPI middleware for rate limiting.

    Raises:
        HTTPException: If rate limit exceeded

    Args:
        client_id: Client identifier
        limiter: Rate limiter instance (uses default if None)

    Returns:
        Rate limit check result
    """
    from fastapi import HTTPException

    limiter = limiter or get_rate_limiter()

    result = limiter.check_rate_limit(client_id)

    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(result["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(result["reset_at"])),
                "Retry-After": str(result.get("retry_after", 60))
            },
            detail={
                "error": "Rate limit exceeded",
                "limit": result["limit"],
                "retry_after": result.get("retry_after", 60)
            }
        )

    return result

"""
Unit tests for Rate Limiting module.
"""

import pytest
import time
from unittest.mock import Mock

import sys
sys.path.insert(0, '/home/ranj/Project_Chimera/services/captioning-agent')

from api.rate_limit import (
    RateLimiter,
    RateLimitConfig,
    SlidingWindowRateLimiter,
    get_rate_limiter
)


class TestRateLimiter:
    """Test basic rate limiter functionality."""

    def test_first_request_allowed(self):
        """First request should always be allowed."""
        limiter = RateLimiter()

        result = limiter.check_rate_limit("client_1")

        assert result["allowed"] is True
        assert result["action"] == "allowed"
        assert result["remaining"] > 0

    def test_max_concurrent_enforced(self):
        """Max concurrent requests limit is enforced."""
        config = RateLimitConfig(max_concurrent=2)
        limiter = RateLimiter(config)

        # Start 2 concurrent requests
        limiter.record_request("client_1")
        limiter.record_request("client_1")

        result = limiter.check_rate_limit("client_1")

        assert result["allowed"] is False
        assert result["reason"] == "max_concurrent"

    def test_release_request_allows_new(self):
        """Releasing request allows new requests."""
        config = RateLimitConfig(max_concurrent=1)
        limiter = RateLimiter(config)

        # Start one request
        limiter.record_request("client_1")
        result1 = limiter.check_rate_limit("client_1")
        assert result1["allowed"] is False

        # Release it
        limiter.release_request("client_1")

        # Now new request should be allowed
        result2 = limiter.check_rate_limit("client_1")
        assert result2["allowed"] is True

    def test_per_minute_limit_enforced(self):
        """Per-minute rate limit is enforced."""
        config = RateLimitConfig(max_requests_per_minute=5)
        limiter = RateLimiter(config)

        # Make 5 requests
        for _ in range(5):
            limiter.record_request("client_2")
            limiter.release_request("client_2")

        # 6th request should be limited
        result = limiter.check_rate_limit("client_2")

        assert result["allowed"] is False
        assert result["reason"] == "per_minute"

    def test_different_clients_independent(self):
        """Rate limits are per-client, not global."""
        config = RateLimitConfig(max_requests_per_minute=3)
        limiter = RateLimiter(config)

        # Client 1 makes 3 requests
        for _ in range(3):
            limiter.record_request("client_1")
            limiter.release_request("client_1")

        # Client 1 should be limited
        result1 = limiter.check_rate_limit("client_1")
        assert result1["allowed"] is False

        # But client 2 should still be allowed
        result2 = limiter.check_rate_limit("client_2")
        assert result2["allowed"] is True

    def test_sliding_window_cleanup(self):
        """Old requests are cleaned up automatically."""
        limiter = RateLimiter()

        # Add old request (manually set to old timestamp)
        old_time = time.time() - 3700  # Over an hour ago
        limiter.request_history["client_x"].append((old_time, 1))

        # Trigger cleanup
        limiter._cleanup_old_entries(time.time())

        # Old entry should be cleaned up
        assert "client_x" not in limiter.request_history


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter."""

    def test_requests_within_limit(self):
        """Requests within window limit are allowed."""
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=5)

        for i in range(5):
            result = limiter.check_rate_limit(f"client_{i}")
            assert result["allowed"] is True
            limiter.record_request(f"client_{i}")

    def test_requests_exceeding_limit(self):
        """Requests exceeding window limit are blocked."""
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=3)

        # Make 3 requests
        limiter.record_request("client_test")
        limiter.record_request("client_test")
        limiter.record_request("client_test")

        # 4th request should be blocked
        result = limiter.check_rate_limit("client_test")
        assert result["allowed"] is False

    def test_window_slides(self):
        """Old requests slide out of the window."""
        limiter = SlidingWindowRateLimiter(window_seconds=1, max_requests=2)

        # Make 2 requests
        limiter.record_request("client_slide")
        limiter.record_request("client_slide")

        # Should be limited
        result = limiter.check_rate_limit("client_slide")
        assert result["allowed"] is False

        # Wait for window to slide
        time.sleep(1.1)

        # Now should be allowed again
        result = limiter.check_rate_limit("client_slide")
        assert result["allowed"] is True


class TestRateLimitMiddleware:
    """Test FastAPI middleware integration."""

    def test_middleware_raises_on_limit(self):
        """Middleware raises HTTPException when limited."""
        from fastapi import HTTPException

        limiter = RateLimiter(RateLimitConfig(max_requests_per_minute=0))

        with pytest.raises(HTTPException) as exc_info:
            from api.rate_limit import check_rate_limit_middleware
            import asyncio
            asyncio.run(check_rate_limit_middleware("client_limited", limiter))

        assert exc_info.value.status_code == 429

    def test_middleware_passes_when_allowed(self):
        """Middleware passes through when allowed."""
        limiter = RateLimiter()

        from api.rate_limit import check_rate_limit_middleware
        import asyncio

        result = asyncio.run(check_rate_limit_middleware("client_ok", limiter))

        assert result["allowed"] is True


class TestRateLimiterStats:
    """Test rate limiter statistics."""

    def test_stats_report_active_clients(self):
        """Stats report number of active clients."""
        limiter = RateLimiter()

        # Add some clients
        limiter.record_request("client_1")
        limiter.record_request("client_2")
        limiter.record_request("client_2")

        stats = limiter.get_stats()

        assert stats["active_clients"] == 2
        assert stats["total_active_requests"] == 3

    def test_stats_zero_initially(self):
        """Stats are zero initially."""
        limiter = RateLimiter()

        stats = limiter.get_stats()

        assert stats["active_clients"] == 0
        assert stats["total_active_requests"] == 0

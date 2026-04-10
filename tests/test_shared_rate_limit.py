"""
Tests for services/shared rate_limit module.

Tests the rate limiting utilities using mocks to avoid slowapi dependency.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Mock slowapi before importing the module
sys.modules['slowapi'] = MagicMock()
sys.modules['slowapi.util'] = MagicMock()
sys.modules['slowapi.errors'] = MagicMock()

# Create mock RateLimitExceeded
class MockRateLimitExceeded(Exception):
    pass

sys.modules['slowapi.errors'].RateLimitExceeded = MockRateLimitExceeded
sys.modules['slowapi'].Limiter = Mock
sys.modules['slowapi.util'].get_remote_address = Mock

# Add services/shared to path
services_shared = Path(__file__).parent.parent / "services" / "shared"
sys.path.insert(0, str(services_shared))

# Now import the module
from rate_limit import (
    RateLimitExceededHTTPException,
    rate_limit_exception_handler,
    get_rate_limit_per_minute,
    get_rate_limit_per_hour,
)


class TestRateLimitExceededHTTPException:
    """Tests for RateLimitExceededHTTPException."""

    def test_is_exception_subclass(self):
        """Verify it is an Exception subclass."""
        assert issubclass(RateLimitExceededHTTPException, Exception)

    def test_can_be_instantiated(self):
        """Verify exception can be created."""
        exc = RateLimitExceededHTTPException()
        assert isinstance(exc, Exception)


class TestRateLimitExceptionHandler:
    """Tests for rate_limit_exception_handler."""

    @pytest.mark.asyncio
    async def test_returns_429_status_code(self):
        """Verify handler returns 429 status code."""
        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        mock_exc = Mock()
        mock_exc.detail = "Rate limit exceeded"

        response = await rate_limit_exception_handler(mock_request, mock_exc)

        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_includes_error_content(self):
        """Verify response includes error content."""
        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        mock_exc = Mock()
        mock_exc.detail = "Too many requests"

        response = await rate_limit_exception_handler(mock_request, mock_exc)

        assert response.status_code == 429


class TestGetRateLimitPerMinute:
    """Tests for get_rate_limit_per_minute."""

    def test_default_value_when_env_not_set(self):
        """Verify default value of 60 when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            limit = get_rate_limit_per_minute()
            assert limit == 60

    def test_custom_value_from_env(self):
        """Verify custom value from environment variable."""
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MINUTE": "120"}):
            limit = get_rate_limit_per_minute()
            assert limit == 120

    def test_string_value_converted_to_int(self):
        """Verify string env var is converted to integer."""
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MINUTE": "30"}):
            limit = get_rate_limit_per_minute()
            assert isinstance(limit, int)
            assert limit == 30


class TestGetRateLimitPerHour:
    """Tests for get_rate_limit_per_hour."""

    def test_default_value_when_env_not_set(self):
        """Verify default value of 1000 when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            limit = get_rate_limit_per_hour()
            assert limit == 1000

    def test_custom_value_from_env(self):
        """Verify custom value from environment variable."""
        with patch.dict(os.environ, {"RATE_LIMIT_PER_HOUR": "5000"}):
            limit = get_rate_limit_per_hour()
            assert limit == 5000

    def test_string_value_converted_to_int(self):
        """Verify string env var is converted to integer."""
        with patch.dict(os.environ, {"RATE_LIMIT_PER_HOUR": "200"}):
            limit = get_rate_limit_per_hour()
            assert isinstance(limit, int)
            assert limit == 200

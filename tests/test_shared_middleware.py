"""
Tests for services/shared middleware module.

Tests the security middleware using mocks to avoid slowapi dependency.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Mock slowapi before importing; use the real installed Starlette package so
# this test does not poison sys.modules for later FastAPI tests.
sys.modules['slowapi'] = MagicMock()
sys.modules['slowapi.util'] = MagicMock()
sys.modules['slowapi.errors'] = MagicMock()

# Create mock classes
class MockRateLimitExceeded(Exception):
    pass

sys.modules['slowapi.errors'].RateLimitExceeded = MockRateLimitExceeded
sys.modules['slowapi'].Limiter = Mock
sys.modules['slowapi.util'].get_remote_address = Mock

# Add services/shared to path
services_shared = Path(__file__).parent.parent / "services" / "shared"
sys.path.insert(0, str(services_shared))

# Now import the module functions that don't need slowapi
import middleware


class TestGetCORSOrigins:
    """Tests for get_cors_origins."""

    def test_default_origins_when_env_not_set(self):
        """Verify default origins when CORS_ORIGINS not set."""
        with patch.dict(os.environ, {}, clear=True):
            origins = middleware.get_cors_origins()
            assert "http://localhost:3000" in origins
            assert "http://localhost:8000" in origins

    def test_single_origin_from_env(self):
        """Verify single origin from environment variable."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com"}):
            origins = middleware.get_cors_origins()
            assert origins == ["https://example.com"]

    def test_multiple_origins_from_env(self):
        """Verify multiple comma-separated origins from environment."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com,https://api.example.com"}):
            origins = middleware.get_cors_origins()
            assert len(origins) == 2
            assert "https://example.com" in origins
            assert "https://api.example.com" in origins

    def test_whitespace_stripped_from_origins(self):
        """Verify whitespace is stripped from origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": " https://example.com , https://api.example.com "}):
            origins = middleware.get_cors_origins()
            assert origins == ["https://example.com", "https://api.example.com"]


class TestConfigureCORS:
    """Tests for configure_cors."""

    def test_adds_middleware_to_app(self):
        """Verify CORS middleware is added to FastAPI app."""
        mock_app = Mock()
        mock_app.add_middleware = Mock()

        with patch.dict(os.environ, {}, clear=True):
            middleware.configure_cors(mock_app)

        mock_app.add_middleware.assert_called_once()

    def test_passes_correct_arguments(self):
        """Verify correct arguments passed to middleware."""
        mock_app = Mock()
        mock_app.add_middleware = Mock()

        with patch.dict(os.environ, {}, clear=True):
            middleware.configure_cors(mock_app)

        call_kwargs = mock_app.add_middleware.call_args[1]
        assert "allow_origins" in call_kwargs
        assert "allow_credentials" in call_kwargs
        assert call_kwargs["allow_credentials"] is True
        assert "allow_methods" in call_kwargs
        assert "allow_headers" in call_kwargs


class TestLimiter:
    """Tests for limiter instance."""

    def test_limiter_instance_exists(self):
        """Verify limiter instance is created."""
        assert hasattr(middleware, 'limiter')
        assert middleware.limiter is not None


class TestSetupRateLimitErrorHandler:
    """Tests for setup_rate_limit_error_handler."""

    def test_adds_exception_handler_to_app(self):
        """Verify exception handler is registered with app."""
        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        middleware.setup_rate_limit_error_handler(mock_app)

        mock_app.add_exception_handler.assert_called_once()


class TestModuleExports:
    """Tests for module exports."""

    def test_has_expected_functions(self):
        """Verify module has expected functions."""
        expected_exports = [
            "get_cors_origins",
            "configure_cors",
            "limiter",
            "setup_rate_limit_error_handler",
        ]

        for export in expected_exports:
            assert hasattr(middleware, export)

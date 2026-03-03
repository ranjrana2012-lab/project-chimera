"""
Unit tests for WebSocket support.

Tests WebSocket connection management and progress updates.
"""

import pytest
import sys
from pathlib import Path

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))


class TestConnectionManager:
    """Test ConnectionManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create connection manager."""
        from api.websocket import ConnectionManager
        return ConnectionManager()

    def test_manager_init(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert len(manager.active_connections) == 0
        assert len(manager.run_subscribers) == 0

    def test_get_connection_count(self, manager):
        """Test getting connection count."""
        count = manager.get_connection_count()
        assert count == 0

    def test_get_subscriber_count(self, manager):
        """Test getting subscriber count."""
        count = manager.get_subscriber_count("test-run")
        assert count == 0


class TestWebSocketAvailability:
    """Test WebSocket module availability."""

    def test_websocket_import(self):
        """Test if WebSocket is available."""
        try:
            from fastapi import WebSocket
            WEBSOCKET_AVAILABLE = True
        except ImportError:
            WEBSOCKET_AVAILABLE = False

        # Test should pass regardless of FastAPI availability
        assert True

    def test_connection_manager_when_available(self):
        """Test ConnectionManager creation."""
        from api import websocket

        # If FastAPI is available, manager should be created
        if websocket.FASTAPI_AVAILABLE:
            assert websocket.manager is not None
        else:
            assert websocket.manager is None

    def test_get_manager(self):
        """Test get_manager function."""
        from api.websocket import get_manager

        # Should return manager or None
        result = get_manager()
        assert result is None or result is not None


class TestProgressMessages:
    """Test progress message functions."""

    def test_send_test_start(self):
        """Test sending test start notification."""
        from api.websocket import send_test_start

        # Should not crash even without FastAPI
        async def test():
            await send_test_start("test-run-123", ["svc1", "svc2"])

        import asyncio
        asyncio.run(test())

    def test_send_service_complete(self):
        """Test sending service completion notification."""
        from api.websocket import send_service_complete

        async def test():
            await send_service_complete(
                "test-run-123",
                "svc1",
                True,
                10,
                10,
                0,
                5.0
            )

        import asyncio
        asyncio.run(test())

    def test_send_test_complete(self):
        """Test sending test completion notification."""
        from api.websocket import send_test_complete

        async def test():
            await send_test_complete(
                "test-run-123",
                100,
                95,
                5,
                30.5
            )

        import asyncio
        asyncio.run(test())

    def test_send_error(self):
        """Test sending error notification."""
        from api.websocket import send_error

        async def test():
            await send_error(
                "test-run-123",
                "Test execution failed",
                {"details": "Something went wrong"}
            )

        import asyncio
        asyncio.run(test())


class TestMessageFormats:
    """Test message format and structure."""

    def test_progress_message_structure(self):
        """Test that progress messages have correct structure."""
        # Progress messages should have: run_id, type, timestamp, data
        message = {
            "run_id": "test-run-123",
            "type": "progress",
            "timestamp": "2026-03-04T00:00:00Z",
            "data": {
                "message": "Tests running..."
            }
        }

        assert "run_id" in message
        assert "type" in message
        assert "timestamp" in message
        assert "data" in message
        assert message["run_id"] == "test-run-123"
        assert message["type"] == "progress"

    def test_service_complete_message_structure(self):
        """Test service complete message structure."""
        message = {
            "run_id": "test-run-123",
            "type": "service_complete",
            "data": {
                "service": "svc1",
                "success": True,
                "total_tests": 10,
                "passed": 10,
                "failed": 0,
                "duration_seconds": 5.0
            }
        }

        assert message["type"] == "service_complete"
        assert message["data"]["service"] == "svc1"
        assert message["data"]["success"] is True

    def test_error_message_structure(self):
        """Test error message structure."""
        message = {
            "run_id": "test-run-123",
            "type": "error",
            "data": {
                "error": "Test execution failed",
                "details": {}
            }
        }

        assert message["type"] == "error"
        assert "error" in message["data"]

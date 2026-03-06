"""Tests for WebSocket connection manager."""

import pytest
from unittest.mock import Mock, AsyncMock

from websocket_manager import ConnectionManager


class TestConnectionManager:
    """Tests for ConnectionManager."""

    @pytest.fixture
    def manager(self):
        """Create a connection manager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test WebSocket connection."""
        connection_id = "test-conn-1"

        await manager.connect(mock_websocket, connection_id)

        assert connection_id in manager.active_connections
        assert connection_id in manager.subscriptions
        assert connection_id in manager.connection_metadata
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnection."""
        connection_id = "test-conn-1"

        await manager.connect(mock_websocket, connection_id)
        manager.disconnect(connection_id)

        assert connection_id not in manager.active_connections
        assert connection_id not in manager.subscriptions
        assert connection_id not in manager.connection_metadata

    def test_subscribe(self, manager):
        """Test subscribing to a channel."""
        connection_id = "test-conn-1"
        manager.subscriptions[connection_id] = set()

        result = manager.subscribe(connection_id, "metrics")

        assert result is True
        assert "metrics" in manager.subscriptions[connection_id]

    def test_unsubscribe(self, manager):
        """Test unsubscribing from a channel."""
        connection_id = "test-conn-1"
        manager.subscriptions[connection_id] = {"metrics", "alerts"}

        result = manager.unsubscribe(connection_id, "metrics")

        assert result is True
        assert "metrics" not in manager.subscriptions[connection_id]

    @pytest.mark.asyncio
    async def test_broadcast(self, manager, mock_websocket):
        """Test broadcasting a message."""
        # Connect two clients
        await manager.connect(mock_websocket, "conn-1")
        await manager.connect(mock_websocket, "conn-2")

        message = {"type": "test", "data": {"value": 123}}

        sent_count = await manager.broadcast(message, "metrics")

        # Should send to both connections
        assert sent_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_metric(self, manager, mock_websocket):
        """Test broadcasting a metric update."""
        await manager.connect(mock_websocket, "conn-1")

        sent_count = await manager.broadcast_metric(
            service_name="test-service",
            metric_name="cpu_percent",
            value=75.5,
            unit="%"
        )

        assert sent_count == 1
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_alert(self, manager, mock_websocket):
        """Test broadcasting an alert."""
        await manager.connect(mock_websocket, "conn-1")

        sent_count = await manager.broadcast_alert(
            alert_id="alert-123",
            severity="warning",
            title="Test Alert",
            message="This is a test alert",
            source="test-service"
        )

        assert sent_count == 1
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_status(self, manager, mock_websocket):
        """Test broadcasting a status update."""
        await manager.connect(mock_websocket, "conn-1")

        sent_count = await manager.broadcast_status(
            service_name="test-service",
            status="up",
            health_check="healthy"
        )

        assert sent_count == 1
        mock_websocket.send_json.assert_called()

    def test_get_connection_count(self, manager):
        """Test getting connection count."""
        assert manager.get_connection_count() == 0

        # Simulate adding connections
        manager.active_connections["conn-1"] = Mock()
        manager.active_connections["conn-2"] = Mock()

        assert manager.get_connection_count() == 2

    def test_get_connection_info(self, manager):
        """Test getting connection info."""
        connection_id = "test-conn-1"
        manager.subscriptions[connection_id] = {"metrics", "alerts"}
        manager.connection_metadata[connection_id] = {
            "connected_at": "2024-01-01T00:00:00",
            "messages_sent": 10,
            "last_message_at": "2024-01-01T00:01:00"
        }

        info = manager.get_connection_info(connection_id)

        assert info is not None
        assert info["connection_id"] == connection_id
        assert "metrics" in info["subscriptions"]
        assert "alerts" in info["subscriptions"]

    def test_get_all_connections_info(self, manager):
        """Test getting all connections info."""
        manager.active_connections["conn-1"] = Mock()
        manager.active_connections["conn-2"] = Mock()
        manager.subscriptions["conn-1"] = {"metrics"}
        manager.subscriptions["conn-2"] = {"alerts"}
        manager.connection_metadata["conn-1"] = {"messages_sent": 5}
        manager.connection_metadata["conn-2"] = {"messages_sent": 10}

        all_info = manager.get_all_connections_info()

        assert len(all_info) == 2

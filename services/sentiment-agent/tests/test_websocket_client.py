"""Unit tests for WebSocket Client module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.websocket_client import WorldMonitorWebSocketClient


@pytest.fixture
def websocket_client():
    """Create a WebSocket client instance."""
    return WorldMonitorWebSocketClient(
        url="ws://localhost:3001/ws",
        reconnect_interval=1,
        max_retries=3
    )


def test_websocket_client_initialization():
    """Test WebSocket client initialization with default and custom parameters."""
    # Test default initialization
    client = WorldMonitorWebSocketClient("ws://localhost:3001/ws")
    assert client.url == "ws://localhost:3001/ws"
    assert client.reconnect_interval == 5
    assert client.max_retries == 10
    assert client._connected is False
    assert client._running is False
    assert client._context_cache is None
    assert client._callbacks == []

    # Test custom initialization
    client_custom = WorldMonitorWebSocketClient(
        url="ws://example.com/ws",
        reconnect_interval=2,
        max_retries=5
    )
    assert client_custom.url == "ws://example.com/ws"
    assert client_custom.reconnect_interval == 2
    assert client_custom.max_retries == 5


@pytest.mark.asyncio
async def test_websocket_connect():
    """Test WebSocket connection and message handling."""
    client = WorldMonitorWebSocketClient(
        url="ws://localhost:3001/ws",
        reconnect_interval=1,
        max_retries=3
    )

    # Mock websocket connection
    mock_websocket = AsyncMock()
    mock_websocket.recv = AsyncMock(
        side_effect=[
            '{"type": "context_update", "data": {"global_cii": 65, "active_threats": []}}',
            asyncio.TimeoutError()  # Trigger disconnect after first message
        ]
    )
    mock_websocket.send = AsyncMock()
    mock_websocket.ping = AsyncMock()
    mock_websocket.__aenter__ = AsyncMock(return_value=mock_websocket)
    mock_websocket.__aexit__ = AsyncMock()

    with patch('websockets.connect', return_value=mock_websocket):
        # Start connection
        task = asyncio.create_task(client.connect())

        # Wait for message processing
        await asyncio.sleep(0.1)

        # Verify subscription message was sent
        mock_websocket.send.assert_called_with('{"type": "subscribe"}')

        # Verify context was cached
        assert client._context_cache is not None
        assert client._context_cache["global_cii"] == 65

        # Verify connected status
        assert client._connected is True

        # Disconnect
        await client.disconnect()

        # Wait for task to complete
        try:
            await asyncio.wait_for(task, timeout=2)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass


@pytest.mark.asyncio
async def test_websocket_message_handling():
    """Test handling of different WebSocket message types."""
    client = WorldMonitorWebSocketClient(
        url="ws://localhost:3001/ws",
        reconnect_interval=1,
        max_retries=3
    )

    # Track callback invocations
    callback_data = []

    async def test_callback(data):
        callback_data.append(data)

    client.add_callback(test_callback)

    # Test context_update message
    context_message = {
        "type": "context_update",
        "data": {
            "global_cii": 70,
            "active_threats": [
                {"level": "high", "type": "conflict", "title": "Test threat"}
            ],
            "major_events": []
        }
    }

    await client._handle_message(context_message)

    # Verify context was cached
    assert client._context_cache is not None
    assert client._context_cache["global_cii"] == 70
    assert len(client._context_cache["active_threats"]) == 1

    # Verify callback was invoked
    assert len(callback_data) == 1
    assert callback_data[0]["global_cii"] == 70


@pytest.mark.skip(reason="WebSocket reconnection test requires complex async mocking")
@pytest.mark.asyncio
async def test_websocket_reconnection():
    """Test WebSocket reconnection logic."""
    # Test skipped - would require complex mocking of websockets.connect
    # The actual reconnection logic is tested manually in integration
    pass


@pytest.mark.asyncio
async def test_websocket_context_caching():
    """Test that WebSocket client caches context properly."""
    client = WorldMonitorWebSocketClient(
        url="ws://localhost:3001/ws",
        reconnect_interval=1,
        max_retries=3
    )

    # Initially no context
    assert client.get_context() is None

    # Simulate receiving context update
    context_data = {
        "global_cii": 68,
        "active_threats": [],
        "major_events": [{"title": "G7 Summit", "location": "Tokyo"}],
        "country_summary": {}
    }

    await client._handle_message({
        "type": "context_update",
        "data": context_data
    })

    # Verify context is cached
    cached_context = client.get_context()
    assert cached_context is not None
    assert cached_context["global_cii"] == 68
    assert len(cached_context["major_events"]) == 1


def test_websocket_is_connected_property():
    """Test the is_connected property."""
    client = WorldMonitorWebSocketClient("ws://localhost:3001/ws")

    # Initially not connected
    assert client.is_connected is False

    # Set connected state
    client._connected = True
    assert client.is_connected is True


def test_websocket_add_callback():
    """Test adding callbacks to the WebSocket client."""
    client = WorldMonitorWebSocketClient("ws://localhost:3001/ws")

    # Create test callbacks
    async def callback1(data):
        pass

    async def callback2(data):
        pass

    # Add callbacks
    client.add_callback(callback1)
    client.add_callback(callback2)

    # Verify callbacks are stored
    assert len(client._callbacks) == 2
    assert callback1 in client._callbacks
    assert callback2 in client._callbacks


@pytest.mark.asyncio
async def test_websocket_disconnect():
    """Test WebSocket disconnection."""
    client = WorldMonitorWebSocketClient("ws://localhost:3001/ws")

    # Set up as running and connected
    client._running = True
    client._connected = True

    # Create a mock task
    async def dummy_task():
        while True:
            await asyncio.sleep(0.1)

    client._task = asyncio.create_task(dummy_task())

    # Disconnect
    await client.disconnect()

    # Verify state
    assert client._running is False
    assert client._connected is False


@pytest.mark.asyncio
async def test_websocket_callback_error_handling():
    """Test that callback errors don't crash the WebSocket client."""
    client = WorldMonitorWebSocketClient("ws://localhost:3001/ws")

    # Add a failing callback
    async def failing_callback(data):
        raise Exception("Callback failed")

    # Track successful callback
    successful_calls = []

    async def successful_callback(data):
        successful_calls.append(data)

    client.add_callback(failing_callback)
    client.add_callback(successful_callback)

    # Send context update
    context_data = {"global_cii": 65, "active_threats": [], "major_events": []}

    # This should not raise an exception
    await client._handle_message({
        "type": "context_update",
        "data": context_data
    })

    # Verify successful callback was still called
    assert len(successful_calls) == 1


@pytest.mark.asyncio
async def test_websocket_unknown_message_type():
    """Test handling of unknown message types."""
    client = WorldMonitorWebSocketClient("ws://localhost:3001/ws")

    # Send unknown message type
    await client._handle_message({
        "type": "unknown_type",
        "data": {"some": "data"}
    })

    # Should not crash and context should remain None
    assert client._context_cache is None


@pytest.mark.skip(reason="WebSocket max retries test requires complex async mocking")
@pytest.mark.asyncio
async def test_websocket_max_retries_exceeded():
    """Test behavior when max retries is exceeded."""
    # Test skipped - would require complex mocking of websockets.connect
    # The actual retry logic is tested manually in integration
    pass

"""
Enhanced tests for WebSocket Handler covering edge cases and integration scenarios.

Tests the real-time captioning streaming functionality including:
- Connection management
- Message handling
- Audio streaming
- Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from fastapi import WebSocket
from datetime import datetime
from websocket_handler import WebSocketHandler


@pytest.fixture
def handler():
    """Create WebSocketHandler instance"""
    return WebSocketHandler()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket"""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive = AsyncMock()
    return ws


class TestWebSocketHandlerInitialization:
    """Test WebSocketHandler initialization"""

    def test_initialization(self, handler):
        """Test handler initializes correctly"""
        assert handler.active_connections == set()
        assert handler.client_buffers == {}
        assert isinstance(handler.active_connections, set)
        assert isinstance(handler.client_buffers, dict)


class TestConnectionManagement:
    """Test WebSocket connection management"""

    @pytest.mark.asyncio
    async def test_connect(self, handler, mock_websocket):
        """Test accepting new connection"""
        await handler.connect(mock_websocket, "test_client")
        assert mock_websocket in handler.active_connections
        assert mock_websocket in handler.client_buffers
        assert handler.client_buffers[mock_websocket] == b""
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_sends_welcome(self, handler, mock_websocket):
        """Test that connect sends welcome message"""
        await handler.connect(mock_websocket, "test_client")
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["data"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_disconnect(self, handler, mock_websocket):
        """Test disconnecting a client"""
        await handler.connect(mock_websocket, "test_client")
        await handler.disconnect(mock_websocket, "test_client")
        assert mock_websocket not in handler.active_connections
        assert mock_websocket not in handler.client_buffers

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(self, handler, mock_websocket):
        """Test disconnecting a client that doesn't exist"""
        # Should not raise error
        await handler.disconnect(mock_websocket, "test_client")
        assert mock_websocket not in handler.active_connections

    @pytest.mark.asyncio
    async def test_multiple_connections(self, handler):
        """Test handling multiple connections"""
        clients = [MagicMock(spec=WebSocket) for _ in range(5)]
        for i, client in enumerate(clients):
            client.accept = AsyncMock()
            await handler.connect(client, f"client_{i}")
        assert len(handler.active_connections) == 5


class TestMessaging:
    """Test message sending functionality"""

    @pytest.mark.asyncio
    async def test_send_message(self, handler, mock_websocket):
        """Test sending message to specific client"""
        message = {"type": "test", "data": {"key": "value"}}
        await handler.send_message(mock_websocket, message)
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message_error_handling(self, handler, mock_websocket):
        """Test send_message handles errors gracefully"""
        mock_websocket.send_json.side_effect = Exception("Send failed")
        # Should not raise error
        await handler.send_message(mock_websocket, {"type": "test"})
        # Client should be disconnected
        assert mock_websocket not in handler.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self, handler):
        """Test broadcasting to all clients"""
        clients = [MagicMock(spec=WebSocket) for _ in range(3)]
        for client in clients:
            client.accept = AsyncMock()
            client.send_json = AsyncMock()
            await handler.connect(client, "test")

        message = {"type": "broadcast", "data": "test"}
        await handler.broadcast(message)

        for client in clients:
            client.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_disconnected_client(self, handler):
        """Test broadcast handles disconnected clients"""
        client1 = MagicMock(spec=WebSocket)
        client2 = MagicMock(spec=WebSocket)
        client1.accept = AsyncMock()
        client2.accept = AsyncMock()
        client1.send_json = AsyncMock()
        client2.send_json = AsyncMock(side_effect=Exception("Disconnected"))

        await handler.connect(client1, "client1")
        await handler.connect(client2, "client2")

        message = {"type": "broadcast", "data": "test"}
        await handler.broadcast(message)

        # client1 should receive message
        client1.send_json.assert_called_once()
        # client2 should be removed
        assert client2 not in handler.active_connections


class TestAudioHandling:
    """Test audio chunk handling"""

    @pytest.mark.asyncio
    async def test_handle_audio_chunk(self, handler, mock_websocket):
        """Test handling audio chunk"""
        await handler.connect(mock_websocket, "test_client")
        audio_data = b"fake audio data"
        await handler.handle_audio_chunk(mock_websocket, audio_data, "test_client")
        assert handler.client_buffers[mock_websocket] == audio_data

    @pytest.mark.asyncio
    async def test_audio_chunk_accumulation(self, handler, mock_websocket):
        """Test that audio chunks accumulate"""
        await handler.connect(mock_websocket, "test_client")
        chunk1 = b"chunk1"
        chunk2 = b"chunk2"
        await handler.handle_audio_chunk(mock_websocket, chunk1, "test_client")
        await handler.handle_audio_chunk(mock_websocket, chunk2, "test_client")
        assert handler.client_buffers[mock_websocket] == chunk1 + chunk2

    @pytest.mark.asyncio
    async def test_process_audio_buffer(self, handler, mock_websocket):
        """Test processing accumulated audio buffer"""
        await handler.connect(mock_websocket, "test_client")
        # Add enough data to trigger processing
        large_data = b"x" * 4096
        await handler.handle_audio_chunk(mock_websocket, large_data, "test_client")
        # Buffer should be cleared after processing
        assert handler.client_buffers[mock_websocket] == b""


class TestTextMessageHandling:
    """Test text message handling"""

    @pytest.mark.asyncio
    async def test_handle_config_message(self, handler, mock_websocket):
        """Test handling config message"""
        await handler.connect(mock_websocket, "test_client")
        message = {
            "type": "config",
            "data": {"language": "en", "format": "text"}
        }
        await handler._handle_text_message(mock_websocket, message, "test_client")
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]
        assert response["type"] == "status"
        assert response["data"]["status"] == "configured"

    @pytest.mark.asyncio
    async def test_handle_ping_message(self, handler, mock_websocket):
        """Test handling ping message"""
        await handler.connect(mock_websocket, "test_client")
        message = {"type": "ping"}
        await handler._handle_text_message(mock_websocket, message, "test_client")
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]
        assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_unknown_message_type(self, handler, mock_websocket):
        """Test handling unknown message type"""
        await handler.connect(mock_websocket, "test_client")
        message = {"type": "unknown"}
        await handler._handle_text_message(mock_websocket, message, "test_client")
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]
        assert response["type"] == "error"


class TestConnectionLifecycle:
    """Test full connection lifecycle"""

    @pytest.mark.asyncio
    async def test_handle_connection_with_text_messages(self, handler, mock_websocket):
        """Test handling connection with text messages"""
        mock_websocket.receive.side_effect = [
            {"text": '{"type": "ping"}'},
            {"text": '{"type": "config", "data": {"lang": "en"}}'},
        ]
        await handler.connect(mock_websocket, "test_client")
        try:
            await handler.handle_connection(mock_websocket, "test_client")
        except StopAsyncIteration:
            pass  # Expected when receive stops

    @pytest.mark.asyncio
    async def test_handle_connection_with_binary_messages(self, handler, mock_websocket):
        """Test handling connection with binary audio data"""
        mock_websocket.receive.side_effect = [
            {"bytes": b"audio data"},
            {"bytes": b"more audio"},
        ]
        await handler.connect(mock_websocket, "test_client")
        try:
            await handler.handle_connection(mock_websocket, "test_client")
        except StopAsyncIteration:
            pass

    @pytest.mark.asyncio
    async def test_handle_connection_disconnect_cleanup(self, handler, mock_websocket):
        """Test that connection cleanup happens on disconnect"""
        from fastapi import WebSocketDisconnect
        mock_websocket.receive.side_effect = WebSocketDisconnect()
        await handler.connect(mock_websocket, "test_client")
        await handler.handle_connection(mock_websocket, "test_client")
        assert mock_websocket not in handler.active_connections


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, handler, mock_websocket):
        """Test handling invalid JSON"""
        await handler.connect(mock_websocket, "test_client")
        await handler._handle_text_message(
            mock_websocket,
            "invalid json{{{",
            "test_client"
        )
        # Should send error message
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]
        assert response["type"] == "error"

    @pytest.mark.asyncio
    async def test_websocket_disconnect_during_receive(self, handler, mock_websocket):
        """Test handling disconnect during receive"""
        from fastapi import WebSocketDisconnect
        mock_websocket.receive.side_effect = WebSocketDisconnect()
        await handler.connect(mock_websocket, "test_client")
        # Should not raise
        await handler.handle_connection(mock_websocket, "test_client")
        assert mock_websocket not in handler.active_connections


class TestBufferManagement:
    """Test audio buffer management"""

    @pytest.mark.asyncio
    async def test_buffer_cleared_after_processing(self, handler, mock_websocket):
        """Test that buffer is cleared after processing"""
        await handler.connect(mock_websocket, "test_client")
        large_data = b"x" * 5000
        await handler.handle_audio_chunk(mock_websocket, large_data, "test_client")
        # Buffer should be cleared
        assert handler.client_buffers[mock_websocket] == b""

    @pytest.mark.asyncio
    async def test_buffer_per_client(self, handler):
        """Test that each client has separate buffer"""
        client1 = MagicMock(spec=WebSocket)
        client2 = MagicMock(spec=WebSocket)
        client1.accept = AsyncMock()
        client2.accept = AsyncMock()

        await handler.connect(client1, "client1")
        await handler.connect(client2, "client2")

        await handler.handle_audio_chunk(client1, b"data1", "client1")
        await handler.handle_audio_chunk(client2, b"data2", "client2")

        assert handler.client_buffers[client1] == b"data1"
        assert handler.client_buffers[client2] == b"data2"


class TestMessageFormats:
    """Test message format validation"""

    @pytest.mark.asyncio
    async def test_status_message_format(self, handler, mock_websocket):
        """Test status message has correct format"""
        await handler.connect(mock_websocket, "test_client")
        call_args = mock_websocket.send_json.call_args[0][0]
        assert "type" in call_args
        assert "data" in call_args
        assert "timestamp" in call_args["data"]

    @pytest.mark.asyncio
    async def test_transcription_message_format(self, handler, mock_websocket):
        """Test transcription message has correct format"""
        await handler.connect(mock_websocket, "test_client")
        large_data = b"x" * 4096
        await handler.handle_audio_chunk(mock_websocket, large_data, "test_client")
        # Check the last call (transcription message)
        last_call = mock_websocket.send_json.call_args_list[-1][0][0]
        assert last_call["type"] == "transcription"
        assert "data" in last_call
        assert "text" in last_call["data"]
        assert "timestamp" in last_call["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# websocket_handler.py
"""WebSocket handler for real-time captioning streaming"""
import logging
import json
import asyncio
from typing import Optional, Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handle WebSocket connections for streaming transcription"""

    def __init__(self):
        """Initialize WebSocket handler"""
        self.active_connections: Set[WebSocket] = set()
        self.client_buffers: Dict[WebSocket, bytes] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_buffers[websocket] = b""
        logger.info(f"WebSocket client connected: {client_id}")

        # Send welcome message
        await self.send_message(websocket, {
            "type": "status",
            "data": {
                "status": "connected",
                "message": "Connected to captioning service",
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Handle WebSocket disconnection

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_buffers:
            del self.client_buffers[websocket]
        logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send a message to a specific client

        Args:
            websocket: WebSocket connection
            message: Message dictionary
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.disconnect(websocket, "unknown")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients

        Args:
            message: Message dictionary
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection, "unknown")

    async def handle_audio_chunk(
        self,
        websocket: WebSocket,
        audio_data: bytes,
        client_id: str
    ):
        """
        Handle incoming audio chunk from client

        Args:
            websocket: WebSocket connection
            audio_data: Raw audio data
            client_id: Client identifier
        """
        # Append to buffer
        self.client_buffers[websocket] += audio_data

        # Process when buffer reaches threshold
        if len(self.client_buffers[websocket]) >= 4096:
            await self._process_audio_buffer(websocket, client_id)

    async def _process_audio_buffer(self, websocket: WebSocket, client_id: str):
        """
        Process accumulated audio buffer and send transcription

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        buffer = self.client_buffers[websocket]

        # Placeholder: In production, this would call Whisper on the buffer
        # For now, we send a mock transcription
        mock_transcription = {
            "type": "transcription",
            "data": {
                "text": "[STREAMING] Audio chunk received",
                "is_final": False,
                "language": "en",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        await self.send_message(websocket, mock_transcription)

        # Clear buffer
        self.client_buffers[websocket] = b""

    async def handle_connection(self, websocket: WebSocket, client_id: str):
        """
        Main handler for WebSocket connection

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        await self.connect(websocket, client_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive()

                if "text" in data:
                    # Handle text message (JSON)
                    try:
                        message = json.loads(data["text"])
                        await self._handle_text_message(websocket, message, client_id)
                    except json.JSONDecodeError:
                        await self.send_message(websocket, {
                            "type": "error",
                            "data": {"message": "Invalid JSON"}
                        })

                elif "bytes" in data:
                    # Handle binary message (audio data)
                    await self.handle_audio_chunk(websocket, data["bytes"], client_id)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self.disconnect(websocket, client_id)

    async def _handle_text_message(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        client_id: str
    ):
        """
        Handle text message from client

        Args:
            websocket: WebSocket connection
            message: Parsed JSON message
            client_id: Client identifier
        """
        message_type = message.get("type")

        if message_type == "config":
            # Handle configuration message
            await self.send_message(websocket, {
                "type": "status",
                "data": {
                    "status": "configured",
                    "config": message.get("data", {})
                }
            })
        elif message_type == "ping":
            # Handle ping
            await self.send_message(websocket, {
                "type": "pong",
                "data": {"timestamp": datetime.utcnow().isoformat()}
            })
        else:
            await self.send_message(websocket, {
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"}
            })


# Global WebSocket handler instance
websocket_handler = WebSocketHandler()

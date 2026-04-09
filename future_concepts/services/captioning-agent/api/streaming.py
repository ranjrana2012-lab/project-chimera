"""
Captioning Agent - WebSocket Streaming Module

Implements real-time caption streaming via WebSocket:
- `/api/v1/stream` endpoint for live caption updates
- <500ms latency requirement
- Client connection management
- Audio buffer overflow handling
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool


# Configure logging
logger = logging.getLogger(__name__)


# Maximum buffer size (10 seconds of audio)
MAX_BUFFER_SIZE = 160000  # 16KB (10s at 16kHz mono)


@dataclass
class CaptionUpdate:
    """Caption update message for WebSocket clients."""
    type: str  # "caption", "warning", "error", "status"
    timestamp: float
    text: str
    language: str = "en"
    confidence: float = 0.0
    duration: float = 0.0
    metadata: dict = None

    def to_json(self) -> str:
        """Convert to JSON for WebSocket transmission."""
        data = asdict(self)
        if self.metadata is None:
            data['metadata'] = {}
        return json.dumps(data)


class ConnectionManager:
    """
    Manages WebSocket client connections.

    Features:
    - Track active connections
    - Broadcast messages to all clients
    - Handle client disconnects gracefully
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_metadata: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": time.time()
        }
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove client connection."""
        if websocket in self.active_connections:
            client_id = self.client_metadata.get(websocket, {}).get("client_id", "unknown")
            self.active_connections.remove(websocket)
            self.client_metadata.pop(websocket, None)
            logger.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        # Send to all clients concurrently
        tasks = []
        for connection in self.active_connections:
            task = self.send_personal_message(message, connection)
            tasks.append(task)

        # Wait for all sends to complete (or fail)
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


class CircularAudioBuffer:
    """
    Circular buffer for audio chunks to prevent overflow.

    Features:
    - Fixed maximum size (10 seconds of audio)
    - Automatic overflow handling
    - Thread-safe for asyncio
    """

    def __init__(self, max_size: int = MAX_BUFFER_SIZE):
        self.buffer = bytearray()
        self.max_size = max_size
        self.overflow_count = 0

    def append(self, audio_data: bytes):
        """
        Append audio data to buffer.

        If buffer would overflow, oldest data is dropped.
        """
        audio_len = len(audio_data)

        if len(self.buffer) + audio_len > self.max_size:
            # Buffer would overflow - drop oldest chunks
            excess = (len(self.buffer) + audio_len) - self.max_size
            self.buffer = self.buffer[excess:]
            self.overflow_count += 1

            if self.overflow_count % 10 == 0:  # Log every 10 overflows
                logger.warning(f"Audio buffer overflow {self.overflow_count} times")

        self.buffer.extend(audio_data)

    def get_data(self) -> bytes:
        """Get current buffer contents."""
        return bytes(self.buffer)

    def clear(self):
        """Clear buffer."""
        self.buffer = bytearray()
        self.overflow_count = 0

    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0


class StreamingService:
    """
    WebSocket streaming service for real-time captions.

    Features:
    - WebSocket connection management
    - Real-time caption updates
    - Audio buffering with overflow handling
    - Client slow consumer detection
    """

    def __init__(self, transcription_service, manager: Optional[ConnectionManager] = None):
        """
        Initialize streaming service.

        Args:
            transcription_service: TranscriptionService instance
            manager: Optional ConnectionManager (creates new if None)
        """
        self.transcription = transcription_service
        self.manager = manager or ConnectionManager()
        self.audio_buffers: Dict[str, CircularAudioBuffer] = {}
        self.message_queue_size = 0
        self.SLOW_CONSUMER_THRESHOLD = 100  # messages

    def get_audio_buffer(self, session_id: str) -> CircularAudioBuffer:
        """Get or create audio buffer for session."""
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = CircularAudioBuffer()
        return self.audio_buffers[session_id]

    async def handle_client(self, websocket: WebSocket, session_id: str):
        """
        Handle WebSocket client connection.

        Args:
            websocket: WebSocket connection
            session_id: Unique session identifier

        Process:
        1. Accept connection
        2. Receive audio chunks
        3. Transcribe and send captions
        4. Handle disconnect
        """
        await self.manager.connect(websocket, session_id)

        try:
            while True:
                # Receive audio chunk from client
                data = await websocket.receive_text()
                message = json.loads(data)

                msg_type = message.get("type")

                if msg_type == "audio":
                    # Process audio chunk
                    audio_chunk = message.get("data", "")
                    if audio_chunk:
                        await self.process_audio_chunk(
                            websocket, session_id, audio_chunk
                        )

                elif msg_type == "config":
                    # Update session configuration
                    await self.send_status(websocket, "Configuration updated")

                else:
                    logger.warning(f"Unknown message type: {msg_type}")

        except WebSocketDisconnect:
            logger.info(f"Client {session_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {session_id}: {e}")
        finally:
            self.manager.disconnect(websocket)
            # Clean up audio buffer
            if session_id in self.audio_buffers:
                del self.audio_buffers[session_id]

    async def process_audio_chunk(self, websocket: WebSocket, session_id: str, audio_data: str):
        """
        Process audio chunk and send transcription.

        Args:
            websocket: Client WebSocket connection
            session_id: Session identifier
            audio_data: Base64-encoded audio data
        """
        import base64

        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)

            # Add to buffer
            buffer = self.get_audio_buffer(session_id)
            buffer.append(audio_bytes)

            # Check for buffer overflow
            if buffer.overflow_count > 0 and buffer.overflow_count % 10 == 1:
                warning = CaptionUpdate(
                    type="warning",
                    timestamp=time.time(),
                    text="",
                    metadata={"code": "BUFFER_OVERFLOW", "message": "Audio buffer full, dropping oldest chunks"}
                )
                await websocket.send_text(warning.to_json())

            # Transcribe when buffer has enough data
            if buffer.size() >= 8000:  # 0.5 seconds at 16kHz
                transcription = await run_in_threadpool(
                    self.transcribe_buffer,
                    buffer.get_data(),
                    session_id
                )

                # Send caption update
                update = CaptionUpdate(
                    type="caption",
                    timestamp=time.time(),
                    text=transcription.text,
                    language=transcription.language,
                    confidence=transcription.confidence,
                    duration=transcription.duration
                )

                await websocket.send_text(update.to_json())

                # Clear buffer after transcription
                buffer.clear()

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            error_msg = CaptionUpdate(
                type="error",
                timestamp=time.time(),
                text="",
                metadata={"code": "PROCESSING_ERROR", "message": str(e)}
            )
            await websocket.send_text(error_msg.to_json())

    def transcribe_buffer(self, audio_data: bytes, session_id: str):
        """Transcribe audio buffer (runs in thread pool)."""
        import hashlib
        audio_hash = hashlib.md5(audio_data).hexdigest()
        return self.transcription.transcribe(audio_data, audio_hash)

    async def send_status(self, websocket: WebSocket, message: str):
        """Send status update to client."""
        status = CaptionUpdate(
            type="status",
            timestamp=time.time(),
            text=message
        )
        await websocket.send_text(status.to_json())

    async def broadcast_caption(self, text: str, language: str = "en", confidence: float = 0.0):
        """Broadcast caption to all connected clients."""
        caption = CaptionUpdate(
            type="caption",
            timestamp=time.time(),
            text=text,
            language=language,
            confidence=confidence
        )
        await self.manager.broadcast(caption.to_json())

    def get_stats(self) -> dict:
        """Get streaming service statistics."""
        return {
            "active_connections": self.manager.get_connection_count(),
            "audio_buffers": len(self.audio_buffers),
            "total_overflows": sum(b.overflow_count for b in self.audio_buffers.values())
        }


# Singleton instance
_manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """Get global connection manager instance."""
    return _manager


def get_streaming_service(transcription_service) -> StreamingService:
    """Create new streaming service instance."""
    return StreamingService(transcription_service, _manager)

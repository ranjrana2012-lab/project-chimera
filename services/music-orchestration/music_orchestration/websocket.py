from typing import Dict, Set
from fastapi import WebSocket
import structlog

from music_orchestration.schemas import GenerationProgress


logger = structlog.get_logger()


class MusicWebSocket:
    """WebSocket manager for real-time progress updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.progress_state: Dict[str, dict] = {}

    async def subscribe(self, request_id: str, websocket: WebSocket) -> None:
        """Subscribe to progress updates for a request"""
        if request_id not in self.active_connections:
            self.active_connections[request_id] = set()

        self.active_connections[request_id].add(websocket)
        logger.info("websocket_subscribed", request_id=request_id)

    async def unsubscribe(self, request_id: str, websocket: WebSocket) -> None:
        """Unsubscribe from progress updates"""
        if request_id in self.active_connections:
            self.active_connections[request_id].discard(websocket)

            if not self.active_connections[request_id]:
                del self.active_connections[request_id]

    async def publish_progress(
        self,
        request_id: str,
        progress: int | None = None,
        stage: str | None = None,
        eta_seconds: int | None = None,
        error: str | None = None
    ) -> None:
        """Publish progress update to all subscribers"""
        msg = GenerationProgress(
            request_id=request_id,
            type="progress" if error is None else "failed",
            progress=progress,
            stage=stage,
            eta_seconds=eta_seconds,
            error=error
        )

        # Store state
        self.progress_state[request_id] = {
            "progress": progress,
            "stage": stage,
            "eta_seconds": eta_seconds,
            "error": error
        }

        # Send to all subscribers
        if request_id in self.active_connections:
            for connection in self.active_connections[request_id]:
                try:
                    await connection.send_json(msg.model_dump())
                except Exception as e:
                    logger.error("websocket_send_failed", request_id=request_id, error=str(e))

    def get_progress(self, request_id: str) -> dict | None:
        """Get current progress state"""
        return self.progress_state.get(request_id)

    async def broadcast_complete(self, request_id: str, music_id: str) -> None:
        """Broadcast completion message"""
        msg = GenerationProgress(
            request_id=request_id,
            type="completed",
            progress=100
        )

        if request_id in self.active_connections:
            for connection in self.active_connections[request_id]:
                try:
                    await connection.send_json({
                        **msg.model_dump(),
                        "music_id": music_id
                    })
                except Exception as e:
                    logger.error("websocket_send_failed", request_id=request_id, error=str(e))

        # Clean up
        self.progress_state.pop(request_id, None)


# Global instance
websocket_manager = MusicWebSocket()

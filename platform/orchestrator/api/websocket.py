"""
WebSocket support for real-time test progress.

Allows clients to subscribe to test execution progress.
"""

import logging
import json
import asyncio
from typing import Dict, Set, Any, Optional
from datetime import datetime, timezone

# WebSocket imports
try:
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.websockets import WebSocketState
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    WebSocket = None  # type: ignore

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for progress updates.

    Handles client subscriptions and broadcasts progress updates.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.run_subscribers: Dict[str, Set[WebSocket]] = {}

        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a new client.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()

        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()

        self.active_connections[client_id].add(websocket)

        logger.info(f"Client {client_id} connected")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Disconnect a client.

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)

            # Remove empty sets
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        # Unsubscribe from any runs
        for run_id, subscribers in self.run_subscribers.items():
            if websocket in subscribers:
                subscribers.discard(websocket)

        logger.info(f"Client {client_id} disconnected")

    def subscribe_to_run(self, websocket: WebSocket, run_id: str):
        """
        Subscribe a client to test run updates.

        Args:
            websocket: WebSocket connection
            run_id: Run identifier
        """
        if run_id not in self.run_subscribers:
            self.run_subscribers[run_id] = set()

        self.run_subscribers[run_id].add(websocket)

        logger.debug(f"Client subscribed to run {run_id}")

    def unsubscribe_from_run(self, websocket: WebSocket, run_id: str):
        """
        Unsubscribe a client from test run updates.

        Args:
            websocket: WebSocket connection
            run_id: Run identifier
        """
        if run_id in self.run_subscribers:
            self.run_subscribers[run_id].discard(websocket)

            # Remove empty sets
            if not self.run_subscribers[run_id]:
                del self.run_subscribers[run_id]

    async def broadcast_progress(
        self,
        run_id: str,
        message_type: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast progress update to run subscribers.

        Args:
            run_id: Run identifier
            message_type: Type of message (progress, complete, error)
            data: Message data
        """
        if run_id not in self.run_subscribers:
            return

        message = {
            "run_id": run_id,
            "type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        # Send to all subscribers
        disconnected = []
        for websocket in self.run_subscribers[run_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.append(websocket)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.run_subscribers[run_id].discard(ws)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
        """
        disconnected = []

        for client_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(message)
                    else:
                        disconnected.append(websocket)
                except Exception as e:
                    logger.warning(f"Failed to broadcast: {e}")
                    disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            for connections in self.active_connections.values():
                connections.discard(ws)

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_subscriber_count(self, run_id: str) -> int:
        """Get number of subscribers for a run."""
        return len(self.run_subscribers.get(run_id, set()))


# Global connection manager
manager = ConnectionManager() if FASTAPI_AVAILABLE else None


def get_manager() -> Optional[ConnectionManager]:
    """Get global connection manager."""
    return manager


async def send_test_start(
    run_id: str,
    services: Optional[list] = None
) -> None:
    """Send test start notification."""
    if manager is None:
        return

    await manager.broadcast_progress(
        run_id,
        "test_start",
        {
            "services": services or [],
            "message": "Test execution started"
        }
    )


async def send_service_complete(
    run_id: str,
    service: str,
    success: bool,
    total_tests: int,
    passed: int,
    failed: int,
    duration: float
) -> None:
    """Send service completion notification."""
    if manager is None:
        return

    await manager.broadcast_progress(
        run_id,
        "service_complete",
        {
            "service": service,
            "success": success,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "duration_seconds": duration
        }
    )


async def send_test_complete(
    run_id: str,
    total_tests: int,
    passed: int,
    failed: int,
    duration: float
) -> None:
    """Send test completion notification."""
    if manager is None:
        return

    await manager.broadcast_progress(
        run_id,
        "test_complete",
        {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "duration_seconds": duration,
            "success_rate": (passed / (total_tests or 1)) * 100
        }
    )


async def send_error(
    run_id: str,
    error: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Send error notification."""
    if manager is None:
        return

    await manager.broadcast_progress(
        run_id,
        "error",
        {
            "error": error,
            "details": details or {}
        }
    )

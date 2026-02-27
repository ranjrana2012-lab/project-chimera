"""WebSocket event streaming endpoints."""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from src.core.event_aggregator import EventAggregator
from src.models.response import EventType, StreamEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/events", tags=["events"])

# Module-level dependency
_aggregator: EventAggregator | None = None


def init_events(aggregator: EventAggregator) -> None:
    """Initialize events routes with dependencies.

    Args:
        aggregator: Event aggregator instance
    """
    global _aggregator
    _aggregator = aggregator


class WebSocketConnection:
    """Manages a WebSocket connection for event streaming."""

    def __init__(self, websocket: WebSocket, event_filter: Optional[dict] = None):
        """Initialize WebSocket connection.

        Args:
            websocket: WebSocket instance
            event_filter: Optional filter for events
        """
        self.websocket = websocket
        self.event_filter = event_filter or {}
        self.queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=100)

    def should_send_event(self, event: StreamEvent) -> bool:
        """Check if event should be sent based on filter.

        Args:
            event: Event to check

        Returns:
            True if event matches filter
        """
        if "event_type" in self.event_filter:
            if event.event_type.value != self.event_filter["event_type"]:
                return False

        if "severity" in self.event_filter:
            if event.severity.value != self.event_filter["severity"]:
                return False

        if "source_service" in self.event_filter:
            if event.source_service != self.event_filter["source_service"]:
                return False

        return True

    async def send_event(self, event: StreamEvent) -> None:
        """Send event to WebSocket.

        Args:
            event: Event to send
        """
        try:
            data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "timestamp": event.timestamp.isoformat(),
                "source_service": event.source_service,
                "title": event.title,
                "message": event.message,
                "data": event.data,
                "requires_approval": event.requires_approval,
                "approval_id": event.approval_id,
            }

            await self.websocket.send_json(data)

        except Exception as e:
            logger.error(f"Error sending event: {e}")


@router.websocket("/stream")
async def event_stream(
    websocket: WebSocket,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    source: Optional[str] = Query(None, description="Filter by source service"),
):
    """WebSocket endpoint for real-time event streaming.

    Connect to receive events as they happen. Optional query parameters
    can filter which events are sent.

    Example: ws://localhost:8007/v1/events/stream?severity=error
    """
    if not _aggregator:
        await websocket.close(code=1011, reason="Event aggregator not available")
        return

    await websocket.accept()

    # Build filter from query params
    event_filter = {}
    if event_type:
        event_filter["event_type"] = event_type
    if severity:
        event_filter["severity"] = severity
    if source:
        event_filter["source_service"] = source

    connection = WebSocketConnection(websocket, event_filter)

    # Subscribe to event aggregator
    queue = _aggregator.subscribe()

    logger.info(f"WebSocket connected: {id(websocket)} with filter: {event_filter}")

    try:
        # Send initial events
        recent_events = _aggregator.get_recent_events(limit=50)
        for event in recent_events:
            if connection.should_send_event(event):
                await connection.send_event(event)

        # Send keepalive and new events
        while True:
            try:
                # Wait for new event or timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)

                if connection.should_send_event(event):
                    await connection.send_event(event)

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "keepalive", "timestamp": "now"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {id(websocket)}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        # Unsubscribe from aggregator
        _aggregator.unsubscribe(queue)
        logger.info(f"WebSocket cleaned up: {id(websocket)}")


@router.get("/recent")
async def get_recent_events(
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
) -> dict:
    """Get recent events from the buffer.

    Args:
        limit: Maximum number of events
        event_type: Optional event type filter

    Returns:
        List of recent events
    """
    if not _aggregator:
        return {"events": [], "total": 0}

    type_filter = EventType(event_type) if event_type else None
    events = _aggregator.get_recent_events(limit=limit, event_type=type_filter)

    return {
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "severity": e.severity.value,
                "timestamp": e.timestamp.isoformat(),
                "source_service": e.source_service,
                "title": e.title,
                "message": e.message,
                "data": e.data,
                "requires_approval": e.requires_approval,
                "approval_id": e.approval_id,
            }
            for e in events
        ],
        "total": len(events),
    }


@router.get("/stats")
async def get_event_stats() -> dict:
    """Get event statistics.

    Returns:
        Event statistics
    """
    if not _aggregator:
        return {}

    return _aggregator.get_stats()

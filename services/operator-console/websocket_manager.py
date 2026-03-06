"""
WebSocket connection manager for Operator Console.

Manages WebSocket connections for real-time metrics and alert streaming.
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize the connection manager."""
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}

        # Connection subscriptions
        self.subscriptions: Dict[str, Set[str]] = {}

        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
        """
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = {"metrics", "alerts", "status"}
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.now().isoformat(),
            "messages_sent": 0,
            "last_message_at": None
        }
        logger.info(f"WebSocket connection established: {connection_id}")

    def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection.

        Args:
            connection_id: Connection identifier to disconnect
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        logger.info(f"WebSocket connection disconnected: {connection_id}")

    def subscribe(self, connection_id: str, channel: str) -> bool:
        """Subscribe a connection to a specific channel.

        Args:
            connection_id: Connection identifier
            channel: Channel to subscribe to (metrics, alerts, status)

        Returns:
            True if subscription successful, False otherwise
        """
        if connection_id not in self.subscriptions:
            return False

        self.subscriptions[connection_id].add(channel)
        logger.debug(f"Connection {connection_id} subscribed to {channel}")
        return True

    def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """Unsubscribe a connection from a specific channel.

        Args:
            connection_id: Connection identifier
            channel: Channel to unsubscribe from

        Returns:
            True if unsubscription successful, False otherwise
        """
        if connection_id not in self.subscriptions:
            return False

        self.subscriptions[connection_id].discard(channel)
        logger.debug(f"Connection {connection_id} unsubscribed from {channel}")
        return True

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> bool:
        """Send a message to a specific connection.

        Args:
            message: Message dictionary to send
            connection_id: Connection identifier

        Returns:
            True if message sent successfully, False otherwise
        """
        if connection_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)

            # Update metadata
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["messages_sent"] += 1
                self.connection_metadata[connection_id]["last_message_at"] = datetime.now().isoformat()

            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.disconnect(connection_id)
            return False

    async def broadcast(self, message: Dict[str, Any], channel: str = None) -> int:
        """Broadcast a message to all subscribed connections.

        Args:
            message: Message dictionary to broadcast
            channel: Channel to broadcast to (if None, sends to all)

        Returns:
            Number of connections the message was sent to
        """
        sent_count = 0

        # Determine target connections
        target_connections = (
            [conn_id for conn_id, subs in self.subscriptions.items()
             if channel is None or channel in subs]
        )

        # Send to all target connections
        for connection_id in target_connections:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1

        return sent_count

    async def broadcast_metric(self, service_name: str, metric_name: str, value: float, unit: str, metadata: Dict[str, Any] = None) -> int:
        """Broadcast a metric update to all subscribed connections.

        Args:
            service_name: Name of the service
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit
            metadata: Optional additional metadata

        Returns:
            Number of connections the metric was sent to
        """
        message = {
            "type": "metric",
            "data": {
                "service": service_name,
                "metric": metric_name,
                "value": value,
                "unit": unit,
                "metadata": metadata or {}
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.broadcast(message, "metrics")

    async def broadcast_alert(self, alert_id: str, severity: str, title: str, message: str, source: str, metadata: Dict[str, Any] = None) -> int:
        """Broadcast an alert to all subscribed connections.

        Args:
            alert_id: Unique alert identifier
            severity: Alert severity (critical, warning, info)
            title: Alert title
            message: Alert message
            source: Alert source service
            metadata: Optional additional metadata

        Returns:
            Number of connections the alert was sent to
        """
        message = {
            "type": "alert",
            "data": {
                "id": alert_id,
                "severity": severity,
                "title": title,
                "message": message,
                "source": source,
                "acknowledged": False,
                "metadata": metadata or {}
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.broadcast(message, "alerts")

    async def broadcast_status(self, service_name: str, status: str, health_check: str, metadata: Dict[str, Any] = None) -> int:
        """Broadcast a service status update to all subscribed connections.

        Args:
            service_name: Name of the service
            status: Service status (up, down, degraded)
            health_check: Health check result
            metadata: Optional additional metadata

        Returns:
            Number of connections the status was sent to
        """
        message = {
            "type": "status",
            "data": {
                "service": service_name,
                "status": status,
                "health_check": health_check,
                "metadata": metadata or {}
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.broadcast(message, "status")

    def get_connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)

    def get_connection_info(self, connection_id: str) -> Dict[str, Any]:
        """Get information about a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Connection information dictionary
        """
        if connection_id not in self.connection_metadata:
            return None

        return {
            "connection_id": connection_id,
            "subscriptions": list(self.subscriptions.get(connection_id, set())),
            **self.connection_metadata.get(connection_id, {})
        }

    def get_all_connections_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections.

        Returns:
            List of connection information dictionaries
        """
        return [
            self.get_connection_info(conn_id)
            for conn_id in self.active_connections.keys()
        ]


# Global connection manager instance
manager = ConnectionManager()


__all__ = [
    "ConnectionManager",
    "manager",
]

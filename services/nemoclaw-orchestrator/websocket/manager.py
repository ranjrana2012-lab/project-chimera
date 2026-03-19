# services/nemoclaw-orchestrator/websocket/manager.py
"""WebSocket connection manager for real-time show updates"""
import json
import logging
from typing import Dict, Any, List
from collections import defaultdict

from policy.engine import PolicyEngine

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates.

    Handles connection lifecycle, message broadcasting with policy filtering,
    and per-connection message history.
    """

    def __init__(self, policy_engine: PolicyEngine):
        """
        Initialize WebSocket manager.

        Args:
            policy_engine: Policy engine for filtering output messages
        """
        self.policy_engine = policy_engine
        self.connections: Dict[str, Any] = {}  # connection_id -> websocket
        self.message_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._max_history_size = 100  # Limit history per connection

    async def connect(self, connection_id: str, websocket: Any) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            connection_id: Unique identifier for the connection
            websocket: WebSocket connection object
        """
        self.connections[connection_id] = websocket
        self.message_history[connection_id] = []
        logger.info(f"WebSocket connection established: {connection_id}")

    async def disconnect(self, connection_id: str) -> None:
        """
        Cleanup and remove a WebSocket connection.

        Args:
            connection_id: Connection identifier to disconnect
        """
        if connection_id in self.connections:
            del self.connections[connection_id]

        if connection_id in self.message_history:
            del self.message_history[connection_id]

        logger.info(f"WebSocket connection closed: {connection_id}")

    async def broadcast(self, message_type: str, data: Dict[str, Any]) -> None:
        """
        Send a message to all connected connections with policy filtering.

        Args:
            message_type: Type of message (e.g., 'state_update', 'agent_response')
            data: Message data to broadcast
        """
        # Filter data through policy to remove PII
        filtered_data = await self._filter_broadcast(data)

        message = {
            "type": message_type,
            "data": filtered_data,
            "timestamp": self._get_timestamp()
        }

        message_json = json.dumps(message)

        # Send to all connected clients
        disconnected = []
        for conn_id, websocket in self.connections.items():
            try:
                await websocket.send_text(message_json)

                # Add to history
                self._add_to_history(conn_id, message)

            except Exception as e:
                logger.error(f"Error broadcasting to {conn_id}: {e}")
                disconnected.append(conn_id)

        # Cleanup disconnected clients
        for conn_id in disconnected:
            await self.disconnect(conn_id)

        logger.debug(f"Broadcasted {message_type} to {len(self.connections)} connections")

    async def send_to(
        self,
        connection_id: str,
        message_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Send a message to a specific connection.

        Args:
            connection_id: Target connection identifier
            message_type: Type of message
            data: Message data
        """
        if connection_id not in self.connections:
            logger.warning(f"Connection {connection_id} not found")
            return

        message = {
            "type": message_type,
            "data": data,
            "timestamp": self._get_timestamp()
        }

        message_json = json.dumps(message)

        try:
            websocket = self.connections[connection_id]
            await websocket.send_text(message_json)

            # Add to history
            self._add_to_history(connection_id, message)

        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def get_history(self, connection_id: str) -> List[Dict[str, Any]]:
        """
        Return message history for a connection.

        Args:
            connection_id: Connection identifier

        Returns:
            List of historical messages for this connection
        """
        return self.message_history.get(connection_id, [])

    async def _filter_broadcast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter broadcast data through policy to remove PII.

        Args:
            data: Raw data to filter

        Returns:
            Filtered data with PII removed
        """
        from policy.filters import OutputFilter
        filter = OutputFilter()
        return await filter.filter(data, agent="broadcast")

    def _add_to_history(self, connection_id: str, message: Dict[str, Any]) -> None:
        """
        Add message to connection history with size limit.

        Args:
            connection_id: Connection identifier
            message: Message to add
        """
        if connection_id not in self.message_history:
            self.message_history[connection_id] = []

        history = self.message_history[connection_id]
        history.append(message)

        # Enforce size limit (FIFO)
        if len(history) > self._max_history_size:
            history.pop(0)

    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO formatted timestamp string
        """
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @property
    def connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.connections)

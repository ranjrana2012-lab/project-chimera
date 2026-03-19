# services/nemoclaw-orchestrator/websocket/handlers.py
"""WebSocket message handlers for real-time show control"""
import logging
from typing import Dict, Any

from websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)


class WebSocketMessageHandler:
    """
    Handles incoming WebSocket messages and routes them to appropriate handlers.

    Supports actions:
    - start_show: Start the show state machine
    - end_show: End the show state machine
    - agent_call: Call a specific agent
    - ping: Health check
    """

    def __init__(
        self,
        state_machine: Any,  # ShowStateMachine (will be implemented separately)
        agent_coordinator: Any,  # AgentCoordinator (will be implemented separately)
        ws_manager: WebSocketManager
    ):
        """
        Initialize message handler.

        Args:
            state_machine: Show state machine instance
            agent_coordinator: Agent coordinator instance
            ws_manager: WebSocket manager instance
        """
        self.state_machine = state_machine
        self.agent_coordinator = agent_coordinator
        self.ws_manager = ws_manager

        # Map action names to handler methods
        self._action_handlers = {
            "start_show": self._handle_start_show,
            "end_show": self._handle_end_show,
            "agent_call": self._handle_agent_call,
            "ping": self._handle_ping,
        }

    async def handle_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """
        Route message to appropriate handler based on action type.

        Args:
            connection_id: WebSocket connection identifier
            message: Incoming message with 'action' and 'data' fields
        """
        action = message.get("action")
        data = message.get("data", {})

        if not action:
            await self._send_error(connection_id, "Missing action in message")
            return

        handler = self._action_handlers.get(action)

        if handler:
            try:
                await handler(connection_id, data)
            except Exception as e:
                logger.error(f"Error handling action '{action}': {e}")
                await self._send_error(
                    connection_id,
                    f"Error processing {action}: {str(e)}"
                )
        else:
            await self._send_error(connection_id, f"Unknown action: {action}")

    async def _handle_start_show(self, connection_id: str, data: Dict[str, Any]) -> None:
        """
        Handle start_show action.

        Args:
            connection_id: WebSocket connection identifier
            data: Action-specific data (unused for start_show)
        """
        logger.info(f"Starting show from connection {connection_id}")

        # Call state machine to start show
        if hasattr(self.state_machine, 'start'):
            await self.state_machine.start()
        elif hasattr(self.state_machine, 'start_show'):
            await self.state_machine.start_show()
        else:
            logger.warning("State machine missing start method")
            await self._send_error(connection_id, "State machine not properly configured")
            return

        # Broadcast state update to all connections
        state_data = {
            "state": "running",
            "triggered_by": connection_id,
            "show_id": data.get("show_id", "default")
        }

        await self.ws_manager.broadcast("state_update", state_data)

    async def _handle_end_show(self, connection_id: str, data: Dict[str, Any]) -> None:
        """
        Handle end_show action.

        Args:
            connection_id: WebSocket connection identifier
            data: Action-specific data (unused for end_show)
        """
        logger.info(f"Ending show from connection {connection_id}")

        # Call state machine to end show
        if hasattr(self.state_machine, 'end'):
            await self.state_machine.end()
        elif hasattr(self.state_machine, 'end_show'):
            await self.state_machine.end_show()
        else:
            logger.warning("State machine missing end method")
            await self._send_error(connection_id, "State machine not properly configured")
            return

        # Broadcast state update to all connections
        state_data = {
            "state": "ended",
            "triggered_by": connection_id,
            "show_id": data.get("show_id", "default")
        }

        await self.ws_manager.broadcast("state_update", state_data)

    async def _handle_agent_call(self, connection_id: str, data: Dict[str, Any]) -> None:
        """
        Handle agent_call action.

        Args:
            connection_id: WebSocket connection identifier
            data: Should contain 'agent', 'skill', and 'params' fields
        """
        agent = data.get("agent")
        skill = data.get("skill")
        params = data.get("params", {})

        if not agent or not skill:
            await self._send_error(
                connection_id,
                "agent_call requires 'agent' and 'skill' fields"
            )
            return

        logger.info(f"Calling agent {agent} with skill {skill}")

        try:
            # Call agent through coordinator
            if hasattr(self.agent_coordinator, 'call_agent'):
                response = await self.agent_coordinator.call_agent(agent, skill, params)
            elif hasattr(self.agent_coordinator, 'coordinate'):
                response = await self.agent_coordinator.coordinate(agent, skill, params)
            else:
                response = {"status": "error", "message": "Agent coordinator not properly configured"}

            # Send response back to the requesting connection only
            await self.ws_manager.send_to(connection_id, "agent_response", response)

        except Exception as e:
            logger.error(f"Error calling agent {agent}: {e}")
            await self._send_error(
                connection_id,
                f"Agent call failed: {str(e)}"
            )

    async def _handle_ping(self, connection_id: str, data: Dict[str, Any]) -> None:
        """
        Handle ping action (health check).

        Args:
            connection_id: WebSocket connection identifier
            data: Optional data to echo back
        """
        pong_data = {
            "message": "pong",
            "connection_id": connection_id,
            "echo": data
        }

        await self.ws_manager.send_to(connection_id, "pong", pong_data)

    async def _send_error(self, connection_id: str, message: str) -> None:
        """
        Send error message to connection.

        Args:
            connection_id: WebSocket connection identifier
            message: Error message text
        """
        error_data = {
            "message": message,
            "connection_id": connection_id
        }

        await self.ws_manager.send_to(connection_id, "error", error_data)

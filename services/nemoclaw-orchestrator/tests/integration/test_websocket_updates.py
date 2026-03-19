# tests/integration/test_websocket_updates.py
"""Integration tests for WebSocket manager with policy filtering"""
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from websocket.manager import WebSocketManager
from websocket.handlers import WebSocketMessageHandler
from policy.engine import PolicyEngine, PolicyRule, PolicyAction


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages = []
        self.closed = False

    async def send_text(self, message: str):
        """Mock send_text"""
        self.messages.append(message)

    async def close(self):
        """Mock close"""
        self.closed = True


class MockStateMachine:
    """Mock state machine for testing"""
    def __init__(self):
        self.state = "idle"
        self.callbacks = []

    async def start_show(self):
        """Mock start show"""
        self.state = "running"
        for cb in self.callbacks:
            await cb(self.state)

    async def end_show(self):
        """Mock end show"""
        self.state = "ended"
        for cb in self.callbacks:
            await cb(self.state)


class MockAgentCoordinator:
    """Mock agent coordinator for testing"""
    def __init__(self):
        self.responses = {
            "test_agent": {"status": "success", "data": "test response"}
        }

    async def call_agent(self, agent_name: str, skill: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock call agent"""
        return self.responses.get(agent_name, {"status": "error", "message": "Agent not found"})


@pytest.fixture
def policy_engine():
    """Create policy engine for testing"""
    policies = [
        PolicyRule(
            name="test_policy",
            agent="test_agent",
            action=PolicyAction.ALLOW,
            conditions={},
            output_filter=True
        )
    ]
    return PolicyEngine(policies)


@pytest.fixture
def ws_manager(policy_engine):
    """Create WebSocket manager for testing"""
    return WebSocketManager(policy_engine)


@pytest.fixture
def state_machine():
    """Create mock state machine"""
    return MockStateMachine()


@pytest.fixture
def agent_coordinator():
    """Create mock agent coordinator"""
    return MockAgentCoordinator()


@pytest.fixture
def ws_handler(state_machine, agent_coordinator, ws_manager):
    """Create WebSocket message handler"""
    return WebSocketMessageHandler(state_machine, agent_coordinator, ws_manager)


@pytest.mark.asyncio
async def test_connect_and_disconnect(ws_manager):
    """Test WebSocket connection and disconnection"""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    # Test connect
    await ws_manager.connect("conn1", ws1)
    await ws_manager.connect("conn2", ws2)

    assert "conn1" in ws_manager.connections
    assert "conn2" in ws_manager.connections
    assert len(ws_manager.connections) == 2

    # Test disconnect
    await ws_manager.disconnect("conn1")

    assert "conn1" not in ws_manager.connections
    assert "conn2" in ws_manager.connections
    assert len(ws_manager.connections) == 1


@pytest.mark.asyncio
async def test_send_to_specific_connection(ws_manager):
    """Test sending message to specific connection"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    # Send message
    await ws_manager.send_to("conn1", "test_type", {"data": "test"})

    assert len(ws.messages) == 1
    import json
    message = json.loads(ws.messages[0])
    assert message["type"] == "test_type"
    assert message["data"] == {"data": "test"}


@pytest.mark.asyncio
async def test_broadcast_to_all_connections(ws_manager):
    """Test broadcasting message to all connections"""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    ws3 = MockWebSocket()

    await ws_manager.connect("conn1", ws1)
    await ws_manager.connect("conn2", ws2)
    await ws_manager.connect("conn3", ws3)

    # Broadcast message
    await ws_manager.broadcast("broadcast_type", {"message": "hello"})

    # All connections should receive the message
    assert len(ws1.messages) == 1
    assert len(ws2.messages) == 1
    assert len(ws3.messages) == 1

    import json
    msg1 = json.loads(ws1.messages[0])
    msg2 = json.loads(ws2.messages[0])
    msg3 = json.loads(ws3.messages[0])

    assert msg1["type"] == "broadcast_type"
    assert msg2["type"] == "broadcast_type"
    assert msg3["type"] == "broadcast_type"


@pytest.mark.asyncio
async def test_broadcast_filters_pii(ws_manager):
    """Test that broadcast filters PII from messages"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    # Broadcast message with PII
    data_with_pii = {
        "user": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "ssn": "123-45-6789",
        "message": "Contact me at 555-123-4567"
    }

    await ws_manager.broadcast("update", data_with_pii)

    assert len(ws.messages) == 1
    import json
    message = json.loads(ws.messages[0])

    # PII should be filtered
    assert "[EMAIL]" in message["data"]["email"]
    assert "[PHONE]" in message["data"]["phone"]
    assert "[SSN]" in message["data"]["ssn"]
    assert "[PHONE]" in message["data"]["message"]


@pytest.mark.asyncio
async def test_message_history_tracking(ws_manager):
    """Test that message history is tracked"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    # Send multiple messages
    await ws_manager.send_to("conn1", "type1", {"msg": "1"})
    await ws_manager.send_to("conn1", "type2", {"msg": "2"})
    await ws_manager.send_to("conn1", "type3", {"msg": "3"})

    # Get history
    history = await ws_manager.get_history("conn1")

    assert len(history) == 3
    assert history[0]["type"] == "type1"
    assert history[1]["type"] == "type2"
    assert history[2]["type"] == "type3"


@pytest.mark.asyncio
async def test_history_per_connection(ws_manager):
    """Test that history is tracked per connection"""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await ws_manager.connect("conn1", ws1)
    await ws_manager.connect("conn2", ws2)

    # Send different messages to each connection
    await ws_manager.send_to("conn1", "type1", {"msg": "to conn1"})
    await ws_manager.send_to("conn2", "type2", {"msg": "to conn2"})

    # Check histories are separate
    history1 = await ws_manager.get_history("conn1")
    history2 = await ws_manager.get_history("conn2")

    assert len(history1) == 1
    assert len(history2) == 1
    assert history1[0]["data"]["msg"] == "to conn1"
    assert history2[0]["data"]["msg"] == "to conn2"


@pytest.mark.asyncio
async def test_handle_start_show(ws_handler, ws_manager):
    """Test handling start_show message"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    message = {
        "action": "start_show",
        "data": {}
    }

    await ws_handler.handle_message("conn1", message)

    # State machine should be started
    assert ws_handler.state_machine.state == "running"

    # Message should be broadcast
    assert len(ws.messages) == 1
    import json
    broadcast_msg = json.loads(ws.messages[0])
    assert broadcast_msg["type"] == "state_update"


@pytest.mark.asyncio
async def test_handle_end_show(ws_handler, ws_manager):
    """Test handling end_show message"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    message = {
        "action": "end_show",
        "data": {}
    }

    await ws_handler.handle_message("conn1", message)

    # State machine should be ended
    assert ws_handler.state_machine.state == "ended"

    # Message should be broadcast
    assert len(ws.messages) == 1
    import json
    broadcast_msg = json.loads(ws.messages[0])
    assert broadcast_msg["type"] == "state_update"


@pytest.mark.asyncio
async def test_handle_agent_call(ws_handler, ws_manager):
    """Test handling agent_call message"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    message = {
        "action": "agent_call",
        "data": {
            "agent": "test_agent",
            "skill": "test_skill",
            "params": {"param1": "value1"}
        }
    }

    await ws_handler.handle_message("conn1", message)

    # Response should be sent to the connection
    assert len(ws.messages) == 1
    import json
    response = json.loads(ws.messages[0])
    assert response["type"] == "agent_response"
    assert response["data"]["status"] == "success"


@pytest.mark.asyncio
async def test_handle_ping(ws_handler, ws_manager):
    """Test handling ping message"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    message = {
        "action": "ping",
        "data": {}
    }

    await ws_handler.handle_message("conn1", message)

    # Pong should be sent
    assert len(ws.messages) == 1
    import json
    response = json.loads(ws.messages[0])
    assert response["type"] == "pong"


@pytest.mark.asyncio
async def test_unknown_action(ws_handler, ws_manager):
    """Test handling unknown action"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    message = {
        "action": "unknown_action",
        "data": {}
    }

    await ws_handler.handle_message("conn1", message)

    # Error response should be sent
    assert len(ws.messages) == 1
    import json
    response = json.loads(ws.messages[0])
    assert response["type"] == "error"
    assert "Unknown action" in response["data"]["message"]


@pytest.mark.asyncio
async def test_disconnect_cleans_up_history(ws_manager):
    """Test that disconnect cleans up connection history"""
    ws = MockWebSocket()
    await ws_manager.connect("conn1", ws)

    # Send some messages
    await ws_manager.send_to("conn1", "type1", {"msg": "1"})
    await ws_manager.send_to("conn1", "type2", {"msg": "2"})

    # Verify history exists
    history = await ws_manager.get_history("conn1")
    assert len(history) == 2

    # Disconnect
    await ws_manager.disconnect("conn1")

    # History should be cleaned up
    history_after = await ws_manager.get_history("conn1")
    assert history_after == []

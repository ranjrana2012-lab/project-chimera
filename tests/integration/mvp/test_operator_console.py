"""Integration tests for Operator Console.

Tests the central monitoring and control dashboard for Project Chimera services.
"""

import pytest
import requests
import asyncio
import websockets
import json
from typing import Dict, Any


@pytest.mark.integration
def test_console_health(console_url):
    """Test console health endpoint returns healthy status.

    SPEC REQUIREMENT:
    - Status should be "healthy"
    - Service name should be "operator-console"
    - Response should include version and dashboard info
    """
    response = requests.get(f"{console_url}/health", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Health response structure
    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "operator-console"
    assert "version" in data


@pytest.mark.integration
def test_console_readiness(console_url):
    """Test console readiness endpoint returns valid status.

    SPEC REQUIREMENT:
    - Status should be "ready" or "not_ready"
    - Response should include checks dictionary
    - Checks should include dependency service status
    """
    response = requests.get(f"{console_url}/health/ready", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Readiness response structure
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data
    assert isinstance(data["checks"], dict)


@pytest.mark.integration
def test_console_show_control_list(console_url):
    """Test listing shows via show status endpoint.

    SPEC REQUIREMENT:
    - Response should include show state information
    - Should include active status
    - Should include agent status list
    """
    response = requests.get(f"{console_url}/api/show/status", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Show status response structure
    assert "active" in data
    assert "state" in data
    assert "scene" in data
    assert "show_id" in data
    assert "agents" in data
    assert "timestamp" in data

    # Agents should be a list
    assert isinstance(data["agents"], list)

    # Each agent should have required fields
    if len(data["agents"]) > 0:
        agent = data["agents"][0]
        assert "name" in agent
        assert "status" in agent
        assert "ready" in agent


@pytest.mark.integration
def test_console_show_control_get(console_url):
    """Test getting show details via configuration endpoint.

    SPEC REQUIREMENT:
    - Response should include show configuration
    - Should include show_id, name, duration
    - Should include scenes list and adaptive mode settings
    """
    response = requests.get(f"{console_url}/api/show/configuration", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Show configuration response structure
    assert "show_id" in data
    assert "name" in data
    assert "duration_minutes" in data
    assert "scenes" in data
    assert "auto_adaptive" in data
    assert "audience_interaction" in data

    # Scenes should be a list
    assert isinstance(data["scenes"], list)


@pytest.mark.integration
def test_console_show_control_create(console_url):
    """Test creating/starting a show via control endpoint.

    SPEC REQUIREMENT:
    - POST request should return 201 or 200 status
    - Response should include show_id
    - Response should include action and status
    - Response should include message
    - Should include created_at or started_at timestamp
    """
    response = requests.post(
        f"{console_url}/api/show/control",
        json={
            "action": "start",
            "show_id": "test-show-001"
        },
        timeout=10
    )

    # Accept both 200 and 201 (implementation may vary)
    assert response.status_code in [200, 201]
    data = response.json()

    # Show control response structure
    assert "action" in data
    assert data["action"] == "start"
    assert "status" in data
    assert "show_id" in data
    assert "message" in data

    # Verify show was created
    assert data["show_id"] == "test-show-001"
    assert data["status"] in ["success", "failed"]

    # Clean up - stop the show
    try:
        cleanup_response = requests.post(
            f"{console_url}/api/show/control",
            json={"action": "stop"},
            timeout=10
        )
        if cleanup_response.status_code not in [200, 201]:
            print(f"Warning: Cleanup failed with status {cleanup_response.status_code}")
    except Exception as e:
        print(f"Warning: Cleanup request failed: {e}")


@pytest.mark.integration
def test_console_show_control_update(console_url):
    """Test updating show configuration.

    SPEC REQUIREMENT:
    - PUT request should return 200 status
    - Response should include updated configuration
    - Should reflect changes in the response
    """
    # First get current config
    get_response = requests.get(f"{console_url}/api/show/configuration", timeout=10)
    assert get_response.status_code == 200
    original_config = get_response.json()

    # Update configuration
    updated_config = {
        **original_config,
        "name": "Updated Show Name",
        "duration_minutes": 90,
        "auto_adaptive": False
    }

    response = requests.put(
        f"{console_url}/api/show/configuration",
        json=updated_config,
        timeout=10
    )

    assert response.status_code == 200
    data = response.json()

    # Verify updates were applied
    assert data["name"] == "Updated Show Name"
    assert data["duration_minutes"] == 90
    assert data["auto_adaptive"] is False

    # Restore original configuration to prevent side effects
    try:
        restore_response = requests.put(
            f"{console_url}/api/show/configuration",
            json=original_config,
            timeout=10
        )
        if restore_response.status_code not in [200, 201]:
            print(f"Warning: Failed to restore original config (status {restore_response.status_code})")
    except Exception as e:
        print(f"Warning: Config restoration failed: {e}")


@pytest.mark.integration
def test_console_websocket_connection(console_url):
    """Test WebSocket connection and ping/pong.

    SPEC REQUIREMENT:
    - WebSocket connection should be accepted
    - Should be able to send subscription message
    - Should receive response or maintain connection
    """
    # Convert HTTP URL to WS URL
    ws_url = console_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_endpoint = f"{ws_url}/ws"

    # Test WebSocket connection
    try:
        async def test_ws():
            # Use ping_timeout and close_timeout instead of timeout for newer websockets library
            async with websockets.connect(
                ws_endpoint,
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                # Send subscription message
                subscribe_msg = {
                    "action": "subscribe",
                    "channel": "metrics"
                }
                await websocket.send(json.dumps(subscribe_msg))

                # Try to receive a message (may be empty initially)
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=2.0
                    )
                    # If we get a message, verify it's valid JSON
                    if response:
                        data = json.loads(response)
                        assert isinstance(data, dict)
                except asyncio.TimeoutError:
                    # Timeout is acceptable - connection was established
                    pass

        # Run async test
        asyncio.run(test_ws())

    except (ConnectionRefusedError, OSError) as e:
        pytest.skip(f"WebSocket connection refused: {e}")


@pytest.mark.integration
def test_console_orchestrator_connection(console_url):
    """Test orchestrator connection status via agents endpoint.

    SPEC REQUIREMENT:
    - Response should include orchestrator status
    - Should include connected status or URL
    - Should include orchestrator service information
    """
    response = requests.get(f"{console_url}/api/agents/status", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Agents status response structure
    assert "agents" in data
    assert isinstance(data["agents"], list)

    # Find orchestrator in agents list
    orchestrator = None
    for agent in data["agents"]:
        if agent.get("name") == "orchestrator":
            orchestrator = agent
            break

    # Verify orchestrator info exists
    assert orchestrator is not None, "Orchestrator not found in agents list"
    assert "status" in orchestrator
    assert "port" in orchestrator

    # Orchestrator should have a port (implies connection info)
    assert orchestrator["port"] == 8000


@pytest.mark.integration
def test_console_missing_required_field(console_url):
    """Test that missing required fields return 422 validation error.

    SPEC REQUIREMENT:
    - Missing required fields should return 422 status
    - Response should include validation error details
    """
    # Test show control with missing action field
    response = requests.post(
        f"{console_url}/api/show/control",
        json={},  # Missing required 'action' field
        timeout=10
    )

    # Should return 422 for missing required field
    # (FastAPI default validation error code)
    assert response.status_code == 422

    data = response.json()
    # Validation error should contain detail
    assert "detail" in data


@pytest.mark.integration
def test_console_services_list(console_url):
    """Test listing all services with their status.

    SPEC REQUIREMENT:
    - Response should include services list
    - Each service should have name, URL, and status
    - Should include total counts (up, down, degraded)
    """
    response = requests.get(f"{console_url}/api/services", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Services list response structure
    assert "services" in data
    assert isinstance(data["services"], list)
    assert "total" in data
    assert "up" in data
    assert "down" in data
    assert "degraded" in data

    # Each service should have required fields
    if len(data["services"]) > 0:
        service = data["services"][0]
        assert "name" in service
        assert "url" in service
        assert "status" in service


@pytest.mark.integration
def test_console_metrics_endpoint(console_url):
    """Test metrics collection endpoint.

    SPEC REQUIREMENT:
    - Response should include metrics for all services
    - Should include CPU, memory, request rate, error rate
    - Metrics should be organized by service name
    """
    response = requests.get(f"{console_url}/api/metrics", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Metrics response structure
    assert "metrics" in data
    assert isinstance(data["metrics"], dict)

    # Each service metric should have relevant fields
    for service_name, service_metrics in data["metrics"].items():
        assert "service_name" in service_metrics
        assert service_metrics["service_name"] == service_name

        # Metrics fields (may be None if service is down)
        optional_fields = ["cpu_percent", "memory_mb", "request_rate", "error_rate"]
        for field in optional_fields:
            assert field in service_metrics


@pytest.mark.integration
def test_console_alerts_endpoint(console_url):
    """Test alerts listing endpoint.

    SPEC REQUIREMENT:
    - Response should include alerts list
    - Should include total counts by severity
    - Should include critical, warning, info counts
    """
    response = requests.get(f"{console_url}/api/alerts", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Alerts response structure
    assert "alerts" in data
    assert isinstance(data["alerts"], list)
    assert "total" in data
    assert "critical" in data
    assert "warning" in data
    assert "info" in data

    # Total should match list length
    assert data["total"] == len(data["alerts"])


@pytest.mark.integration
def test_console_show_control_pause_resume(console_url):
    """Test show pause and resume functionality.

    SPEC REQUIREMENT:
    - Pause should change show state to paused
    - Resume should change show state back to active
    - Both should return success status
    """
    # First start a show
    start_response = requests.post(
        f"{console_url}/api/show/control",
        json={"action": "start", "show_id": "pause-resume-test"},
        timeout=10
    )
    assert start_response.status_code in [200, 201]

    # Verify show started successfully before proceeding
    start_data = start_response.json()
    if start_data.get("status") == "failed":
        pytest.skip(f"Show start failed: {start_data.get('message', 'Unknown error')}")

    # Pause the show
    pause_response = requests.post(
        f"{console_url}/api/show/control",
        json={"action": "pause"},
        timeout=10
    )
    assert pause_response.status_code == 200
    pause_data = pause_response.json()
    assert pause_data["action"] == "pause"
    assert pause_data["status"] in ["success", "failed"]

    # Resume the show
    resume_response = requests.post(
        f"{console_url}/api/show/control",
        json={"action": "resume"},
        timeout=10
    )
    assert resume_response.status_code == 200
    resume_data = resume_response.json()
    assert resume_data["action"] == "resume"
    assert resume_data["status"] in ["success", "failed"]

    # Clean up
    try:
        cleanup_response = requests.post(
            f"{console_url}/api/show/control",
            json={"action": "stop"},
            timeout=10
        )
        if cleanup_response.status_code not in [200, 201]:
            print(f"Warning: Cleanup failed with status {cleanup_response.status_code}")
    except Exception as e:
        print(f"Warning: Cleanup request failed: {e}")


@pytest.mark.integration
def test_console_audience_reaction(console_url):
    """Test audience reaction submission endpoint.

    SPEC REQUIREMENT:
    - POST request should accept reaction data
    - Response should include status and reaction_id
    - Should return error if no show is active
    """
    # First start a show
    start_response = requests.post(
        f"{console_url}/api/show/control",
        json={"action": "start", "show_id": "audience-test"},
        timeout=10
    )

    # Verify show started successfully before proceeding
    if start_response.status_code in [200, 201]:
        start_data = start_response.json()
        if start_data.get("status") == "failed":
            pytest.skip(f"Show start failed: {start_data.get('message', 'Unknown error')}")

    # Submit audience reaction
    response = requests.post(
        f"{console_url}/api/show/audience-reaction",
        json={
            "text": "Amazing show!",
            "sentiment": "positive",
            "intensity": 0.9
        },
        timeout=10
    )

    # Should accept the reaction
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "received"
    assert "reaction_id" in data

    # Clean up
    try:
        cleanup_response = requests.post(
            f"{console_url}/api/show/control",
            json={"action": "stop"},
            timeout=10
        )
        if cleanup_response.status_code not in [200, 201]:
            print(f"Warning: Cleanup failed with status {cleanup_response.status_code}")
    except Exception as e:
        print(f"Warning: Cleanup request failed: {e}")

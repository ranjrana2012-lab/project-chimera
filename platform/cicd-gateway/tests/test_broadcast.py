"""
Unit tests for status broadcast service.

Tests WebSocket broadcasting of pipeline status updates.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

# Add cicd-gateway to path
gateway_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(gateway_path))


class TestBroadcastMessage:
    """Test broadcast message dataclass."""

    def test_message_creation(self):
        """Test creating broadcast message."""
        from gateway.broadcast import BroadcastMessage

        msg = BroadcastMessage(
            type="pipeline_started",
            data={"pipeline_id": "4527", "run_id": "test-run-abc"}
        )
        assert msg.type == "pipeline_started"
        assert msg.data["pipeline_id"] == "4527"

    def test_message_to_dict(self):
        """Test converting message to dict."""
        from gateway.broadcast import BroadcastMessage

        msg = BroadcastMessage(
            type="pipeline_completed",
            data={"status": "success"}
        )

        data = msg.to_dict()
        assert "type" in data
        assert "timestamp" in data


class TestStatusBroadcastService:
    """Test status broadcast service."""

    @pytest.fixture
    def service(self):
        """Create broadcast service."""
        from gateway.broadcast import StatusBroadcastService
        return StatusBroadcastService(ws_url="ws://dashboard:8007/ws")

    def test_service_init(self, service):
        """Test service initialization."""
        assert service.ws_url == "ws://dashboard:8007/ws"

    def test_broadcast_pipeline_started(self, service):
        """Test broadcasting pipeline started event."""
        # Mock WebSocket send
        service._send_to_ws = lambda msg: True

        result = service.broadcast_pipeline_started(
            pipeline_id="4527",
            run_id="test-run-abc",
            branch="main"
        )
        assert result is True

    def test_broadcast_pipeline_completed(self, service):
        """Test broadcasting pipeline completed event."""
        service._send_to_ws = lambda msg: True

        result = service.broadcast_pipeline_completed(
            pipeline_id="4527",
            run_id="test-run-abc",
            status="success",
            total_tests=100,
            passed=95,
            failed=5
        )
        assert result is True

    def test_broadcast_pipeline_failed(self, service):
        """Test broadcasting pipeline failed event."""
        service._send_to_ws = lambda msg: True

        result = service.broadcast_pipeline_failed(
            pipeline_id="4527",
            run_id="test-run-abc",
            error="Tests failed"
        )
        assert result is True

    def test_broadcast_test_progress(self, service):
        """Test broadcasting test progress event."""
        service._send_to_ws = lambda msg: True

        result = service.broadcast_test_progress(
            run_id="test-run-abc",
            service="scenespeak-agent",
            passed=45,
            failed=5,
            total=50
        )
        assert result is True


class TestEventType:
    """Test event type constants."""

    def test_event_types(self):
        """Test event type values."""
        from gateway.broadcast import EventType

        assert EventType.PIPELINE_STARTED.value == "pipeline_started"
        assert EventType.PIPELINE_COMPLETED.value == "pipeline_completed"
        assert EventType.PIPELINE_FAILED.value == "pipeline_failed"
        assert EventType.TEST_PROGRESS.value == "test_progress"
        assert EventType.COVERAGE_UPDATE.value == "coverage_update"

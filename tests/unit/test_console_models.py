"""Unit tests for Operator Console models."""

import pytest
from datetime import datetime, timedelta

from services.operator_console.src.models.request import (
    OverrideRequest,
    OverrideType,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
)
from services.operator_console.src.models.response import (
    ServiceHealth,
    ServiceStatus,
    ConsoleStatus,
    EventType,
    EventSeverity,
    StreamEvent,
    EventStream,
    Alert,
)


class TestOverrideRequest:
    """Tests for OverrideRequest model."""

    def test_create_emergency_stop_request(self):
        """Test creating an emergency stop request."""
        request = OverrideRequest(
            override_type=OverrideType.EMERGENCY_STOP,
            target_service="all",
            reason="Critical safety issue",
        )
        assert request.override_type == OverrideType.EMERGENCY_STOP
        assert request.target_service == "all"
        assert request.reason == "Critical safety issue"
        assert request.parameter is None

    def test_create_service_pause_request(self):
        """Test creating a service pause request."""
        request = OverrideRequest(
            override_type=OverrideType.SERVICE_PAUSE,
            target_service="script-agent",
            reason="Manual intervention required",
            parameter={"duration_seconds": 300},
        )
        assert request.override_type == OverrideType.SERVICE_PAUSE
        assert request.parameter["duration_seconds"] == 300


class TestApprovalRequest:
    """Tests for ApprovalRequest model."""

    def test_create_approval_request(self):
        """Test creating an approval request."""
        request = ApprovalRequest(
            request_id="test-approval-1",
            source_service="script-agent",
            content_type="script",
            content_preview="Generated script scene 1...",
            priority="high",
        )
        assert request.request_id == "test-approval-1"
        assert request.source_service == "script-agent"
        assert request.content_type == "script"
        assert request.priority == "high"

    def test_approval_request_with_expiry(self):
        """Test approval request with expiry time."""
        expires = datetime.now() + timedelta(minutes=30)
        request = ApprovalRequest(
            request_id="test-approval-2",
            source_service="lighting-agent",
            content_type="lighting_cue",
            content_preview="Lighting change...",
            expires_at=expires,
        )
        assert request.expires_at == expires


class TestApprovalResponse:
    """Tests for ApprovalResponse model."""

    def test_create_approval_response(self):
        """Test creating an approval response."""
        response = ApprovalResponse(
            request_id="test-approval-1",
            status=ApprovalStatus.APPROVED,
            approved_by="operator",
            reason="Content approved",
        )
        assert response.request_id == "test-approval-1"
        assert response.status == ApprovalStatus.APPROVED
        assert response.approved_by == "operator"

    def test_create_rejection_response(self):
        """Test creating a rejection response."""
        response = ApprovalResponse(
            request_id="test-approval-2",
            status=ApprovalStatus.REJECTED,
            approved_by="operator",
            reason="Inappropriate content",
        )
        assert response.status == ApprovalStatus.REJECTED


class TestServiceHealth:
    """Tests for ServiceHealth model."""

    def test_create_healthy_service(self):
        """Test creating a healthy service status."""
        health = ServiceHealth(
            service_name="script-agent",
            status=ServiceStatus.HEALTHY,
            last_seen=datetime.now(),
            uptime_seconds=3600.0,
        )
        assert health.service_name == "script-agent"
        assert health.status == ServiceStatus.HEALTHY
        assert health.uptime_seconds == 3600.0
        assert health.error_count == 0

    def test_create_degraded_service(self):
        """Test creating a degraded service status."""
        health = ServiceHealth(
            service_name="audio-agent",
            status=ServiceStatus.DEGRADED,
            last_seen=datetime.now(),
            error_count=5,
        )
        assert health.status == ServiceStatus.DEGRADED
        assert health.error_count == 5


class TestConsoleStatus:
    """Tests for ConsoleStatus model."""

    def test_create_console_status(self):
        """Test creating console status."""
        services = {
            "script-agent": ServiceHealth(
                service_name="script-agent",
                status=ServiceStatus.HEALTHY,
                last_seen=datetime.now(),
            )
        }
        status = ConsoleStatus(
            services=services,
            pending_approvals=3,
            active_alerts=1,
            system_mode="automatic",
            console_uptime=7200.0,
        )
        assert status.pending_approvals == 3
        assert status.active_alerts == 1
        assert status.system_mode == "automatic"
        assert "script-agent" in status.services


class TestStreamEvent:
    """Tests for StreamEvent model."""

    def test_create_info_event(self):
        """Test creating an info event."""
        event = StreamEvent(
            event_id="event-1",
            event_type=EventType.SCRIPT_GENERATED,
            source_service="script-agent",
            title="Script Generated",
            message="Scene 1 script generated successfully",
        )
        assert event.event_id == "event-1"
        assert event.event_type == EventType.SCRIPT_GENERATED
        assert event.severity == EventSeverity.INFO
        assert event.requires_approval is False

    def test_create_alert_event(self):
        """Test creating an alert event."""
        event = StreamEvent(
            event_id="event-2",
            event_type=EventType.ALERT,
            severity=EventSeverity.WARNING,
            source_service="safety-filter",
            title="Content Flagged",
            message="Inappropriate content detected",
            requires_approval=True,
            approval_id="approval-1",
        )
        assert event.severity == EventSeverity.WARNING
        assert event.requires_approval is True
        assert event.approval_id == "approval-1"


class TestAlert:
    """Tests for Alert model."""

    def test_create_critical_alert(self):
        """Test creating a critical alert."""
        alert = Alert(
            alert_id="alert-1",
            severity=EventSeverity.CRITICAL,
            title="System Failure",
            message="Script agent unresponsive",
            source_service="script-agent",
            action_required=True,
        )
        assert alert.severity == EventSeverity.CRITICAL
        assert alert.action_required is True
        assert alert.resolved is False

    def test_mark_alert_resolved(self):
        """Test marking an alert as resolved."""
        alert = Alert(
            alert_id="alert-2",
            severity=EventSeverity.ERROR,
            title="Error Detected",
            message="Processing error",
            source_service="audio-agent",
        )
        alert.resolved = True
        assert alert.resolved is True

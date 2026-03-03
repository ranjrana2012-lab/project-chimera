"""
Unit tests for alerts and incidents panel.

Tests alert creation, severity levels, and incident tracking.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(dashboard_path))


class TestAlertSeverity:
    """Test alert severity levels."""

    def test_severity_ordering(self):
        """Test severity level ordering."""
        from components.alerts import AlertSeverity

        # Critical is highest
        assert AlertSeverity.CRITICAL.value > AlertSeverity.ERROR.value
        assert AlertSeverity.ERROR.value > AlertSeverity.WARNING.value
        assert AlertSeverity.WARNING.value > AlertSeverity.INFO.value

    def test_severity_from_string(self):
        """Test creating severity from string."""
        from components.alerts import AlertSeverity

        assert AlertSeverity.from_string("critical") == AlertSeverity.CRITICAL
        assert AlertSeverity.from_string("error") == AlertSeverity.ERROR
        assert AlertSeverity.from_string("warning") == AlertSeverity.WARNING
        assert AlertSeverity.from_string("info") == AlertSeverity.INFO


class TestAlert:
    """Test Alert dataclass."""

    def test_alert_creation(self):
        """Test creating an alert."""
        from components.alerts import Alert, AlertSeverity

        alert = Alert(
            id="alert-1",
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="This is a test alert"
        )
        assert alert.id == "alert-1"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Test Alert"

    def test_alert_is_active(self):
        """Test alert active status."""
        from components.alerts import Alert, AlertSeverity

        # Active alert (not acknowledged, not auto-dismissed)
        alert1 = Alert(
            id="alert-1",
            severity=AlertSeverity.INFO,
            title="Info",
            message="Message"
        )
        assert alert1.is_active() is True

        # Acknowledged alert
        alert2 = Alert(
            id="alert-2",
            severity=AlertSeverity.WARNING,
            title="Warning",
            message="Message",
            acknowledged=True
        )
        assert alert2.is_active() is False

        # Old info alert (auto-dismissed)
        old_time = datetime.now(timezone.utc) - timedelta(seconds=31)
        alert3 = Alert(
            id="alert-3",
            severity=AlertSeverity.INFO,
            title="Info",
            message="Message",
            created_at=old_time
        )
        assert alert3.is_active() is False

    def test_alert_age(self):
        """Test alert age calculation."""
        from components.alerts import Alert, AlertSeverity

        old_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        alert = Alert(
            id="alert-1",
            severity=AlertSeverity.INFO,
            title="Info",
            message="Message",
            created_at=old_time
        )
        assert alert.age_seconds >= 59  # Allow for test execution time

    def test_alert_to_dict(self):
        """Test converting alert to dict."""
        from components.alerts import Alert, AlertSeverity

        alert = Alert(
            id="alert-1",
            severity=AlertSeverity.ERROR,
            title="Error",
            message="Something went wrong"
        )
        data = alert.to_dict()
        assert data["id"] == "alert-1"
        assert data["severity"] == "error"
        assert data["title"] == "Error"


class TestIncident:
    """Test Incident dataclass."""

    def test_incident_creation(self):
        """Test creating an incident."""
        from components.alerts import Incident, IncidentStatus

        incident = Incident(
            id="incident-1",
            title="Service Outage",
            description="Service is down"
        )
        assert incident.id == "incident-1"
        assert incident.status == IncidentStatus.OPEN

    def test_incident_is_active(self):
        """Test incident active status."""
        from components.alerts import Incident, IncidentStatus

        # Open incident
        incident1 = Incident(
            id="incident-1",
            title="Test",
            description="Test"
        )
        assert incident1.is_active() is True

        # Resolved incident
        incident2 = Incident(
            id="incident-2",
            title="Test",
            description="Test",
            status=IncidentStatus.RESOLVED
        )
        assert incident2.is_active() is False

    def test_incident_duration(self):
        """Test incident duration calculation."""
        from components.alerts import Incident

        start = datetime.now(timezone.utc) - timedelta(hours=2)
        end = datetime.now(timezone.utc)

        incident = Incident(
            id="incident-1",
            title="Test",
            description="Test",
            started_at=start,
            resolved_at=end
        )
        # Duration should be approximately 2 hours
        duration = incident.duration_seconds
        assert 7190 <= duration <= 7210  # Allow some variance


class TestAlertManager:
    """Test AlertManager class."""

    @pytest.fixture
    def manager(self):
        """Create alert manager."""
        from components.alerts import AlertManager
        return AlertManager()

    def test_manager_init(self, manager):
        """Test manager initialization."""
        assert len(manager.alerts) == 0
        assert len(manager.incidents) == 0

    def test_create_alert(self, manager):
        """Test creating an alert."""
        from components.alerts import AlertSeverity

        alert = manager.create_alert(
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Test message"
        )
        assert alert.id is not None
        assert len(manager.alerts) == 1

    def test_acknowledge_alert(self, manager):
        """Test acknowledging an alert."""
        from components.alerts import AlertSeverity

        alert = manager.create_alert(
            severity=AlertSeverity.ERROR,
            title="Error",
            message="Error message"
        )

        manager.acknowledge_alert(alert.id)
        assert manager.get_alert(alert.id).acknowledged is True

    def test_dismiss_alert(self, manager):
        """Test dismissing an alert."""
        from components.alerts import AlertSeverity

        alert = manager.create_alert(
            severity=AlertSeverity.INFO,
            title="Info",
            message="Info message"
        )

        manager.dismiss_alert(alert.id)
        assert manager.get_alert(alert.id) is None

    def test_get_active_alerts(self, manager):
        """Test getting active alerts."""
        from components.alerts import AlertSeverity

        alert1 = manager.create_alert(AlertSeverity.ERROR, "Error", "Msg")
        alert2 = manager.create_alert(AlertSeverity.WARNING, "Warning", "Msg")

        # Acknowledge one
        manager.acknowledge_alert(alert1.id)

        active = manager.get_active_alerts()
        assert len(active) == 1
        assert active[0].id == alert2.id

    def test_get_alerts_by_severity(self, manager):
        """Test filtering alerts by severity."""
        from components.alerts import AlertSeverity

        manager.create_alert(AlertSeverity.CRITICAL, "Critical", "Msg")
        manager.create_alert(AlertSeverity.ERROR, "Error", "Msg")
        manager.create_alert(AlertSeverity.ERROR, "Error2", "Msg")
        manager.create_alert(AlertSeverity.WARNING, "Warning", "Msg")

        critical = manager.get_alerts_by_severity(AlertSeverity.CRITICAL)
        errors = manager.get_alerts_by_severity(AlertSeverity.ERROR)

        assert len(critical) == 1
        assert len(errors) == 2

    def test_auto_dismiss_info_alerts(self, manager):
        """Test auto-dismissing old info alerts."""
        from components.alerts import AlertSeverity

        # Create old info alert
        old_time = datetime.now(timezone.utc) - timedelta(seconds=31)
        alert = manager.create_alert(AlertSeverity.INFO, "Info", "Msg")
        alert.created_at = old_time

        # Auto-dismiss should remove it
        manager.auto_dismiss_old_alerts()
        assert len(manager.get_active_alerts()) == 0

    def test_create_incident(self, manager):
        """Test creating an incident."""
        incident = manager.create_incident(
            title="Service Outage",
            description="Service is down",
            severity="critical"
        )
        assert incident.id is not None
        assert len(manager.incidents) == 1

    def test_resolve_incident(self, manager):
        """Test resolving an incident."""
        incident = manager.create_incident(
            title="Test",
            description="Test"
        )

        manager.resolve_incident(incident.id, "Fixed the issue")
        incident = manager.get_incident(incident.id)
        assert incident.status.value == "resolved"
        assert incident.resolution == "Fixed the issue"

    def test_get_active_incidents(self, manager):
        """Test getting active incidents."""
        incident1 = manager.create_incident("Incident 1", "Description")
        incident2 = manager.create_incident("Incident 2", "Description")

        manager.resolve_incident(incident1.id, "Fixed")

        active = manager.get_active_incidents()
        assert len(active) == 1
        assert active[0].id == incident2.id


class TestAlertRules:
    """Test alert rule evaluation."""

    def test_high_latency_rule(self):
        """Test high latency alert rule."""
        from components.alerts import AlertManager, AlertSeverity

        manager = AlertManager()
        alerts = manager.check_service_health(
            service_name="test-service",
            latency_ms=6000,
            error_rate=0.0
        )

        # High latency should trigger warning
        assert len(alerts) > 0
        assert any(a.severity == AlertSeverity.WARNING for a in alerts)

    def test_coverage_drop_rule(self):
        """Test coverage drop alert rule."""
        from components.alerts import AlertManager, AlertSeverity

        manager = AlertManager()

        # First check establishes baseline
        manager.check_coverage("svc1", 85.0)

        # Second check with drop
        alerts = manager.check_coverage("svc1", 78.0)

        # Coverage drop should trigger alert
        assert len(alerts) > 0
        assert any(a.severity == AlertSeverity.WARNING for a in alerts)

    def test_flaky_tests_rule(self):
        """Test flaky tests alert rule."""
        from components.alerts import AlertManager, AlertSeverity

        manager = AlertManager()
        alerts = manager.check_flaky_tests(
            service="test-service",
            flaky_count=3
        )

        # Flaky tests should trigger warning
        assert len(alerts) > 0

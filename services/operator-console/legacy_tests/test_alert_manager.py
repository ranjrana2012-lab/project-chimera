"""Tests for alert manager."""

import pytest
from datetime import datetime

from alert_manager import AlertManager, AlertThreshold
from models import AlertSeverity


class TestAlertManager:
    """Tests for AlertManager."""

    @pytest.fixture
    def alert_manager(self):
        """Create an alert manager instance."""
        return AlertManager()

    def test_create_alert(self, alert_manager):
        """Test creating an alert."""
        import asyncio

        async def test_create():
            alert = await alert_manager.create_alert(
                severity=AlertSeverity.WARNING,
                title="Test Alert",
                message="This is a test alert",
                source="test-service"
            )

            assert alert is not None
            assert alert.id is not None
            assert alert.severity == AlertSeverity.WARNING
            assert alert.title == "Test Alert"
            assert alert.acknowledged is False

        asyncio.run(test_create())

    def test_create_alert_with_metadata(self, alert_manager):
        """Test creating an alert with metadata."""
        import asyncio

        async def test_create():
            alert = await alert_manager.create_alert(
                severity=AlertSeverity.CRITICAL,
                title="Critical Alert",
                message="This is critical",
                source="test-service",
                metadata={"metric_name": "cpu_percent", "metric_value": 95.0}
            )

            assert alert.metadata["metric_name"] == "cpu_percent"
            assert alert.metadata["metric_value"] == 95.0

        asyncio.run(test_create())

    def test_acknowledge_alert(self, alert_manager):
        """Test acknowledging an alert."""
        import asyncio

        async def test_ack():
            # Create an alert first
            alert = await alert_manager.create_alert(
                severity=AlertSeverity.INFO,
                title="Info Alert",
                message="Informational message",
                source="test-service"
            )

            alert_id = alert.id

            # Acknowledge it
            success = alert_manager.acknowledge_alert(alert_id)

            assert success is True

        asyncio.run(test_ack())

    def test_acknowledge_nonexistent_alert(self, alert_manager):
        """Test acknowledging a non-existent alert."""
        success = alert_manager.acknowledge_alert("nonexistent-id")

        assert success is False

    def test_get_active_alerts(self, alert_manager):
        """Test getting active alerts."""
        import asyncio

        async def test_active():
            # Create some alerts
            await alert_manager.create_alert(
                AlertSeverity.WARNING, "Alert 1", "Message 1", "service-1"
            )
            await alert_manager.create_alert(
                AlertSeverity.CRITICAL, "Alert 2", "Message 2", "service-2"
            )

            active_alerts = alert_manager.get_active_alerts()

            assert len(active_alerts) == 2

        asyncio.run(test_active())

    def test_get_alert_history(self, alert_manager):
        """Test getting alert history."""
        import asyncio

        async def test_history():
            # Create some alerts
            await alert_manager.create_alert(
                AlertSeverity.INFO, "Alert 1", "Message 1", "service-1"
            )
            await alert_manager.create_alert(
                AlertSeverity.WARNING, "Alert 2", "Message 2", "service-2"
            )
            await alert_manager.create_alert(
                AlertSeverity.CRITICAL, "Alert 3", "Message 3", "service-3"
            )

            # Acknowledge one alert
            alert_manager.acknowledge_alert(list(alert_manager._active_alerts.keys())[0])

            # Get history with limit
            history = alert_manager.get_alert_history(limit=2)

            assert len(history) <= 2

        asyncio.run(test_history())

    def test_clear_active_alerts(self, alert_manager):
        """Test clearing all active alerts."""
        import asyncio

        async def test_clear():
            # Create some alerts
            await alert_manager.create_alert(
                AlertSeverity.WARNING, "Alert 1", "Message 1", "service-1"
            )
            await alert_manager.create_alert(
                AlertSeverity.CRITICAL, "Alert 2", "Message 2", "service-2"
            )

            # Clear all
            count = alert_manager.clear_active_alerts()

            assert count == 2
            assert len(alert_manager.get_active_alerts()) == 0

        asyncio.run(test_clear())

    def test_get_alert_count(self, alert_manager):
        """Test getting alert counts by severity."""
        import asyncio

        async def test_count():
            # Create alerts of different severities
            await alert_manager.create_alert(
                AlertSeverity.CRITICAL, "Critical", "Critical message", "service-1"
            )
            await alert_manager.create_alert(
                AlertSeverity.CRITICAL, "Critical 2", "Critical message 2", "service-2"
            )
            await alert_manager.create_alert(
                AlertSeverity.WARNING, "Warning", "Warning message", "service-3"
            )
            await alert_manager.create_alert(
                AlertSeverity.INFO, "Info", "Info message", "service-4"
            )

            counts = alert_manager.get_alert_count()

            assert counts["critical"] == 2
            assert counts["warning"] == 1
            assert counts["info"] == 1

        asyncio.run(test_count())

    def test_set_threshold(self, alert_manager):
        """Test setting an alert threshold."""
        threshold = AlertThreshold(
            metric_name="cpu_percent",
            warning_threshold=70.0,
            critical_threshold=90.0
        )

        alert_manager.set_threshold("test-service", threshold)

        assert "test-service" in alert_manager.thresholds
        assert alert_manager.thresholds["test-service"].metric_name == "cpu_percent"

    def test_remove_threshold(self, alert_manager):
        """Test removing an alert threshold."""
        threshold = AlertThreshold(metric_name="cpu_percent")
        alert_manager.set_threshold("test-service", threshold)

        alert_manager.remove_threshold("test-service")

        assert "test-service" not in alert_manager.thresholds

    def test_subscribe_unsubscribe(self, alert_manager):
        """Test subscribing and unsubscribing from alerts."""
        callback_called = []

        def test_callback(alert):
            callback_called.append(alert)

        alert_manager.subscribe(test_callback)
        assert test_callback in alert_manager._subscribers

        alert_manager.unsubscribe(test_callback)
        assert test_callback not in alert_manager._subscribers


class TestAlertThreshold:
    """Tests for AlertThreshold."""

    def test_threshold_creation(self):
        """Test creating an alert threshold."""
        threshold = AlertThreshold(
            metric_name="cpu_percent",
            warning_threshold=70.0,
            critical_threshold=90.0,
            comparison="greater_than"
        )

        assert threshold.metric_name == "cpu_percent"
        assert threshold.warning_threshold == 70.0
        assert threshold.critical_threshold == 90.0
        assert threshold.comparison == "greater_than"

    def test_threshold_optional_fields(self):
        """Test creating threshold with optional fields."""
        threshold = AlertThreshold(
            metric_name="memory_mb",
            critical_threshold=2000.0
        )

        assert threshold.warning_threshold is None
        assert threshold.critical_threshold == 2000.0
        assert threshold.comparison == "greater_than"  # Default

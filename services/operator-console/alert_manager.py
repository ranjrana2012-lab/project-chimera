"""
Alert manager for Operator Console.

Manages alert generation, threshold checking, and alert history.
"""

import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from models import Alert, AlertSeverity

logger = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Threshold configuration for generating alerts."""
    metric_name: str
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison: str = "greater_than"  # greater_than, less_than, equal_to


class AlertManager:
    """Manages alert generation and tracking."""

    def __init__(self, thresholds: Dict[str, AlertThreshold] = None):
        """Initialize the alert manager.

        Args:
            thresholds: Dictionary mapping service names to their alert thresholds
        """
        self.thresholds = thresholds or {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._subscribers: List[Callable] = []
        self._last_alert_time: Dict[str, datetime] = {}

        # Alert cooldown to prevent spamming
        self._alert_cooldown = timedelta(minutes=5)

    def set_threshold(self, service_name: str, threshold: AlertThreshold) -> None:
        """Set alert threshold for a service.

        Args:
            service_name: Name of the service
            threshold: Alert threshold configuration
        """
        self.thresholds[service_name] = threshold
        logger.info(f"Set alert threshold for {service_name}: {threshold.metric_name}")

    def remove_threshold(self, service_name: str) -> None:
        """Remove alert threshold for a service.

        Args:
            service_name: Name of the service
        """
        if service_name in self.thresholds:
            del self.thresholds[service_name]
            logger.info(f"Removed alert threshold for {service_name}")

    def subscribe(self, callback: Callable[[Alert], None]) -> None:
        """Subscribe to new alerts.

        Args:
            callback: Function to call when new alert is generated
        """
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Alert], None]) -> None:
        """Unsubscribe from alerts.

        Args:
            callback: Callback function to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def check_metrics(self, service_name: str, metrics: Dict[str, float]) -> List[Alert]:
        """Check metrics against thresholds and generate alerts.

        Args:
            service_name: Name of the service
            metrics: Dictionary of metric names to values

        Returns:
            List of generated alerts
        """
        generated_alerts = []

        if service_name not in self.thresholds:
            return generated_alerts

        threshold = self.thresholds[service_name]

        # Check if metric exists
        if threshold.metric_name not in metrics:
            return generated_alerts

        value = metrics[threshold.metric_name]

        # Check threshold based on comparison type
        should_alert = False
        severity = None

        if threshold.comparison == "greater_than":
            if threshold.critical_threshold is not None and value >= threshold.critical_threshold:
                should_alert = True
                severity = AlertSeverity.CRITICAL
            elif threshold.warning_threshold is not None and value >= threshold.warning_threshold:
                should_alert = True
                severity = AlertSeverity.WARNING
        elif threshold.comparison == "less_than":
            if threshold.critical_threshold is not None and value <= threshold.critical_threshold:
                should_alert = True
                severity = AlertSeverity.CRITICAL
            elif threshold.warning_threshold is not None and value <= threshold.warning_threshold:
                should_alert = True
                severity = AlertSeverity.WARNING

        if should_alert and severity:
            # Check cooldown
            alert_key = f"{service_name}:{threshold.metric_name}"
            now = datetime.now()

            if alert_key in self._last_alert_time:
                time_since_last = now - self._last_alert_time[alert_key]
                if time_since_last < self._alert_cooldown:
                    logger.debug(f"Alert for {alert_key} is in cooldown")
                    return generated_alerts

            # Create alert
            alert = await self.create_alert(
                severity=severity,
                title=f"{service_name} {threshold.metric_name} threshold exceeded",
                message=f"{threshold.metric_name} is {value:.2f}, threshold is {threshold.critical_threshold or threshold.warning_threshold}",
                source=service_name,
                metadata={"metric_name": threshold.metric_name, "metric_value": value}
            )

            self._last_alert_time[alert_key] = now
            generated_alerts.append(alert)

        return generated_alerts

    async def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str,
        metadata: Dict[str, any] = None
    ) -> Alert:
        """Create a new alert.

        Args:
            severity: Alert severity
            title: Alert title
            message: Alert message
            source: Alert source service
            metadata: Optional additional metadata

        Returns:
            Created alert
        """
        # Generate unique alert ID
        alert_hash = hashlib.md5(f"{title}{message}{source}{datetime.now().isoformat()}".encode()).hexdigest()
        alert_id = f"alert_{alert_hash[:12]}"

        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            acknowledged=False,
            metadata=metadata or {}
        )

        # Add to active alerts
        self._active_alerts[alert_id] = alert

        # Add to history
        self._alert_history.append(alert)

        # Keep history limited to last 1000 alerts
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-1000:]

        # Notify subscribers
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Alert subscriber error: {e}")

        logger.warning(f"Alert created: [{severity.value}] {title} from {source}")
        return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge

        Returns:
            True if alert was acknowledged, False otherwise
        """
        if alert_id not in self._active_alerts:
            return False

        self._active_alerts[alert_id].acknowledged = True

        # Remove from active alerts
        alert = self._active_alerts.pop(alert_id)
        self._alert_history.append(alert)

        logger.info(f"Alert acknowledged: {alert_id}")
        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts.

        Returns:
            List of active alerts
        """
        return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of historical alerts
        """
        return self._alert_history[-limit:]

    def clear_active_alerts(self) -> int:
        """Clear all active alerts.

        Returns:
            Number of alerts cleared
        """
        count = len(self._active_alerts)
        self._active_alerts.clear()
        logger.info(f"Cleared {count} active alerts")
        return count

    def get_alert_count(self) -> Dict[str, int]:
        """Get count of active alerts by severity.

        Returns:
            Dictionary mapping severity to count
        """
        counts = {
            "critical": 0,
            "warning": 0,
            "info": 0
        }

        for alert in self._active_alerts.values():
            counts[alert.severity.value] += 1

        return counts


__all__ = [
    "AlertManager",
    "AlertThreshold",
]

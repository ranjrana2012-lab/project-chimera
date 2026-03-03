"""
Alerts and incidents panel for dashboard.

Tracks alerts, incidents, and provides rule-based alerting.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = 4
    ERROR = 3
    WARNING = 2
    INFO = 1

    @classmethod
    def from_string(cls, value: str) -> "AlertSeverity":
        """Create severity from string."""
        mapping = {
            "critical": cls.CRITICAL,
            "error": cls.ERROR,
            "warning": cls.WARNING,
            "info": cls.INFO
        }
        return mapping.get(value.lower(), cls.INFO)


class IncidentStatus(Enum):
    """Incident status values."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """
    Represents a single alert.

    Attributes:
        id: Unique alert identifier
        severity: Alert severity level
        title: Alert title
        message: Alert message
        created_at: When the alert was created
        acknowledged: Whether alert has been acknowledged
        service: Related service (optional)
        metadata: Additional data
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    service: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Info alerts auto-dismiss after 30 seconds
    AUTO_DISMISS_SECONDS = 30

    def is_active(self) -> bool:
        """Check if alert is still active."""
        if self.acknowledged:
            return False

        # Auto-dismiss old info alerts
        if (self.severity == AlertSeverity.INFO and
            (datetime.now(timezone.utc) - self.created_at).total_seconds() > self.AUTO_DISMISS_SECONDS):
            return False

        return True

    @property
    def age_seconds(self) -> float:
        """Get alert age in seconds."""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "severity": self.severity.name.lower(),
            "severity_value": self.severity.value,
            "title": self.title,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "service": self.service,
            "is_active": self.is_active(),
            "age_seconds": self.age_seconds
        }


@dataclass
class Incident:
    """
    Represents an incident.

    Attributes:
        id: Unique incident identifier
        title: Incident title
        description: Incident description
        status: Incident status
        severity: Incident severity
        started_at: When incident started
        resolved_at: When incident was resolved
        resolution: Resolution description
        related_alerts: IDs of related alerts
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: IncidentStatus = IncidentStatus.OPEN
    severity: str = "warning"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    related_alerts: List[str] = field(default_factory=list)

    def is_active(self) -> bool:
        """Check if incident is still active."""
        return self.status != IncidentStatus.RESOLVED

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get incident duration in seconds."""
        if self.resolved_at is None:
            return (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return (self.resolved_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "severity": self.severity,
            "started_at": self.started_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution": self.resolution,
            "is_active": self.is_active(),
            "duration_seconds": self.duration_seconds
        }


class AlertManager:
    """
    Manages alerts and incidents.

    Provides rule-based alerting and incident tracking.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.incidents: Dict[str, Incident] = {}
        self._coverage_baseline: Dict[str, float] = {}

        logger.info("AlertManager initialized")

    def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        service: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Create a new alert.

        Args:
            severity: Alert severity
            title: Alert title
            message: Alert message
            service: Related service
            metadata: Additional data

        Returns:
            Created alert
        """
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            service=service,
            metadata=metadata or {}
        )
        self.alerts[alert.id] = alert
        logger.info(f"Created alert: {title} ({severity.name})")
        return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if acknowledged
        """
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            logger.info(f"Acknowledged alert: {alert_id}")
            return True
        return False

    def dismiss_alert(self, alert_id: str) -> bool:
        """
        Dismiss (remove) an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if dismissed
        """
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Dismissed alert: {alert_id}")
            return True
        return False

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.alerts.get(alert_id)

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        active = [a for a in self.alerts.values() if a.is_active()]
        # Sort by severity (highest first) then by time (newest first)
        active.sort(key=lambda a: (a.severity.value, a.created_at), reverse=True)
        return active

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity level."""
        return [a for a in self.alerts.values() if a.severity == severity]

    def auto_dismiss_old_alerts(self) -> int:
        """
        Auto-dismiss old info alerts.

        Returns:
            Number of alerts dismissed
        """
        to_dismiss = [
            alert_id for alert_id, alert in self.alerts.items()
            if not alert.is_active()
        ]

        for alert_id in to_dismiss:
            del self.alerts[alert_id]

        if to_dismiss:
            logger.info(f"Auto-dismissed {len(to_dismiss)} alerts")

        return len(to_dismiss)

    def create_incident(
        self,
        title: str,
        description: str,
        severity: str = "warning"
    ) -> Incident:
        """
        Create a new incident.

        Args:
            title: Incident title
            description: Incident description
            severity: Incident severity

        Returns:
            Created incident
        """
        incident = Incident(
            title=title,
            description=description,
            severity=severity
        )
        self.incidents[incident.id] = incident
        logger.info(f"Created incident: {title}")
        return incident

    def resolve_incident(self, incident_id: str, resolution: str) -> bool:
        """
        Resolve an incident.

        Args:
            incident_id: Incident identifier
            resolution: Resolution description

        Returns:
            True if resolved
        """
        if incident_id in self.incidents:
            self.incidents[incident_id].status = IncidentStatus.RESOLVED
            self.incidents[incident_id].resolved_at = datetime.now(timezone.utc)
            self.incidents[incident_id].resolution = resolution
            logger.info(f"Resolved incident: {incident_id}")
            return True
        return False

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get an incident by ID."""
        return self.incidents.get(incident_id)

    def get_active_incidents(self) -> List[Incident]:
        """Get all active incidents."""
        return [i for i in self.incidents.values() if i.is_active()]

    # Rule-based alerting methods

    def check_service_health(
        self,
        service_name: str,
        latency_ms: float,
        error_rate: float
    ) -> List[Alert]:
        """
        Check service health and create alerts if needed.

        Args:
            service_name: Service name
            latency_ms: Response time in milliseconds
            error_rate: Error rate (0-1)

        Returns:
            List of new alerts
        """
        alerts = []

        # High latency check
        if latency_ms > 5000:
            alerts.append(self.create_alert(
                severity=AlertSeverity.WARNING,
                title=f"{service_name} high latency",
                message=f"Response time is {latency_ms:.0f}ms (>5s threshold)",
                service=service_name,
                metadata={"latency_ms": latency_ms}
            ))

        # High error rate check
        if error_rate > 0.05:  # 5%
            alerts.append(self.create_alert(
                severity=AlertSeverity.ERROR,
                title=f"{service_name} high error rate",
                message=f"Error rate is {error_rate * 100:.1f}% (>5% threshold)",
                service=service_name,
                metadata={"error_rate": error_rate}
            ))

        return alerts

    def check_coverage(
        self,
        service_name: str,
        current_coverage: float,
        threshold: float = 80.0
    ) -> List[Alert]:
        """
        Check coverage and create alerts if dropped.

        Args:
            service_name: Service name
            current_coverage: Current coverage percentage
            threshold: Coverage threshold

        Returns:
            List of new alerts
        """
        alerts = []

        # Establish baseline if not exists
        if service_name not in self._coverage_baseline:
            self._coverage_baseline[service_name] = current_coverage
            return alerts

        baseline = self._coverage_baseline[service_name]

        # Check for drop
        if current_coverage < threshold and baseline >= threshold:
            alerts.append(self.create_alert(
                severity=AlertSeverity.WARNING,
                title=f"Coverage drop in {service_name}",
                message=f"Coverage dropped from {baseline:.1f}% to {current_coverage:.1f}% (<{threshold}%)",
                service=service_name,
                metadata={
                    "baseline": baseline,
                    "current": current_coverage
                }
            ))

        # Update baseline gradually
        self._coverage_baseline[service_name] = (
            0.9 * baseline + 0.1 * current_coverage
        )

        return alerts

    def check_flaky_tests(
        self,
        service: str,
        flaky_count: int,
        threshold: int = 2
    ) -> List[Alert]:
        """
        Check for flaky tests and create alerts.

        Args:
            service: Service name
            flaky_count: Number of flaky tests
            threshold: Alert threshold

        Returns:
            List of new alerts
        """
        alerts = []

        if flaky_count >= threshold:
            alerts.append(self.create_alert(
                severity=AlertSeverity.WARNING,
                title=f"{flaky_count} flaky tests detected in {service}",
                message=f"{flaky_count} tests are showing inconsistent results",
                service=service,
                metadata={"flaky_count": flaky_count}
            ))

        return alerts

    def get_summary(self) -> Dict[str, Any]:
        """
        Get alert and incident summary.

        Returns:
            Summary dictionary
        """
        active_alerts = self.get_active_alerts()

        return {
            "active_alerts": len(active_alerts),
            "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "error": len([a for a in active_alerts if a.severity == AlertSeverity.ERROR]),
            "warning": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
            "info": len([a for a in active_alerts if a.severity == AlertSeverity.INFO]),
            "active_incidents": len(self.get_active_incidents()),
            "alerts": [a.to_dict() for a in active_alerts[:10]],  # Top 10
            "incidents": [i.to_dict() for i in self.get_active_incidents()]
        }

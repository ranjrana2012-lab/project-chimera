"""Response models for Operator Console."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNRESPONSIVE = "unresponsive"
    OFFLINE = "offline"


class ServiceHealth(BaseModel):
    """Health status of a service."""

    service_name: str = Field(..., description="Name of the service")
    status: ServiceStatus = Field(..., description="Current health status")
    last_seen: datetime = Field(..., description="Last heartbeat timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime")
    error_count: int = Field(default=0, description="Recent error count")
    metrics: Optional[dict] = Field(default_factory=dict, description="Service metrics")


class ConsoleStatus(BaseModel):
    """Overall console status."""

    services: dict[str, ServiceHealth] = Field(
        default_factory=dict, description="Status of all services"
    )
    pending_approvals: int = Field(..., description="Count of pending approvals")
    active_alerts: int = Field(..., description="Count of active alerts")
    active_overrides: list[str] = Field(
        default_factory=list, description="Currently active overrides"
    )
    system_mode: str = Field(default="automatic", description="Current system mode")
    console_uptime: float = Field(..., description="Console uptime in seconds")


class EventType(str, Enum):
    """Types of events in the stream."""

    SCRIPT_GENERATED = "script_generated"
    LIGHTING_CHANGED = "lighting_changed"
    AUDIO_PLAYED = "audio_played"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DECIDED = "approval_decided"
    OVERRIDE_TRIGGERED = "override_triggered"
    SERVICE_STATUS_CHANGE = "service_status_change"
    ALERT = "alert"
    INFO = "info"


class EventSeverity(str, Enum):
    """Event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class StreamEvent(BaseModel):
    """Event in the stream."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Severity")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event time")
    source_service: str = Field(..., description="Service that generated event")
    title: str = Field(..., description="Event title")
    message: str = Field(..., description="Event message")
    data: Optional[dict[str, Any]] = Field(default_factory=dict, description="Event data")
    requires_approval: bool = Field(default=False, description="Needs approval")
    approval_id: Optional[str] = Field(None, description="Associated approval ID")


class EventStream(BaseModel):
    """Wrapper for event stream."""

    events: list[StreamEvent] = Field(default_factory=list, description="Recent events")
    total_count: int = Field(..., description="Total event count")
    filtered: bool = Field(default=False, description="Whether results are filtered")


class Alert(BaseModel):
    """Active alert."""

    alert_id: str = Field(..., description="Unique alert identifier")
    severity: EventSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    source_service: str = Field(..., description="Service that raised alert")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert time")
    resolved: bool = Field(default=False, description="Whether alert is resolved")
    action_required: bool = Field(default=False, description="Requires action")

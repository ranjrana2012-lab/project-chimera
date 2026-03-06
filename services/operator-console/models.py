"""
Pydantic models for Operator Console.

Data models for requests, responses, and internal data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """Service health status."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status: alive or dead")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    status: str = Field(description="Service status: ready or not_ready")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Health check results per service")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ServiceInfo(BaseModel):
    """Service information."""
    name: str = Field(description="Service name")
    url: str = Field(description="Service URL")
    status: ServiceStatus = Field(default=ServiceStatus.UNKNOWN, description="Current service status")
    health_check_url: Optional[str] = Field(default=None, description="Health check endpoint URL")
    metrics_url: Optional[str] = Field(default=None, description="Metrics endpoint URL")


class ServiceList(BaseModel):
    """List of all services."""
    services: list[ServiceInfo] = Field(description="List of services")
    total: int = Field(description="Total number of services")
    up: int = Field(default=0, description="Number of services up")
    down: int = Field(default=0, description="Number of services down")
    degraded: int = Field(default=0, description="Number of degraded services")


class ServiceMetrics(BaseModel):
    """Metrics for a single service."""
    service_name: str = Field(description="Service name")
    cpu_percent: Optional[float] = Field(default=None, description="CPU usage percentage")
    memory_mb: Optional[float] = Field(default=None, description="Memory usage in MB")
    request_rate: Optional[float] = Field(default=None, description="Request rate per second")
    error_rate: Optional[float] = Field(default=None, description="Error rate as percentage")
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metrics timestamp")


class AllMetrics(BaseModel):
    """Metrics for all services."""
    metrics: Dict[str, ServiceMetrics] = Field(default_factory=dict, description="Service name to metrics mapping")
    timestamp: datetime = Field(default_factory=datetime.now, description="Collection timestamp")


class Alert(BaseModel):
    """Alert notification."""
    id: str = Field(description="Unique alert ID")
    severity: AlertSeverity = Field(description="Alert severity")
    title: str = Field(description="Alert title")
    message: str = Field(description="Alert message")
    source: str = Field(description="Alert source service")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert creation time")
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional alert metadata")


class AlertList(BaseModel):
    """List of alerts."""
    alerts: list[Alert] = Field(description="List of alerts")
    total: int = Field(description="Total number of alerts")
    critical: int = Field(default=0, description="Number of critical alerts")
    warning: int = Field(default=0, description="Number of warning alerts")
    info: int = Field(default=0, description="Number of info alerts")


class ServiceControlRequest(BaseModel):
    """Service control request."""
    action: str = Field(description="Action: start, stop, restart, or reload")
    reason: Optional[str] = Field(default=None, description="Reason for control action")


class ServiceControlResponse(BaseModel):
    """Service control response."""
    service: str = Field(description="Service name")
    action: str = Field(description="Action performed")
    status: str = Field(description="Action status: success or failed")
    message: str = Field(description="Status message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str = Field(description="Message type: metric, alert, or status")
    data: Dict[str, Any] = Field(description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class MetricUpdate(BaseModel):
    """Real-time metric update."""
    service: str = Field(description="Service name")
    metric: str = Field(description="Metric name")
    value: float = Field(description="Metric value")
    unit: str = Field(description="Metric unit")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metric timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

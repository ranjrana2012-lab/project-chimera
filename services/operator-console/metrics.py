"""
Prometheus metrics for Operator Console.

Provides metrics collection and reporting for the operator console service.
"""

from prometheus_client import Gauge, Counter, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Service information
service_info = Info(
    'operator_console',
    'Operator console service information'
)

# WebSocket connections
websocket_connections = Gauge(
    'operator_console_websocket_connections',
    'Number of active WebSocket connections'
)

# Service health status
service_up = Gauge(
    'operator_console_service_up',
    'Service health status (1=up, 0=down)',
    ['service_name']
)

# Service metrics collected
service_cpu = Gauge(
    'operator_console_service_cpu_percent',
    'Service CPU usage percentage',
    ['service_name']
)

service_memory = Gauge(
    'operator_console_service_memory_mb',
    'Service memory usage in MB',
    ['service_name']
)

service_request_rate = Gauge(
    'operator_console_service_request_rate',
    'Service request rate per second',
    ['service_name']
)

service_error_rate = Gauge(
    'operator_console_service_error_rate',
    'Service error rate as percentage',
    ['service_name']
)

# Alerts
alerts_total = Counter(
    'operator_console_alerts_total',
    'Total number of alerts generated',
    ['severity']
)

active_alerts = Gauge(
    'operator_console_active_alerts',
    'Number of active alerts',
    ['severity']
)

# Metrics collection
metrics_collection_duration = Histogram(
    'operator_console_metrics_collection_duration_seconds',
    'Time spent collecting metrics from services',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

metrics_collection_errors = Counter(
    'operator_console_metrics_collection_errors_total',
    'Total number of metrics collection errors',
    ['service_name']
)

# WebSocket messages
websocket_messages_sent = Counter(
    'operator_console_websocket_messages_sent_total',
    'Total number of WebSocket messages sent',
    ['message_type']
)

websocket_message_duration = Histogram(
    'operator_console_websocket_message_duration_seconds',
    'Time to send WebSocket message',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25]
)


def init_service_info(service_name: str, version: str = "1.0.0") -> None:
    """Initialize service information metric.

    Args:
        service_name: Name of the service
        version: Service version
    """
    try:
        service_info.info({
            'service': service_name,
            'version': version
        })
        logger.info(f"Service info initialized: {service_name} v{version}")
    except Exception as e:
        logger.error(f"Failed to initialize service info: {e}")


def record_service_status(service_name: str, is_up: bool) -> None:
    """Record service health status.

    Args:
        service_name: Name of the service
        is_up: Whether the service is up
    """
    try:
        service_up.labels(service_name=service_name).set(1 if is_up else 0)
    except Exception as e:
        logger.error(f"Failed to record service status: {e}")


def record_service_metrics(
    service_name: str,
    cpu_percent: Optional[float] = None,
    memory_mb: Optional[float] = None,
    request_rate: Optional[float] = None,
    error_rate: Optional[float] = None
) -> None:
    """Record service metrics.

    Args:
        service_name: Name of the service
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in MB
        request_rate: Request rate per second
        error_rate: Error rate as percentage
    """
    try:
        if cpu_percent is not None:
            service_cpu.labels(service_name=service_name).set(cpu_percent)
        if memory_mb is not None:
            service_memory.labels(service_name=service_name).set(memory_mb)
        if request_rate is not None:
            service_request_rate.labels(service_name=service_name).set(request_rate)
        if error_rate is not None:
            service_error_rate.labels(service_name=service_name).set(error_rate)
    except Exception as e:
        logger.error(f"Failed to record service metrics: {e}")


def record_alert(severity: str) -> None:
    """Record an alert.

    Args:
        severity: Alert severity (critical, warning, info)
    """
    try:
        alerts_total.labels(severity=severity).inc()
        active_alerts.labels(severity=severity).inc()
    except Exception as e:
        logger.error(f"Failed to record alert: {e}")


def acknowledge_alert(severity: str) -> None:
    """Acknowledge an alert.

    Args:
        severity: Alert severity
    """
    try:
        active_alerts.labels(severity=severity).dec()
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")


def record_metrics_collection_duration(duration: float) -> None:
    """Record metrics collection duration.

    Args:
        duration: Duration in seconds
    """
    try:
        metrics_collection_duration.observe(duration)
    except Exception as e:
        logger.error(f"Failed to record collection duration: {e}")


def record_collection_error(service_name: str) -> None:
    """Record a metrics collection error.

    Args:
        service_name: Name of the service
    """
    try:
        metrics_collection_errors.labels(service_name=service_name).inc()
    except Exception as e:
        logger.error(f"Failed to record collection error: {e}")


def record_websocket_message(message_type: str, duration: float) -> None:
    """Record a WebSocket message.

    Args:
        message_type: Type of message (metric, alert, status)
        duration: Time to send message in seconds
    """
    try:
        websocket_messages_sent.labels(message_type=message_type).inc()
        websocket_message_duration.observe(duration)
    except Exception as e:
        logger.error(f"Failed to record websocket message: {e}")


def update_websocket_connections(count: int) -> None:
    """Update WebSocket connection count.

    Args:
        count: Number of active connections
    """
    try:
        websocket_connections.set(count)
    except Exception as e:
        logger.error(f"Failed to update websocket connections: {e}")


def get_metrics_text() -> bytes:
    """Get Prometheus metrics text format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest()


__all__ = [
    "init_service_info",
    "record_service_status",
    "record_service_metrics",
    "record_alert",
    "acknowledge_alert",
    "record_metrics_collection_duration",
    "record_collection_error",
    "record_websocket_message",
    "update_websocket_connections",
    "get_metrics_text",
    "CONTENT_TYPE_LATEST",
]

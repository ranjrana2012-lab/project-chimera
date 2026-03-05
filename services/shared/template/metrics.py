# metrics.py
from prometheus_client import Counter, Histogram, Info
import time

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics (to be extended by services)
business_metrics = Counter(
    'business_operations_total',
    'Total business operations',
    ['operation', 'status']
)

# Service info
service_info = Info(
    'service',
    'Service information'
)


def init_service_info(service_name: str, version: str = "1.0.0"):
    """Initialize service info metric"""
    service_info.info({
        'name': service_name,
        'version': version
    })


def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    request_count.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()
    request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_business_operation(operation: str, status: str = "success"):
    """Record business operation metric"""
    business_metrics.labels(
        operation=operation,
        status=status
    ).inc()

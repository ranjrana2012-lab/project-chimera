"""OpenTelemetry instrumentation module for distributed tracing.

This module provides utilities for setting up OpenTelemetry tracing
with Jaeger exporter, automatic FastAPI instrumentation, and helper
functions for manual span instrumentation.
"""

import os
from typing import Optional

# OpenTelemetry imports - wrapped in try/except for optional installation
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.sdk.trace import Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

# Jaeger exporter is optional
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False


def setup_telemetry(service_name: str, jaeger_host: str = "jaeger.shared.svc.cluster.local"):
    """Set up OpenTelemetry tracing and metrics.

    Args:
        service_name: Name of the service being instrumented
        jaeger_host: Hostname of the Jaeger agent (default: jaeger.shared.svc.cluster.local)

    Returns:
        Tracer instance for creating manual spans, or None if OpenTelemetry is not available

    Example:
        >>> tracer = setup_telemetry("scenespeak-agent")
        >>> with tracer.start_as_current_span("my_operation"):
        ...     # Your code here
        ...     pass
    """
    if not OPENTELEMETRY_AVAILABLE:
        print("Warning: OpenTelemetry not installed, returning mock tracer")
        return None

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })

    # Set up tracing provider
    provider = TracerProvider(resource=resource)

    # Configure sampling (10% of traces)
    sampler = TraceIdRatioBased(0.1)

    # Add Jaeger exporter if available
    jaeger_enabled = JAEGER_AVAILABLE
    if JAEGER_AVAILABLE:
        try:
            # Import JaegerExporter here to avoid import errors when not available
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            provider.add_span_processor(
                BatchSpanProcessor(
                    JaegerExporter(
                        agent_host_name=jaeger_host,
                        agent_port=6831,
                    )
                )
            )
        except ImportError:
            print("Warning: Jaeger exporter import failed, using console exporter only")
            jaeger_enabled = False
    else:
        print("Warning: Jaeger exporter not available, using console exporter only")

    # Add console exporter for development
    if os.getenv("ENVIRONMENT") == "development" or not jaeger_enabled:
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    # Set the global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    tracer = trace.get_tracer(__name__, service_name)

    return tracer


def instrument_fastapi(app):
    """Instrument FastAPI app with automatic tracing.

    This function automatically instruments all FastAPI endpoints
    and outgoing HTTPX requests.

    Args:
        app: FastAPI application instance

    Example:
        >>> from fastapi import FastAPI
        >>> from platform.monitoring.telemetry import setup_telemetry, instrument_fastapi
        >>>
        >>> tracer = setup_telemetry("my-service")
        >>> app = FastAPI()
        >>> instrument_fastapi(app)
    """
    if not OPENTELEMETRY_AVAILABLE:
        print("Warning: OpenTelemetry not installed, skipping instrumentation")
        return

    # Instrument FastAPI app
    FastAPIInstrumentor.instrument_app(app)

    # Instrument HTTPX for outgoing calls
    HTTPXClientInstrumentor().instrument()


def add_span_attributes(span, attributes: dict):
    """Add attributes to current span.

    Args:
        span: OpenTelemetry span instance
        attributes: Dictionary of attributes to add

    Example:
        >>> from opentelemetry import trace
        >>> from platform.monitoring.telemetry import add_span_attributes
        >>>
        >>> current_span = trace.get_current_span()
        >>> add_span_attributes(current_span, {
        ...     "user.id": "123",
        ...     "request.path": "/api/v1/generate"
        ... })
    """
    if not OPENTELEMETRY_AVAILABLE or span is None:
        return

    for key, value in attributes.items():
        span.set_attribute(key, value)


def record_error(span, error: Exception, attributes: dict = None):
    """Record error on span.

    Args:
        span: OpenTelemetry span instance
        error: Exception to record
        attributes: Optional dictionary of error-related attributes

    Example:
        >>> from opentelemetry import trace
        >>> from platform.monitoring.telemetry import record_error
        >>>
        >>> current_span = trace.get_current_span()
        >>> try:
        ...     # Some operation that might fail
        ...     pass
        ... except Exception as e:
        ...     record_error(current_span, e, {"error.context": "database_query"})
    """
    if not OPENTELEMETRY_AVAILABLE or span is None:
        return

    # Record the exception
    span.record_exception(error)

    # Set span status to error
    span.set_status(Status(StatusCode.ERROR, str(error)))

    # Add additional attributes if provided
    if attributes:
        add_span_attributes(span, attributes)

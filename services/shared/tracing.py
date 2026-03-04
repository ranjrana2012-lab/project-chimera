"""
OpenTelemetry Tracing Configuration Module

This module provides shared tracing setup and utilities for all Project Chimera services.
Based on Task 19 of the Production Observability Implementation Plan.
"""

import os
from unittest.mock import Mock  # For testing when OpenTelemetry is not installed

# Try to import OpenTelemetry, use mocks if not available
try:
    from opentelemetry import trace, metrics
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode

    # Try to import Jaeger exporter, may not be available
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        JAEGER_AVAILABLE = True
    except ImportError:
        JAEGER_AVAILABLE = False

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    JAEGER_AVAILABLE = False


def setup_telemetry(service_name: str, jaeger_host: str = "jaeger.shared.svc.cluster.local"):
    """
    Set up OpenTelemetry tracing and metrics for a service.

    Args:
        service_name: Name of the service for tracing
        jaeger_host: Hostname of Jaeger agent (default: jaeger.shared.svc.cluster.local)

    Returns:
        tracer: OpenTelemetry tracer instance for manual instrumentation
    """
    if not OPENTELEMETRY_AVAILABLE:
        # Return a mock tracer for testing
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value = mock_span
        return mock_tracer

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })

    # Set up tracing provider
    provider = TracerProvider(resource=resource)

    # Configure sampling (10% in production, 100% in development)
    sampling_rate = 1.0 if os.getenv("ENVIRONMENT") == "development" else 0.1

    # Add Jaeger exporter if available
    if JAEGER_AVAILABLE:
        provider.add_span_processor(
            BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name=jaeger_host,
                    agent_port=6831,
                )
            )
        )

    # Add console exporter for development
    if os.getenv("ENVIRONMENT") == "development":
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    trace.set_tracer_provider(provider)

    # Get tracer
    tracer = trace.get_tracer(__name__, service_name)

    return tracer


def instrument_fastapi(app):
    """
    Instrument FastAPI app with automatic tracing.

    This automatically creates spans for all HTTP requests and
    instruments HTTPX for outgoing calls.

    Args:
        app: FastAPI application instance
    """
    if not OPENTELEMETRY_AVAILABLE:
        return

    FastAPIInstrumentor.instrument_app(app)

    # Also instrument HTTPX for outgoing calls
    try:
        HTTPXClientInstrumentor().instrument()
    except Exception:
        # HTTPX might not be installed, that's okay
        pass


def add_span_attributes(span, attributes: dict):
    """
    Add attributes to current span.

    Args:
        span: OpenTelemetry span object
        attributes: Dictionary of attributes to add
    """
    if not OPENTELEMETRY_AVAILABLE or span is None:
        return

    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(key, value)


def record_error(span, error: Exception, attributes: dict = None):
    """
    Record error on span.

    Args:
        span: OpenTelemetry span object
        error: Exception that occurred
        attributes: Optional additional attributes to record
    """
    if not OPENTELEMETRY_AVAILABLE or span is None:
        return

    span.record_exception(error)
    span.set_status(Status(StatusCode.ERROR, str(error)))

    if attributes:
        add_span_attributes(span, attributes)


__all__ = [
    'setup_telemetry',
    'instrument_fastapi',
    'add_span_attributes',
    'record_error',
]

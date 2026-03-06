"""
Distributed tracing module for Operator Console.

Provides OpenTelemetry instrumentation for the operator console service.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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
    logger.warning("OpenTelemetry not installed, tracing will be disabled")

# OTLP exporter is optional
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    logger.debug("OTLP exporter not available, will use console exporter")


def setup_telemetry(
    service_name: str = "operator-console",
    otlp_endpoint: str = "http://localhost:4317",
    sample_rate: float = 0.1
) -> Optional[object]:
    """Set up OpenTelemetry tracing and metrics for Operator Console.

    Args:
        service_name: Name of the service being instrumented (default: "operator-console")
        otlp_endpoint: OTLP collector endpoint (default: http://localhost:4317)
        sample_rate: Fraction of traces to sample (default: 0.1 = 10%)

    Returns:
        Tracer instance for creating manual spans, or None if OpenTelemetry is not available

    Example:
        >>> tracer = setup_telemetry("operator-console")
        >>> with tracer.start_as_current_span("collect_metrics"):
        ...     # Your metrics collection code here
        ...     pass
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not installed, returning None tracer")
        return None

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.component": "operator-console"
    })

    # Set up tracing provider
    provider = TracerProvider(resource=resource)

    # Configure sampling
    sampler = TraceIdRatioBased(sample_rate)
    provider.sampler = sampler

    # Add OTLP exporter if available
    otlp_enabled = OTLP_AVAILABLE
    if OTLP_AVAILABLE:
        try:
            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                )
            )
            logger.info(f"OTLP exporter configured for {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"OTLP exporter setup failed: {e}, using console exporter")
            otlp_enabled = False
    else:
        logger.debug("OTLP exporter not available, using console exporter")

    # Add console exporter for development or when OTLP is unavailable
    if os.getenv("ENVIRONMENT") == "development" or not otlp_enabled:
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    # Set the global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    tracer = trace.get_tracer(__name__, service_name)

    logger.info(f"Telemetry setup complete for {service_name} with {sample_rate:.0%} sampling")

    return tracer


def instrument_fastapi(app) -> None:
    """Instrument FastAPI app with automatic tracing.

    This function automatically instruments all FastAPI endpoints
    and outgoing HTTPX requests for distributed tracing.

    Args:
        app: FastAPI application instance

    Example:
        >>> from fastapi import FastAPI
        >>> from tracing import setup_telemetry, instrument_fastapi
        >>>
        >>> tracer = setup_telemetry("operator-console")
        >>> app = FastAPI()
        >>> instrument_fastapi(app)
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not installed, skipping FastAPI instrumentation")
        return

    try:
        # Instrument FastAPI app
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation complete")

        # Instrument HTTPX for outgoing calls
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation complete")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def add_span_attributes(span, attributes: dict) -> None:
    """Add attributes to current span.

    This helper function adds multiple attributes to a span in a single call.
    Useful for enriching spans with operator console-specific context.

    Args:
        span: OpenTelemetry span instance (can be None)
        attributes: Dictionary of attributes to add

    Example:
        >>> from opentelemetry import trace
        >>> from tracing import add_span_attributes
        >>>
        >>> current_span = trace.get_current_span()
        >>> add_span_attributes(current_span, {
        ...     "service.name": "bsl-agent",
        ...     "metric.name": "cpu_percent",
        ...     "metric.value": 75.5
        ... })
    """
    if not OPENTELEMETRY_AVAILABLE or span is None:
        return

    for key, value in attributes.items():
        try:
            span.set_attribute(key, value)
        except Exception as e:
            logger.debug(f"Failed to set span attribute {key}: {e}")


def record_error(span, error: Exception, attributes: dict = None) -> None:
    """Record error on span with optional additional context.

    This helper function records an exception on a span and sets the span status
    to ERROR. Additional attributes can be provided for error context.

    Args:
        span: OpenTelemetry span instance (can be None)
        error: Exception to record
        attributes: Optional dictionary of error-related attributes

    Example:
        >>> from opentelemetry import trace
        >>> from tracing import record_error
        >>>
        >>> current_span = trace.get_current_span()
        >>> try:
        ...     # Some operation that might fail
        ...     collect_service_metrics(...)
        ... except Exception as e:
        ...     record_error(current_span, e, {
        ...         "error.context": "metrics_collection",
        ...     })
    """
    if not OPENTELEMETRY_AVAILABLE or span is None:
        return

    try:
        # Record the exception
        span.record_exception(error)

        # Set span status to error
        span.set_status(Status(StatusCode.ERROR, str(error)))

        # Add additional attributes if provided
        if attributes:
            add_span_attributes(span, attributes)
    except Exception as e:
        logger.debug(f"Failed to record error on span: {e}")


__all__ = [
    "setup_telemetry",
    "instrument_fastapi",
    "add_span_attributes",
    "record_error",
    "OPENTELEMETRY_AVAILABLE",
    "OTLP_AVAILABLE",
]

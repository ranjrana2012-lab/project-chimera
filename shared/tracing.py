"""
Shared OpenTelemetry Tracing Module
Project Chimera v0.5.0

This module provides centralized OpenTelemetry tracing configuration
for all Project Chimera services. It includes:

- Automatic instrumentation for FastAPI applications
- Custom span creation and context management
- OTLP span export to Jaeger/Tempo
- Console export for development debugging
- Graceful fallback when OpenTelemetry is unavailable

Usage:
    from shared.tracing import setup_tracing, instrument_fastapi

    # Setup tracing for your service
    tracer = setup_tracing(
        service_name="my-service",
        service_version="1.0.0"
    )

    # Instrument FastAPI app
    instrument_fastapi(app)

    # Use in code
    with tracer.start_as_current_span("operation_name"):
        # Your code here
        pass
"""

import logging
import os
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.propagate import inject
    from opentelemetry.context import Context
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer = None
_provider = None


@contextmanager
def nullcontext():
    """A no-op context manager for when tracing is disabled."""
    yield None


class NoOpSpan:
    """No-op span class for when tracing is disabled."""

    def __init__(self, name: str = "noop"):
        self.name = name

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class NoOpTracer:
    """No-op tracer class for when tracing is disabled."""

    def start_as_current_span(self, name: str, **kwargs):
        """Return a no-op span."""
        return nullcontext()

    def start_span(self, name: str, **kwargs):
        """Return a no-op span."""
        return NoOpSpan(name)


def setup_tracing(
    service_name: str,
    service_version: str = "0.5.0",
    otlp_endpoint: Optional[str] = None,
    environment: str = "development",
    enable_console_export: bool = False
):
    """
    Set up OpenTelemetry tracing for a service.

    Args:
        service_name: Name of the service (e.g., "bsl-agent")
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (default: from env or http://localhost:4317)
        environment: Environment (development, staging, production)
        enable_console_export: Enable console span exporter for debugging

    Returns:
        Configured tracer instance or no-op tracer if OTEL unavailable

    Environment Variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint
        OTEL_EXPORTER_OTLP_HEADERS: OTLP exporter headers (for auth)
        OTEL_SERVICE_NAME: Override service name
        OTEL_ENVIRONMENT: Override environment
    """
    global _tracer, _provider

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, returning no-op tracer")
        return NoOpTracer()

    try:
        # Get configuration from environment if not provided
        otlp_endpoint = otlp_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://localhost:4317"
        )
        environment = os.getenv("OTEL_ENVIRONMENT", environment)
        service_name = os.getenv("OTEL_SERVICE_NAME", service_name)

        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": environment,
            "service.namespace": "project-chimera",
            "service.language": "python",
        })

        # Set up trace provider
        _provider = TracerProvider(resource=resource)

        # Add OTLP exporter if endpoint is configured
        if otlp_endpoint and otlp_endpoint != "":
            try:
                # Get OTLP headers from environment if available
                headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")

                exporter_kwargs = {
                    "endpoint": otlp_endpoint,
                    "insecure": True,
                }

                # Add headers if provided
                if headers:
                    # Parse headers in format "key1=value1,key2=value2"
                    header_dict = {}
                    for h in headers.split(","):
                        if "=" in h:
                            key, value = h.split("=", 1)
                            header_dict[key.strip()] = value.strip()
                    if header_dict:
                        exporter_kwargs["headers"] = header_dict

                otlp_exporter = OTLPSpanExporter(**exporter_kwargs)
                _provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP tracing enabled: {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize OTLP exporter: {e}")
                if enable_console_export:
                    console_exporter = ConsoleSpanExporter()
                    _provider.add_span_processor(BatchSpanProcessor(console_exporter))
                    logger.info("Using console span exporter")
        elif enable_console_export:
            console_exporter = ConsoleSpanExporter()
            _provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Using console span exporter")

        # Set as global default provider
        trace.set_tracer_provider(_provider)

        # Create tracer
        _tracer = trace.get_tracer(__name__)

        logger.info(
            f"OpenTelemetry tracing initialized for {service_name} v{service_version}"
        )
        return _tracer

    except Exception as e:
        logger.error(f"Failed to set up tracing: {e}")
        return NoOpTracer()


def instrument_fastapi(app):
    """
    Instrument FastAPI application with automatic tracing.

    Automatically creates spans for all HTTP requests with attributes:
    - http.method: Request method
    - http.url: Request URL
    - http.status_code: Response status code
    - http.route: Matched route pattern

    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, skipping FastAPI instrumentation")
        return

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def get_tracer():
    """
    Get the global tracer instance.

    Returns:
        Tracer instance or no-op tracer
    """
    if _tracer is None:
        return NoOpTracer()
    return _tracer


def shutdown_tracing():
    """Shutdown tracing provider and flush spans."""
    global _provider

    if not OTEL_AVAILABLE:
        return

    if _provider:
        try:
            _provider.shutdown()
            logger.info("Tracing provider shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown tracing provider: {e}")


@contextmanager
def trace_operation(operation_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for tracing an operation.

    Args:
        operation_name: Name of the operation/span
        attributes: Optional attributes to add to the span

    Yields:
        Span object or no-op context

    Example:
        with trace_operation("generate_dialogue", {"prompt_length": 100}):
            result = generate(prompt)
    """
    if not OTEL_AVAILABLE:
        yield nullcontext()
        return

    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name) as span:
        if span and attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def add_span_attributes(span, attributes: Dict[str, Any]) -> None:
    """
    Add attributes to a span.

    Args:
        span: Span object
        attributes: Dictionary of attributes to add
    """
    if not OTEL_AVAILABLE or span is None:
        return

    try:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    except Exception as e:
        logger.warning(f"Failed to add span attributes: {e}")


def record_error(span, error: Exception, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Record an exception on a span.

    Args:
        span: Span object
        error: Exception to record
        attributes: Optional additional attributes
    """
    if not OTEL_AVAILABLE or span is None:
        return

    try:
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
    except Exception as e:
        logger.warning(f"Failed to record exception: {e}")


def add_span_event(span, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add an event to a span.

    Args:
        span: Span object
        name: Event name
        attributes: Optional event attributes
    """
    if not OTEL_AVAILABLE or span is None:
        return

    try:
        span.add_event(name, attributes)
    except Exception as e:
        logger.warning(f"Failed to add span event: {e}")


def inject_context(headers: Dict[str, str]) -> None:
    """
    Inject tracing context into headers for outgoing requests.

    Args:
        headers: Dictionary to inject trace context into

    Example:
        headers = {}
        inject_context(headers)
        # Now headers contains traceparent header for distributed tracing
    """
    if not OTEL_AVAILABLE:
        return

    try:
        inject(headers)
    except Exception as e:
        logger.warning(f"Failed to inject context: {e}")


# Standard span attributes for Project Chimera services
class SpanAttributes:
    """Standard attribute names for spans."""

    # Service attributes
    SERVICE_NAME = "service.name"
    SERVICE_VERSION = "service.version"
    SERVICE_NAMESPACE = "service.namespace"

    # Operation attributes
    OPERATION_NAME = "operation.name"
    OPERATION_TYPE = "operation.type"

    # Request attributes
    REQUEST_ID = "request.id"
    SHOW_ID = "show.id"
    SCENE_NUMBER = "scene.number"

    # Model attributes
    MODEL_NAME = "model.name"
    MODEL_TYPE = "model.type"
    MODEL_VERSION = "model.version"

    # Performance attributes
    LATENCY_MS = "latency.ms"
    TOKENS_INPUT = "tokens.input"
    TOKENS_OUTPUT = "tokens.output"

    # Error attributes
    ERROR_TYPE = "error.type"
    ERROR_MESSAGE = "error.message"


def create_service_attributes(
    service_name: str,
    service_version: str
) -> Dict[str, str]:
    """Create standard service attributes."""
    return {
        SpanAttributes.SERVICE_NAME: service_name,
        SpanAttributes.SERVICE_VERSION: service_version,
        SpanAttributes.SERVICE_NAMESPACE: "project-chimera",
    }


def create_operation_attributes(
    operation_name: str,
    operation_type: str,
    show_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, str]:
    """Create standard operation attributes."""
    attrs = {
        SpanAttributes.OPERATION_NAME: operation_name,
        SpanAttributes.OPERATION_TYPE: operation_type,
    }

    if show_id:
        attrs[SpanAttributes.SHOW_ID] = show_id
    if request_id:
        attrs[SpanAttributes.REQUEST_ID] = request_id

    return attrs

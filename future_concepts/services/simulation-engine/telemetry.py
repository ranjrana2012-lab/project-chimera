"""OpenTelemetry distributed tracing for the simulation engine."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Status, StatusCode
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager, contextmanager

logger = logging.getLogger(__name__)

# Global tracer
_tracer: Optional[trace.Tracer] = None
_exporter_initialized = False


def setup_telemetry(
    service_name: str = "simulation-engine",
    service_version: str = "0.1.0",
    use_console_exporter: bool = True
) -> None:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for tracing
        service_version: Version of the service
        use_console_exporter: Use console exporter for Phase 1 (production would use OTLP)
    """
    global _tracer, _exporter_initialized

    if _exporter_initialized:
        logger.debug("Telemetry already initialized")
        return

    try:
        # Create resource with service name
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            "deployment.environment": "development"
        })

        # Create provider
        provider = TracerProvider(resource=resource)

        # Create exporter (console for Phase 1, production would use OTLP/GRPC)
        if use_console_exporter:
            exporter = ConsoleSpanExporter()
        else:
            # Placeholder for OTLP exporter in Phase 2
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter()

        # Add exporter to provider
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(__name__)

        _exporter_initialized = True
        logger.info(f"OpenTelemetry initialized for service '{service_name}' v{service_version}")

    except ImportError as e:
        logger.warning(f"OpenTelemetry dependencies not installed: {e}")
        logger.warning("Telemetry will be disabled")
        _tracer = trace.get_tracer(__name__)
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        _tracer = trace.get_tracer(__name__)


def get_tracer() -> trace.Tracer:
    """
    Get the global tracer instance.

    Returns:
        The global tracer, initializing if necessary
    """
    global _tracer
    if _tracer is None:
        setup_telemetry()
    return _tracer


def is_initialized() -> bool:
    """
    Check if telemetry has been initialized.

    Returns:
        True if telemetry is initialized
    """
    return _exporter_initialized


@asynccontextmanager
async def trace_simulation(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for tracing simulation operations.

    Usage:
        async with trace_simulation("simulation", {"agent_count": 10}) as span:
            # Do simulation work
            span.set_attribute("result", "success")

    Args:
        name: Name of the span
        attributes: Optional attributes to add to the span

    Yields:
        The current span
    """
    tracer = get_tracer()
    attributes = attributes or {}

    with tracer.start_as_current_span(name) as span:
        # Set attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    span_kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Synchronous context manager for tracing operations.

    Args:
        operation_name: Name of the operation
        attributes: Optional attributes to add to the span
        span_kind: Kind of span (internal, server, client, etc.)

    Yields:
        The current span
    """
    tracer = get_tracer()
    attributes = attributes or {}

    with tracer.start_as_current_span(operation_name, kind=span_kind) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


@asynccontextmanager
async def trace_async_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    span_kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Async context manager for tracing operations.

    Args:
        operation_name: Name of the operation
        attributes: Optional attributes to add to the span
        span_kind: Kind of span (internal, server, client, etc.)

    Yields:
        The current span
    """
    tracer = get_tracer()
    attributes = attributes or {}

    with tracer.start_as_current_span(operation_name, kind=span_kind) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """
    Add attributes to the current span.

    Args:
        attributes: Dictionary of attributes to add
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add an event to the current span.

    Args:
        name: Name of the event
        attributes: Optional event attributes
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def record_exception(exception: Exception) -> None:
    """
    Record an exception on the current span.

    Args:
        exception: The exception to record
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.record_exception(exception)
        current_span.set_status(Status(StatusCode.ERROR, str(exception)))


def set_span_error(message: str) -> None:
    """
    Set the current span status to error.

    Args:
        message: Error message
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_status(Status(StatusCode.ERROR, message))

"""
Distributed tracing module for BSL Agent.

Provides OpenTelemetry instrumentation for BSL translation with span enrichment
for show-specific attributes like show.id, scene.number, gloss metrics, and avatar rendering.
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

# Jaeger exporter is optional
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
    logger.debug("Jaeger exporter not available, will use console exporter")


def setup_telemetry(
    service_name: str = "bsl-agent",
    jaeger_host: str = "jaeger.shared.svc.cluster.local",
    sample_rate: float = 0.1
) -> Optional[object]:
    """Set up OpenTelemetry tracing and metrics for BSL Agent.

    Args:
        service_name: Name of the service being instrumented (default: "bsl-agent")
        jaeger_host: Hostname of the Jaeger agent (default: jaeger.shared.svc.cluster.local)
        sample_rate: Fraction of traces to sample (default: 0.1 = 10%)

    Returns:
        Tracer instance for creating manual spans, or None if OpenTelemetry is not available

    Example:
        >>> tracer = setup_telemetry("bsl-agent")
        >>> with tracer.start_as_current_span("translate_text"):
        ...     # Your translation code here
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
        "service.component": "bsl-translation"
    })

    # Set up tracing provider
    provider = TracerProvider(resource=resource)

    # Configure sampling
    sampler = TraceIdRatioBased(sample_rate)
    provider.sampler = sampler

    # Add Jaeger exporter if available
    jaeger_enabled = JAEGER_AVAILABLE
    if JAEGER_AVAILABLE:
        try:
            provider.add_span_processor(
                BatchSpanProcessor(
                    JaegerExporter(
                        agent_host_name=jaeger_host,
                        agent_port=6831,
                    )
                )
            )
            logger.info(f"Jaeger exporter configured for {jaeger_host}:6831")
        except Exception as e:
            logger.warning(f"Jaeger exporter setup failed: {e}, using console exporter")
            jaeger_enabled = False
    else:
        logger.debug("Jaeger exporter not available, using console exporter")

    # Add console exporter for development or when Jaeger is unavailable
    if os.getenv("ENVIRONMENT") == "development" or not jaeger_enabled:
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
        >>> tracer = setup_telemetry("bsl-agent")
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
    Useful for enriching spans with BSL-specific context.

    Args:
        span: OpenTelemetry span instance (can be None)
        attributes: Dictionary of attributes to add

    Example:
        >>> from opentelemetry import trace
        >>> from tracing import add_span_attributes
        >>>
        >>> current_span = trace.get_current_span()
        >>> add_span_attributes(current_span, {
        ...     "show.id": "bards-tale-2024",
        ...     "translation.gloss_format": "singspell",
        ...     "translation.word_count": 10,
        ...     "translation.duration_estimate": 5.0
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
        ...     translate_text(...)
        ... except Exception as e:
        ...     record_error(current_span, e, {
        ...         "error.context": "translation",
        ...         "error.text_length": len(text)
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


def add_translation_span_attributes(
    span,
    show_id: str,
    text_length: int,
    gloss_word_count: Optional[int] = None,
    gloss_format: str = "singspell",
    confidence: Optional[float] = None,
    translation_time_ms: Optional[float] = None
) -> None:
    """Add BSL translation-specific attributes to a span.

    Convenience function for adding all standard translation attributes
    to a span in a single call.

    Args:
        span: OpenTelemetry span instance
        show_id: The show identifier
        text_length: Length of input text
        gloss_word_count: Optional number of words in gloss
        gloss_format: The gloss notation format used
        confidence: Optional confidence score
        translation_time_ms: Optional translation time in milliseconds

    Example:
        >>> from tracing import setup_telemetry, add_translation_span_attributes
        >>>
        >>> tracer = setup_telemetry("bsl-agent")
        >>> with tracer.start_as_current_span("translate_text") as span:
        ...     add_translation_span_attributes(
        ...         span,
        ...         show_id="bards-tale-2024",
        ...         text_length=50,
        ...         gloss_word_count=10,
        ...         gloss_format="singspell",
        ...         confidence=0.85,
        ...         translation_time_ms=150
        ...     )
    """
    attributes = {
        "show.id": show_id,
        "translation.text_length": text_length,
        "translation.gloss_format": gloss_format
    }

    # Add optional attributes
    if gloss_word_count is not None:
        attributes["translation.gloss_word_count"] = gloss_word_count

    if confidence is not None:
        attributes["translation.confidence"] = confidence

    if translation_time_ms is not None:
        attributes["translation.time_ms"] = translation_time_ms

    add_span_attributes(span, attributes)


__all__ = [
    "setup_telemetry",
    "instrument_fastapi",
    "add_span_attributes",
    "record_error",
    "add_translation_span_attributes",
    "OPENTELEMETRY_AVAILABLE",
    "JAEGER_AVAILABLE",
]

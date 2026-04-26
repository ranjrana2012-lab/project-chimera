"""
Distributed tracing module for Safety Filter.

Provides OpenTelemetry instrumentation for content moderation with span enrichment
for moderation-specific attributes.
"""

import os
import logging
from contextlib import contextmanager
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


class NoOpTracer:
    """Tracer-compatible fallback used when OpenTelemetry is not installed."""

    @contextmanager
    def start_as_current_span(self, *args, **kwargs):
        yield None


def setup_telemetry(
    service_name: str = "safety-filter",
    jaeger_host: str = "jaeger.shared.svc.cluster.local",
    sample_rate: float = 0.1
) -> Optional[object]:
    """Set up OpenTelemetry tracing and metrics for Safety Filter.

    Args:
        service_name: Name of the service being instrumented (default: "safety-filter")
        jaeger_host: Hostname of the Jaeger agent (default: jaeger.shared.svc.cluster.local)
        sample_rate: Fraction of traces to sample (default: 0.1 = 10%)

    Returns:
        Tracer instance for creating manual spans. Returns a no-op tracer if
        OpenTelemetry is not available so request handlers can keep running.
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not installed, using no-op tracer")
        return NoOpTracer()

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.component": "content-moderation"
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

    Args:
        app: FastAPI application instance
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

    Args:
        span: OpenTelemetry span instance (can be None)
        attributes: Dictionary of attributes to add
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

    Args:
        span: OpenTelemetry span instance (can be None)
        error: Exception to record
        attributes: Optional dictionary of error-related attributes
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


def add_moderation_span_attributes(
    span,
    is_safe: bool,
    action: str,
    policy: str,
    content_length: int,
    pattern_matches: Optional[int] = None,
    confidence: Optional[float] = None,
    processing_time_ms: Optional[float] = None
) -> None:
    """Add moderation-specific attributes to a span.

    Args:
        span: OpenTelemetry span instance
        is_safe: Whether content was deemed safe
        action: Action taken (allow, block, flag)
        policy: Moderation policy used
        content_length: Length of content moderated
        pattern_matches: Optional number of pattern matches
        confidence: Optional confidence score
        processing_time_ms: Optional processing time
    """
    attributes = {
        "moderation.is_safe": is_safe,
        "moderation.action": action,
        "moderation.policy": policy,
        "moderation.content_length": content_length,
    }

    # Add optional attributes
    if pattern_matches is not None:
        attributes["moderation.pattern_matches"] = pattern_matches

    if confidence is not None:
        attributes["moderation.confidence"] = confidence

    if processing_time_ms is not None:
        attributes["moderation.processing_time_ms"] = processing_time_ms

    add_span_attributes(span, attributes)


__all__ = [
    "setup_telemetry",
    "instrument_fastapi",
    "add_span_attributes",
    "record_error",
    "add_moderation_span_attributes",
    "OPENTELEMETRY_AVAILABLE",
    "JAEGER_AVAILABLE",
]

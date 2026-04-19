"""
Distributed tracing module for Lighting-Sound-Music Service.

Provides OpenTelemetry instrumentation for lighting, audio, and synchronization
operations with span enrichment for theatrical production attributes.
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
    service_name: str = "lighting-sound-music",
    jaeger_host: str = "jaeger.shared.svc.cluster.local",
    sample_rate: float = 0.1
) -> Optional[object]:
    """Set up OpenTelemetry tracing and metrics for Lighting-Sound-Music Service.

    Args:
        service_name: Name of the service being instrumented (default: "lighting-sound-music")
        jaeger_host: Hostname of the Jaeger agent (default: jaeger.shared.svc.cluster.local)
        sample_rate: Fraction of traces to sample (default: 0.1 = 10%)

    Returns:
        Tracer instance for creating manual spans, or None if OpenTelemetry is not available

    Example:
        >>> tracer = setup_telemetry("lighting-sound-music")
        >>> with tracer.start_as_current_span("set_lighting_scene"):
        ...     # Your lighting control code here
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
        "service.component": "lighting-audio-control"
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
        >>> tracer = setup_telemetry("lighting-sound-music")
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
    Useful for enriching spans with lighting-sound-music specific context.

    Args:
        span: OpenTelemetry span instance (can be None)
        attributes: Dictionary of attributes to add

    Example:
        >>> from opentelemetry import trace
        >>> from tracing import add_span_attributes
        >>>
        >>> current_span = trace.get_current_span()
        >>> add_span_attributes(current_span, {
        ...     "scene.id": "scene-1-intro",
        ...     "lighting.channels_count": 12,
        ...     "audio.cue_id": "intro-music",
        ...     "sync.offset_ms": 15
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
        ...     set_lighting_scene(...)
        ... except Exception as e:
        ...     record_error(current_span, e, {
        ...         "error.context": "lighting_control",
        ...         "error.scene_id": scene_id
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


def add_lighting_span_attributes(
    span,
    scene_id: str,
    channel_count: Optional[int] = None,
    fade_time_ms: Optional[int] = None,
    universe: Optional[int] = None
) -> None:
    """Add lighting-specific attributes to a span.

    Convenience function for adding all standard lighting control attributes
    to a span in a single call.

    Args:
        span: OpenTelemetry span instance
        scene_id: The scene identifier
        channel_count: Optional number of DMX channels
        fade_time_ms: Optional fade time in milliseconds
        universe: Optional DMX universe number

    Example:
        >>> from tracing import setup_telemetry, add_lighting_span_attributes
        >>>
        >>> tracer = setup_telemetry("lighting-sound-music")
        >>> with tracer.start_as_current_span("set_lighting_scene") as span:
        ...     add_lighting_span_attributes(
        ...         span,
        ...         scene_id="scene-1-intro",
        ...         channel_count=12,
        ...         fade_time_ms=2000,
        ...         universe=1
        ...     )
    """
    attributes = {
        "lighting.scene_id": scene_id
    }

    # Add optional attributes
    if channel_count is not None:
        attributes["lighting.channel_count"] = channel_count

    if fade_time_ms is not None:
        attributes["lighting.fade_time_ms"] = fade_time_ms

    if universe is not None:
        attributes["lighting.universe"] = universe

    add_span_attributes(span, attributes)


def add_audio_span_attributes(
    span,
    cue_id: str,
    file_path: Optional[str] = None,
    volume: Optional[float] = None,
    loop: Optional[bool] = None
) -> None:
    """Add audio-specific attributes to a span.

    Convenience function for adding all standard audio control attributes
    to a span in a single call.

    Args:
        span: OpenTelemetry span instance
        cue_id: The cue identifier
        file_path: Optional audio file path
        volume: Optional volume level
        loop: Optional loop flag

    Example:
        >>> from tracing import setup_telemetry, add_audio_span_attributes
        >>>
        >>> tracer = setup_telemetry("lighting-sound-music")
        >>> with tracer.start_as_current_span("play_audio_cue") as span:
        ...     add_audio_span_attributes(
        ...         span,
        ...         cue_id="intro-music",
        ...         file_path="/audio/intro.mp3",
        ...         volume=0.8,
        ...         loop=False
        ...     )
    """
    attributes = {
        "audio.cue_id": cue_id
    }

    # Add optional attributes
    if file_path is not None:
        attributes["audio.file_path"] = file_path

    if volume is not None:
        attributes["audio.volume"] = volume

    if loop is not None:
        attributes["audio.loop"] = loop

    add_span_attributes(span, attributes)


def add_sync_span_attributes(
    span,
    scene_id: str,
    lighting_triggered_at: float,
    audio_triggered_at: float,
    sync_offset_ms: float,
    within_tolerance: bool
) -> None:
    """Add sync-specific attributes to a span.

    Convenience function for adding all standard synchronization attributes
    to a span in a single call.

    Args:
        span: OpenTelemetry span instance
        scene_id: The scene identifier
        lighting_triggered_at: Timestamp when lighting was triggered
        audio_triggered_at: Timestamp when audio was triggered
        sync_offset_ms: Synchronization offset in milliseconds
        within_tolerance: Whether sync was within tolerance

    Example:
        >>> from tracing import setup_telemetry, add_sync_span_attributes
        >>>
        >>> tracer = setup_telemetry("lighting-sound-music")
        >>> with tracer.start_as_current_span("trigger_sync_scene") as span:
        ...     add_sync_span_attributes(
        ...         span,
        ...         scene_id="scene-1-sync",
        ...         lighting_triggered_at=1234567890.123,
        ...         audio_triggered_at=1234567890.138,
        ...         sync_offset_ms=15.0,
        ...         within_tolerance=True
        ...     )
    """
    attributes = {
        "sync.scene_id": scene_id,
        "sync.lighting_triggered_at": lighting_triggered_at,
        "sync.audio_triggered_at": audio_triggered_at,
        "sync.offset_ms": sync_offset_ms,
        "sync.within_tolerance": within_tolerance
    }

    add_span_attributes(span, attributes)


__all__ = [
    "setup_telemetry",
    "instrument_fastapi",
    "add_span_attributes",
    "record_error",
    "add_lighting_span_attributes",
    "add_audio_span_attributes",
    "add_sync_span_attributes",
    "OPENTELEMETRY_AVAILABLE",
    "JAEGER_AVAILABLE",
]

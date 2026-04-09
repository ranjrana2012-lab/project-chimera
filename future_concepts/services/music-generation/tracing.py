"""
Music Generation Service - OpenTelemetry Tracing Module
Project Chimera v0.5.0

This module configures OpenTelemetry tracing for the music generation service,
including automatic instrumentation for FastAPI and custom span creation.

Falls back gracefully if OpenTelemetry packages are not installed.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.propagate import inject
    from opentelemetry.context import Context
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)

# No-op context manager for when tracing is disabled
@contextmanager
def nullcontext():
    """A no-op context manager for when tracing is disabled."""
    yield None

# Global tracer instance
_tracer = None
_provider = None


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
    service_name: str = "music-generation",
    service_version: str = "0.5.0",
    otlp_endpoint: str = "http://localhost:4317",
    environment: str = "development",
    enable_console_export: bool = False
):
    """
    Set up OpenTelemetry tracing for the service.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint
        environment: Environment (development, staging, production)
        enable_console_export: Enable console span exporter for debugging

    Returns:
        Configured tracer instance or no-op tracer if OTEL unavailable
    """
    global _tracer, _provider

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, returning no-op tracer")
        return NoOpTracer()

    try:
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": environment,
            "service.namespace": "project-chimera",
        })

        # Set up trace provider
        _provider = TracerProvider(resource=resource)

        # Add OTLP exporter
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=True
            )
            _provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP tracing enabled: {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to initialize OTLP exporter: {e}")
            if enable_console_export:
                console_exporter = ConsoleSpanExporter()
                _provider.add_span_processor(BatchSpanProcessor(console_exporter))
                logger.info("Using console span exporter")

        # Set as global default provider
        trace.set_tracer_provider(_provider)

        # Create tracer
        _tracer = trace.get_tracer(__name__)

        logger.info("OpenTelemetry tracing initialized successfully")
        return _tracer

    except Exception as e:
        logger.error(f"Failed to set up tracing: {e}")
        return NoOpTracer()


def instrument_fastapi(app):
    """
    Instrument FastAPI application with automatic tracing.

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
def trace_model_loading(model_name: str):
    """
    Context manager for tracing model loading operations.

    Args:
        model_name: Name of the model being loaded

    Yields:
        Span object or no-op context
    """
    if not OTEL_AVAILABLE:
        yield nullcontext()
        return

    tracer = get_tracer()
    with tracer.start_as_current_span(f"model.load.{model_name}") as span:
        if span:
            span.set_attribute("model.name", model_name)
            span.set_attribute("model.action", "load")
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


def record_error(span, error: Exception) -> None:
    """
    Record an exception on a span.

    Args:
        span: Span object
        error: Exception to record
    """
    if not OTEL_AVAILABLE or span is None:
        return

    try:
        span.record_exception(error)
    except Exception as e:
        logger.warning(f"Failed to record exception: {e}")

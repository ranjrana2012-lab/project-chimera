"""
Music Generation Service - OpenTelemetry Tracing Module
Project Chimera v0.5.0

This module configures OpenTelemetry tracing for the music generation service,
including automatic instrumentation for FastAPI and custom span creation.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time

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

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_provider: Optional[TracerProvider] = None


def setup_tracing(
    service_name: str = "music-generation",
    service_version: str = "0.5.0",
    otlp_endpoint: str = "http://localhost:4317",
    environment: str = "development",
    enable_console_export: bool = False
) -> trace.Tracer:
    """
    Set up OpenTelemetry tracing for the service.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint
        environment: Environment (development, staging, production)
        enable_console_export: Enable console span exporter for debugging

    Returns:
        Configured tracer instance
    """
    global _tracer, _provider

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
        # Return a no-op tracer if setup fails
        _tracer = trace.get_tracer(__name__)
        return _tracer


def instrument_fastapi(app):
    """
    Instrument FastAPI application with automatic tracing.

    Args:
        app: FastAPI application instance
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")


def instrument_httpx():
    """
    Instrument HTTPX client for outgoing request tracing.
    """
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")


def get_tracer() -> Optional[trace.Tracer]:
    """
    Get the global tracer instance.

    Returns:
        Tracer instance or None if not initialized
    """
    return _tracer


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing custom operations.

    Args:
        operation_name: Name of the operation to trace
        attributes: Additional attributes to add to the span

    Yields:
        The current span for adding attributes and events
    """
    if _tracer is None:
        logger.warning("Tracer not initialized, operation not traced")
        yield None
        return

    span = _tracer.start_span(operation_name)
    try:
        # Set initial attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        span.set_attribute("operation.type", "custom")

        yield span

    except Exception as e:
        # Record exception in span
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        raise
    finally:
        span.end()


def add_span_attributes(attributes: Dict[str, Any]):
    """
    Add attributes to the current span.

    Args:
        attributes: Dictionary of attributes to add
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Add an event to the current span.

    Args:
        name: Event name
        attributes: Event attributes
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def set_span_error(exception: Exception):
    """
    Set error status on the current span.

    Args:
        exception: The exception to record
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.record_exception(exception)
        current_span.set_status(
            Status(StatusCode.ERROR, str(exception))
        )


class TracedOperation:
    """
    Decorator class for tracing function calls.
    """

    def __init__(self, operation_name: str = None, **attributes):
        """
        Initialize the decorator.

        Args:
            operation_name: Name for the operation (defaults to function name)
            **attributes: Additional span attributes
        """
        self.operation_name = operation_name
        self.attributes = attributes

    def __call__(self, func):
        """Decorator implementation."""

        def wrapper(*args, **kwargs):
            if _tracer is None:
                return func(*args, **kwargs)

            op_name = self.operation_name or func.__name__

            with trace_operation(op_name, self.attributes) as span:
                if span:
                    # Add function-specific attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    # Add parameter info (be careful with sensitive data)
                    span.set_attribute("function.args.count", len(args))
                    span.set_attribute("function.kwargs.keys", list(kwargs.keys()))

                return func(*args, **kwargs)

        return wrapper


def inject_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into headers for outgoing requests.

    Args:
        headers: Existing headers dictionary

    Returns:
        Headers dictionary with trace context added
    """
    if headers is None:
        headers = {}

    inject(headers)
    return headers


@contextmanager
def trace_model_loading(model_name: str, model_path: str):
    """
    Context manager for tracing model loading operations.

    Args:
        model_name: Name of the model being loaded
        model_path: Path to the model

    Yields:
        The current span
    """
    attributes = {
        "model.name": model_name,
        "model.path": model_path,
        "operation.type": "model_load"
    }

    with trace_operation("model.load", attributes) as span:
        if span:
            add_span_event("model.load.start", {
                "model.name": model_name,
                "model.path": model_path
            })

            start_time = time.time()
            yield span

            duration = time.time() - start_time
            span.set_attribute("model.load.duration_seconds", duration)
            add_span_event("model.load.complete", {
                "duration_seconds": duration
            })
        else:
            yield span


@contextmanager
def trace_generation(
    model_name: str,
    prompt: str,
    duration: float,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing music generation operations.

    Args:
        model_name: Name of the model being used
        prompt: Generation prompt (truncated for privacy)
        duration: Expected audio duration
        parameters: Additional generation parameters

    Yields:
        The current span
    """
    # Sanitize prompt for tracing (remove potentially sensitive content)
    safe_prompt = prompt[:100] if prompt else ""
    if len(prompt) > 100:
        safe_prompt += "..."

    attributes = {
        "model.name": model_name,
        "generation.prompt_length": len(prompt) if prompt else 0,
        "generation.duration_seconds": duration,
        "operation.type": "generation"
    }

    if parameters:
        for key, value in parameters.items():
            if key not in ["prompt", "text"]:  # Skip potentially sensitive fields
                attributes[f"generation.param.{key}"] = str(value)

    with trace_operation("generation.execute", attributes) as span:
        if span:
            add_span_event("generation.start", {
                "model": model_name,
                "duration": duration
            })

            start_time = time.time()
            yield span

            generation_time = time.time() - start_time
            span.set_attribute("generation.time_seconds", generation_time)
            span.set_attribute("generation.ratio", generation_time / duration if duration > 0 else 0)
            add_span_event("generation.complete", {
                "duration_seconds": generation_time
            })
        else:
            yield span


def shutdown_tracing():
    """
    Shutdown the tracing provider and flush remaining spans.
    """
    global _provider, _tracer

    if _provider:
        try:
            _provider.shutdown()
            logger.info("Tracing provider shutdown successfully")
        except Exception as e:
            logger.error(f"Error during tracing shutdown: {e}")
        finally:
            _provider = None
            _tracer = None

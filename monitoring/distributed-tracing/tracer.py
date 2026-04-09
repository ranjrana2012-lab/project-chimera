#!/usr/bin/env python3
"""
Project Chimera Phase 2 - Distributed Tracing Integration

This module provides distributed tracing instrumentation for Phase 2 services
using OpenTelemetry and Jaeger for end-to-end request tracking and observability.

Usage:
    python -m monitoring.distributed_tracing.tracer
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.semconv.trace import SpanKind


class TracingConfig:
    """Configuration for distributed tracing."""

    # Jaeger endpoint
    JAEGER_AGENT_HOST = "localhost"
    JAEGER_AGENT_PORT = 6831

    # Service names
    DMX_SERVICE = "dmx-controller"
    AUDIO_SERVICE = "audio-controller"
    BSL_SERVICE = "bsl-avatar-service"

    # Sampling
    TRACE_SAMPLE_RATE = 1.0  # 100% sampling for now


class ChimeraTracer:
    """
    Distributed tracer for Project Chimera services.

    Provides automatic tracing for HTTP requests and manual tracing
    for custom operations.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = None
        self.instrumentor = None

        self._setup_tracing()

    def _setup_tracing(self):
        """Set up distributed tracing."""
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=TracingConfig.JAEGER_AGENT_HOST,
            agent_port=TracingConfig.JAEGER_AGENT_PORT,
        )

        # Configure span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)

        # Configure tracer provider
        provider = TracerProvider(
            resource=SERVICE_NAME,
            span_processor=span_processor,
        )

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Create tracer
        self.tracer = trace.get_tracer(
            __name__,
            service_name=self.service_name,
        )

    def trace_request(self, operation_name: str):
        """
        Decorator to trace HTTP requests.

        Usage:
            @tracer.trace_request("get_fixture")
            def get_fixture(fixture_id: str):
                return fixture_data
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(
                    operation_name,
                    kind=SpanKind.SERVER,
                    attributes={
                        "service": self.service_name,
                        "operation": operation_name,
                    }
                ) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_status("ok")
                        return result
                    except Exception as e:
                        span.set_status("error", str(e))
                        span.record_exception(e)
                        raise
            return wrapper
        return decorator

    def trace_operation(self, operation_name: str):
        """
        Context manager for tracing custom operations.

        Usage:
            with tracer.trace_operation("calculate_scene"):
                # Do work
                pass
        """
        class TracingContext:
            def __enter__(self):
                self.span = self.tracer.start_as_current_span(
                    operation_name,
                    kind=SpanKind.INTERNAL,
                    attributes={
                        "service": self.service_name,
                        "operation": operation_name,
                    }
                )
                return self.span

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    self.span.set_status("error", str(exc_val))
                    self.span.record_exception(exc_val)
                self.span.end()
                return False

        return TracingContext()

    def add_span_attributes(self, attributes: Dict[str, Any]):
        """Add attributes to the current span."""
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attributes(attributes)

    def add_span_event(self, name: str, attributes: Dict[str, Any]):
        """Add an event to the current span."""
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes=attributes)


class MetricsCollector:
    """
    Custom metrics collector for Phase 2 services.

    Provides business-specific metrics beyond standard Prometheus metrics.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._setup_metrics()

    def _setup_metrics(self):
        """Set up custom metrics."""
        # Custom metrics would be configured here
        # This is a placeholder for the pattern
        pass

    def record_adaptive_decision(
        self,
        sentiment_before: float,
        sentiment_after: float,
        decision: str,
        context: Dict[str, Any]
    ):
        """Record an adaptive decision for analysis."""
        # Implementation would record metrics like:
        # - chimera_adaptive_decisions_total
        # - chimera_adaptive_decision_sentiment_change
        # - chimera_adaptive_decision_context
        pass

    def record_scene_activation(
        self,
        scene_name: str,
        transition_time_ms: int,
        fixtures_affected: int,
        success: bool
    ):
        """Record a scene activation for analysis."""
        # Implementation would record metrics like:
        # - chimera_scene_activation_total
        # - chimera_scene_transition_duration_seconds
        # - chimera_scene_fixtures_affected
        pass

    def record_translation_performance(
        self,
        text_length: int,
        gestures_used: int,
        fingerspelled: int,
        library_hit_rate: float,
        render_time_ms: int
    ):
        """Record BSL translation performance."""
        # Implementation would record metrics like:
        # - chimera_translation_text_length
        # - chimera_translation_gestures_used
        # # chimera_translation_library_hit_rate
        # # chimera_translation_render_duration_seconds
        pass


class InstrumentedFastAPI:
    """
    FastAPI app with automatic tracing instrumentation.

    Usage:
        app = InstrumentedFastAPI(__name__)
        @app.get("/")
        async def root():
            return {"message": "Hello"}
    """

    def __init__(self, name: str):
        self.app = FastAPI(title=name)
        self._setup_instrumentation()

    def _setup_instrumentation(self):
        """Set up automatic tracing for FastAPI."""
        # Instrument FastAPI automatically
        self.instrumentor = FastAPIInstrumentor.instrument_app(self.app)

    def get_app(self):
        """Get the instrumented FastAPI app."""
        return self.instrumentor


# Service-specific tracer instances
_dmx_tracer = None
_audio_tracer = None
_bsl_tracer = None


def get_dmx_tracer() -> ChimeraTracer:
    """Get or create DMX controller tracer."""
    global _dmx_tracer
    if _dmx_tracer is None:
        _dmx_tracer = ChimeraTracer(TracingConfig.DMX_SERVICE)
    return _dmx_tracer


def get_audio_tracer() -> ChimeraTracer:
    """Get or create Audio controller tracer."""
    global _audio_tracer
    if _audio_tracer is None:
        _audio_tracer = ChimeraTracer(TracingConfig.AUDIO_SERVICE)
    return _audio_tracer


def get_bsl_tracer() -> ChimeraTracer:
    """Get or create BSL avatar service tracer."""
    global _bsl_tracer
    if _bsl_tracer is None:
        _bsl_tracer = ChimeraTracer(TracingConfig.BSL_SERVICE)
    return _bsl_tracer


# Convenience functions
def trace_service_operation(service: str, operation: str):
    """
    Decorator to trace service operations.

    Usage:
        @trace_service_operation("dmx", "activate_scene")
        def activate_scene(scene_name: str):
            return scene_data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = None

            if service == "dmx":
                tracer = get_dmx_tracer()
            elif service == "audio":
                tracer = get_audio_tracer()
            elif service == "bsl":
                tracer = get_bsl_tracer()
            else:
                return func(*args, **kwargs)

            with tracer.trace_operation(operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize tracing for a service
    tracer = ChimeraTracer(TracingConfig.DMX_SERVICE)

    # Use trace decorator
    @tracer.trace_request("get_fixtures")
    def get_fixtures():
        return [{"id": "mh_1", "name": "Moving Head 1"}]

    # Use trace context manager
    with tracer.trace_operation("calculate_scene"):
        time.sleep(0.1)  # Simulate work

    print("Tracing example complete")

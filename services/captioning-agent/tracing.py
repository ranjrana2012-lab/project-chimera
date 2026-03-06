# tracing.py
"""OpenTelemetry tracing setup for Captioning Agent"""
import logging

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry, but provide stubs if not available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available, tracing will be disabled")


def setup_telemetry(service_name: str, otlp_endpoint: str = "http://localhost:4317"):
    """Set up OpenTelemetry tracing for the captioning agent"""
    if not OTEL_AVAILABLE:
        logger.warning(f"OpenTelemetry not available, skipping telemetry setup for {service_name}")
        return None

    # Create resource with service name
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "project-chimera",
        "service.component": "captioning"
    })

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Set up OTLP exporter (for Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True
    )

    # Add exporter to provider
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(f"Telemetry initialized for {service_name}")

    return trace.get_tracer(__name__)


def instrument_fastapi(app, service_name: str):
    """Instrument FastAPI app with automatic tracing"""
    if not OTEL_AVAILABLE:
        logger.warning(f"OpenTelemetry not available, skipping instrumentation for {service_name}")
        return

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
    logger.info(f"FastAPI instrumented for {service_name}")


def add_span_attributes(attributes: dict):
    """Add custom attributes to current span"""
    if not OTEL_AVAILABLE:
        return

    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def record_error(exception: Exception):
    """Record exception in current span"""
    if not OTEL_AVAILABLE:
        return

    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception)

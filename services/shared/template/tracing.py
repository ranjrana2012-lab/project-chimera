# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)


def setup_telemetry(service_name: str) -> trace.Tracer:
    """Set up OpenTelemetry tracing for the service"""

    # Create resource with service name
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "project-chimera"
    })

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Set up OTLP exporter (for Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
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
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
    logger.info(f"FastAPI instrumented for {service_name}")


def add_span_attributes(attributes: dict):
    """Add custom attributes to current span"""
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def record_error(exception: Exception):
    """Record exception in current span"""
    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception)

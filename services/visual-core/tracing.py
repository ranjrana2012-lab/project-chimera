"""Visual Core Tracing.

OpenTelemetry distributed tracing setup for the visual core service.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import logging

logger = logging.getLogger(__name__)


def setup_tracing(
    service_name: str,
    service_version: str,
    otlp_endpoint: str,
    environment: str = "development"
) -> trace.Tracer:
    """
    Set up OpenTelemetry distributed tracing.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP endpoint (e.g., http://localhost:4317)
        environment: Deployment environment

    Returns:
        Configured tracer
    """
    try:
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": environment,
            "service.type": "visual-core"
        })

        # Set up tracer provider
        provider = TracerProvider(resource=resource)

        # Set up OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True
        )

        # Add batch span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        tracer = trace.get_tracer(__name__)

        logger.info(f"Tracing initialized for {service_name} v{service_version}")
        return tracer

    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")
        # Return a no-op tracer
        return trace.get_tracer(__name__)


def instrument_fastapi(app):
    """
    Instrument FastAPI app with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")


def instrument_httpx():
    """Instrument HTTPX for HTTP client tracing."""
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")


def get_tracer():
    """Get the global tracer instance."""
    return trace.get_tracer(__name__)


def shutdown_tracing():
    """Shutdown tracing provider."""
    try:
        trace.get_tracer_provider().shutdown()
        logger.info("Tracing shutdown complete")
    except Exception as e:
        logger.warning(f"Error during tracing shutdown: {e}")

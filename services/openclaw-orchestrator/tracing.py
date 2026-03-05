from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)

# Try to import OTLP exporter, fall back to console if not available
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    logger.warning("OTLP exporter not available, falling back to console exporter")
    OTLP_AVAILABLE = False

def setup_telemetry(service_name: str, otlp_endpoint: str = "http://localhost:4317") -> trace.Tracer:
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "project-chimera"
    })

    provider = TracerProvider(resource=resource)

    if OTLP_AVAILABLE:
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True
        )
        processor = BatchSpanProcessor(otlp_exporter)
        logger.info(f"Telemetry initialized with OTLP exporter for {service_name}")
    else:
        # Fall back to console exporter
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        logger.info(f"Telemetry initialized with console exporter for {service_name}")

    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    return trace.get_tracer(__name__)

def instrument_fastapi(app, service_name: str):
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
        logger.info(f"FastAPI instrumented for {service_name}")
    except ImportError:
        logger.warning("FastAPI instrumentation not available")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)

def setup_telemetry(service_name: str) -> trace.Tracer:
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "project-chimera"
    })

    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )

    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    logger.info(f"Telemetry initialized for {service_name}")
    return trace.get_tracer(__name__)

def instrument_fastapi(app, service_name: str):
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
    logger.info(f"FastAPI instrumented for {service_name}")

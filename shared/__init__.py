# shared/__init__.py
"""Project Chimera shared utilities and models."""

from shared.tracing import (
    setup_tracing,
    instrument_fastapi,
    get_tracer,
    shutdown_tracing,
    trace_operation,
    add_span_attributes,
    record_error,
    add_span_event,
    inject_context,
    SpanAttributes,
    create_service_attributes,
    create_operation_attributes,
)

from shared.trace_exporter import (
    TraceExporter,
    TraceAnalyzer,
    LatencyValidator,
    SpanMetrics,
    PerformanceReport,
    calculate_percentiles,
    format_duration_ms,
)

__all__ = [
    # Tracing
    "setup_tracing",
    "instrument_fastapi",
    "get_tracer",
    "shutdown_tracing",
    "trace_operation",
    "add_span_attributes",
    "record_error",
    "add_span_event",
    "inject_context",
    "SpanAttributes",
    "create_service_attributes",
    "create_operation_attributes",
    # Trace Exporter
    "TraceExporter",
    "TraceAnalyzer",
    "LatencyValidator",
    "SpanMetrics",
    "PerformanceReport",
    "calculate_percentiles",
    "format_duration_ms",
]

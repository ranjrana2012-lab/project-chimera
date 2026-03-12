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

from shared.resilience import (
    retry_on_exception,
    retry_on_condition,
    async_retry_on_exception,
    RetryConfig,
    RetryStrategy,
    RetryTracker,
    RETRY_CONFIGS,
)

from shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerRegistry,
    with_circuit_breaker,
    get_circuit_breaker,
    get_all_circuit_breaker_stats,
    CIRCUIT_CONFIGS,
)

from shared.degradation import (
    DegradationLevel,
    DegradationState,
    DegradationManager,
    ServiceCapability,
    ServiceHealthMonitor,
    with_degradation_fallback,
    get_degradation_manager,
    get_all_degradation_stats,
    DEGRADATION_PRESETS,
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
    # Resilience
    "retry_on_exception",
    "retry_on_condition",
    "async_retry_on_exception",
    "RetryConfig",
    "RetryStrategy",
    "RetryTracker",
    "RETRY_CONFIGS",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitBreakerRegistry",
    "with_circuit_breaker",
    "get_circuit_breaker",
    "get_all_circuit_breaker_stats",
    "CIRCUIT_CONFIGS",
    # Degradation
    "DegradationLevel",
    "DegradationState",
    "DegradationManager",
    "ServiceCapability",
    "ServiceHealthMonitor",
    "with_degradation_fallback",
    "get_degradation_manager",
    "get_all_degradation_stats",
    "DEGRADATION_PRESETS",
]

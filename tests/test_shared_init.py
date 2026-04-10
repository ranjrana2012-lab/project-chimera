"""
Tests for shared/__init__.py module exports.

Tests that all expected exports are accessible from the shared module.
"""

import pytest
import sys
from pathlib import Path

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Import from the shared module (not submodules directly)
from shared import (
    # Tracing
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
    # Trace Exporter
    TraceExporter,
    TraceAnalyzer,
    LatencyValidator,
    SpanMetrics,
    PerformanceReport,
    calculate_percentiles,
    format_duration_ms,
    # Resilience
    retry_on_exception,
    retry_on_condition,
    async_retry_on_exception,
    RetryConfig,
    RetryStrategy,
    RetryTracker,
    RETRY_CONFIGS,
    # Circuit Breaker
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerRegistry,
    with_circuit_breaker,
    get_circuit_breaker,
    get_all_circuit_breaker_stats,
    CIRCUIT_CONFIGS,
    # Degradation
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


class TestTracingExports:
    """Tests for tracing module exports."""

    def test_setup_tracing_exported(self):
        """Verify setup_tracing is exported."""
        assert setup_tracing is not None
        assert callable(setup_tracing)

    def test_instrument_fastapi_exported(self):
        """Verify instrument_fastapi is exported."""
        assert instrument_fastapi is not None
        assert callable(instrument_fastapi)

    def test_get_tracer_exported(self):
        """Verify get_tracer is exported."""
        assert get_tracer is not None
        assert callable(get_tracer)

    def test_shutdown_tracing_exported(self):
        """Verify shutdown_tracing is exported."""
        assert shutdown_tracing is not None
        assert callable(shutdown_tracing)

    def test_trace_operation_exported(self):
        """Verify trace_operation is exported."""
        assert trace_operation is not None
        assert callable(trace_operation)

    def test_add_span_attributes_exported(self):
        """Verify add_span_attributes is exported."""
        assert add_span_attributes is not None
        assert callable(add_span_attributes)

    def test_record_error_exported(self):
        """Verify record_error is exported."""
        assert record_error is not None
        assert callable(record_error)

    def test_add_span_event_exported(self):
        """Verify add_span_event is exported."""
        assert add_span_event is not None
        assert callable(add_span_event)

    def test_inject_context_exported(self):
        """Verify inject_context is exported."""
        assert inject_context is not None
        assert callable(inject_context)

    def test_SpanAttributes_exported(self):
        """Verify SpanAttributes class is exported."""
        assert SpanAttributes is not None

    def test_create_service_attributes_exported(self):
        """Verify create_service_attributes is exported."""
        assert create_service_attributes is not None
        assert callable(create_service_attributes)

    def test_create_operation_attributes_exported(self):
        """Verify create_operation_attributes is exported."""
        assert create_operation_attributes is not None
        assert callable(create_operation_attributes)


class TestTraceExporterExports:
    """Tests for trace_exporter module exports."""

    def test_TraceExporter_exported(self):
        """Verify TraceExporter class is exported."""
        assert TraceExporter is not None

    def test_TraceAnalyzer_exported(self):
        """Verify TraceAnalyzer class is exported."""
        assert TraceAnalyzer is not None

    def test_LatencyValidator_exported(self):
        """Verify LatencyValidator class is exported."""
        assert LatencyValidator is not None

    def test_SpanMetrics_exported(self):
        """Verify SpanMetrics class is exported."""
        assert SpanMetrics is not None

    def test_PerformanceReport_exported(self):
        """Verify PerformanceReport class is exported."""
        assert PerformanceReport is not None

    def test_calculate_percentiles_exported(self):
        """Verify calculate_percentiles is exported."""
        assert calculate_percentiles is not None
        assert callable(calculate_percentiles)

    def test_format_duration_ms_exported(self):
        """Verify format_duration_ms is exported."""
        assert format_duration_ms is not None
        assert callable(format_duration_ms)


class TestResilienceExports:
    """Tests for resilience module exports."""

    def test_retry_on_exception_exported(self):
        """Verify retry_on_exception is exported."""
        assert retry_on_exception is not None
        assert callable(retry_on_exception)

    def test_retry_on_condition_exported(self):
        """Verify retry_on_condition is exported."""
        assert retry_on_condition is not None
        assert callable(retry_on_condition)

    def test_async_retry_on_exception_exported(self):
        """Verify async_retry_on_exception is exported."""
        assert async_retry_on_exception is not None
        assert callable(async_retry_on_exception)

    def test_RetryConfig_exported(self):
        """Verify RetryConfig class is exported."""
        assert RetryConfig is not None

    def test_RetryStrategy_exported(self):
        """Verify RetryStrategy enum is exported."""
        assert RetryStrategy is not None

    def test_RetryTracker_exported(self):
        """Verify RetryTracker class is exported."""
        assert RetryTracker is not None

    def test_RETRY_CONFIGS_exported(self):
        """Verify RETRY_CONFIGS dict is exported."""
        assert RETRY_CONFIGS is not None
        assert isinstance(RETRY_CONFIGS, dict)


class TestCircuitBreakerExports:
    """Tests for circuit_breaker module exports."""

    def test_CircuitBreaker_exported(self):
        """Verify CircuitBreaker class is exported."""
        assert CircuitBreaker is not None

    def test_CircuitBreakerError_exported(self):
        """Verify CircuitBreakerError class is exported."""
        assert CircuitBreakerError is not None

    def test_CircuitBreakerConfig_exported(self):
        """Verify CircuitBreakerConfig class is exported."""
        assert CircuitBreakerConfig is not None

    def test_CircuitState_exported(self):
        """Verify CircuitState enum is exported."""
        assert CircuitState is not None

    def test_CircuitBreakerRegistry_exported(self):
        """Verify CircuitBreakerRegistry class is exported."""
        assert CircuitBreakerRegistry is not None

    def test_with_circuit_breaker_exported(self):
        """Verify with_circuit_breaker is exported."""
        assert with_circuit_breaker is not None
        assert callable(with_circuit_breaker)

    def test_get_circuit_breaker_exported(self):
        """Verify get_circuit_breaker is exported."""
        assert get_circuit_breaker is not None
        assert callable(get_circuit_breaker)

    def test_get_all_circuit_breaker_stats_exported(self):
        """Verify get_all_circuit_breaker_stats is exported."""
        assert get_all_circuit_breaker_stats is not None
        assert callable(get_all_circuit_breaker_stats)

    def test_CIRCUIT_CONFIGS_exported(self):
        """Verify CIRCUIT_CONFIGS dict is exported."""
        assert CIRCUIT_CONFIGS is not None
        assert isinstance(CIRCUIT_CONFIGS, dict)


class TestDegradationExports:
    """Tests for degradation module exports."""

    def test_DegradationLevel_exported(self):
        """Verify DegradationLevel enum is exported."""
        assert DegradationLevel is not None

    def test_DegradationState_exported(self):
        """Verify DegradationState class is exported."""
        assert DegradationState is not None

    def test_DegradationManager_exported(self):
        """Verify DegradationManager class is exported."""
        assert DegradationManager is not None

    def test_ServiceCapability_exported(self):
        """Verify ServiceCapability enum is exported."""
        assert ServiceCapability is not None

    def test_ServiceHealthMonitor_exported(self):
        """Verify ServiceHealthMonitor class is exported."""
        assert ServiceHealthMonitor is not None

    def test_with_degradation_fallback_exported(self):
        """Verify with_degradation_fallback is exported."""
        assert with_degradation_fallback is not None
        assert callable(with_degradation_fallback)

    def test_get_degradation_manager_exported(self):
        """Verify get_degradation_manager is exported."""
        assert get_degradation_manager is not None
        assert callable(get_degradation_manager)

    def test_get_all_degradation_stats_exported(self):
        """Verify get_all_degradation_stats is exported."""
        assert get_all_degradation_stats is not None
        assert callable(get_all_degradation_stats)

    def test_DEGRADATION_PRESETS_exported(self):
        """Verify DEGRADATION_PRESETS dict is exported."""
        assert DEGRADATION_PRESETS is not None
        assert isinstance(DEGRADATION_PRESETS, dict)


class TestModuleAll:
    """Tests for __all__ export list."""

    def test_all_exports_exist(self):
        """Verify all items in __all__ can be imported."""
        import shared

        for name in shared.__all__:
            assert hasattr(shared, name), f"{name} is in __all__ but not exported"

    def test_all_count(self):
        """Verify __all__ contains expected number of exports."""
        import shared

        # Count the actual exports
        assert len(shared.__all__) == 44

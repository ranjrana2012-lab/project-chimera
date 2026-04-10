"""Tests for shared module imports."""
import pytest


class TestSharedImports:
    """Tests that all shared module exports are accessible."""

    def test_import_tracing_exports(self):
        """Test tracing exports are accessible."""
        from shared import (
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
        # Verify they're callable
        assert callable(setup_tracing)
        assert callable(instrument_fastapi)
        assert callable(get_tracer)

    def test_import_trace_exporter_exports(self):
        """Test trace exporter exports are accessible."""
        from shared import (
            TraceExporter,
            TraceAnalyzer,
            LatencyValidator,
            SpanMetrics,
            PerformanceReport,
            calculate_percentiles,
            format_duration_ms,
        )
        # Verify they're classes or callable
        assert callable(TraceExporter)
        assert callable(calculate_percentiles)

    def test_import_resilience_exports(self):
        """Test resilience exports are accessible."""
        from shared import (
            retry_on_exception,
            retry_on_condition,
            async_retry_on_exception,
            RetryConfig,
            RetryStrategy,
            RetryTracker,
            RETRY_CONFIGS,
        )
        # Verify they're callable
        assert callable(retry_on_exception)
        assert callable(retry_on_condition)
        assert callable(async_retry_on_exception)
        assert isinstance(RETRY_CONFIGS, dict)

    def test_import_circuit_breaker_exports(self):
        """Test circuit breaker exports are accessible."""
        from shared import (
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
        # Verify they're callable or classes
        assert callable(CircuitBreaker)
        assert callable(with_circuit_breaker)
        assert isinstance(CIRCUIT_CONFIGS, dict)

    def test_import_degradation_exports(self):
        """Test degradation exports are accessible."""
        from shared import (
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
        # Verify they're callable or enums
        assert callable(get_degradation_manager)
        assert callable(get_all_degradation_stats)
        assert isinstance(DEGRADATION_PRESETS, dict)

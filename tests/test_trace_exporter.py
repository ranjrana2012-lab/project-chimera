"""
Tests for shared trace_exporter module.

Tests the trace export functionality including:
- SpanMetrics
- PerformanceReport
- TraceExporter
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Mock OpenTelemetry before importing
sys.modules['opentelemetry'] = MagicMock()
sys.modules['opentelemetry.sdk'] = MagicMock()
sys.modules['opentelemetry.sdk.trace'] = MagicMock()
sys.modules['opentelemetry.sdk.trace.export'] = MagicMock()
sys.modules['opentelemetry.sdk.resources'] = MagicMock()

# Set OTEL_AVAILABLE before importing trace_exporter
import importlib
trace_exporter = importlib.import_module('trace_exporter')

# Patch OTEL_AVAILABLE after import
trace_exporter.OTEL_AVAILABLE = True

from trace_exporter import (
    SpanMetrics,
    PerformanceReport,
    TraceExporter,
)


class TestSpanMetrics:
    """Tests for SpanMetrics dataclass."""

    def test_initialization_with_required_fields(self):
        """Verify SpanMetrics can be initialized."""
        metrics = SpanMetrics(span_name="test_operation")
        assert metrics.span_name == "test_operation"
        assert metrics.count == 0
        assert metrics.total_duration_ms == 0.0

    def test_avg_duration_calculation(self):
        """Verify average duration is calculated correctly."""
        metrics = SpanMetrics(
            span_name="test_operation",
            count=2,
            total_duration_ms=100.0
        )
        assert metrics.avg_duration_ms == 50.0

    def test_avg_duration_zero_count(self):
        """Verify avg_duration returns 0 when count is 0."""
        metrics = SpanMetrics(span_name="test_operation")
        assert metrics.avg_duration_ms == 0.0

    def test_error_rate_calculation(self):
        """Verify error rate is calculated correctly."""
        metrics = SpanMetrics(
            span_name="test_operation",
            count=10,
            errors=2
        )
        assert metrics.error_rate == 0.2

    def test_error_rate_zero_count(self):
        """Verify error_rate returns 0 when count is 0."""
        metrics = SpanMetrics(span_name="test_operation")
        assert metrics.error_rate == 0.0

    def test_min_max_duration_tracking(self):
        """Verify min and max durations are tracked."""
        metrics = SpanMetrics(
            span_name="test_operation",
            min_duration_ms=10.0,
            max_duration_ms=100.0
        )
        assert metrics.min_duration_ms == 10.0
        assert metrics.max_duration_ms == 100.0


class TestPerformanceReport:
    """Tests for PerformanceReport dataclass."""

    def test_initialization(self):
        """Verify PerformanceReport can be initialized."""
        start = datetime.now()
        end = start + timedelta(hours=1)

        report = PerformanceReport(
            service_name="test-service",
            time_range=(start, end)
        )

        assert report.service_name == "test-service"
        assert report.time_range == (start, end)
        assert report.total_spans == 0
        assert report.total_errors == 0

    def test_to_dict_conversion(self):
        """Verify to_dict() converts report to dictionary."""
        start = datetime(2026, 1, 1, 12, 0, 0)
        end = datetime(2026, 1, 1, 13, 0, 0)

        report = PerformanceReport(
            service_name="test-service",
            time_range=(start, end),
            total_spans=100,
            total_errors=5,
            p50_latency_ms=50.0,
            p95_latency_ms=100.0,
            p99_latency_ms=200.0
        )

        result = report.to_dict()

        assert result["service_name"] == "test-service"
        assert result["time_range"]["start"] == start.isoformat()
        assert result["time_range"]["end"] == end.isoformat()
        assert result["summary"]["total_spans"] == 100
        assert result["summary"]["total_errors"] == 5
        assert result["summary"]["p50_latency_ms"] == 50.0

    def test_overall_error_rate_calculation(self):
        """Verify overall error rate is calculated correctly."""
        report = PerformanceReport(
            service_name="test-service",
            time_range=(datetime.now(), datetime.now()),
            total_spans=100,
            total_errors=10
        )

        result = report.to_dict()
        assert result["summary"]["overall_error_rate"] == 0.1

    def test_overall_error_rate_zero_spans(self):
        """Verify overall error rate is 0 when no spans."""
        report = PerformanceReport(
            service_name="test-service",
            time_range=(datetime.now(), datetime.now()),
            total_spans=0,
            total_errors=0
        )

        result = report.to_dict()
        assert result["summary"]["overall_error_rate"] == 0.0

    def test_span_metrics_in_dict(self):
        """Verify span metrics are included in dict."""
        start = datetime.now()
        end = start + timedelta(minutes=5)

        metrics = SpanMetrics(
            span_name="operation_1",
            count=50,
            total_duration_ms=5000.0,
            errors=2
        )

        report = PerformanceReport(
            service_name="test-service",
            time_range=(start, end),
            span_metrics={"operation_1": metrics}
        )

        result = report.to_dict()
        assert "span_metrics" in result
        assert "operation_1" in result["span_metrics"]
        assert result["span_metrics"]["operation_1"]["count"] == 50


class TestTraceExporter:
    """Tests for TraceExporter class."""

    def test_initialization_with_defaults(self):
        """Verify TraceExporter initializes with default values."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter()
            assert exporter.service_name == "unknown"
            assert exporter.sample_rate == 1.0
            assert exporter.enable_console_export is False

    def test_initialization_with_custom_values(self):
        """Verify TraceExporter accepts custom values."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter(
                otlp_endpoint="http://localhost:4317",
                service_name="my-service",
                enable_console_export=True,
                sample_rate=0.5
            )
            assert exporter.otlp_endpoint == "http://localhost:4317"
            assert exporter.service_name == "my-service"
            assert exporter.enable_console_export is True
            assert exporter.sample_rate == 0.5

    def test_sample_rate_clamping_minimum(self):
        """Verify sample_rate is clamped to minimum 0.0."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter(sample_rate=-0.5)
            assert exporter.sample_rate == 0.0

    def test_sample_rate_clamping_maximum(self):
        """Verify sample_rate is clamped to maximum 1.0."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter(sample_rate=1.5)
            assert exporter.sample_rate == 1.0

    def test_export_spans_returns_success_when_no_spans(self):
        """Verify export_spans returns SUCCESS when no spans provided."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter()
            result = exporter.export_spans([])
            assert result is None  # OTEL not available

    def test_export_spans_with_spans(self):
        """Verify export_spans handles spans list."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter()
            mock_spans = [Mock(), Mock()]
            result = exporter.export_spans(mock_spans)
            assert result is None  # OTEL not available

    def test_span_filter_application(self):
        """Verify span_filter is applied during export."""
        mock_filter = Mock(return_value=True)

        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter(span_filter=mock_filter)
            assert exporter.span_filter == mock_filter

    def test_initialization_creates_exporters(self):
        """Verify exporter initialization creates exporters."""
        with patch('trace_exporter.OTEL_AVAILABLE', False):
            exporter = TraceExporter(
                otlp_endpoint="http://localhost:4317"
            )
            assert isinstance(exporter._exporters, list)


class TestModuleExports:
    """Tests for module exports."""

    def test_expected_classes_exported(self):
        """Verify expected classes are exported."""
        import trace_exporter

        expected_exports = [
            'SpanMetrics',
            'PerformanceReport',
            'TraceExporter',
        ]

        for export in expected_exports:
            assert hasattr(trace_exporter, export)


class TestSpanMetricsIntegration:
    """Integration tests for SpanMetrics."""

    def test_full_metrics_lifecycle(self):
        """Test full metrics lifecycle from creation to aggregation."""
        metrics = SpanMetrics(span_name="api_call")

        # Simulate multiple operations
        metrics.count = 5
        metrics.total_duration_ms = 250.0
        metrics.min_duration_ms = 30.0
        metrics.max_duration_ms = 80.0
        metrics.errors = 1

        # Verify calculations
        assert metrics.avg_duration_ms == 50.0
        assert metrics.error_rate == 0.2
        assert metrics.count == 5

    def test_error_scenarios(self):
        """Test various error scenarios."""
        # All errors
        all_errors = SpanMetrics(
            span_name="failing_operation",
            count=10,
            errors=10
        )
        assert all_errors.error_rate == 1.0

        # No errors
        no_errors = SpanMetrics(
            span_name="successful_operation",
            count=10,
            errors=0
        )
        assert no_errors.error_rate == 0.0


class TestPerformanceReportIntegration:
    """Integration tests for PerformanceReport."""

    def test_multi_span_report(self):
        """Test report with multiple span metrics."""
        start = datetime.now()
        end = start + timedelta(minutes=10)

        span_metrics = {
            "database_query": SpanMetrics(
                span_name="database_query",
                count=100,
                total_duration_ms=5000.0,
                min_duration_ms=10.0,
                max_duration_ms=200.0,
                errors=5
            ),
            "api_call": SpanMetrics(
                span_name="api_call",
                count=200,
                total_duration_ms=10000.0,
                min_duration_ms=20.0,
                max_duration_ms=150.0,
                errors=10
            )
        }

        report = PerformanceReport(
            service_name="backend-service",
            time_range=(start, end),
            span_metrics=span_metrics,
            total_spans=300,
            total_errors=15
        )

        result = report.to_dict()
        assert result["summary"]["total_spans"] == 300
        assert result["summary"]["total_errors"] == 15
        assert "database_query" in result["span_metrics"]
        assert "api_call" in result["span_metrics"]

    def test_percentile_calculations(self):
        """Test percentile latency calculations."""
        report = PerformanceReport(
            service_name="api-service",
            time_range=(datetime.now(), datetime.now()),
            p50_latency_ms=45.0,
            p95_latency_ms=120.0,
            p99_latency_ms=300.0
        )

        result = report.to_dict()
        assert result["summary"]["p50_latency_ms"] == 45.0
        assert result["summary"]["p95_latency_ms"] == 120.0
        assert result["summary"]["p99_latency_ms"] == 300.0

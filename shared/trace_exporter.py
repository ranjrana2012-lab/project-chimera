"""
Shared Trace Exporter Module
Project Chimera v0.5.0

This module provides trace export functionality for Project Chimera services,
including:

- OTLP export to Jaeger/Tempo
- Console export for development
- Span filtering and sampling
- Performance analysis utilities

Usage:
    from shared.trace_exporter import TraceExporter, TraceAnalyzer

    # Create exporter
    exporter = TraceExporter(
        otlp_endpoint="http://localhost:4317",
        service_name="my-service"
    )

    # Export traces
    exporter.export_spans(spans)

    # Analyze traces
    analyzer = TraceAnalyzer()
    report = analyzer.generate_performance_report(traces)
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExporter, ExportResult
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    ReadableSpan = None  # type: ignore
    ExportResult = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class SpanMetrics:
    """Metrics calculated from a collection of spans."""
    span_name: str
    count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    errors: int = 0

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration."""
        return self.total_duration_ms / self.count if self.count > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return self.errors / self.count if self.count > 0 else 0.0


@dataclass
class PerformanceReport:
    """Performance analysis report."""
    service_name: str
    time_range: tuple[datetime, datetime]
    span_metrics: Dict[str, SpanMetrics] = field(default_factory=dict)
    total_spans: int = 0
    total_errors: int = 0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "service_name": self.service_name,
            "time_range": {
                "start": self.time_range[0].isoformat(),
                "end": self.time_range[1].isoformat(),
            },
            "summary": {
                "total_spans": self.total_spans,
                "total_errors": self.total_errors,
                "overall_error_rate": self.total_errors / self.total_spans if self.total_spans > 0 else 0.0,
                "p50_latency_ms": self.p50_latency_ms,
                "p95_latency_ms": self.p95_latency_ms,
                "p99_latency_ms": self.p99_latency_ms,
            },
            "span_metrics": {
                name: {
                    "count": metrics.count,
                    "avg_duration_ms": metrics.avg_duration_ms,
                    "min_duration_ms": metrics.min_duration_ms,
                    "max_duration_ms": metrics.max_duration_ms,
                    "error_rate": metrics.error_rate,
                }
                for name, metrics in self.span_metrics.items()
            }
        }


class TraceExporter:
    """
    Trace exporter with support for multiple backends.

    Supports:
    - OTLP export to Jaeger/Tempo
    - Console export for debugging
    - Custom span filtering
    - Sampling
    """

    def __init__(
        self,
        otlp_endpoint: Optional[str] = None,
        service_name: str = "unknown",
        enable_console_export: bool = False,
        sample_rate: float = 1.0,
        span_filter: Optional[Callable[[Any], bool]] = None
    ):
        """
        Initialize trace exporter.

        Args:
            otlp_endpoint: OTLP collector endpoint
            service_name: Name of the service
            enable_console_export: Enable console export
            sample_rate: Sampling rate (0.0 to 1.0)
            span_filter: Optional filter function for spans
        """
        self.otlp_endpoint = otlp_endpoint
        self.service_name = service_name
        self.enable_console_export = enable_console_export
        self.sample_rate = max(0.0, min(1.0, sample_rate))
        self.span_filter = span_filter

        self._exporters = []
        self._initialize_exporters()

    def _initialize_exporters(self):
        """Initialize configured exporters."""
        if not OTEL_AVAILABLE:
            logger.warning("OpenTelemetry not available, skipping exporter initialization")
            return

        # Add OTLP exporter if endpoint configured
        if self.otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                from opentelemetry.sdk.trace.export import BatchSpanProcessor

                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.otlp_endpoint,
                    insecure=True
                )
                self._exporters.append(("otlp", otlp_exporter))
                logger.info(f"OTLP exporter configured: {self.otlp_endpoint}")
            except Exception as e:
                logger.error(f"Failed to initialize OTLP exporter: {e}")

        # Add console exporter if enabled
        if self.enable_console_export:
            try:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

                console_exporter = ConsoleSpanExporter()
                self._exporters.append(("console", console_exporter))
                logger.info("Console exporter configured")
            except Exception as e:
                logger.error(f"Failed to initialize console exporter: {e}")

    def export_spans(self, spans: List[Any]) -> Any:
        """
        Export spans to configured exporters.

        Args:
            spans: List of spans to export

        Returns:
            Export result (SUCCESS or FAIL)
        """
        if not OTEL_AVAILABLE:
            logger.warning("OpenTelemetry not available, skipping span export")
            return None

        if not spans:
            return ExportResult.SUCCESS  # type: ignore

        # Apply sampling
        sampled_spans = self._apply_sampling(spans)

        # Apply filtering
        filtered_spans = self._apply_filtering(sampled_spans)

        if not filtered_spans:
            return ExportResult.SUCCESS

        # Export to all configured exporters
        results = []
        for name, exporter in self._exporters:
            try:
                result = exporter.export(filtered_spans)
                results.append(result)
                logger.debug(f"Exported {len(filtered_spans)} spans to {name}")
            except Exception as e:
                logger.error(f"Failed to export spans to {name}: {e}")
                results.append(ExportResult.FAIL)

        # Return FAIL if any exporter failed
        return ExportResult.FAIL if ExportResult.FAIL in results else ExportResult.SUCCESS

    def _apply_sampling(self, spans: List[Any]) -> List[Any]:
        """Apply sampling to spans."""
        if self.sample_rate >= 1.0:
            return spans

        # Simple random sampling
        import random
        sampled_count = int(len(spans) * self.sample_rate)
        return random.sample(spans, min(sampled_count, len(spans)))

    def _apply_filtering(self, spans: List[Any]) -> List[Any]:
        """Apply custom filter to spans."""
        if not self.span_filter:
            return spans

        return [s for s in spans if self.span_filter(s)]

    def shutdown(self):
        """Shutdown all exporters."""
        for name, exporter in self._exporters:
            try:
                if hasattr(exporter, "shutdown"):
                    exporter.shutdown()
                    logger.info(f"Shutdown {name} exporter")
            except Exception as e:
                logger.error(f"Failed to shutdown {name} exporter: {e}")


class TraceAnalyzer:
    """
    Analyze traces to generate performance reports.

    Calculates:
    - Latency percentiles (p50, p95, p99)
    - Error rates
    - Span duration statistics
    - Performance anomalies
    """

    def __init__(self):
        """Initialize trace analyzer."""
        self.spans: List[Any] = []

    def add_spans(self, spans: List[Any]) -> None:
        """Add spans for analysis."""
        self.spans.extend(spans)

    def clear(self) -> None:
        """Clear stored spans."""
        self.spans.clear()

    def generate_performance_report(
        self,
        service_name: str,
        time_range: Optional[tuple[datetime, datetime]] = None
    ) -> PerformanceReport:
        """
        Generate a performance report from collected spans.

        Args:
            service_name: Name of the service
            time_range: Optional time range to filter spans

        Returns:
            PerformanceReport with metrics
        """
        if not self.spans:
            return PerformanceReport(
                service_name=service_name,
                time_range=(datetime.now(), datetime.now())
            )

        # Filter by time range if provided
        spans = self._filter_by_time_range(self.spans, time_range)

        if not spans:
            return PerformanceReport(
                service_name=service_name,
                time_range=time_range or (datetime.now(), datetime.now())
            )

        # Calculate metrics by span name
        span_metrics = self._calculate_span_metrics(spans)

        # Calculate overall latency percentiles
        all_durations = [
            self._get_span_duration(s) for s in spans
            if self._get_span_duration(s) is not None
        ]

        if all_durations:
            all_durations.sort()
            p50_idx = int(len(all_durations) * 0.5)
            p95_idx = int(len(all_durations) * 0.95)
            p99_idx = int(len(all_durations) * 0.99)

            p50 = all_durations[p50_idx]
            p95 = all_durations[p95_idx]
            p99 = all_durations[p99_idx]
        else:
            p50 = p95 = p99 = 0.0

        # Count total errors
        total_errors = sum(m.errors for m in span_metrics.values())

        # Determine time range
        start_time = min(
            self._get_span_start_time(s) for s in spans
            if self._get_span_start_time(s) is not None
        ) or datetime.now()

        end_time = max(
            self._get_span_end_time(s) for s in spans
            if self._get_span_end_time(s) is not None
        ) or datetime.now()

        return PerformanceReport(
            service_name=service_name,
            time_range=(start_time, end_time),
            span_metrics=span_metrics,
            total_spans=len(spans),
            total_errors=total_errors,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99
        )

    def _filter_by_time_range(
        self,
        spans: List[Any],
        time_range: Optional[tuple[datetime, datetime]]
    ) -> List[Any]:
        """Filter spans by time range."""
        if not time_range:
            return spans

        start, end = time_range
        filtered = []

        for span in spans:
            start_time = self._get_span_start_time(span)
            if start_time and start <= start_time <= end:
                filtered.append(span)

        return filtered

    def _calculate_span_metrics(self, spans: List[Any]) -> Dict[str, SpanMetrics]:
        """Calculate metrics grouped by span name."""
        metrics_by_name: Dict[str, SpanMetrics] = defaultdict(
            lambda: SpanMetrics(span_name="")
        )

        for span in spans:
            name = self._get_span_name(span)
            duration = self._get_span_duration(span)
            is_error = self._is_error_span(span)

            metrics = metrics_by_name[name]
            metrics.span_name = name
            metrics.count += 1

            if duration is not None:
                metrics.total_duration_ms += duration
                metrics.min_duration_ms = min(metrics.min_duration_ms, duration)
                metrics.max_duration_ms = max(metrics.max_duration_ms, duration)

            if is_error:
                metrics.errors += 1

        # Reset infinities
        for metrics in metrics_by_name.values():
            if metrics.min_duration_ms == float('inf'):
                metrics.min_duration_ms = 0.0

        return dict(metrics_by_name)

    def _get_span_name(self, span: Any) -> str:
        """Extract span name."""
        if hasattr(span, 'name'):
            return span.name
        elif hasattr(span, '_span_processor'):
            return getattr(span, 'name', 'unknown')
        return 'unknown'

    def _get_span_duration(self, span: Any) -> Optional[float]:
        """Extract span duration in milliseconds."""
        try:
            if hasattr(span, 'end_time') and hasattr(span, 'start_time'):
                # OpenTelemetry span
                start = span.start_time
                end = span.end_time
                if start and end:
                    return (end - start) / 1_000_000  # Convert nanoseconds to milliseconds
            elif hasattr(span, 'duration_ms'):
                return span.duration_ms
            elif hasattr(span, 'duration'):
                return span.duration * 1000  # Convert seconds to milliseconds
        except Exception:
            pass
        return None

    def _get_span_start_time(self, span: Any) -> Optional[datetime]:
        """Extract span start time."""
        try:
            if hasattr(span, 'start_time'):
                return datetime.fromtimestamp(span.start_time / 1_000_000_000)
            elif hasattr(span, 'timestamp'):
                return span.timestamp
        except Exception:
            pass
        return None

    def _get_span_end_time(self, span: Any) -> Optional[datetime]:
        """Extract span end time."""
        try:
            if hasattr(span, 'end_time'):
                return datetime.fromtimestamp(span.end_time / 1_000_000_000)
        except Exception:
            pass
        return None

    def _is_error_span(self, span: Any) -> bool:
        """Check if span represents an error."""
        try:
            if hasattr(span, 'status'):
                return span.status.is_error
            elif hasattr(span, 'events'):
                return any(
                    getattr(e, 'name', '') == 'exception'
                    for e in span.events
                )
        except Exception:
            pass
        return False


class LatencyValidator:
    """
    Validate latency against TRD requirements.

    TRD Requirements:
    - SceneSpeak: <2s (p95)
    - BSL: <1s (p95)
    - Captioning: <500ms (p95)
    - Sentiment: <200ms (p95)
    - End-to-end: <5s (p95)
    """

    # TRD latency requirements (p95, in milliseconds)
    REQUIREMENTS = {
        "scenespeak": 2000,
        "bsl": 1000,
        "captioning": 500,
        "sentiment": 200,
        "end_to_end": 5000,
    }

    @classmethod
    def validate(cls, service_name: str, p95_latency_ms: float) -> Dict[str, Any]:
        """
        Validate p95 latency against TRD requirement.

        Args:
            service_name: Name of the service
            p95_latency_ms: p95 latency in milliseconds

        Returns:
            Validation result with pass/fail status
        """
        # Normalize service name
        service_key = service_name.lower().replace("-", "_").replace(" ", "_")
        service_key = service_key.replace("_agent", "").replace("_service", "")

        # Get requirement
        requirement = cls.REQUIREMENTS.get(service_key)

        if requirement is None:
            return {
                "service": service_name,
                "status": "unknown",
                "p95_latency_ms": p95_latency_ms,
                "requirement_ms": None,
                "message": f"No latency requirement defined for {service_name}"
            }

        # Check if passes
        passes = p95_latency_ms <= requirement

        return {
            "service": service_name,
            "status": "pass" if passes else "fail",
            "p95_latency_ms": p95_latency_ms,
            "requirement_ms": requirement,
            "margin_ms": requirement - p95_latency_ms,
            "message": (
                f"p95 latency {p95_latency_ms}ms "
                f"{'meets' if passes else 'exceeds'} requirement of {requirement}ms"
            )
        }

    @classmethod
    def validate_report(cls, report: PerformanceReport) -> Dict[str, Dict[str, Any]]:
        """
        Validate all services in a performance report.

        Args:
            report: Performance report

        Returns:
            Dictionary of validation results by service
        """
        results = {}

        for span_name, metrics in report.span_metrics.items():
            # Extract service name from span name
            service_name = span_name.split("/")[0].split(".")[0]

            # Use p95 max as proxy for p95 latency
            p95_latency = metrics.max_duration_ms

            results[span_name] = cls.validate(service_name, p95_latency)

        return results


# Utility functions

def calculate_percentiles(values: List[float], percentiles: List[float]) -> Dict[float, float]:
    """
    Calculate percentiles from a list of values.

    Args:
        values: List of numeric values
        percentiles: List of percentiles to calculate (0.0 to 1.0)

    Returns:
        Dictionary mapping percentile to value
    """
    if not values:
        return {p: 0.0 for p in percentiles}

    sorted_values = sorted(values)
    n = len(sorted_values)

    return {
        p: sorted_values[int(n * p)] if int(n * p) < n else sorted_values[-1]
        for p in percentiles
    }


def format_duration_ms(ms: float) -> str:
    """Format duration in milliseconds to human-readable string."""
    if ms < 1:
        return f"{ms * 1000:.2f}μs"
    elif ms < 1000:
        return f"{ms:.2f}ms"
    else:
        return f"{ms / 1000:.2f}s"

"""Trace Analyzer for analyzing Jaeger traces for performance issues"""

from dataclasses import dataclass, field
from typing import List, Optional
import requests


@dataclass
class TraceIssue:
    """Represents an issue found in a trace"""
    severity: str  # "warning", "error"
    span: str
    message: str


@dataclass
class TraceReport:
    """Report containing analysis results for a trace"""
    trace_id: str
    duration_ms: int
    span_count: int
    issues: List[TraceIssue] = field(default_factory=list)
    score: float = 1.0


class TraceAnalyzer:
    """Analyze Jaeger traces for performance issues"""

    # Default threshold for considering a span as slow (2 seconds in microseconds)
    SLOW_SPAN_THRESHOLD_US = 2_000_000

    def __init__(self, jaeger_url: str = "http://jaeger.shared.svc.cluster.local:16686"):
        """
        Initialize the trace analyzer.

        Args:
            jaeger_url: URL of the Jaeger API server
        """
        self.jaeger_url = jaeger_url

    def analyze_trace(self, trace_id: str) -> TraceReport:
        """
        Analyze a trace for performance issues.

        Args:
            trace_id: The Jaeger trace ID to analyze

        Returns:
            TraceReport containing analysis results
        """
        # Fetch trace from Jaeger
        trace = self._fetch_trace(trace_id)
        if not trace:
            return TraceReport(
                trace_id=trace_id,
                duration_ms=0,
                span_count=0,
                issues=[TraceIssue("error", "trace_fetch", "Trace not found")],
                score=0.0
            )

        issues = []

        # Check for slow spans
        for span in trace.get("spans", []):
            duration_us = span.get("duration", 0)
            operation = span.get("operationName", "unknown")

            # Check for slow spans (threshold is in microseconds)
            if duration_us > self.SLOW_SPAN_THRESHOLD_US:
                duration_ms = duration_us / 1000
                issues.append(TraceIssue(
                    severity="warning",
                    span=operation,
                    message=f"Slow operation: {duration_ms:.0f}ms"
                ))

            # Check for errors and warnings
            if span.get("warnings") or span.get("errors"):
                issues.append(TraceIssue(
                    severity="error",
                    span=operation,
                    message="Span has warnings or errors"
                ))

        # Check for missing expected spans
        expected_spans = self._get_expected_spans(trace)
        actual_spans = {s.get("operationName") for s in trace.get("spans", [])}
        missing = expected_spans - actual_spans

        if missing:
            issues.append(TraceIssue(
                severity="error",
                span="trace_flow",
                message=f"Missing expected spans: {missing}"
            ))

        # Calculate quality score
        score = self._calculate_score(trace, issues)

        return TraceReport(
            trace_id=trace_id,
            duration_ms=trace.get("duration", 0),
            span_count=len(trace.get("spans", [])),
            issues=issues,
            score=score
        )

    def _fetch_trace(self, trace_id: str) -> Optional[dict]:
        """
        Fetch trace from Jaeger API.

        Args:
            trace_id: The trace ID to fetch

        Returns:
            Trace data dict or None if not found/error
        """
        try:
            response = requests.get(
                f"{self.jaeger_url}/api/traces/{trace_id}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0] if data.get("data") else None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching trace: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing trace response: {e}")
            return None

    def _get_expected_spans(self, trace: dict) -> set:
        """
        Get expected span names based on trace service.

        Args:
            trace: Trace data dictionary

        Returns:
            Set of expected span operation names
        """
        # Common expected spans for Project Chimera services
        # These represent the key operations that should be present in a healthy trace
        return {
            "generate_dialogue",
            "load_adapter",
            "llm_inference",
            "cache_lookup",
            "safety_check"
        }

    def _calculate_score(self, trace: dict, issues: List[TraceIssue]) -> float:
        """
        Calculate trace quality score (0-1).

        Args:
            trace: Trace data dictionary
            issues: List of issues found in the trace

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not issues:
            return 1.0

        score = 1.0
        for issue in issues:
            if issue.severity == "error":
                score -= 0.2
            elif issue.severity == "warning":
                score -= 0.05

        return max(0.0, score)

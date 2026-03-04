"""Tests for trace analyzer module"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch
from analyzer import TraceAnalyzer, TraceReport, TraceIssue


def test_analyze_trace_detects_slow_spans():
    """Test that analyzer detects slow spans"""
    analyzer = TraceAnalyzer()

    # Mock trace with slow span
    mock_trace = {
        "traceID": "test-trace-id",
        "duration": 5000000,  # 5 seconds
        "spans": [
            {
                "operationName": "generate_dialogue",
                "duration": 3000000,  # 3 seconds - slow!
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            },
            {
                "operationName": "cache_lookup",
                "duration": 50000,  # 50ms - fast
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            }
        ]
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-trace-id")

    assert report.trace_id == "test-trace-id"
    assert report.duration_ms == 5000000
    assert report.span_count == 2
    assert any("Slow operation" in issue.message for issue in report.issues)
    assert any(issue.span == "generate_dialogue" for issue in report.issues)


def test_analyze_trace_detects_error_spans():
    """Test that analyzer detects spans with errors"""
    analyzer = TraceAnalyzer()

    # Mock trace with error span
    mock_trace = {
        "traceID": "test-trace-error",
        "duration": 1000000,
        "spans": [
            {
                "operationName": "llm_inference",
                "duration": 500000,
                "process": {"serviceName": "scenespeak-agent"},
                "warnings": ["Timeout waiting for LLM response"],
                "tags": []
            }
        ]
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-trace-error")

    assert any("warnings or errors" in issue.message for issue in report.issues)
    assert any(issue.severity == "error" for issue in report.issues)


def test_analyze_trace_detects_missing_spans():
    """Test that analyzer detects missing expected spans"""
    analyzer = TraceAnalyzer()

    # Mock trace with only one span (missing expected spans)
    mock_trace = {
        "traceID": "test-trace-missing",
        "duration": 500000,
        "spans": [
            {
                "operationName": "generate_dialogue",
                "duration": 500000,
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            }
        ]
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-trace-missing")

    assert any("Missing expected spans" in issue.message for issue in report.issues)


def test_analyze_trace_perfect_score():
    """Test that a clean trace gets score of 1.0"""
    analyzer = TraceAnalyzer()

    # Mock clean trace
    mock_trace = {
        "traceID": "test-trace-clean",
        "duration": 500000,
        "spans": [
            {
                "operationName": "generate_dialogue",
                "duration": 500,
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            },
            {
                "operationName": "load_adapter",
                "duration": 100,
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            },
            {
                "operationName": "llm_inference",
                "duration": 300000,
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            },
            {
                "operationName": "cache_lookup",
                "duration": 50,
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            },
            {
                "operationName": "safety_check",
                "duration": 100,
                "process": {"serviceName": "scenespeak-agent"},
                "tags": []
            }
        ]
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-trace-clean")

    assert report.score == 1.0
    assert len(report.issues) == 0


def test_analyze_trace_not_found():
    """Test behavior when trace is not found"""
    analyzer = TraceAnalyzer()

    with patch.object(analyzer, '_fetch_trace', return_value=None):
        report = analyzer.analyze_trace("nonexistent-trace")

    assert report.trace_id == "nonexistent-trace"
    assert report.duration_ms == 0
    assert report.span_count == 0
    assert report.score == 0.0
    assert any("Trace not found" in issue.message for issue in report.issues)


def test_calculate_score_with_errors():
    """Test score calculation with error severity issues"""
    analyzer = TraceAnalyzer()

    # Each error should reduce score by 0.2
    # Include all expected spans to avoid missing spans error
    mock_trace = {
        "traceID": "test-score-errors",
        "duration": 1000000,
        "spans": [
            {
                "operationName": "span1",
                "duration": 500000,
                "process": {"serviceName": "test"},
                "warnings": ["Error 1"]
            },
            {
                "operationName": "span2",
                "duration": 500000,
                "process": {"serviceName": "test"},
                "warnings": ["Error 2"]
            },
            {
                "operationName": "generate_dialogue",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "load_adapter",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "llm_inference",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "cache_lookup",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "safety_check",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            }
        ]
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-score-errors")

    # 2 errors * 0.2 = 0.4 reduction, so score should be 0.6
    assert abs(report.score - 0.6) < 0.001


def test_calculate_score_with_warnings():
    """Test score calculation with warning severity issues"""
    analyzer = TraceAnalyzer()

    # Each warning should reduce score by 0.05
    # Include all expected spans to avoid missing spans error
    mock_trace = {
        "traceID": "test-score-warnings",
        "duration": 10000000,
        "spans": [
            {
                "operationName": "slow_span_1",
                "duration": 3000000,  # 3 seconds - warning
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "slow_span_2",
                "duration": 4000000,  # 4 seconds - warning
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "generate_dialogue",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "load_adapter",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "llm_inference",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "cache_lookup",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            },
            {
                "operationName": "safety_check",
                "duration": 100,
                "process": {"serviceName": "test"},
                "tags": []
            }
        ]
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-score-warnings")

    # 2 warnings * 0.05 = 0.1 reduction, so score should be 0.9
    assert abs(report.score - 0.9) < 0.001


def test_calculate_score_floor_at_zero():
    """Test that score never goes below 0.0"""
    analyzer = TraceAnalyzer()

    # Create many errors to try to drive score below 0
    # Include all expected spans to avoid missing spans error
    spans = [
        {
            "operationName": f"span_{i}",
            "duration": 100000,
            "process": {"serviceName": "test"},
            "warnings": [f"Error {i}"]
        }
        for i in range(10)  # 10 errors = -2.0, should floor at 0.0
    ]

    # Add expected spans
    spans.extend([
        {
            "operationName": "generate_dialogue",
            "duration": 100,
            "process": {"serviceName": "test"},
            "tags": []
        },
        {
            "operationName": "load_adapter",
            "duration": 100,
            "process": {"serviceName": "test"},
            "tags": []
        },
        {
            "operationName": "llm_inference",
            "duration": 100,
            "process": {"serviceName": "test"},
            "tags": []
        },
        {
            "operationName": "cache_lookup",
            "duration": 100,
            "process": {"serviceName": "test"},
            "tags": []
        },
        {
            "operationName": "safety_check",
            "duration": 100,
            "process": {"serviceName": "test"},
            "tags": []
        }
    ])

    mock_trace = {
        "traceID": "test-score-floor",
        "duration": 1000000,
        "spans": spans
    }

    with patch.object(analyzer, '_fetch_trace', return_value=mock_trace):
        report = analyzer.analyze_trace("test-score-floor")

    assert report.score == 0.0


def test_trace_issue_dataclass():
    """Test TraceIssue dataclass structure"""
    issue = TraceIssue(
        severity="error",
        span="test_span",
        message="Test error message"
    )

    assert issue.severity == "error"
    assert issue.span == "test_span"
    assert issue.message == "Test error message"


def test_trace_report_dataclass():
    """Test TraceReport dataclass structure"""
    issues = [
        TraceIssue("warning", "span1", "Warning message"),
        TraceIssue("error", "span2", "Error message")
    ]

    report = TraceReport(
        trace_id="test-trace",
        duration_ms=1000,
        span_count=5,
        issues=issues,
        score=0.75
    )

    assert report.trace_id == "test-trace"
    assert report.duration_ms == 1000
    assert report.span_count == 5
    assert len(report.issues) == 2
    assert report.score == 0.75


def test_custom_jaeger_url():
    """Test that custom Jaeger URL is used"""
    custom_url = "http://custom-jaeger:16686"
    analyzer = TraceAnalyzer(jaeger_url=custom_url)

    assert analyzer.jaeger_url == custom_url

"""
Safety Filter Tracing Module

Domain-specific tracing instrumentation for safety filtering operations.
Implements span attributes for safety tracking as specified in Task 21.
"""

import time
from contextlib import contextmanager
from typing import Optional, List

# Import shared tracing utilities
import sys
import os
shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../shared'))
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)
from shared.tracing import setup_telemetry, add_span_attributes, record_error


# Global tracer instance
_tracer = None


def get_tracer():
    """Get or create the safety filter tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = setup_telemetry("safety-filter")
    return _tracer


@contextmanager
def trace_safety_check(content: str, policy: str, content_id: Optional[str] = None):
    """
    Context manager for tracing safety check operations.

    Automatically records safety.action, pattern.matched, and content.length span attributes.

    Args:
        content: Content being checked
        policy: Safety policy being applied
        content_id: Optional content identifier

    Yields:
        span: The active span for adding custom attributes
    """
    tracer = get_tracer()
    start_time = time.time()

    with tracer.start_as_current_span("safety_check") as span:
        # Add initial attributes
        add_span_attributes(span, {
            "content.length": len(content),
            "safety.policy": policy,
            "content.id": content_id or "unknown"
        })

        try:
            yield span

            # Record check duration
            check_duration_ms = int((time.time() - start_time) * 1000)
            add_span_attributes(span, {
                "safety.check_duration_ms": check_duration_ms
            })

        except Exception as e:
            record_error(span, e)
            raise


def record_safety_result(span, is_safe: bool, action: str, matched_patterns: Optional[List[str]] = None, severity: Optional[str] = None):
    """
    Record safety check result on span.

    Args:
        span: The span to record on
        is_safe: Whether content passed safety check
        action: Action taken (e.g., "allow", "block", "flag")
        matched_patterns: Optional list of matched patterns/terms
        severity: Optional severity level
    """
    attributes = {
        "safety.is_safe": is_safe,
        "safety.action": action
    }

    if matched_patterns:
        # Join patterns for span attribute
        attributes["pattern.matched"] = ", ".join(matched_patterns[:5])  # Limit to first 5
        attributes["pattern.matched_count"] = len(matched_patterns)

    if severity:
        attributes["safety.severity"] = severity

    add_span_attributes(span, attributes)


@contextmanager
def trace_layer_check(layer_name: str, content_length: int):
    """
    Context manager for tracing individual safety layer checks.

    Args:
        layer_name: Name of the safety layer (e.g., "keyword", "ml", "contextual")
        content_length: Length of content being checked

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(f"layer_{layer_name}") as span:
        add_span_attributes(span, {
            "safety.layer": layer_name,
            "content.length": content_length
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


def record_layer_result(span, passed: bool, matched_terms: Optional[List[str]] = None):
    """
    Record layer check result on span.

    Args:
        span: The span to record on
        passed: Whether the layer was passed
        matched_terms: Optional list of matched terms
    """
    attributes = {
        "layer.passed": passed
    }

    if matched_terms:
        add_span_attributes(span, {
            "layer.matched_terms": ", ".join(matched_terms[:10]),
            "layer.matched_count": len(matched_terms)
        })

    add_span_attributes(span, attributes)


@contextmanager
def trace_batch_check(content_count: int, policy: str):
    """
    Context manager for tracing batch safety checks.

    Args:
        content_count: Number of content items being checked
        policy: Safety policy being applied

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("batch_safety_check") as span:
        add_span_attributes(span, {
            "batch.content_count": content_count,
            "safety.policy": policy
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


@contextmanager
def trace_policy_evaluation(policy_name: str):
    """
    Context manager for tracing policy evaluation.

    Args:
        policy_name: Name of policy being evaluated

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("policy_evaluation") as span:
        add_span_attributes(span, {
            "safety.policy": policy_name
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


__all__ = [
    'get_tracer',
    'trace_safety_check',
    'record_safety_result',
    'trace_layer_check',
    'record_layer_result',
    'trace_batch_check',
    'trace_policy_evaluation',
]

"""
BSL Agent Tracing Module

Domain-specific tracing instrumentation for BSL translation operations.
Implements span attributes for translation tracking as specified in Task 21.
"""

import time
from contextlib import contextmanager
from typing import Optional

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
    """Get or create the BSL tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = setup_telemetry("bsl-agent")
    return _tracer


@contextmanager
def trace_translation(request_id: str, source_language: str = "en", sign_language: str = "bsl"):
    """
    Context manager for tracing BSL translation operations.

    Automatically records translation.request_id and sign_language span attributes.

    Args:
        request_id: Unique identifier for the translation request
        source_language: Source language code (default: "en")
        sign_language: Target sign language (default: "bsl")

    Yields:
        span: The active span for adding custom attributes
    """
    tracer = get_tracer()
    start_time = time.time()

    with tracer.start_as_current_span("translation") as span:
        # Add required attributes
        add_span_attributes(span, {
            "translation.request_id": request_id,
            "sign_language": sign_language,
            "translation.source_language": source_language
        })

        try:
            yield span

            # Record translation duration
            translation_duration_ms = int((time.time() - start_time) * 1000)
            add_span_attributes(span, {
                "translation.duration_ms": translation_duration_ms
            })

        except Exception as e:
            record_error(span, e)
            raise


@contextmanager
def trace_gloss_generation(request_id: str, gloss_format: str):
    """
    Context manager for tracing gloss generation.

    Args:
        request_id: Translation request identifier
        gloss_format: Format of gloss notation (e.g., "singspell")

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("gloss_generation") as span:
        add_span_attributes(span, {
            "translation.request_id": request_id,
            "gloss.format": gloss_format
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


def record_gloss_result(span, gloss_length: int, confidence: float):
    """
    Record gloss generation result on span.

    Args:
        span: The span to record on
        gloss_length: Length of generated gloss
        confidence: Confidence score (0-1)
    """
    add_span_attributes(span, {
        "gloss.length": gloss_length,
        "gloss.confidence": confidence
    })


@contextmanager
def trace_batch_translation(request_count: int):
    """
    Context manager for tracing batch translation operations.

    Args:
        request_count: Number of translations in the batch

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("batch_translation") as span:
        add_span_attributes(span, {
            "batch.request_count": request_count,
            "sign_language": "bsl"
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


@contextmanager
def trace_non_manual_markers(request_id: str):
    """
    Context manager for tracing non-manual marker generation.

    Args:
        request_id: Translation request identifier

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("non_manual_markers") as span:
        add_span_attributes(span, {
            "translation.request_id": request_id
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


__all__ = [
    'get_tracer',
    'trace_translation',
    'trace_gloss_generation',
    'record_gloss_result',
    'trace_batch_translation',
    'trace_non_manual_markers',
]

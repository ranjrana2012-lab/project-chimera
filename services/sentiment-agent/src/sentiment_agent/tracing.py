"""
Sentiment Agent Tracing Module

Domain-specific tracing instrumentation for sentiment analysis operations.
Implements span attributes for sentiment tracking as specified in Task 21.
"""

import time
from contextlib import contextmanager
from typing import Optional, List

# Import shared tracing utilities
import sys
import os
shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../shared'))
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)
from shared.tracing import setup_telemetry, add_span_attributes, record_error


# Global tracer instance
_tracer = None


def get_tracer():
    """Get or create the sentiment tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = setup_telemetry("sentiment-agent")
    return _tracer


@contextmanager
def trace_sentiment_analysis(audience_size: int, text_length: Optional[int] = None):
    """
    Context manager for tracing sentiment analysis operations.

    Automatically records sentiment.score and audience.size span attributes.

    Args:
        audience_size: Size of the audience being analyzed
        text_length: Optional length of text being analyzed

    Yields:
        span: The active span for adding custom attributes
    """
    tracer = get_tracer()
    start_time = time.time()

    with tracer.start_as_current_span("sentiment_analysis") as span:
        # Add initial attributes
        add_span_attributes(span, {
            "audience.size": audience_size
        })

        if text_length is not None:
            add_span_attributes(span, {
                "analysis.text_length": text_length
            })

        try:
            yield span

            # Record analysis duration
            analysis_duration_ms = int((time.time() - start_time) * 1000)
            add_span_attributes(span, {
                "analysis.duration_ms": analysis_duration_ms
            })

        except Exception as e:
            record_error(span, e)
            raise


def record_sentiment_score(span, score: float, confidence: Optional[float] = None):
    """
    Record sentiment analysis result on span.

    Args:
        span: The span to record on
        score: Sentiment score (-1.0 to 1.0)
        confidence: Optional confidence score (0-1)
    """
    attributes = {
        "sentiment.score": score
    }

    if confidence is not None:
        attributes["sentiment.confidence"] = confidence

    add_span_attributes(span, attributes)


@contextmanager
def trace_emotion_detection(audience_size: int):
    """
    Context manager for tracing emotion detection operations.

    Args:
        audience_size: Size of the audience

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("emotion_detection") as span:
        add_span_attributes(span, {
            "audience.size": audience_size
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


def record_emotion_scores(span, emotions: dict):
    """
    Record emotion detection results on span.

    Args:
        span: The span to record on
        emotions: Dictionary of emotion names to scores
                  (e.g., {"joy": 0.8, "surprise": 0.3, "neutral": 0.5})
    """
    for emotion, score in emotions.items():
        add_span_attributes(span, {
            f"emotion.{emotion}": score
        })

    # Also record dominant emotion
    if emotions:
        dominant_emotion = max(emotions, key=emotions.get)
        add_span_attributes(span, {
            "emotion.dominant": dominant_emotion
        })


@contextmanager
def trace_batch_analysis(audience_size: int, text_count: int):
    """
    Context manager for tracing batch sentiment analysis.

    Args:
        audience_size: Total audience size
        text_count: Number of texts being analyzed

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("batch_sentiment_analysis") as span:
        add_span_attributes(span, {
            "audience.size": audience_size,
            "batch.text_count": text_count
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


@contextmanager
def trace_aggregation(show_id: str, time_window: str):
    """
    Context manager for tracing sentiment aggregation operations.

    Args:
        show_id: Show identifier
        time_window: Time window for aggregation (e.g., "5m", "1h")

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("sentiment_aggregation") as span:
        add_span_attributes(span, {
            "show_id": show_id,
            "aggregation.time_window": time_window
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


__all__ = [
    'get_tracer',
    'trace_sentiment_analysis',
    'record_sentiment_score',
    'trace_emotion_detection',
    'record_emotion_scores',
    'trace_batch_analysis',
    'trace_aggregation',
]

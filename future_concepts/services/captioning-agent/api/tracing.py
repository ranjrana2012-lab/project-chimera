"""
Captioning Agent Tracing Module

Domain-specific tracing instrumentation for captioning operations.
Implements span attributes for caption latency tracking as specified in Task 21.
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
    """Get or create the captioning tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = setup_telemetry("captioning-agent")
    return _tracer


@contextmanager
def trace_transcription(audio_size_bytes: Optional[int] = None, language: Optional[str] = None):
    """
    Context manager for tracing transcription operations.

    Automatically records caption_latency_ms span attribute.

    Args:
        audio_size_bytes: Size of audio data in bytes
        language: Language code for transcription

    Yields:
        span: The active span for adding custom attributes
    """
    tracer = get_tracer()
    start_time = time.time()

    with tracer.start_as_current_span("transcription") as span:
        # Add initial attributes
        attributes = {}
        if audio_size_bytes is not None:
            attributes["audio.size_bytes"] = audio_size_bytes
        if language is not None:
            attributes["transcription.language"] = language

        add_span_attributes(span, attributes)

        try:
            yield span

            # Calculate and record caption latency
            caption_latency_ms = int((time.time() - start_time) * 1000)
            add_span_attributes(span, {
                "caption_latency_ms": caption_latency_ms
            })

        except Exception as e:
            record_error(span, e)
            raise


@contextmanager
def trace_streaming_session(session_id: str):
    """
    Context manager for tracing WebSocket streaming sessions.

    Args:
        session_id: Unique identifier for the streaming session

    Yields:
        span: The active span for the session
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("streaming_session") as span:
        add_span_attributes(span, {
            "streaming.session_id": session_id,
            "streaming.protocol": "websocket"
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


@contextmanager
def trace_cache_lookup(cache_key: str):
    """
    Context manager for tracing cache lookup operations.

    Args:
        cache_key: The cache key being looked up

    Yields:
        span: The active span
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("cache_lookup") as span:
        add_span_attributes(span, {
            "cache.key": cache_key
        })

        try:
            yield span
        except Exception as e:
            record_error(span, e)
            raise


def record_cache_result(span, hit: bool):
    """
    Record cache lookup result on span.

    Args:
        span: The span to record on
        hit: Whether the cache was hit
    """
    add_span_attributes(span, {
        "cache.hit": hit
    })


__all__ = [
    'get_tracer',
    'trace_transcription',
    'trace_streaming_session',
    'trace_cache_lookup',
    'record_cache_result',
]

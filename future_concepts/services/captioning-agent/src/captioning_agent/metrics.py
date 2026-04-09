"""
Business metrics for Captioning Agent.

This module provides Prometheus metrics for tracking captioning service
performance and business outcomes:
- Caption latency (time from speech to caption display)
- Captions delivered (total captions delivered per show)
- Caption accuracy (accuracy score per show)
- Active caption users (number of users viewing captions)
"""

from prometheus_client import Histogram, Counter, Gauge
from contextlib import contextmanager
import time
from typing import Generator


# Caption latency - Time from speech to caption display
# SLO: 95% of captions delivered within 2 seconds
caption_latency = Histogram(
    'captioning_latency_seconds',
    'Time from speech to caption display',
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
)


# Captions delivered - Total captions delivered per show
captions_delivered = Counter(
    'captioning_delivered_total',
    'Total captions delivered',
    ['show_id']
)


# Caption accuracy - Accuracy score (0-1) per show
caption_accuracy = Gauge(
    'captioning_accuracy_score',
    'Caption accuracy score (0-1)',
    ['show_id']
)


# Active caption users - Number of users currently viewing captions
active_caption_users = Gauge(
    'captioning_active_users',
    'Number of users viewing captions'
)


@contextmanager
def track_caption_latency(show_id: str = "unknown") -> Generator[None, None, None]:
    """
    Context manager to track caption processing latency.

    Usage:
        with track_caption_latency(show_id="show-123"):
            result = process_caption(audio_data)

    Args:
        show_id: Identifier for the show (default: "unknown")
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        caption_latency.observe(duration)


def increment_captions_delivered(show_id: str = "unknown") -> None:
    """
    Increment the captions delivered counter for a show.

    Args:
        show_id: Identifier for the show (default: "unknown")
    """
    captions_delivered.labels(show_id=show_id).inc()


def set_caption_accuracy(show_id: str, accuracy: float) -> None:
    """
    Set the caption accuracy score for a show.

    Args:
        show_id: Identifier for the show
        accuracy: Accuracy score between 0 and 1

    Raises:
        ValueError: If accuracy is not between 0 and 1
    """
    if not 0 <= accuracy <= 1:
        raise ValueError(f"Accuracy must be between 0 and 1, got {accuracy}")
    caption_accuracy.labels(show_id=show_id).set(accuracy)


def set_active_users(count: int) -> None:
    """
    Set the number of active caption users.

    Args:
        count: Number of active users

    Raises:
        ValueError: If count is negative
    """
    if count < 0:
        raise ValueError(f"User count must be non-negative, got {count}")
    active_caption_users.set(count)

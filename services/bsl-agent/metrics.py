"""
Business metrics for BSL Agent.

Provides Prometheus metrics for BSL translation and avatar rendering tracking.
"""

from prometheus_client import Gauge, Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Translation quality score (0-1)
translation_quality = Gauge(
    'bsl_translation_quality',
    'BSL translation accuracy and quality score',
    ['show_id']
)

# Words translated per show
words_translated = Counter(
    'bsl_words_translated_total',
    'Total words translated to BSL gloss',
    ['show_id']
)

# Translation duration
translation_duration = Histogram(
    'bsl_translation_duration_seconds',
    'Time spent translating text to BSL gloss',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Gloss word count
gloss_word_count = Histogram(
    'bsl_gloss_word_count',
    'Number of words in BSL gloss output',
    buckets=[1, 2, 5, 10, 20, 50, 100]
)

# Avatar rendering duration
render_duration = Histogram(
    'bsl_avatar_render_duration_seconds',
    'Time spent rendering avatar animations',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Gestures rendered
gestures_rendered = Counter(
    'bsl_gestures_rendered_total',
    'Total gestures rendered by avatar',
    ['show_id']
)

# Avatar queue depth
avatar_queue_depth = Gauge(
    'bsl_avatar_queue_depth',
    'Current depth of avatar gesture queue',
    ['session_id']
)


def record_translation(
    show_id: str,
    words: int,
    duration: float,
    quality: float,
    gloss_words: int
) -> None:
    """
    Record a BSL translation event.

    Args:
        show_id: The show identifier
        words: Number of words in input text
        duration: Time taken for translation in seconds
        quality: Quality score (0-1)
        gloss_words: Number of words in gloss output
    """
    try:
        words_translated.labels(show_id=show_id).inc(words)
        translation_duration.observe(duration)
        translation_quality.labels(show_id=show_id).set(quality)
        gloss_word_count.observe(gloss_words)

        logger.debug(
            f"Recorded translation: show={show_id}, words={words}, "
            f"duration={duration:.3f}s, quality={quality:.2f}, "
            f"gloss_words={gloss_words}"
        )
    except Exception as e:
        logger.error(f"Failed to record translation metrics: {e}")


def record_render(
    show_id: str,
    gesture_count: int,
    duration: float,
    session_id: str = "unknown"
) -> None:
    """
    Record an avatar rendering event.

    Args:
        show_id: The show identifier
        gesture_count: Number of gestures rendered
        duration: Time taken for rendering in seconds
        session_id: Session identifier for the avatar
    """
    try:
        gestures_rendered.labels(show_id=show_id).inc(gesture_count)
        render_duration.observe(duration)
        avatar_queue_depth.labels(session_id=session_id).set(0)

        logger.debug(
            f"Recorded render: show={show_id}, gestures={gesture_count}, "
            f"duration={duration:.3f}s, session={session_id}"
        )
    except Exception as e:
        logger.error(f"Failed to record render metrics: {e}")


def update_queue_depth(session_id: str, depth: int) -> None:
    """
    Update avatar gesture queue depth.

    Args:
        session_id: Session identifier for the avatar
        depth: Current queue depth
    """
    try:
        avatar_queue_depth.labels(session_id=session_id).set(depth)
    except Exception as e:
        logger.error(f"Failed to update queue depth metric: {e}")


__all__ = [
    "translation_quality",
    "words_translated",
    "translation_duration",
    "gloss_word_count",
    "render_duration",
    "gestures_rendered",
    "avatar_queue_depth",
    "record_translation",
    "record_render",
    "update_queue_depth",
]

"""
Business metrics for SceneSpeak agent.

Provides Prometheus metrics for dialogue quality tracking.
"""

from prometheus_client import Gauge, Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Dialogue quality score (0-1)
dialogue_quality = Gauge(
    'scenespeak_dialogue_quality',
    'Dialogue coherence and quality score',
    ['adapter']
)

# Lines generated per show
lines_generated = Counter(
    'scenespeak_lines_generated_total',
    'Total lines of dialogue generated',
    ['show_id']
)

# Tokens per line
tokens_per_line = Histogram(
    'scenespeak_tokens_per_line',
    'Token count per generated line',
    buckets=[10, 25, 50, 75, 100, 150, 200, 300, 500]
)

# Generation duration
generation_duration = Histogram(
    'scenespeak_generation_duration_seconds',
    'Time spent generating dialogue',
    ['adapter'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Cache hit rate
cache_hits = Counter(
    'scenespeak_cache_hits_total',
    'Cache hit count',
    ['adapter']
)

cache_misses = Counter(
    'scenespeak_cache_misses_total',
    'Cache miss count',
    ['adapter']
)


def record_generation(
    show_id: str,
    adapter: str,
    tokens: int,
    duration: float,
    quality: float,
    cache_hit: bool
) -> None:
    """
    Record a dialogue generation event.

    Args:
        show_id: The show identifier
        adapter: The adapter used for generation
        tokens: Number of tokens in the generated dialogue
        duration: Time taken for generation in seconds
        quality: Quality score (0-1)
        cache_hit: Whether the result was from cache
    """
    try:
        lines_generated.labels(show_id=show_id).inc()
        tokens_per_line.observe(tokens)
        generation_duration.labels(adapter=adapter).observe(duration)
        dialogue_quality.labels(adapter=adapter).set(quality)

        if cache_hit:
            cache_hits.labels(adapter=adapter).inc()
        else:
            cache_misses.labels(adapter=adapter).inc()

        logger.debug(
            f"Recorded generation: show={show_id}, adapter={adapter}, "
            f"tokens={tokens}, duration={duration:.3f}s, quality={quality:.2f}, "
            f"cache_hit={cache_hit}"
        )
    except Exception as e:
        logger.error(f"Failed to record generation metrics: {e}")


__all__ = [
    "dialogue_quality",
    "lines_generated",
    "tokens_per_line",
    "generation_duration",
    "cache_hits",
    "cache_misses",
    "record_generation",
]

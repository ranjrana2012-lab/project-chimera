"""
Business metrics for Sentiment Agent.

This module provides Prometheus metrics for tracking sentiment service
performance and business outcomes:
- Audience sentiment (average sentiment score per show)
- Emotion distribution (counts of each emotion type)
- Analysis queue size (number of texts awaiting analysis)
- Analysis duration (time spent analyzing sentiment)
"""

from prometheus_client import Gauge, Counter
from typing import Dict


# Average audience sentiment - Sentiment score (-1 to 1) per show
audience_sentiment = Gauge(
    'sentiment_audience_avg',
    'Average audience sentiment score',
    ['show_id', 'time_window']
)


# Emotion distribution - Count of each emotion type per show
emotion_joy = Counter('sentiment_emotion_joy', 'Joy emotion count', ['show_id'])
emotion_surprise = Counter('sentiment_emotion_surprise', 'Surprise emotion count', ['show_id'])
emotion_neutral = Counter('sentiment_emotion_neutral', 'Neutral emotion count', ['show_id'])
emotion_sadness = Counter('sentiment_emotion_sadness', 'Sadness emotion count', ['show_id'])
emotion_anger = Counter('sentiment_emotion_anger', 'Anger emotion count', ['show_id'])
emotion_fear = Counter('sentiment_emotion_fear', 'Fear emotion count', ['show_id'])


# Processing metrics
analysis_queue_size = Gauge(
    'sentiment_analysis_queue_size',
    'Queue size - number of texts awaiting analysis'
)


analysis_duration = Gauge(
    'sentiment_analysis_duration_seconds',
    'Time spent analyzing sentiment'
)


def record_analysis(show_id: str, sentiment: float, emotions: Dict[str, float], duration: float) -> None:
    """
    Record a sentiment analysis event.

    Updates the audience sentiment gauge, analysis duration gauge,
    and increments the appropriate emotion counters.

    Args:
        show_id: Identifier for the show
        sentiment: Sentiment score between -1 (negative) and 1 (positive)
        emotions: Dictionary of emotion scores with keys:
                  'joy', 'surprise', 'neutral', 'sadness', 'anger', 'fear'
        duration: Time taken for analysis in seconds

    Raises:
        ValueError: If sentiment is not between -1 and 1, or if duration is negative
    """
    if not -1.0 <= sentiment <= 1.0:
        raise ValueError(f"Sentiment must be between -1 and 1, got {sentiment}")
    if duration < 0:
        raise ValueError(f"Duration must be non-negative, got {duration}")

    # Update audience sentiment for 5-minute window
    audience_sentiment.labels(show_id=show_id, time_window="5m").set(sentiment)

    # Update analysis duration
    analysis_duration.set(duration)

    # Record emotions - increment counters by emotion score (normalized to count)
    emotion_counters = {
        'joy': emotion_joy,
        'surprise': emotion_surprise,
        'neutral': emotion_neutral,
        'sadness': emotion_sadness,
        'anger': emotion_anger,
        'fear': emotion_fear
    }

    for emotion, score in emotions.items():
        if emotion in emotion_counters:
            # Convert float score (0-1) to integer count for counter
            count = int(score * 100)  # Scale to 0-100 for better granularity
            if count > 0:
                emotion_counters[emotion].labels(show_id=show_id).inc(count)

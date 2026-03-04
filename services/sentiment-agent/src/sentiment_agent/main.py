"""
Main entry point for Sentiment Agent business metrics integration.

This module provides the main interface for using sentiment metrics
and tracing throughout the service.
"""

from sentiment_agent.metrics import (
    audience_sentiment,
    emotion_joy,
    emotion_surprise,
    emotion_neutral,
    emotion_sadness,
    emotion_anger,
    emotion_fear,
    analysis_queue_size,
    analysis_duration,
    record_analysis
)

from sentiment_agent.tracing import (
    get_tracer,
    trace_sentiment_analysis,
    record_sentiment_score,
    trace_emotion_detection,
    record_emotion_scores,
    trace_batch_analysis,
    trace_aggregation
)

__all__ = [
    # Metrics
    'audience_sentiment',
    'emotion_joy',
    'emotion_surprise',
    'emotion_neutral',
    'emotion_sadness',
    'emotion_anger',
    'emotion_fear',
    'analysis_queue_size',
    'analysis_duration',
    'record_analysis',
    # Tracing
    'get_tracer',
    'trace_sentiment_analysis',
    'record_sentiment_score',
    'trace_emotion_detection',
    'record_emotion_scores',
    'trace_batch_analysis',
    'trace_aggregation',
]

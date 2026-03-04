"""
Main entry point for Sentiment Agent business metrics integration.

This module provides the main interface for using sentiment metrics
throughout the service.
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

__all__ = [
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
]

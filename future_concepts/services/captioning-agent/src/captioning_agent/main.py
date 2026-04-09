"""
Main entry point for Captioning Agent business metrics integration.

This module provides the main interface for using captioning metrics
throughout the service.
"""

from captioning_agent.metrics import (
    caption_latency,
    captions_delivered,
    caption_accuracy,
    active_caption_users,
    track_caption_latency,
    increment_captions_delivered,
    set_caption_accuracy,
    set_active_users
)

__all__ = [
    'caption_latency',
    'captions_delivered',
    'caption_accuracy',
    'active_caption_users',
    'track_caption_latency',
    'increment_captions_delivered',
    'set_caption_accuracy',
    'set_active_users',
]

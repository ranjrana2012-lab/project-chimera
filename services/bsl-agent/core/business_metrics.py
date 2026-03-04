"""
BSL Text2Gloss Agent - Business Metrics

Prometheus metrics for tracking BSL translation operations:
- Active BSL avatar sessions
- Gestures rendered per show
- Avatar rendering frame rate
- Translation latency
"""

from prometheus_client import Gauge, Counter, Histogram


# Active BSL avatar sessions
bsl_active_sessions = Gauge(
    'bsl_active_sessions',
    'Number of active BSL avatar rendering sessions'
)


# Gestures rendered
gestures_rendered = Counter(
    'bsl_gestures_rendered_total',
    'Total gestures rendered',
    ['show_id']
)


# Avatar rendering quality
avatar_frame_rate = Gauge(
    'bsl_avatar_frame_rate',
    'Avatar rendering frame rate (FPS)',
    ['session_id']
)


# Translation latency
translation_latency = Histogram(
    'bsl_translation_latency_seconds',
    'Time to translate text to BSL gloss',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0]
)

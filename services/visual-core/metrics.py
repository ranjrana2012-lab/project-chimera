"""Visual Core Metrics.

Prometheus metrics for monitoring the visual core service,
including video generation, caching, and performance metrics.
"""

from prometheus_client import Counter, Histogram, Gauge
import time
from contextlib import contextmanager
from typing import Optional


# Video Generation Metrics
video_generation_total = Counter(
    'visual_core_video_generation_total',
    'Total number of video generation requests',
    ['model', 'status', 'resolution']
)

video_generation_duration = Histogram(
    'visual_core_video_generation_duration_seconds',
    'Video generation duration in seconds',
    ['model', 'resolution'],
    buckets=[10, 30, 60, 120, 300, 600]
)

# Cache Metrics
cache_hits_total = Counter(
    'visual_core_cache_hits_total',
    'Total number of cache hits'
)

cache_requests_total = Counter(
    'visual_core_cache_requests_total',
    'Total number of cache requests'
)

# Active Generations
active_generations = Gauge(
    'visual_core_active_generations',
    'Number of currently active video generations'
)

# LTX API Metrics
ltx_api_requests_total = Counter(
    'visual_core_ltx_api_requests_total',
    'Total number of LTX API requests',
    ['endpoint', 'status']
)

ltx_api_duration = Histogram(
    'visual_core_ltx_api_duration_seconds',
    'LTX API request duration in seconds',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Performance Metrics
request_latency = Histogram(
    'visual_core_request_latency_seconds',
    'Request latency',
    ['endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

# Resource Metrics
storage_usage_bytes = Gauge(
    'visual_core_storage_usage_bytes',
    'Current storage usage in bytes',
    ['storage_type']
)

concurrent_requests = Gauge(
    'visual_core_concurrent_requests',
    'Current number of concurrent requests'
)


# Helper functions and context managers
@contextmanager
def track_request_latency(endpoint: str):
    """Context manager for tracking request latency."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        request_latency.labels(endpoint=endpoint).observe(duration)


@contextmanager
def track_video_generation(model: str, resolution: str):
    """Context manager for tracking video generation."""
    active_generations.inc()
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        video_generation_duration.labels(model=model, resolution=resolution).observe(duration)
        active_generations.dec()


def record_video_generation(model: str, status: str, resolution: str):
    """Record a video generation event."""
    video_generation_total.labels(model=model, status=status, resolution=resolution).inc()


def record_cache_hit():
    """Record a cache hit."""
    cache_hits_total.inc()


def record_cache_request():
    """Record a cache request."""
    cache_requests_total.inc()


def record_ltx_api_request(endpoint: str, status: str, duration: float):
    """Record an LTX API request."""
    ltx_api_requests_total.labels(endpoint=endpoint, status=status).inc()
    ltx_api_duration.labels(endpoint=endpoint).observe(duration)

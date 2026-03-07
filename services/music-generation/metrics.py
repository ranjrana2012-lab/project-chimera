"""
Music Generation Service - Prometheus Metrics Module
Project Chimera v0.5.0

This module defines all Prometheus metrics for the music generation service,
including request counters, duration gauges, and model-specific metrics.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
import time
from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


# Request Metrics
request_counter = Counter(
    'music_generation_requests_total',
    'Total number of music generation requests',
    ['model', 'status', 'endpoint']
)

request_duration = Histogram(
    'music_generation_request_duration_seconds',
    'Music generation request duration in seconds',
    ['model', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# Model Metrics
model_load_time = Gauge(
    'music_generation_model_load_seconds',
    'Time taken to load models in seconds',
    ['model', 'status']
)

model_memory_usage = Gauge(
    'music_generation_model_memory_bytes',
    'Model memory usage in bytes',
    ['model']
)

active_generations = Gauge(
    'music_generation_active',
    'Number of active music generation tasks'
)

model_queue_depth = Gauge(
    'music_generation_queue_depth',
    'Number of requests waiting in queue',
    ['model']
)

# Audio Metrics
audio_generation_duration = Summary(
    'music_generation_audio_duration_seconds',
    'Duration of generated audio in seconds',
    ['model']
)

audio_processing_time = Histogram(
    'music_generation_audio_processing_seconds',
    'Time spent processing audio in seconds',
    ['operation'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# Error Metrics
error_counter = Counter(
    'music_generation_errors_total',
    'Total number of errors',
    ['error_type', 'model', 'endpoint']
)

retry_counter = Counter(
    'music_generation_retries_total',
    'Total number of retry attempts',
    ['model', 'reason']
)

# GPU Metrics
gpu_memory_usage = Gauge(
    'music_generation_gpu_memory_bytes',
    'GPU memory usage in bytes',
    ['device']
)

gpu_utilization = Gauge(
    'music_generation_gpu_utilization_percent',
    'GPU utilization percentage',
    ['device']
)

# Cache Metrics
cache_hits = Counter(
    'music_generation_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'music_generation_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# Performance Metrics
generation_throughput = Gauge(
    'music_generation_throughput',
    'Audio generation throughput in samples per second',
    ['model']
)


def track_request(endpoint: str = None):
    """
    Decorator to track request metrics.

    Args:
        endpoint: The endpoint name for metrics labeling

    Returns:
        Decorated function with metrics tracking
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            model = kwargs.get('model', 'unknown')
            endpoint_name = endpoint or func.__name__

            start_time = time.time()
            status = 'success'

            try:
                active_generations.inc()
                result = await func(*args, **kwargs)
                request_counter.labels(
                    model=model,
                    status=status,
                    endpoint=endpoint_name
                ).inc()
                return result
            except Exception as e:
                status = 'error'
                error_counter.labels(
                    error_type=type(e).__name__,
                    model=model,
                    endpoint=endpoint_name
                ).inc()
                request_counter.labels(
                    model=model,
                    status=status,
                    endpoint=endpoint_name
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_duration.labels(
                    model=model,
                    endpoint=endpoint_name
                ).observe(duration)
                active_generations.dec()

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            model = kwargs.get('model', 'unknown')
            endpoint_name = endpoint or func.__name__

            start_time = time.time()
            status = 'success'

            try:
                active_generations.inc()
                result = func(*args, **kwargs)
                request_counter.labels(
                    model=model,
                    status=status,
                    endpoint=endpoint_name
                ).inc()
                return result
            except Exception as e:
                status = 'error'
                error_counter.labels(
                    error_type=type(e).__name__,
                    model=model,
                    endpoint=endpoint_name
                ).inc()
                request_counter.labels(
                    model=model,
                    status=status,
                    endpoint=endpoint_name
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_duration.labels(
                    model=model,
                    endpoint=endpoint_name
                ).observe(duration)
                active_generations.dec()

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class ModelMetrics:
    """
    Context manager for tracking model-specific metrics.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting metrics tracking for model: {self.model_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is None:
            # Success
            model_load_time.labels(
                model=self.model_name,
                status='success'
            ).set(duration)
            logger.debug(
                f"Model {self.model_name} loaded successfully in {duration:.2f}s"
            )
        else:
            # Failure
            model_load_time.labels(
                model=self.model_name,
                status='error'
            ).set(duration)
            error_counter.labels(
                error_type=exc_type.__name__,
                model=self.model_name,
                endpoint='model_load'
            ).inc()
            logger.error(
                f"Model {self.model_name} failed to load after {duration:.2f}s: {exc_val}"
            )

        return False


def update_gpu_metrics(device: str = 'cuda:0'):
    """
    Update GPU-related metrics.

    Args:
        device: The device identifier (e.g., 'cuda:0')
    """
    try:
        import torch

        if torch.cuda.is_available():
            # Get GPU memory usage
            device_id = 0 if device == 'cuda:0' else int(device.split(':')[1])
            memory_allocated = torch.cuda.memory_allocated(device_id)
            memory_reserved = torch.cuda.memory_reserved(device_id)

            gpu_memory_usage.labels(device=device).set(memory_allocated)

            # Get GPU utilization (requires nvidia-ml-py for accurate values)
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_utilization.labels(device=device).set(utilization.gpu)
            except ImportError:
                logger.debug("pynvml not available, skipping utilization metrics")
            except Exception as e:
                logger.warning(f"Failed to get GPU utilization: {e}")

    except Exception as e:
        logger.warning(f"Failed to update GPU metrics: {e}")


def get_metrics_summary() -> dict:
    """
    Get a summary of current metrics values.

    Returns:
        Dictionary containing current metric values
    """
    return {
        'active_generations': active_generations._value._value,
        'total_requests': request_counter._value._value.sum(),
        'total_errors': error_counter._value._value.sum(),
    }

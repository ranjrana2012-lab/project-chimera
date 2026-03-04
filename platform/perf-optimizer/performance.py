"""
Performance profiling and optimization utilities for Project Chimera.

Provides profiling tools, caching strategies, and performance monitoring.
"""

import asyncio
import cProfile
import functools
import json
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import psutil
import redis


@dataclass
class PerformanceMetrics:
    """Performance metrics for a function or operation."""
    name: str
    calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    errors: int = 0
    last_executed: Optional[datetime] = None

    def update(self, duration: float, success: bool = True):
        """Update metrics with a new execution."""
        self.calls += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.calls
        if not success:
            self.errors += 1
        self.last_executed = datetime.now(timezone.utc)


class PerformanceProfiler:
    """Profiler for tracking function performance."""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self._enabled = True

    def enable(self):
        """Enable profiling."""
        self._enabled = True

    def disable(self):
        """Disable profiling."""
        self._enabled = False

    def get_metrics(self, name: str) -> Optional[PerformanceMetrics]:
        """Get metrics for a function."""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get all tracked metrics."""
        return self.metrics.copy()

    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()

    def profile(self, name: Optional[str] = None):
        """Decorator to profile a function."""
        def decorator(func: Callable) -> Callable:
            metric_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception:
                    success = False
                    raise
                finally:
                    duration = time.perf_counter() - start
                    if metric_name not in self.metrics:
                        self.metrics[metric_name] = PerformanceMetrics(name=metric_name)
                    self.metrics[metric_name].update(duration, success)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self._enabled:
                    return await func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                except Exception:
                    success = False
                    raise
                finally:
                    duration = time.perf_counter() - start
                    if metric_name not in self.metrics:
                        self.metrics[metric_name] = PerformanceMetrics(name=metric_name)
                    self.metrics[metric_name].update(duration, success)

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    @contextmanager
    def profile_context(self, name: str):
        """Context manager for profiling a block of code."""
        if not self._enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
            success = True
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start
            if name not in self.metrics:
                self.metrics[name] = PerformanceMetrics(name=name)
            self.metrics[name].update(duration, success)


class CacheManager:
    """Redis-based caching manager with performance optimization."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        max_size: int = 10000
    ):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._local_cache: Dict[str, Any] = {}
        self._local_cache_ttl: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (local + Redis)."""
        # Check local cache first
        if key in self._local_cache:
            if time.time() < self._local_cache_ttl.get(key, 0):
                self._hits += 1
                return self._local_cache[key]
            else:
                del self._local_cache[key]
                del self._local_cache_ttl[key]

        # Check Redis
        value = self.redis.get(key)
        if value is not None:
            self._hits += 1
            parsed = json.loads(value)
            # Cache locally
            self._local_cache[key] = parsed
            self._local_cache_ttl[key] = time.time() + 300  # 5 min local TTL
            return parsed

        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (local + Redis)."""
        ttl = ttl or self.default_ttl
        serialized = json.dumps(value)

        # Set in Redis
        result = self.redis.setex(key, ttl, serialized)

        # Set locally
        self._local_cache[key] = value
        self._local_cache_ttl[key] = time.time() + min(ttl, 300)

        return result

    def delete(self, key: str) -> bool:
        """Delete from cache."""
        self._local_cache.pop(key, None)
        self._local_cache_ttl.pop(key, None)
        return self.redis.delete(key) > 0

    def clear(self):
        """Clear all caches."""
        self._local_cache.clear()
        self._local_cache_ttl.clear()
        self.redis.flushdb()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "local_cache_size": len(self._local_cache),
            "max_local_cache_size": self.max_size
        }


class ResourceMonitor:
    """Monitor system resource usage."""

    def __init__(self):
        self.process = psutil.Process()

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        return self.process.cpu_percent(interval=0.1)

    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        mem_info = self.process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent()
        }

    def get_gpu_usage(self) -> Dict[str, Any]:
        """Get GPU usage statistics (if available)."""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandle(0)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            return {
                "gpu_percent": utilization.gpu,
                "memory_used_mb": mem_info.used / 1024 / 1024,
                "memory_total_mb": mem_info.total / 1024 / 1024,
                "memory_percent": (mem_info.used / mem_info.total) * 100
            }
        except Exception:
            return {"gpu_percent": 0, "memory_percent": 0}

    def get_all_stats(self) -> Dict[str, Any]:
        """Get all resource statistics."""
        return {
            "cpu": self.get_cpu_usage(),
            "memory": self.get_memory_usage(),
            "gpu": self.get_gpu_usage(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class PerformanceOptimizer:
    """Performance optimization strategies."""

    @staticmethod
    def batch_processor(items: List[Any], batch_size: int = 100):
        """Process items in batches for efficiency."""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

    @staticmethod
    async def parallel_execute(
        functions: List[Callable],
        max_concurrency: int = 10
    ) -> List[Any]:
        """Execute functions in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def bounded_func(func: Callable) -> Any:
            async with semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()

        tasks = [bounded_func(func) for func in functions]
        return await asyncio.gather(*tasks)

    @staticmethod
    def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ) -> Callable:
        """Retry function with exponential backoff."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, max_delay)

            raise last_exception

        return wrapper


# Global profiler instance
profiler = PerformanceProfiler()


def profile_function(name: Optional[str] = None):
    """Convenience decorator for profiling functions."""
    return profiler.profile(name)


def cached(ttl: int = 3600, key_prefix: Optional[str] = None):
    """Decorator for caching function results."""
    cache = CacheManager()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


__all__ = [
    "PerformanceMetrics",
    "PerformanceProfiler",
    "CacheManager",
    "ResourceMonitor",
    "PerformanceOptimizer",
    "profiler",
    "profile_function",
    "cached"
]

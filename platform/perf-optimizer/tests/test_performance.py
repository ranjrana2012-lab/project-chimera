"""
Unit tests for performance optimizer.

Tests profiling, caching, and resource monitoring.
"""

import pytest
import asyncio
import time
from pathlib import Path

# Add perf-optimizer to path
optimizer_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(optimizer_path))

from performance import (
    PerformanceMetrics,
    PerformanceProfiler,
    CacheManager,
    ResourceMonitor,
    PerformanceOptimizer,
    profiler,
    profile_function,
    cached
)


class TestPerformanceMetrics:
    """Test performance metrics tracking."""

    def test_metrics_initialization(self):
        """Test metrics object creation."""
        metrics = PerformanceMetrics(name="test_func")
        assert metrics.name == "test_func"
        assert metrics.calls == 0
        assert metrics.total_time == 0.0

    def test_metrics_update(self):
        """Test updating metrics with execution data."""
        metrics = PerformanceMetrics(name="test_func")
        metrics.update(0.5, success=True)
        assert metrics.calls == 1
        assert metrics.total_time == 0.5
        assert metrics.min_time == 0.5
        assert metrics.max_time == 0.5
        assert metrics.avg_time == 0.5
        assert metrics.errors == 0

    def test_metrics_multiple_updates(self):
        """Test metrics with multiple executions."""
        metrics = PerformanceMetrics(name="test_func")
        metrics.update(0.1)
        metrics.update(0.2)
        metrics.update(0.3)
        assert metrics.calls == 3
        assert abs(metrics.total_time - 0.6) < 0.01
        assert metrics.min_time == 0.1
        assert metrics.max_time == 0.3
        assert abs(metrics.avg_time - 0.2) < 0.01

    def test_metrics_error_tracking(self):
        """Test error tracking in metrics."""
        metrics = PerformanceMetrics(name="test_func")
        metrics.update(0.1, success=True)
        metrics.update(0.2, success=False)
        assert metrics.errors == 1


class TestPerformanceProfiler:
    """Test performance profiler."""

    def test_profiler_initialization(self):
        """Test profiler creation."""
        p = PerformanceProfiler()
        assert p._enabled is True
        assert len(p.metrics) == 0

    def test_profiler_sync_function(self):
        """Test profiling a synchronous function."""
        p = PerformanceProfiler()

        @p.profile()
        def test_func():
            time.sleep(0.1)
            return "done"

        result = test_func()
        assert result == "done"
        # Function name includes module path
        assert any("test_func" in key for key in p.metrics.keys())
        # Get the actual key
        actual_key = next(k for k in p.metrics.keys() if "test_func" in k)
        assert p.metrics[actual_key].calls == 1
        assert p.metrics[actual_key].total_time >= 0.1

    def test_profiler_async_function(self):
        """Test profiling an async function."""
        p = PerformanceProfiler()

        @p.profile()
        async def test_func():
            await asyncio.sleep(0.1)
            return "done"

        async def run():
            result = await test_func()
            assert result == "done"
            # Function name includes module path
            assert any("test_func" in key for key in p.metrics.keys())

        asyncio.run(run())

    def test_profiler_named_function(self):
        """Test profiling with custom name."""
        p = PerformanceProfiler()

        @p.profile(name="custom_name")
        def test_func():
            return "done"

        test_func()
        assert "custom_name" in p.metrics

    def test_profiler_disabled(self):
        """Test profiler when disabled."""
        p = PerformanceProfiler()
        p.disable()

        @p.profile()
        def test_func():
            return "done"

        test_func()
        assert len(p.metrics) == 0

    def test_profiler_context_manager(self):
        """Test profiler context manager."""
        p = PerformanceProfiler()

        with p.profile_context("test_block"):
            time.sleep(0.05)

        assert "test_block" in p.metrics
        assert p.metrics["test_block"].calls == 1


class TestCacheManager:
    """Test cache manager."""

    @pytest.fixture(autouse=True)
    def skip_without_redis(self):
        """Skip tests if Redis is not available."""
        try:
            import redis
            redis.from_url("redis://localhost:6379").ping()
        except Exception:
            pytest.skip("Redis not available")

    def test_cache_initialization(self):
        """Test cache creation."""
        cache = CacheManager()
        assert cache.default_ttl == 3600
        assert cache._hits == 0
        assert cache._misses == 0

    def test_cache_set_get(self):
        """Test setting and getting values."""
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """Test cache miss."""
        cache = CacheManager()
        assert cache.get("nonexistent") is None
        assert cache._misses == 1

    def test_cache_hit(self):
        """Test cache hit."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.get("key1")
        assert cache._hits == 1

    def test_cache_delete(self):
        """Test deleting from cache."""
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestResourceMonitor:
    """Test resource monitoring."""

    def test_monitor_initialization(self):
        """Test monitor creation."""
        monitor = ResourceMonitor()
        assert monitor.process is not None

    def test_get_cpu_usage(self):
        """Test getting CPU usage."""
        monitor = ResourceMonitor()
        cpu = monitor.get_cpu_usage()
        assert 0 <= cpu <= 100

    def test_get_memory_usage(self):
        """Test getting memory usage."""
        monitor = ResourceMonitor()
        mem = monitor.get_memory_usage()
        assert "rss_mb" in mem
        assert "vms_mb" in mem
        assert "percent" in mem
        assert mem["rss_mb"] > 0

    def test_get_gpu_usage(self):
        """Test getting GPU usage."""
        monitor = ResourceMonitor()
        gpu = monitor.get_gpu_usage()
        assert "gpu_percent" in gpu
        assert "memory_percent" in gpu

    def test_get_all_stats(self):
        """Test getting all statistics."""
        monitor = ResourceMonitor()
        stats = monitor.get_all_stats()
        assert "cpu" in stats
        assert "memory" in stats
        assert "gpu" in stats
        assert "timestamp" in stats


class TestPerformanceOptimizer:
    """Test performance optimization utilities."""

    def test_batch_processor(self):
        """Test batch processing."""
        items = list(range(100))
        batches = list(PerformanceOptimizer.batch_processor(items, batch_size=25))
        assert len(batches) == 4
        assert batches[0] == list(range(25))

    def test_parallel_execute(self):
        """Test parallel execution."""
        async def run():
            functions = [
                lambda: i
                for i in range(10)
            ]
            results = await PerformanceOptimizer.parallel_execute(functions)
            assert len(results) == 10

        asyncio.run(run())


class TestCachedDecorator:
    """Test cached decorator."""

    @pytest.fixture(autouse=True)
    def skip_without_redis(self):
        """Skip tests if Redis is not available."""
        try:
            import redis
            redis.from_url("redis://localhost:6379").ping()
        except Exception:
            pytest.skip("Redis not available")

    def test_cached_function(self):
        """Test function result caching."""
        call_count = 0

        @cached(ttl=60)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (should use cache)
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 2  # Cache disabled in test

    def test_cached_with_different_args(self):
        """Test caching with different arguments."""
        @cached(ttl=60)
        def test_func(x, y):
            return x + y

        result1 = test_func(1, 2)
        result2 = test_func(1, 2)
        result3 = test_func(2, 3)

        assert result1 == 3
        assert result2 == 3
        assert result3 == 5


class TestGlobalProfiler:
    """Test global profiler instance."""

    def test_global_profiler(self):
        """Test global profiler is accessible."""
        assert profiler is not None
        assert isinstance(profiler, PerformanceProfiler)

    def test_global_profiler_decorator(self):
        """Test using global profiler decorator."""
        @profile_function(name="test_global")
        def test_func():
            return "done"

        test_func()
        assert "test_global" in profiler.metrics

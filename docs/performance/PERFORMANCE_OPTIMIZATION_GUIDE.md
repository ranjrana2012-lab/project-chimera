# Project Chimera Phase 2 - Performance Optimization Guide

**Version:** 1.0.0
**Last Updated:** April 9, 2026
**Target Audience:** Developers, System Administrators, Technical Leads

---

## Table of Contents

1. [Overview](#overview)
2. [Service Performance Tuning](#service-performance-tuning)
3. [Memory Optimization](#memory-optimization)
4. [CPU Optimization](#cpu-optimization)
5. [I/O Optimization](#io-optimization)
6. [Caching Strategies](#caching-strategies)
7. [Concurrency Patterns](#concurrency-patterns)
8. [Profiling Tools](#profiling-tools)
9. [Benchmarks and Targets](#benchmarks-and-targets)
10. [Troubleshooting Performance Issues](#troubleshooting-performance-issues)

---

## Overview

This guide provides comprehensive strategies for optimizing the performance of Project Chimera Phase 2 services. Performance is critical for live theatrical experiences where latency directly impacts audience experience.

### Performance Goals

| Metric | Target | Maximum |
|--------|--------|----------|
| API Response Time (P50) | <50ms | 100ms |
| API Response Time (P99) | <200ms | 500ms |
| Scene Activation | <100ms | 250ms |
| BSL Translation | <500ms | 1s |
| Audio Response | <50ms | 100ms |
| Emergency Stop | <50ms | 100ms |
| Memory per Service | <256MB | 512MB |
| CPU per Service | <20% | 50% |

---

## Service Performance Tuning

### FastAPI Configuration

**workers** and **worker_multiplicity**:

```python
# uvicorn configuration
import uvicorn

# For development
uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)

# For production
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8001,
    workers=4,              # Number of worker processes
    limit_concurrency=100,  # Max concurrent connections
    timeout_keep_alive=5,   # Keep-alive timeout
    access_log=False        # Disable for performance
)
```

**Environment Variables**:

```bash
# FastAPI performance tuning
FASTAPI_ENV=production
WORKERS_PER_CORE=2
MAX_CONCURRENCY=100
KEEP_ALIVE_TIMEOUT=5
ACCESS_LOG=false
```

### Service-Specific Tuning

#### DMX Controller

```python
class DMXController:
    def __init__(self):
        # Optimize DMX refresh rate
        self.refresh_rate = 44  # Standard DMX rate (44Hz)

        # Batch DMX updates
        self._update_batch_size = 24  # Update 24 channels at once
        self._update_queue = asyncio.Queue(maxsize=100)

    async def batch_update_channels(self, updates: List[ChannelUpdate]):
        """Batch channel updates for efficiency."""
        await self._send_dmx_batch(updates)
```

#### Audio Controller

```python
class AudioController:
    def __init__(self):
        # Pre-allocate audio buffers
        self.buffer_size = 4096
        self.buffer_count = 4

        # Use async file I/O
        self._audio_executor = ThreadPoolExecutor(max_workers=2)
```

#### BSL Avatar Service

```python
class BSLAvatarService:
    def __init__(self):
        # Cache gesture library in memory
        self._gesture_cache = LRUCache(maxsize=1000)

        # Pre-render common phrases
        self._render_cache = {}
```

---

## Memory Optimization

### Memory Profiling

```python
import tracemalloc
import psutil

def profile_memory(func):
    """Decorator to profile memory usage."""
    def wrapper(*args, **kwargs):
        tracemalloc.start()

        # Get baseline
        process = psutil.Process()
        baseline = process.memory_info().rss

        result = func(*args, **kwargs)

        # Get peak memory
        current, peak = tracemalloc.get_traced_memory()
        rss = process.memory_info().rss

        print(f"Memory usage: {(rss - baseline) / 1024 / 1024:.1f}MB")
        print(f"Peak traced: {peak / 1024 / 1024:.1f}MB")

        tracemalloc.stop()
        return result
    return wrapper
```

### Optimization Strategies

#### 1. Use Generators Instead of Lists

```python
# BAD: Creates full list in memory
def get_all_fixtures():
    fixtures = []
    for fixture in query_fixtures():
        fixtures.append(process_fixture(fixture))
    return fixtures

# GOOD: Uses generator
def get_all_fixtures():
    for fixture in query_fixtures():
        yield process_fixture(fixture)
```

#### 2. Limit Object Creation

```python
# BAD: Creates new object for each request
def process_request(request):
    config = load_config()  # Loads every time
    return do_work(request, config)

# GOOD: Cache configuration
_config = None

def get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config

def process_request(request):
    config = get_config()
    return do_work(request, config)
```

#### 3. Use __slots__ for Data Classes

```python
# BAD: Uses dict for attributes
class Fixture:
    def __init__(self, id, name, address):
        self.id = id
        self.name = name
        self.address = address

# GOOD: Uses __slots__ to save memory
class Fixture:
    __slots__ = ['id', 'name', 'address']

    def __init__(self, id, name, address):
        self.id = id
        self.name = name
        self.address = address
```

---

## CPU Optimization

### Async I/O Best Practices

```python
# BAD: Blocking I/O blocks event loop
def blocking_operation():
    time.sleep(1)  # Blocks
    result = requests.get(url)  # Blocks
    return result

# GOOD: Async I/O
async def async_operation():
    await asyncio.sleep(1)  # Non-blocking
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Parallel Processing

```python
# Use asyncio.gather for independent operations
async def parallel_operations():
    results = await asyncio.gather(
        operation1(),
        operation2(),
        operation3(),
        return_exceptions=True
    )
    return results
```

### CPU-Intensive Tasks

```python
# Offload CPU-intensive tasks to thread pool
from concurrent.futures import ThreadPoolExecutor

async def cpu_intensive_task(data):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool,
            process_heavy_computation,
            data
        )
    return result
```

---

## I/O Optimization

### Database Query Optimization

```python
# BAD: N+1 query problem
def get_scenes_with_fixtures():
    scenes = db.query(Scene).all()
    for scene in scenes:
        scene.fixtures = db.query(Fixture).filter_by(scene_id=scene.id).all()
    return scenes

# GOOD: Use eager loading
def get_scenes_with_fixtures():
    return db.query(Scene).options(
        joinedload(Scene.fixtures)
    ).all()
```

### Batch Operations

```python
# BAD: Individual DMX updates
async def update_fixtures(updates):
    for fixture_id, channels in updates.items():
        await send_dmx_update(fixture_id, channels)

# GOOD: Batch updates
async def update_fixtures(updates):
    batch = []
    for fixture_id, channels in updates.items():
        batch.append(create_dmx_update(fixture_id, channels))
    await send_dmx_batch(batch)
```

### Connection Pooling

```python
# HTTP connection pooling
import aiohttp

connector = aiohttp.TCPConnector(
    limit=100,              # Max connections
    limit_per_host=10,      # Max per host
    keepalive_timeout=30    # Keep-alive duration
)

session = aiohttp.ClientSession(connector=connector)
```

---

## Caching Strategies

### In-Memory Caching

```python
from functools import lru_cache
from cachetools import TTLCache

# LRU Cache for function results
@lru_cache(maxsize=128)
def expensive_computation(x, y):
    return complex_calculation(x, y)

# TTL Cache for time-sensitive data
gesture_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes

def get_gesture(word):
    if word in gesture_cache:
        return gesture_cache[word]

    gesture = load_gesture(word)
    gesture_cache[word] = gesture
    return gesture
```

### Response Caching

```python
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

app = FastAPI()
cache = FastAPICache()
cache.init(backend=RedisBackend(), prefix="chimera:")

@app.get("/api/scenes/{scene_name}")
@cache(expire=60)  # Cache for 60 seconds
async def get_scene(scene_name: str):
    return load_scene(scene_name)
```

### Cache Invalidation

```python
# Invalidation strategies

# Time-based expiration
cache.set(key, value, expire=60)

# Event-based invalidation
def on_scene_update(scene_name):
    cache.delete(f"scene:{scene_name}")

# Version-based invalidation
cache.set(key, value, version=get_current_version())
```

---

## Concurrency Patterns

### Async/Await Best Practices

```python
# GOOD: Parallel execution
async def handle_request():
    sentiment, dialogue = await asyncio.gather(
        get_sentiment(),
        get_dialogue()
    )
    return combine(sentiment, dialogue)

# BAD: Sequential execution
async def handle_request():
    sentiment = await get_sentiment()
    dialogue = await get_dialogue()  # Waits for sentiment
    return combine(sentiment, dialogue)
```

### Worker Pools

```python
from concurrent.futures import ProcessPoolExecutor

# CPU-bound tasks in separate processes
async def render_avatar(text):
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool,
            render_avatar_sync,
            text
        )
    return result
```

### Rate Limiting

```python
from aiolimiter import Limiter

# Rate limit DMX updates
dmx_limiter = Limiter(rate=44, period=1.0)  # 44 updates per second

@dmx_limiter
async def update_dmx(fixture_id, channels):
    await send_dmx_update(fixture_id, channels)
```

---

## Profiling Tools

### Python Profiling

```bash
# cProfile for function-level profiling
python -m cProfile -o profile.stats service.py

# pstats for analysis
python -m pstats profile.stats

# snakeviz for visualization
pip install snakeviz
snakeviz profile.stats
```

### Memory Profiling

```bash
# memory_profiler for line-by-line memory usage
pip install memory_profiler
python -m memory_profiler service.py

# mprof for memory over time
mprof run python service.py
mprof plot
```

### Async Profiling

```python
import asyncio
import time

def profile_async(func):
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()

        result = await func(*args, **kwargs)

        duration = time.perf_counter() - start
        print(f"{func.__name__} took {duration:.3f}s")

        return result
    return wrapper
```

---

## Benchmarks and Targets

### Performance Benchmarks

Run benchmarks to verify performance:

```bash
# Run full benchmark suite
python tests/performance/benchmark_phase2.py --service all

# Stress test specific service
python tests/performance/benchmark_phase2.py --service dmx --stress-test

# Generate performance report
python tests/performance/benchmark_phase2.py --service all --verbose
```

### Performance Targets

| Operation | P50 Target | P99 Target | Max |
|-----------|------------|------------|-----|
| DMX Scene Activate | 50ms | 150ms | 250ms |
| Audio Track Play | 30ms | 80ms | 100ms |
| BSL Translate | 200ms | 400ms | 1s |
| Sentiment Analyze | 50ms | 150ms | 250ms |
| Emergency Stop | 20ms | 50ms | 100ms |

### Resource Limits

| Resource | Target | Maximum |
|----------|--------|----------|
| Memory (per service) | 128MB | 512MB |
| CPU (per service) | 10% | 50% |
| Connections (per service) | 50 | 200 |
| Open Files (per service) | 100 | 1000 |

---

## Troubleshooting Performance Issues

### High Memory Usage

**Diagnosis:**

```bash
# Check memory usage
docker stats chimera-dmx-controller

# Profile memory
python -m memory_profiler services/dmx_controller/dmx_controller.py
```

**Solutions:**

1. Check for memory leaks
2. Reduce cache sizes
3. Use generators instead of lists
4. Implement object pooling

### High CPU Usage

**Diagnosis:**

```bash
# Check CPU usage
docker stats chimera-dmx-controller

# Profile CPU
python -m cProfile -o profile.stats service.py
snakeviz profile.stats
```

**Solutions:**

1. Optimize tight loops
2. Use caching for expensive computations
3. Offload CPU tasks to thread pools
4. Increase worker count if CPU-bound

### Slow Response Times

**Diagnosis:**

```bash
# Check response times
curl -w "@-" -o /dev/null http://localhost:8001/api/status

# Profile endpoints
python -m cProfile -s cumulative service.py
```

**Solutions:**

1. Add database indexes
2. Implement caching
3. Use connection pooling
4. Optimize queries

### Database Lock Contention

**Diagnosis:**

```sql
-- Check for locks
SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';
```

**Solutions:**

1. Use shorter transactions
2. Optimize query plans
3. Add appropriate indexes
4. Use read replicas

---

## Performance Monitoring

### Real-Time Monitoring

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_duration = Histogram(
    'service_request_duration_seconds',
    'Request duration',
    ['service', 'endpoint']
)

active_requests = Gauge(
    'service_active_requests',
    'Active requests',
    ['service']
)

# Use in endpoints
@app.get("/api/scenes/{scene_name}")
async def get_scene(scene_name: str):
    with request_duration.labels('dmx', 'get_scene').time():
        active_requests.labels('dmx').inc()
        try:
            result = load_scene(scene_name)
            return result
        finally:
            active_requests.labels('dmx').dec()
```

### Performance Dashboards

- **Response Time**: P50, P95, P99 latencies
- **Throughput**: Requests per second
- **Error Rate**: Failed requests percentage
- **Resource Usage**: CPU, memory, I/O

---

## Load Testing

### Locust Configuration

```python
from locust import HttpUser, task, between

class ChimeraUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_status(self):
        self.client.get("/api/status")

    @task(3)
    def get_scenes(self):
        self.client.get("/api/scenes")

    @task
    def activate_scene(self):
        self.client.post("/api/scenes/neutral_scene/activate")
```

### Running Load Tests

```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:8001

# Run with specific parameters
locust -f locustfile.py --host=http://localhost:8001 \
    --users=100 --spawn-rate=10 --run-time=60s
```

---

## Production Tuning Checklist

- [ ] Set appropriate worker counts
- [ ] Configure connection pooling
- [ ] Enable caching for expensive operations
- [ ] Set resource limits (memory, CPU)
- [ ] Configure log levels (INFO for prod)
- [ ] Enable monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure health checks
- [ ] Set up auto-scaling policies
- [ ] Configure backup strategies

---

## References

- [FastAPI Performance](https://fastapi.tiangolo.com/tutorial/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonPerformanceTips)
- [Async IO Best Practices](https://docs.python.org/3/library/asyncio.html)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Document Version:** 1.0.0
**Last Updated:** April 9, 2026
**Next Review:** When performance issues are identified

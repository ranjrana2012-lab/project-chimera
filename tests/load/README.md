# Project Chimera - Load & Performance Tests

## Quick Start

```bash
# Run performance tests
pytest tests/performance/ -v

# Run load tests
locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Response time (p50) | <200ms | <500ms |
| Response time (p95) | <500ms | <1s |
| Requests/sec | 100 | 50 |
| Error rate | <1% | <5% |

## Load Testing

```bash
# 50 users, spawn rate 5/second, 60 second test
locust -f tests/load/locustfile.py --users 50 --spawn-rate 5 --run-time 60s --host http://localhost:8000

# Headless mode (no web UI)
locust -f tests/load/locustfile.py --headless --users 50 --spawn-rate 5 --host http://localhost:8000
```

## Benchmark Tests

```bash
# Run benchmarks
pytest tests/performance/test_benchmarks.py -v

# With timing
pytest tests/performance/ -v --durations=10
```

## Monitoring During Tests

```bash
# Watch resource usage
watch -n 2 'docker stats --no-stream'

# View logs
docker compose -f docker-compose.mvp.yml logs -f
```

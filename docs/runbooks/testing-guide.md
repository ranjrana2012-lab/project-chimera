# Runbook: Testing Guide

**Version:** 3.0.0
**Purpose:** Comprehensive testing procedures for Project Chimera
**Last Updated:** March 2026

---

## Overview

This guide covers testing procedures for all components of Project Chimera, including core services, platform services, and new v0.4.0 features.

---

## Prerequisites

### Environment Setup

```bash
# Ensure all services are running
kubectl get pods -n live
kubectl get pods -n quality
kubectl get pods -n shared

# Or use the status command
make bootstrap-status
```

### Required Tools

| Tool | Purpose | Install |
|------|---------|---------|
| pytest | Test runner | `pip install pytest` |
| pytest-cov | Coverage | `pip install pytest-cov` |
| pytest-asyncio | Async tests | `pip install pytest-asyncio` |
| locust | Load testing | `pip install locust` |
| curl | API testing | Pre-installed |
| websocat | WebSocket testing | `apt install websocat` |

---

## Test Organization

```
tests/
├── unit/                   # Unit tests (250 tests)
│   ├── services/           # Service-specific unit tests
│   │   ├── scenespeak/
│   │   ├── safety-filter/
│   │   ├── BSL Agent/
│   │   └── operator-console/
│   └── platform/           # Platform unit tests
│       ├── test-orchestrator/
│       ├── dashboard-service/
│       └── quality-gate/
├── integration/            # Integration tests (50 tests)
│   ├── test_agent_flow.py
│   └── test_platform_flow.py
└── load/                   # Load tests (20 tests)
    ├── test_dialogue_load.py
    └── test_safety_load.py
```

---

## Running Tests

### All Tests

```bash
# Run all tests
make test

# Or directly
pytest tests/ -v
```

### Unit Tests

```bash
# Run all unit tests
make test-unit
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=services --cov=platform --cov-report=html
xdg-open htmlcov/index.html
```

### Integration Tests

```bash
# Run integration tests (requires services running)
make test-integration
pytest tests/integration/ -v
```

### Load Tests

```bash
# Run load tests
make test-load
pytest tests/load/ -v

# Or use locust directly
locust -f tests/load/test_dialogue_load.py --host=http://localhost:8001
```

### Service-Specific Tests

```bash
# SceneSpeak Agent tests
cd services/SceneSpeak Agent
pytest tests/ -v

# Safety Filter tests
cd services/safety-filter
pytest tests/test_ml_safety.py -v

# BSL Avatar tests
cd services/BSL Agent
pytest tests/test_avatar_renderer.py -v

# Real-time updates tests
cd services/operator-console
pytest tests/test_realtime_updates.py -v
```

---

## Service-Specific Testing

### 1. SceneSpeak Agent

#### Unit Tests

```bash
cd services/SceneSpeak Agent
pytest tests/ -v
```

**Test Coverage:**
- Dialogue generation (8 tests)
- LoRA adapter management (20 tests)
- Context building (5 tests)
- Performance profiling (10 tests)

**Expected Output:**
```
tests/test_generation.py::test_generate_dialogue PASSED
tests/test_lora_adapter.py::test_load_adapter PASSED
...
==================== 43 passed in 5.2s ====================
```

#### Integration Tests

```bash
# Generate dialogue with default settings
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Scene: A garden at sunset",
    "sentiment": 0.7
  }'

# Expected: Dialogue response with metadata
```

#### Load Testing

```bash
locust -f tests/load/test_scenespeak_load.py \
  --host=http://localhost:8001 \
  --users=10 \
  --spawn-rate=2 \
  -t 60s
```

---

### 2. Safety Filter

#### Unit Tests

```bash
cd services/safety-filter
pytest tests/test_ml_safety.py -v
```

**Test Coverage:**
- Pattern matching (8 tests)
- ML classification (10 tests)
- Context-aware filtering (10 tests)
- Audit logging (5 tests)

**Expected Output:**
```
tests/test_ml_safety.py::TestPatternFilter::test_check_safe_content PASSED
tests/test_ml_safety.py::TestSafetyFilter::test_check_blocked_content PASSED
...
==================== 33 passed in 3.8s ====================
```

#### Integration Tests

```bash
# Check safe content
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, how are you?"}'

# Expected: {"action": "allow", ...}

# Check blocked content
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{"content": "Here is my password: secret123"}'

# Expected: {"action": "block", "layer": "pattern", ...}
```

---

### 3. BSL Agent

#### Unit Tests

```bash
cd services/BSL Agent
pytest tests/test_avatar_renderer.py -v
```

**Test Coverage:**
- Gesture library (10 tests)
- Avatar renderer (15 tests)
- Avatar service (10 tests)

**Expected Output:**
```
tests/test_avatar_renderer.py::TestGestureLibrary::test_load_gesture PASSED
tests/test_avatar_renderer.py::TestBSLAvatarRenderer::test_queue_text PASSED
...
==================== 35 passed in 4.1s ====================
```

#### Integration Tests

```bash
# Translate text to gloss
curl -X POST http://localhost:8003/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, welcome to the theatre."}'

# Expected: Gloss notation

# Queue for avatar signing
curl -X POST http://localhost:8003/api/v1/avatar/sign \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The performance will begin shortly",
    "session_id": "test_session"
  }'

# Check avatar state
curl "http://localhost:8003/api/v1/avatar/state?session_id=test_session"
```

---

### 4. Operator Console

#### Unit Tests

```bash
cd services/operator-console
pytest tests/test_realtime_updates.py -v
```

**Test Coverage:**
- WebSocket connections (12 tests)
- Metrics collection (10 tests)
- Alert management (8 tests)

**Expected Output:**
```
tests/test_realtime_updates.py::TestWebSocketConnection::test_subscribe PASSED
tests/test_realtime_updates.py::TestMetricsCollector::test_collect_metrics PASSED
...
==================== 30 passed in 3.5s ====================
```

#### WebSocket Testing

```bash
# Install websocat
sudo apt install websocat

# Connect to real-time updates
websocat ws://localhost:8007/ws/realtime

# Send subscription message
{"action": "subscribe", "channels": ["metrics:*", "alerts"]}

# Expected: Real-time metric and alert updates
```

---

### 5. Platform Services

#### Dashboard Service (8010)

```bash
# Get dashboard data
curl http://localhost:8010/api/v1/dashboard

# Get service details
curl http://localhost:8010/api/v1/services/SceneSpeak Agent
```

#### Test Orchestrator (8011)

```bash
# Run all tests
curl -X POST http://localhost:8011/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{"suite": "all", "parallel": true}'

# Get latest results
curl http://localhost:8011/api/v1/results/latest
```

#### Quality Gate (8013)

```bash
# Check quality gate
curl http://localhost:8013/api/v1/gate/check

# Get quality metrics
curl http://localhost:8013/api/v1/metrics

# Generate report
curl "http://localhost:8013/api/v1/report?format=json"
```

---

## New v0.4.0 Feature Testing

### LoRA Adapter Testing

```bash
# List available adapters
curl http://localhost:8001/v1/adapters

# Load adapter
curl -X POST http://localhost:8001/v1/adapters/load \
  -H "Content-Type: application/json" \
  -d '{"name": "dramatic-theatre"}'

# Generate with adapter
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Detective enters the dimly lit office",
    "adapter": "noir"
  }'

# Benchmark adapter
curl -X POST http://localhost:8001/v1/adapters/benchmark \
  -H "Content-Type: application/json" \
  -d '{
    "adapter": "comedy",
    "iterations": 10
  }'
```

### Multi-Layer Safety Testing

```bash
# Test with conversation history
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "content": "That sounds great!",
    "conversation_history": [
      {"user": "Hi there"},
      {"assistant": "Hello! How can I help you?"}
    ]
  }'

# Get audit log
curl "http://localhost:8006/api/v1/audit?limit=10"

# Get statistics
curl http://localhost:8006/api/v1/statistics
```

### Avatar Rendering Testing

```bash
# Sign text with avatar
curl -X POST http://localhost:8003/api/v1/avatar/sign \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, welcome to the theatre!",
    "session_id": "test_user"
  }'

# Get avatar state
curl "http://localhost:8003/api/v1/avatar/state?session_id=test_user"

# List active avatars
curl http://localhost:8003/api/v1/avatar/list
```

### Real-time Updates Testing

```bash
# Using websocat
websocat ws://localhost:8007/ws/realtime

# Subscribe to metrics
{"action": "subscribe", "channels": ["metrics:SceneSpeak Agent"]}

# Expected: Metric updates every ~33ms (30 FPS)
```

---

## Health Checks

All services expose health endpoints:

```bash
# Service health
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done

# Platform services
for port in 8010 8011 8012 8013; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done
```

---

## Performance Testing

### Response Time Testing

```bash
# Test SceneSpeak response time
time curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "Test context"}'

# Expected: < 500ms for generation
```

### Load Testing Script

```bash
#!/bin/bash
# test_load.sh

# Test with 100 concurrent requests
for i in {1..100}; do
  curl -s -X POST http://localhost:8001/v1/generate \
    -H "Content-Type: application/json" \
    -d '{"context": "Test request '"$i"'"}' &
done
wait

echo "Completed 100 requests"
```

---

## Troubleshooting Tests

### Test Failures

```bash
# Run with verbose output
pytest tests/unit/services/scenespeak/ -vv

# Run specific test
pytest tests/unit/services/scenespeak/test_generation.py::test_generate_dialogue -v

# Run with debugger
pytest tests/unit/services/scenespeak/ --pdb
```

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/home/ranj/Project_Chimera:$PYTHONPATH

# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### Service Not Available

```bash
# Check if service is running
kubectl get pods -n live | grep scenespeak

# Check service logs
kubectl logs -f -n live deployment/SceneSpeak Agent

# Port forward to test locally
kubectl port-forward -n live svc/SceneSpeak Agent 8001:8001
```

### Redis Connection Issues

```bash
# Check if Redis is running
kubectl get pods -n shared | grep redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Or use kubectl port-forward
kubectl port-forward -n shared svc/redis 6379:6379
```

---

## Continuous Testing

### Pre-commit Testing

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI/CD Testing

Tests run automatically in CI/CD on:
- Pull request creation
- Push to main branch
- Manual workflow dispatch

```bash
# Trigger CI workflow manually
gh workflow run test.yml
```

---

## Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Core Services | 80% | 82.5% |
| Platform Services | 80% | 85.0% |
| Overall | 80% | 83.2% |

---

## Summary Checklist

Before considering testing complete:

- [ ] All unit tests pass (300+ tests)
- [ ] Integration tests pass (50+ tests)
- [ ] Load tests pass (20+ tests)
- [ ] Coverage threshold met (80%+)
- [ ] All health checks pass
- [ ] Manual API testing completed
- [ ] WebSocket connections tested
- [ ] LoRA adapters tested
- [ ] ML safety layers tested
- [ ] Avatar rendering tested

---

*Last Updated: March 2026*
*Testing Guide v0.4.0*

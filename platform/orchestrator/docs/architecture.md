# Test Orchestrator - Architecture Document

**Version:** 1.0.0
**Date:** 2026-03-04
**Author:** Project Chimera Team

---

## Overview

The Test Orchestrator is a centralized platform service that discovers, executes, and aggregates test results across all Project Chimera microservices. It provides parallel test execution, coverage measurement, and historical trend analysis.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Test Orchestrator Service                           │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────────────┐  │
│  │   REST API  │  │  WebSocket   │  │       Test Discovery Core        │  │
│  │   /api/v1   │  │  /progress   │  │  ┌────────────────────────────┐  │  │
│  │             │  │              │  │  │  Pytest Collector          │  │  │
│  │ POST /run   │  │  Real-time   │  │  │  - Scans services/        │  │  │
│  │ GET /result │  │  updates     │  │  │  - Finds test_*.py        │  │  │
│  │ GET /status │  │              │  │  │  - Builds test tree       │  │  │
│  └─────────────┘  └──────────────┘  │  └────────────────────────────┘  │  │
│                                   │                                      │  │
│                                   │  ┌────────────────────────────┐      │  │
│                                   │  │  Parallel Executor         │      │  │
│  ┌────────────────────────────┐   │  │  - Service isolation      │      │  │
│  │   Result Aggregator        │◄──┤  │  - pytest-xdist           │      │  │
│  │  - Combines results        │   │  │  - Worker pools           │      │  │
│  │  - Calculates metrics      │   │  │  - Timeout handling       │      │  │
│  └────────────────────────────┘   │  └────────────────────────────┘      │  │
│           │                         │                                      │  │
│           ▼                         │  ┌────────────────────────────┐      │  │
│  ┌────────────────────────────┐    │  │  Coverage Collector        │      │  │
│  │   PostgreSQL Storage       │◄───┤  │  - pytest-cov integration  │      │  │
│  │  - Test history            │    │  │  - Per-service reports     │      │  │
│  │  - Coverage trends         │    │  │  - Aggregate metrics       │      │  │
│  │  - Execution metadata      │    │  └────────────────────────────┘      │  │
│  └────────────────────────────┘    └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Services Under Test                                  │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │SceneSpeak   │ │ Captioning  │ │    BSL      │ │  Safety     │           │
│  │Agent        │ │ Agent       │ │ Agent       │ │ Filter      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │Sentiment    │ │  Lighting   │ │ OpenClaw    │ │ Operator    │           │
│  │Agent        │ │ Service     │ │ Orchestrator│ │ Console     │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Test Discovery Core

**Purpose:** Discover and catalog all pytest tests across services.

**Discovery Strategy:**
- **Recursive Scan:** Traverse `services/` directory
- **Pattern Matching:** Find `test_*.py` and `*_test.py` files
- **Test Collection:** Use `pytest --collect-only` to enumerate tests
- **Categorization:** Group by service, test type (unit/integration/e2e)

**Output:** Test catalog with metadata
```python
{
    "service": "openclaw-orchestrator",
    "test_file": "tests/test_scene_manager.py",
    "tests": [
        {"name": "test_scene_activation", "type": "unit"},
        {"name": "test_multi_scene_orchestration", "type": "integration"}
    ]
}
```

---

### 2. Parallel Executor

**Purpose:** Execute tests in parallel with service isolation.

**Execution Strategy:**
- **Worker Pools:** One worker per service (max 8 concurrent)
- **Isolation:** Each service runs in isolated subprocess
- **Timeout:** Per-test and per-run timeouts
- **Resource Limits:** CPU/memory limits per worker

**Technology:**
- `pytest-xdist` for parallel test execution
- `pytest-timeout` for test timeout enforcement
- `pytest-asyncio` for async test support

---

### 3. Coverage Collector

**Purpose:** Generate and aggregate code coverage reports.

**Strategy:**
- **Per-Service:** Generate `.coverage` files per service
- **Aggregation:** Combine into project-wide coverage
- **Formats:** HTML, JSON, XML (for CI/CD)
- **Thresholds:** Enforce minimum coverage (target: 80%)

**Technology:**
- `pytest-cov` for coverage measurement
- `coverage.py` for report generation

---

### 4. Result Aggregator

**Purpose:** Combine results from all test runs into unified output.

**Aggregation Logic:**
```
Total Tests = Σ(service_tests)
Passed = Σ(service_passed)
Failed = Σ(service_failed)
Skipped = Σ(service_skipped)
Duration = Max(service_duration)
```

**Output Formats:**
- JSON (API consumption)
- HTML (human-readable)
- JUnit XML (CI/CD integration)

---

### 5. PostgreSQL Storage

**Purpose:** Store test history for trend analysis.

**Schema:**
```sql
-- Test runs
CREATE TABLE test_runs (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    total_tests INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    skipped INTEGER NOT NULL,
    duration_seconds FLOAT NOT NULL,
    coverage_percent FLOAT
);

-- Per-test results
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    service VARCHAR(50) NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- passed, failed, skipped
    duration_ms FLOAT,
    error_message TEXT,
    FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
);

-- Coverage history
CREATE TABLE coverage_history (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    service VARCHAR(50) NOT NULL,
    coverage_percent FLOAT NOT NULL,
    lines_covered INTEGER NOT NULL,
    lines_total INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
);
```

---

## Test Discovery Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Start Scan  │────▶│ List        │────▶│ For each path   │────▶│ Collect      │
│ services/   │     │ subdirs     │     │ with tests/     │     │ tests via    │
│             │     │             │     │                 │     │ pytest       │
└─────────────┘     └─────────────┘     └─────────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Return      │◀────│ Build test  │◀────│ Categorize      │◀────│ Extract      │
│ catalog     │     │ catalog     │     │ (service, type) │     │ metadata     │
└─────────────┘     └─────────────┘     └─────────────────┘     └──────────────┘
```

---

## API Endpoints

### Test Execution

**POST /api/v1/run-tests**
```json
{
    "services": ["openclaw-orchestrator", "captioning-agent"],
    "test_pattern": "test_scene_*",  // Optional: filter tests
    "parallel": true,
    "coverage": true
}
```

**Response:**
```json
{
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "estimated_duration": 120
}
```

### Results

**GET /api/v1/results/{run_id}**
```json
{
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "complete",
    "summary": {
        "total": 203,
        "passed": 203,
        "failed": 0,
        "skipped": 0,
        "duration": 45.2,
        "coverage": 84.5
    },
    "by_service": [
        {
            "service": "openclaw-orchestrator",
            "passed": 189,
            "failed": 0,
            "coverage": 86.2
        },
        {
            "service": "captioning-agent",
            "passed": 14,
            "failed": 0,
            "coverage": 78.1
        }
    ]
}
```

### WebSocket Progress

**WS /api/v1/progress/{run_id}**
```json
{
    "service": "openclaw-orchestrator",
    "test": "test_scene_activation",
    "status": "passed",
    "progress": 150,
    "total": 203
}
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Test Framework | pytest 7.x |
| Parallel Execution | pytest-xdist |
| Coverage | pytest-cov, coverage.py |
| Async Tests | pytest-asyncio |
| Database | PostgreSQL 15 |
| API Framework | FastAPI |
| WebSocket | FastAPI WebSocket |
| Scheduling | APScheduler |

---

## Test Categorization

### By Type
- **Unit Tests:** Single function/class tests
- **Integration Tests:** Service-component integration
- **End-to-End Tests:** Full workflow tests

### By Service
- **Agent Services:** SceneSpeak, Captioning, BSL, Sentiment
- **Infrastructure:** OpenClaw Orchestrator, Lighting, Safety
- **Frontend:** Operator Console

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Discovery Time | <5 seconds for full catalog |
| Test Execution | <2 minutes for full suite |
| Result Aggregation | <1 second |
| API Response | <100ms (p95) |
| WebSocket Latency | <50ms |

---

## Security Considerations

- **RBAC:** Restrict test execution to authorized users
- **Secrets:** Never log sensitive data in test output
- **Isolation:** Tests run in isolated environments
- **Audit:** Log all test runs with user attribution

---

## Future Enhancements

1. **Flaky Test Detection:** Track tests that intermittently fail
2. **Test Impact Analysis:** Run only tests affected by code changes
3. **Visual Regression:** UI snapshot testing for Operator Console
4. **Load Testing:** Integration with Locust/K6
5. **A/B Testing:** Compare performance across versions

---

**Status:** ✅ Architecture Complete
**Next Step:** Implement test discovery (Task 3.1.2)

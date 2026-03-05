# Test Orchestrator API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8011`
**Service:** Test discovery, execution, and reporting

---

## Overview

The Test Orchestrator manages test discovery, execution, and reporting across the entire Chimera platform.

---

## Endpoints

### 1. Run All Tests

Execute all tests.

**Endpoint:** `POST /api/v1/tests/run`

**Request Body:**

```json
{
  "suite": "all",
  "parallel": true,
  "workers": 4
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `suite` | string | No | Test suite: `all`, `unit`, `integration`, `load`. Default: `all` |
| `parallel` | boolean | No | Run tests in parallel. Default: `true` |
| `workers` | integer | No | Number of parallel workers. Default: `4` |
| `module` | string | No | Specific module to test |

**Response:**

```json
{
  "run_id": "run_abc123",
  "status": "running",
  "started_at": "2026-03-04T12:00:00Z",
  "estimated_duration": 120
}
```

---

### 2. Get Test Results

Get results of a test run.

**Endpoint:** `GET /api/v1/results/{run_id}`

**Response:**

```json
{
  "run_id": "run_abc123",
  "status": "completed",
  "started_at": "2026-03-04T12:00:00Z",
  "completed_at": "2026-03-04T12:01:45",
  "duration": 105,
  "summary": {
    "total": 320,
    "passed": 315,
    "failed": 5,
    "skipped": 0,
    "pass_rate": 0.984
  },
  "results": [
    {
      "service": "scenespeak-agent",
      "suite": "unit",
      "total": 25,
      "passed": 25,
      "failed": 0,
      "duration": 2.5
    }
  ]
}
```

---

### 3. Get Latest Results

Get results of the most recent test run.

**Endpoint:** `GET /api/v1/results/latest`

**Response:** Same as `/api/v1/results/{run_id}`

---

### 4. List Test Suites

List all available test suites.

**Endpoint:** `GET /api/v1/suites`

**Response:**

```json
{
  "suites": [
    {
      "name": "unit",
      "description": "Unit tests",
      "test_count": 250
    },
    {
      "name": "integration",
      "description": "Integration tests",
      "test_count": 50
    },
    {
      "name": "load",
      "description": "Load tests",
      "test_count": 20
    }
  ],
  "total": 320
}
```

---

### 5. Discover Tests

Discover all tests in the codebase.

**Endpoint:** `POST /api/v1/tests/discover`

**Request Body:**

```json
{
  "path": "services/",
  "pattern": "test_*.py"
}
```

**Response:**

```json
{
  "tests": [
    {
      "id": "test_scenespeak_generation",
      "path": "services/scenespeak-agent/tests/test_generation.py",
      "suite": "unit"
    }
  ],
  "total": 320
}
```

---

### 6. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

## Examples

### Run All Tests

```bash
curl -X POST http://localhost:8011/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "suite": "all",
    "parallel": true
  }'
```

### Run Specific Module Tests

```bash
curl -X POST http://localhost:8011/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "suite": "unit",
    "module": "services/scenespeak-agent"
  }'
```

### Get Latest Results

```bash
curl http://localhost:8011/api/v1/results/latest
```

---

*Last Updated: March 2026*
*Test Orchestrator v0.4.0*

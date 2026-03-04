# Quality Gate API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8013`
**Service:** Quality threshold enforcement and reporting

---

## Overview

The Quality Gate enforces quality thresholds for coverage, test pass rates, and performance metrics before allowing deployments.

---

## Endpoints

### 1. Check Quality Gate

Check if current quality meets all thresholds.

**Endpoint:** `GET /api/v1/gate/check`

**Response:**

```json
{
  "status": "passed",
  "checked_at": "2026-03-04T12:00:00Z",
  "thresholds": {
    "coverage": {
      "actual": 82.5,
      "threshold": 80.0,
      "status": "passed"
    },
    "test_pass_rate": {
      "actual": 98.4,
      "threshold": 95.0,
      "status": "passed"
    },
    "flaky_test_rate": {
      "actual": 2.1,
      "threshold": 5.0,
      "status": "passed"
    }
  }
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| `passed` | All thresholds met |
| `failed` | One or more thresholds not met |
| `warning` | Below recommended levels but above minimum |

---

### 2. Check Pull Request

Check quality gate for a specific pull request.

**Endpoint:** `POST /api/v1/gate/check-pr`

**Request Body:**

```json
{
  "pr_id": "123",
  "base_branch": "main",
  "head_branch": "feature/new-dialogue"
}
```

**Response:**

```json
{
  "pr_id": "123",
  "status": "passed",
  "checked_at": "2026-03-04T12:00:00Z",
  "metrics": {
    "coverage_change": "+2.5%",
    "tests_added": 15,
    "tests_failing": 0
  }
}
```

---

### 3. Get Quality Metrics

Get current quality metrics.

**Endpoint:** `GET /api/v1/metrics`

**Response:**

```json
{
  "coverage": {
    "overall": 82.5,
    "by_service": {
      "scenespeak-agent": 85.2,
      "safety-filter": 88.1,
      "bsl-agent": 76.5
    }
  },
  "tests": {
    "total": 320,
    "passing": 315,
    "failing": 5,
    "pass_rate": 98.4
  },
  "flaky_tests": {
    "count": 7,
    "rate": 2.1
  },
  "performance": {
    "avg_response_time_ms": 150,
    "p95_response_time_ms": 320,
    "p99_response_time_ms": 580
  }
}
```

---

### 4. Get Quality Report

Generate a comprehensive quality report.

**Endpoint:** `GET /api/v1/report`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Report format: `json` or `html` |

**Response (JSON):**

```json
{
  "generated_at": "2026-03-04T12:00:00Z",
  "summary": {
    "overall_status": "passed",
    "score": 92
  },
  "sections": [
    {
      "name": "Code Coverage",
      "status": "passed",
      "details": {...}
    },
    {
      "name": "Test Quality",
      "status": "passed",
      "details": {...}
    }
  ]
}
```

---

### 5. Update Thresholds

Update quality gate thresholds (admin only).

**Endpoint:** `POST /api/v1/thresholds`

**Request Body:**

```json
{
  "min_coverage": 85.0,
  "min_pass_rate": 97.0,
  "max_flaky_rate": 3.0
}
```

**Response:**

```json
{
  "updated": true,
  "thresholds": {
    "min_coverage": 85.0,
    "min_pass_rate": 97.0,
    "max_flaky_rate": 3.0
  }
}
```

---

### 6. Get Current Thresholds

Get current quality gate thresholds.

**Endpoint:** `GET /api/v1/thresholds`

**Response:**

```json
{
  "min_coverage": 80.0,
  "min_pass_rate": 95.0,
  "max_flaky_rate": 5.0,
  "max_performance_p99_ms": 1000
}
```

---

### 7. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

## Examples

### Check Quality Gate

```bash
curl http://localhost:8013/api/v1/gate/check
```

### Get Quality Metrics

```bash
curl http://localhost:8013/api/v1/metrics
```

### Generate Report

```bash
curl "http://localhost:8013/api/v1/report?format=json"
```

### Update Thresholds

```bash
curl -X POST http://localhost:8013/api/v1/thresholds \
  -H "Content-Type: application/json" \
  -d '{
    "min_coverage": 85.0,
    "min_pass_rate": 97.0
  }'
```

---

## Quality Gate Decision Matrix

| Metric | Below Minimum | Between Min and Target | At/Above Target |
|--------|---------------|----------------------|-----------------|
| Coverage | Failed | Warning | Passed |
| Pass Rate | Failed | Warning | Passed |
| Flaky Rate | Failed | Warning | Passed |

Overall gate status:
- `failed` if any metric is Failed
- `warning` if no Failed but at least one Warning
- `passed` if all metrics are Passed

---

*Last Updated: March 2026*
*Quality Gate v3.0.0*

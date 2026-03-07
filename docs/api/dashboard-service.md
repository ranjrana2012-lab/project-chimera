# Dashboard Service API Documentation

**Version:** v0.5.0
**Base URL:** `http://localhost:8010`
**Service:** Quality platform dashboards and visualization

---

## Overview

The Dashboard Service provides web-based dashboards for monitoring quality metrics, test results, and system health across the Chimera platform.

---

## Endpoints

### 1. Web Dashboard

**Endpoint:** `GET /`

**Response:** HTML dashboard interface

---

### 2. Get Dashboard Data

Get data for the main dashboard.

**Endpoint:** `GET /api/v1/dashboard`

**Response:**

```json
{
  "summary": {
    "total_services": 12,
    "healthy_services": 12,
    "failing_services": 0,
    "total_tests": 320,
    "passing_tests": 315,
    "failing_tests": 5
  },
  "services": [
    {
      "name": "SceneSpeak Agent",
      "status": "healthy",
      "port": 8001,
      "test_pass_rate": 0.98,
      "coverage": 85.2
    }
  ],
  "recent_alerts": [
    {
      "id": "alert_001",
      "severity": "warning",
      "message": "High memory usage",
      "timestamp": "2026-03-04T12:00:00Z"
    }
  ]
}
```

---

### 3. Get Service Details

Get detailed metrics for a specific service.

**Endpoint:** `GET /api/v1/services/{service_name}`

**Response:**

```json
{
  "name": "SceneSpeak Agent",
  "status": "healthy",
  "metrics": {
    "cpu_percent": 45.2,
    "memory_mb": 1024,
    "request_rate": 12.5,
    "error_rate": 0.01
  },
  "tests": {
    "total": 25,
    "passing": 24,
    "failing": 1,
    "pass_rate": 0.96
  },
  "coverage": 85.2
}
```

---

### 4. Get Test Results

Get test results for all services.

**Endpoint:** `GET /api/v1/tests/results`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `suite` | string | Filter by test suite (unit, integration, load) |
| `service` | string | Filter by service name |

**Response:**

```json
{
  "results": [
    {
      "service": "SceneSpeak Agent",
      "suite": "unit",
      "total": 20,
      "passing": 20,
      "failing": 0,
      "duration": 2.5
    }
  ],
  "summary": {
    "total": 320,
    "passing": 315,
    "failing": 5
  }
}
```

---

### 5. Get Quality Metrics

Get quality gate metrics.

**Endpoint:** `GET /api/v1/quality/metrics`

**Response:**

```json
{
  "coverage": {
    "overall": 82.5,
    "threshold": 80.0,
    "status": "pass"
  },
  "test_pass_rate": {
    "overall": 98.4,
    "threshold": 95.0,
    "status": "pass"
  },
  "flaky_test_rate": {
    "overall": 2.1,
    "threshold": 5.0,
    "status": "pass"
  }
}
```

---

### 6. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

## Examples

### Get Dashboard Data

```bash
curl http://localhost:8010/api/v1/dashboard
```

### Get Service Details

```bash
curl http://localhost:8010/api/v1/services/SceneSpeak Agent
```

---

*Last Updated: March 2026*
*Dashboard Service v0.4.0*

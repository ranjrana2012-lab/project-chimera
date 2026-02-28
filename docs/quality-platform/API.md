# Chimera Quality Platform - API Documentation

## Test Orchestrator API (Port 8008)

### POST /api/v1/run/start
Start a new test run for a commit.

**Request:**
```json
{
  "commit_sha": "abc123",
  "branch": "main",
  "test_filter": ["tests/unit/*"],
  "full_suite": true
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "status": "pending",
  "message": "Test run started"
}
```

### GET /api/v1/run/{run_id}
Get status of a test run.

**Response:**
```json
{
  "run_id": "uuid",
  "status": "running",
  "progress": 45,
  "total": 100,
  "passed": 40,
  "failed": 5
}
```

### WebSocket /ws/run/{run_id}
Live test execution updates.

**Message Format:**
```json
{
  "type": "test_complete",
  "test_id": "tests/unit/test_example.py::test_func",
  "status": "passed",
  "duration_ms": 150
}
```

### GET /api/v1/tests/discover
Discover all tests in the codebase.

**Response:**
```json
{
  "total": 500,
  "tests": ["test_id1", "test_id2", ...]
}
```

## Dashboard Service API (Port 8009)

### GET /api/v1/runs
List test runs with pagination.

**Query Parameters:**
- `limit`: Max 100 (default: 10)
- `offset`: For pagination (default: 0)

**Response:**
```json
{
  "runs": [...],
  "total": 50,
  "limit": 10,
  "offset": 0
}
```

### GET /api/v1/runs/{run_id}/summary
Get run summary with coverage and mutation scores.

**Response:**
```json
{
  "run_id": "uuid",
  "commit_sha": "abc123",
  "status": "completed",
  "total": 500,
  "passed": 485,
  "failed": 12,
  "skipped": 3,
  "duration_seconds": 245,
  "coverage_pct": 94.2,
  "mutation_score": 97.8
}
```

### GET /api/v1/trends
Get historical trend data.

**Query Parameters:**
- `metric`: Metric name (coverage, mutations, duration)
- `days`: Number of days (1-365, default: 30)

**Response:**
```json
{
  "metric": "coverage",
  "days": 30,
  "data": [
    {"date": "2026-02-28", "value": 94.2},
    {"date": "2026-02-27", "value": 93.8}
  ]
}
```

### WebSocket /ws/runs/{run_id}
Real-time test execution updates.

**Message Format:**
```json
{
  "type": "test_complete",
  "data": {...}
}
```

## CI/CD Gateway API (Port 8010)

### POST /webhooks/github
GitHub webhook endpoint.

**Headers:**
- `X-Hub-Signature-256`: HMAC signature verification

**Events:**
- `push`: Trigger test run on push to main branch
- `pull_request`: Trigger affected tests on PR

### POST /webhooks/gitlab
GitLab webhook endpoint.

**Events:**
- `Push`: Trigger test run on push
- `Merge Request`: Trigger affected tests

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ci-gateway"
}
```

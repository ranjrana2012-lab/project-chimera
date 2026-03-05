# Quality Platform Service Documentation

**Version:** 0.4.0
**Last Updated:** March 2026

---

## Overview

The Quality Platform provides comprehensive testing infrastructure, quality gates, and CI/CD integration for Project Chimera. It ensures code quality, test coverage, and deployment reliability.

---

## Components

| Service | Port | Description |
|---------|------|-------------|
| Test Orchestrator | 8011 | Test discovery and execution |
| Dashboard Service | 8009 | Real-time quality metrics visualization |
| CI/CD Gateway | 8010 | GitHub/GitLab integration |
| Quality Gate | 8013 | SLO-based deployment blocking |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   GitHub/GitLab │────▶│  CI/CD Gateway   │────▶│ Test Orchestrator│
│                 │     │  (Port 8010)     │     │   (Port 8011)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                               │
                               ┌───────────────────────────────┘
                               │
                               ▼
                        ┌──────────────┐     ┌──────────────┐
                        │ Quality Gate │────▶│ Prometheus   │
                        │ (Port 8013)  │     │   (SLOs)     │
                        └──────┬───────┘     └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Dashboard   │
                        │ (Port 8009)  │
                        └──────────────┘
```

---

## Test Orchestrator (Port 8011)

### Purpose

Discovers, schedules, and executes tests across all services.

### API Endpoints

#### List All Tests
```http
GET /api/v1/tests
```

**Response:**
```json
{
  "tests": [
    {
      "id": "scenespeak-unit",
      "name": "SceneSpeak Unit Tests",
      "service": "scenespeak-agent",
      "type": "unit",
      "status": "passing",
      "last_run": "2026-03-05T12:00:00Z",
      "coverage": 85.5
    }
  ]
}
```

#### Run Tests
```http
POST /api/v1/tests/run
Content-Type: application/json

{
  "test_ids": ["scenespeak-unit", "captioning-integration"],
  "parallel": true
}
```

### Configuration

Environment variables:
- `REDIS_URL`: Redis connection for test queue
- `DATABASE_URL`: PostgreSQL for test results storage
- `MAX_PARALLEL_TESTS`: Maximum concurrent tests (default: 5)

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `test_orchestrator_tests_run_total` | Counter | Total tests executed |
| `test_orchestrator_tests_passed` | Counter | Tests passing |
| `test_orchestrator_tests_failed` | Counter | Tests failing |
| `test_orchestrator_queue_size` | Gauge | Tests awaiting execution |

---

## Dashboard Service (Port 8009)

### Purpose

Real-time visualization of quality metrics, test results, and SLO compliance.

### Web Interface

Access at: `http://localhost:8009` or `http://<ingress>/quality-dashboard`

### Features

**Test Results Dashboard:**
- Pass/fail rates by service
- Test execution trends
- Coverage reports

**SLO Dashboard:**
- Real-time SLO compliance
- Error budget tracking
- Burn rate alerts

**Quality Gate Status:**
- Deployment readiness
- SLO blocking status
- Error budget remaining

---

## CI/CD Gateway (Port 8010)

### Purpose

Integrates with GitHub/GitLab to trigger tests, report status, and enable auto-merge for trusted contributors.

### GitHub Integration

**Webhook Events Handled:**
- `pull_request` - Trigger tests on PR
- `pull_request_review` - Check auto-merge eligibility
- `push` - Trigger branch tests

**Auto-Merge Criteria:**
- Contributor has 3+ merged PRs
- All tests passing
- No merge conflicts
- At least one approval
- SLO compliance > 95%

---

## Quality Gate (Port 8013)

### Purpose

SLO-based deployment blocking to prevent bad deployments from reaching production.

### SLO Checks

| Service | SLO Target | Blocking Threshold |
|---------|------------|-------------------|
| OpenClaw | 99.9% | < 99.5% |
| SceneSpeak | 99.5% | < 99.0% |
| Captioning | 99.5% | < 99.0% |
| BSL | 99.0% | < 98.5% |
| Safety | 99.9% | < 99.5% |
| Console | 99.5% | < 99.0% |

### API Endpoints

#### Check Deployment Readiness
```http
POST /api/v1/gate/check
Content-Type: application/json

{
  "service": "scenespeak-agent",
  "version": "v0.4.0",
  "commit_sha": "abc123"
}
```

**Response:**
```json
{
  "status": "pass",
  "can_deploy": true,
  "slo_compliance": {
    "current": 99.3,
    "threshold": 99.0,
    "error_budget_remaining": 0.82
  }
}
```

---

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r platform/requirements.txt

# Run Test Orchestrator
cd platform && python -m orchestrator.main

# Run Dashboard Service
cd platform/dashboard && python -m main
```

### Kubernetes

```bash
# Deploy all platform services
kubectl apply -f platform/deployment/quality-platform/

# Verify deployment
kubectl get pods -n chimera-platform
```

---

## Monitoring

All Quality Platform services expose Prometheus metrics at `/metrics` endpoint and use OpenTelemetry for distributed tracing.

See [Observability Guide](../observability.md) for complete monitoring setup.

---

## Related Documentation

- [Observability Guide](../observability.md) - Monitoring and SLOs
- [SLO Handbook](../runbooks/slo-handbook.md) - SLO definitions
- [Testing Guide](../runbooks/testing-guide.md) - Test procedures
- [ADR-004: Quality Platform](../architecture/004-quality-platform.md) - Architecture decision

---

**Need help?** Join our [office hours](../getting-started/office-hours.md) or check [FAQ](../getting-started/faq.md).

# CI/CD Gateway Architecture Design

**Version:** 1.0.0
**Date:** 2026-03-04
**Author:** Project Chimera Team

---

## Overview

The CI/CD Gateway provides integration between GitHub Actions and the Project Chimera test platform. It receives webhooks, triggers test pipelines, and syncs results back to the orchestrator and dashboard.

---

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GITHUB ACTIONS                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │  Push Event │  │  PR Event    │  │ Workflow Run │  │  Status Update│               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
│         │                  │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼──────────────────┼─────────────────────┘
          │                  │                  │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD GATEWAY                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                        WEBHOOK HANDLER                                   │  │
│  │  • Verify GitHub signature                                              │  │
│  │  • Parse webhook events                                                  │  │
│  │  • Validate repository/branch                                             │  │
│  └───────────────────────────────┬────────────────────────────────────────┘  │
│                                  ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    PIPELINE TRIGGER SERVICE                              │  │
│  │  • Start test orchestrator runs                                          │  │
│  │  • Track pipeline → run mapping                                          │  │
│  │  • Handle concurrent triggers                                             │  │
│  └───────────────────────────────┬────────────────────────────────────────┘  │
│                                  ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                     RESULT SYNC SERVICE                                  │  │
│  │  • Poll GitHub Actions for results                                       │  │
│  │  • Parse test reports (JUnit, coverage)                                  │  │
│  │  • Update orchestrator storage                                           │  │
│  └───────────────────────────────┬────────────────────────────────────────┘  │
│                                  ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    STATUS BROADCAST SERVICE                              │  │
│  │  • Broadcast status updates via WebSocket                                │  │
│  │  • Update dashboard CI/CD display                                         │  │
│  │  • Trigger alerts on failures                                             │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  TEST ORCHESTRATOR│ │  DASHBOARD     │ │  POSTGRES      │
│  (REST API)      │ │  (WebSocket)   │ │  (Storage)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Component Specifications

### 1. Webhook Handler

**Purpose:** Receive and validate GitHub webhook events

**Endpoints:**
- `POST /api/v1/webhook/github` - GitHub webhook endpoint

**Events Handled:**
- `push` - Code pushed to branch
- `pull_request` - PR opened/updated/synchronized
- `workflow_run` - CI workflow started/completed

**Webhook Validation:**
- Verify HMAC signature using `GITHUB_WEBHOOK_SECRET`
- Check event type
- Validate repository matches configured repo

**Request Format:**
```json
{
  "event": "workflow_run",
  "action": "completed",
  "repository": "ranjrana2012-lab/project-chimera",
  "branch": "main",
  "commit": "abc123",
  "workflow_id": "4527",
  "status": "success",
  "run_url": "https://github.com/..."
}
```

---

### 2. Pipeline Trigger Service

**Purpose:** Trigger test runs based on webhook events

**Trigger Conditions:**
- Push to main branch → Full test suite
- Push to feature branch → Affected services only
- PR opened/sync → Full test suite + comment on PR

**Trigger Flow:**
```
1. Receive webhook event
2. Determine affected services (changed paths)
3. Call Orchestrator POST /api/v1/run-tests
4. Store pipeline → run ID mapping
5. Return acknowledgement
```

**Service Mapping:**
```
platform/agents/scenespeak/* → scenespeak-agent
platform/agents/captioning/* → captioning-agent
platform/agents/bsl/* → bsl-agent
platform/agents/sentiment/* → sentiment-agent
platform/services/lighting/* → lighting-service
platform/services/safety/* → safety-filter
platform/orchestrator/* → openclaw-orchestrator
platform/console/* → operator-console
```

---

### 3. Result Sync Service

**Purpose:** Poll GitHub Actions for test results and sync to orchestrator

**Polling Strategy:**
- Every 30 seconds for running workflows
- Every 2 minutes for completed workflows

**Result Parsing:**
- Parse JUnit XML reports from workflow artifacts
- Parse coverage reports (coverage.json or lcov.info)
- Extract pass/fail counts, duration, coverage percentage

**Sync Flow:**
```
1. Poll running workflows from GitHub API
2. Download test artifacts
3. Parse test results
4. POST to Orchestrator /api/v1/results/{run_id}
5. Update dashboard via WebSocket
```

**GitHub API Endpoints Used:**
- `GET /repos/{owner}/{repo}/actions/runs` - List workflow runs
- `GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts` - List artifacts
- `GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}/{archive_format}` - Download artifact

---

### 4. Status Broadcast Service

**Purpose:** Broadcast CI/CD status updates to connected clients

**WebSocket Events:**
```json
{
  "type": "pipeline_started",
  "data": {
    "pipeline_id": "4527",
    "run_id": "test-run-abc",
    "branch": "main",
    "commit": "abc123"
  }
}

{
  "type": "pipeline_completed",
  "data": {
    "pipeline_id": "4527",
    "run_id": "test-run-abc",
    "status": "success",
    "total_tests": 547,
    "passed": 523,
    "failed": 24
  }
}
```

---

## REST API Specification

### POST /api/v1/webhook/github
Receive GitHub webhook events.

**Headers:**
- `X-GitHub-Event`: Event type
- `X-Hub-Signature-256`: HMAC signature

**Body:** Raw GitHub webhook payload

**Response:** 202 Accepted

---

### POST /api/v1/pipelines/trigger
Manually trigger a pipeline run.

**Request:**
```json
{
  "branch": "main",
  "commit": "abc123",
  "services": ["scenespeak-agent", "captioning-agent"]
}
```

**Response:**
```json
{
  "pipeline_id": "4528",
  "run_id": "test-run-def",
  "status": "triggered"
}
```

---

### GET /api/v1/pipelines/{pipeline_id}
Get pipeline status.

**Response:**
```json
{
  "pipeline_id": "4527",
  "status": "running",
  "run_id": "test-run-abc",
  "started_at": "2026-03-04T10:00:00Z",
  "url": "https://github.com/.../actions/runs/4527"
}
```

---

## Environment Configuration

```bash
# GitHub Integration
GITHUB_REPO=ranjrana2012-lab/project-chimera
GITHUB_WEBHOOK_SECRET=webhook_secret_value
GITHUB_TOKEN=ghp_personal_access_token

# Orchestrator Integration
ORCHESTRATOR_URL=http://orchestrator:8000
ORCHESTRATOR_API_KEY=orchestrator_api_key

# Sync Settings
SYNC_INTERVAL_SECONDS=30
ARTIFACT_RETENTION_HOURS=24

# WebSocket
WS_BROADCAST_URL=http://dashboard:8007/ws
```

---

## PostgreSQL Schema

```sql
-- Pipeline to run mapping
CREATE TABLE pipeline_mappings (
    pipeline_id VARCHAR(50) PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,
    branch VARCHAR(100),
    commit_hash VARCHAR(40),
    status VARCHAR(20),
    triggered_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    INDEX idx_run_id (run_id),
    INDEX idx_status (status)
);

-- Webhook event log
CREATE TABLE webhook_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    payload JSONB,
    received_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    INDEX idx_processed (processed)
);
```

---

## Error Handling

### Webhook Validation Failures
- Return 401 Unauthorized
- Log invalid signature attempts

### Orchestrator Unavailable
- Queue trigger request
- Retry with exponential backoff
- Alert after 3 failed attempts

### Artifact Download Failures
- Log warning and continue
- Mark pipeline as "partial" results
- Alert for manual intervention

---

## Status Codes

| Pipeline Status | Description |
|----------------|-------------|
| `triggered` | Pipeline triggered, waiting for GitHub |
| `queued` | Queued in GitHub Actions |
| `running` | Tests running |
| `completed` | Finished successfully |
| `failed` | Tests failed |
| `cancelled` | Cancelled by user |
| `error` | System error |

---

**Status:** ✅ Design Complete
**Next Step:** Implement webhook handler (Task 3.3.2)

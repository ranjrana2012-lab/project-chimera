# CI/CD Gateway API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8012`
**Service:** GitHub/GitLab webhook integration for CI/CD

---

## Overview

The CI/CD Gateway receives webhooks from GitHub/GitLab and orchestrates CI/CD workflows including testing, quality checks, and deployments.

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

### 2. GitHub Webhook

**Endpoint:** `POST /webhooks/github`

Receives GitHub webhook events for:
- Pull request events
- Push events
- Workflow dispatch events

**Headers:**

| Header | Description |
|--------|-------------|
| `X-GitHub-Event` | Event type |
| `X-Hub-Signature-256` | HMAC signature |

**Response:**

```json
{
  "status": "received",
  "event_type": "pull_request",
  "action": "opened",
  "run_id": "run_abc123"
}
```

---

### 3. GitLab Webhook

**Endpoint:** `POST /webhooks/gitlab`

Receives GitLab webhook events.

**Headers:**

| Header | Description |
|--------|-------------|
| `X-GitLab-Event` | Event type |
| `X-GitLab-Token` | Secret token |

**Response:**

```json
{
  "status": "received",
  "event_type": "Merge Request Hook",
  "run_id": "run_def456"
}
```

---

### 4. Trigger Deployment

Manually trigger a deployment.

**Endpoint:** `POST /api/v1/deploy`

**Request Body:**

```json
{
  "environment": "staging",
  "ref": "main",
  "services": ["scenespeak-agent", "safety-filter"]
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `environment` | string | Yes | Target environment: `staging`, `production` |
| `ref` | string | Yes | Git ref (branch, tag, commit) |
| `services` | array | No | Specific services to deploy (empty = all) |

**Response:**

```json
{
  "deployment_id": "deploy_ghi789",
  "status": "pending",
  "environment": "staging",
  "ref": "main",
  "started_at": "2026-03-04T12:00:00Z"
}
```

---

### 5. Get Deployment Status

Get status of a deployment.

**Endpoint:** `GET /api/v1/deployments/{deployment_id}`

**Response:**

```json
{
  "deployment_id": "deploy_ghi789",
  "status": "success",
  "environment": "staging",
  "ref": "main",
  "started_at": "2026-03-04T12:00:00Z",
  "completed_at": "2026-03-04T12:05:00Z",
  "duration": 300,
  "services": [
    {
      "name": "scenespeak-agent",
      "status": "deployed",
      "image": "localhost:30500/project-chimera/scenespeak-agent:abc123"
    }
  ]
}
```

---

### 6. Get Workflow Runs

Get recent CI/CD workflow runs.

**Endpoint:** `GET /api/v1/runs`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (default: 50) |
| `status` | string | Filter by status |

**Response:**

```json
{
  "runs": [
    {
      "run_id": "run_abc123",
      "event_type": "pull_request",
      "status": "completed",
      "result": "success",
      "started_at": "2026-03-04T12:00:00Z",
      "duration": 180
    }
  ],
  "total": 100
}
```

---

## Webhook Event Types

### GitHub Events

| Event | Description |
|-------|-------------|
| `pull_request` | PR opened, synchronized, or closed |
| `push` | Code pushed to branch |
| `workflow_dispatch` | Manual workflow trigger |
| `release` | Release published |

### GitLab Events

| Event | Description |
|-------|-------------|
| `Merge Request Hook` | MR opened, updated, or merged |
| `Push Hook` | Code pushed to branch |
| `Release Hook` | Release published |

---

## Examples

### Manual Deployment

```bash
curl -X POST http://localhost:8012/api/v1/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "staging",
    "ref": "feature/new-dialogue"
  }'
```

### Get Deployment Status

```bash
curl http://localhost:8012/api/v1/deployments/deploy_ghi789
```

### List Recent Runs

```bash
curl "http://localhost:8012/api/v1/runs?limit=10&status=completed"
```

---

*Last Updated: March 2026*
*CI/CD Gateway v0.4.0*

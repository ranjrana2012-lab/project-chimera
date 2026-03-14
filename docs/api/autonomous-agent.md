# Autonomous Agent API Documentation

**Version:** v1.0.0
**Base URL:** `http://localhost:8008`
**Service:** Autonomous task execution with Ralph Engine and GSD Orchestrator

---

## Overview

The Autonomous Agent provides:
- GSD (Discuss→Plan→Execute→Verify) task orchestration
- Ralph Mode with persistent retries (5-retry backstop)
- Flow-Next architecture for fresh context per iteration
- External state persistence (STATE.md, PLAN.md, REQUIREMENTS.md)
- Async task execution with status polling

---

## Endpoints

### Health & Metrics

#### Health Check
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "autonomous-agent",
  "version": "1.0.0",
  "timestamp": "2026-03-14T10:30:00Z"
}
```

#### Status
**Endpoint:** `GET /status`

**Response:**
```json
{
  "current_task": "task-uuid-123",
  "completed_tasks": ["task-uuid-456"],
  "pending_tasks": ["task-uuid-789"],
  "retry_count": 2,
  "last_updated": "2026-03-14T10:30:00Z"
}
```

#### Metrics
**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format

---

### Task Execution

#### 1. Execute Task

Execute a task using GSD Discuss→Plan→Execute with Ralph Mode.

**Endpoint:** `POST /execute`

**Request Body:**
```json
{
  "user_request": "Create a new user authentication module",
  "requirements": ["use JWT", "support refresh tokens"],
  "timeout": 3600
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_request` | string | Yes | Natural language description of the task |
| `requirements` | array | No | Additional requirements |
| `timeout` | integer | No | Max execution time in seconds (default: 3600) |

**Response:** (202 Accepted)
```json
{
  "task_id": "abc-123-def",
  "status": "pending",
  "created_at": "2026-03-14T10:30:00Z"
}
```

---

#### 2. Get Task Status

Get status of an executing task.

**Endpoint:** `GET /execute/{task_id}`

**Response:**
```json
{
  "task_id": "abc-123-def",
  "status": "complete",
  "phases_completed": ["discuss", "plan", "execute"],
  "requirements": {
    "goal": "Create a new user authentication module",
    "constraints": ["use JWT", "support refresh tokens"],
    "acceptance_criteria": ["login endpoint", "token validation"]
  },
  "plan_tasks": [
    "Design authentication schema",
    "Implement JWT token generation",
    "Create login endpoint",
    "Add token refresh mechanism"
  ],
  "result": "Authentication module created successfully",
  "error": null,
  "retry_count": 1
}
```

**Status Values:**
- `pending` - Task queued, not started
- `in_progress` - Task is executing
- `complete` - Task completed successfully
- `failed` - Task failed after max retries

---

## GSD Phases

### Discuss Phase
Extracts requirements from user request.
- Output: REQUIREMENTS.md
- Includes: Goal, constraints, acceptance criteria

### Plan Phase
Creates implementation plan from requirements.
- Output: PLAN.md
- Includes: Task breakdown, dependencies, estimates

### Execute Phase
Executes plan with Ralph Mode (persistent retries).
- Output: STATE.md updates
- Retries up to 5 times before backstop
- Fresh context per iteration (Flow-Next)

---

## State Files

### REQUIREMENTS.md
Generated during Discuss phase. Contains:
- Goal statement
- Constraints
- Acceptance criteria

### PLAN.md
Generated during Plan phase. Contains:
- Task breakdown
- Dependencies
- Time estimates

### STATE.md
Updated throughout execution. Contains:
- Current task status
- Retry count
- Completed phases
- Result or error

---

## Ralph Mode

Ralph Mode provides persistent execution with fresh context:

1. **Fresh Context**: Each iteration loads state from files (not memory)
2. **Persistent Retries**: Up to 5 attempts with backstop
3. **Promise Verification**: Validates results against requirements
4. **State Persistence**: Updates STATE.md after each attempt

**Configuration:**
- `MAX_RETRIES`: 5 (environment variable)
- `RETRY_DELAY_SECONDS`: 10 (environment variable)

---

## Examples

### Basic Task Execution

```bash
# Submit task
curl -X POST http://localhost:8008/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add user registration endpoint"
  }'

# Response: {"task_id": "abc-123", "status": "pending"}

# Check status
curl http://localhost:8008/execute/abc-123
```

### Task with Requirements

```bash
curl -X POST http://localhost:8008/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Implement email notifications",
    "requirements": [
      "use SMTP",
      "support HTML templates",
      "add retry logic"
    ],
    "timeout": 7200
  }'
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

**HTTP Status Codes:**
- `202` - Task accepted for execution
- `404` - Task not found
- `500` - Internal server error

---

## Metrics

The Autonomous Agent exposes Prometheus metrics:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `autonomous_active_tasks` | Gauge | - | Currently executing tasks |
| `autonomous_tasks_total` | Counter | status, phase | Total tasks executed |
| `autonomous_task_duration_seconds` | Histogram | phase | Task execution duration |
| `autonomous_gsd_phase_duration` | Histogram | phase | GSD phase duration |
| `autonomous_retries_total` | Counter | - | Total Ralph Mode retries |

---

*Last Updated: March 2026*
*Autonomous Agent v1.0.0*

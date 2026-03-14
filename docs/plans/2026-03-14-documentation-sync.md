# Documentation Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Push 26 autonomous-agent commits to GitHub and update all documentation to reflect the new service.

**Architecture:** Sequential execution - git push first, then documentation updates in parallel where possible.

**Tech Stack:** Git, Markdown, FastAPI docs format

---

## Task 1: Push Commits to GitHub

**Files:**
- None (git operation)

**Step 1: Verify git remote**

Run: `git remote -v`
Expected: Shows origin pointing to GitHub repository

**Step 2: Push 26 commits to origin/main**

Run: `git push origin main`
Expected: All commits pushed successfully

**Step 3: Verify remote commits**

Run: `git log origin/main --oneline -26`
Expected: Shows 26 commits starting with design doc

**Commit:**
```bash
git log --oneline -26 > /tmp/commit_log.txt
echo "Pushed 26 commits to GitHub" | git commit --allow-empty -m -
```

---

## Task 2: Update SERVICE_STATUS.md

**Files:**
- Modify: `docs/SERVICE_STATUS.md:5-16` (Core Services table)
- Modify: `docs/SERVICE_STATUS.md:362-374` (Service Build Status)

**Step 1: Add autonomous-agent to Core Services table**

Find the table section starting with `| **WorldMonitor Sidecar** | 8010 |` (line 17) and add after it:

```markdown
| **Autonomous Agent** | 8008 | `/health`, `/status` | `/execute`, `/metrics` | CPU | ✅ Built |
```

**Step 2: Update service count from 8 to 9**

Find line 5: `## Core Services (8 Services)` and change to:

```markdown
## Core Services (9 Services)
```

**Step 3: Add to SERVICES array in health check script**

Find the SERVICES array (around line 53) and add:

```bash
  "8008:Autonomous Agent"
```

**Step 4: Add to quick curl commands section**

After the WorldMonitor section (around line 153), add:

```markdown
# Autonomous Agent
curl http://localhost:8008/health
```

**Step 5: Update Service Build Status**

Find "All 8 core services are built" (line 362) and change to:

```markdown
All 9 core services are built and ready:
```

Add to the list after WorldMonitor:

```markdown
9. ✅ Autonomous Agent (Ralph Engine + GSD Orchestrator)
```

**Step 6: Commit**

```bash
git add docs/SERVICE_STATUS.md
git commit -m "docs: add autonomous-agent to SERVICE_STATUS.md

- Add autonomous-agent row to Core Services table (port 8008)
- Update service count from 8 to 9
- Add to health check script
- Add to quick curl commands
- Update Service Build Status section

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Create API Documentation

**Files:**
- Create: `docs/api/autonomous-agent.md`

**Step 1: Write the API documentation file**

Create `docs/api/autonomous-agent.md` with:

```markdown
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
```

**Step 2: Commit**

```bash
git add docs/api/autonomous-agent.md
git commit -m "docs: add autonomous-agent API documentation

- Document all 5 endpoints (health, status, metrics, execute, task status)
- Include GSD phases explanation
- Document Ralph Mode behavior
- Add state files reference
- Include examples and metrics

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Create Service Documentation

**Files:**
- Create: `docs/services/autonomous-agent.md`

**Step 1: Write the service documentation file**

Create `docs/services/autonomous-agent.md` with:

```markdown
# Autonomous Agent Service

**Version:** v1.0.0
**Port:** 8008
**Status:** ✅ Operational

---

## Overview

The Autonomous Agent is an intelligent task execution engine that implements:
- **Ralph Engine**: Persistent execution with fresh context per iteration
- **GSD Orchestrator**: Discuss→Plan→Execute→Verify lifecycle
- **Flow-Next Manager**: External state management for memory persistence

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                   │
│                      (Port 8008)                        │
└─────────────┬─────────────┬─────────────┬───────────────┘
              │             │             │
      ┌───────▼──────┐ ┌───▼────┐ ┌────▼─────────┐
      │ Ralph Engine │ │   GSD   │ │  Flow-Next   │
      │              │ │Orchestr│ │   Manager    │
      │ - Persistent │ │ator    │ │              │
      │   Retries    │ │-Discuss│ │ - Fresh      │
      │ - Fresh      │ │-Plan   │ │   Context    │
      │   Context    │ │-Execute│ │ - State      │
      └──────────────┘ └────────┘ │   Files      │
                                  └──────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
              ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
              │STATE.md   │       │PLAN.md    │       │REQUIREMENTS│
              │           │       │           │       │.md        │
              │- Task     │       │- Tasks    │       │- Goal     │
              │  Status   │       │- Deps     │       │- Constraints│
              │- Retry    │       │- Hours    │       │- Criteria │
              │  Count    │       │           │       │           │
              └───────────┘       └───────────┘       └───────────┘
```

---

## Components

### Ralph Engine
**Purpose:** Persistent task execution with context isolation

**Features:**
- 5-retry backstop (configurable via `MAX_RETRIES`)
- Fresh context loaded from external state files each iteration
- Promise verification against requirements
- Exponential backoff between retries

**Key Methods:**
- `execute_until_promise()` - Execute with persistent retries
- `load_fresh_context()` - Load state from files (not memory)
- `verify_result()` - Validate against requirements

---

### GSD Orchestrator
**Purpose:** Task lifecycle management (Discuss→Plan→Execute→Verify)

**Phases:**
1. **Discuss**: Extract requirements from user request
2. **Plan**: Create implementation plan with task breakdown
3. **Execute**: Execute plan with Ralph Mode
4. **Verify**: Validate results against acceptance criteria

**Key Methods:**
- `discuss_phase()` - Generate REQUIREMENTS.md
- `plan_phase()` - Generate PLAN.md
- `execute_phase()` - Execute with Ralph Engine

---

### Flow-Next Manager
**Purpose:** External state management for memory persistence

**Features:**
- Reads/writes state from external markdown files
- Creates fresh sessions (empty history) per iteration
- Prevents context rot across retries

**State Files:**
- `STATE.md` - Current task status, retry count, results
- `PLAN.md` - Implementation plan with tasks and dependencies
- `REQUIREMENTS.md` - Goal, constraints, acceptance criteria

---

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `autonomous-agent` | Service identifier |
| `PORT` | integer | `8008` | HTTP server port |
| `MAX_RETRIES` | integer | `5` | Ralph Mode max retries |
| `RETRY_DELAY_SECONDS` | integer | `10` | Delay between retries |
| `STATE_DIR` | string | `./state` | State files directory |
| `OTLP_ENDPOINT` | string | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | string | `INFO` | Logging level |

---

## Deployment

### Kubernetes (K3s)

**Horizontal Pod Autoscaler:**
- Replicas: 2-10
- Scale on CPU: 70%
- Scale on Memory: 80%

**Resource Limits:**
```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "2000m"
    memory: "2Gi"
```

**Deployment:**
```bash
kubectl apply -f k8s/autonomous-agent/
kubectl get pods -n live -l app=autonomous-agent
```

---

## Monitoring

### Prometheus Metrics

**Business Metrics:**
- `autonomous_active_tasks` - Currently executing tasks
- `autonomous_tasks_total` - Total tasks by status/phase
- `autonomous_task_duration_seconds` - Task execution duration
- `autonomous_gsd_phase_duration` - GSD phase duration
- `autonomous_retries_total` - Total Ralph Mode retries

**Alerts:**
- `AutonomousAgentStuck` - Task in same phase > 30 minutes
- `AutonomousAgentHighRetries` - > 3 retries in 10 minutes
- `AutonomousAgentFailureRate` - > 50% failure rate

---

## State Management

### State File Format

**STATE.md:**
```markdown
# Current State

## Task abc-123
- Status: In Progress
- Current Phase: execute
- Retry Count: 2
- Updated At: 2026-03-14T10:30:00Z

## Phases Completed
- discuss
- plan
```

**REQUIREMENTS.md:**
```markdown
# Requirements

## Goal
Create user authentication module

## Constraints
- Use JWT tokens
- Support refresh tokens

## Acceptance Criteria
- Login endpoint working
- Token validation implemented
```

**PLAN.md:**
```markdown
# Implementation Plan

## Overview
- Total Tasks: 4
- Estimated Hours: 8

## Tasks
### Task 1: Design authentication schema
- Status: pending
- Dependencies: None

### Task 2: Implement JWT generation
- Status: pending
- Dependencies: Task 1
```

---

## Troubleshooting

### Task Stuck in "pending"

**Cause:** Background task failed to start

**Solution:**
```bash
# Check service logs
kubectl logs -f -n live deployment/autonomous-agent

# Restart service
kubectl rollout restart deployment/autonomous-agent -n live
```

---

### High Retry Count

**Cause:** Requirements too vague or execution environment issues

**Solution:**
1. Check STATE.md for error details
2. Verify requirements are specific enough
3. Check agent dependencies (OpenClaw, LLM access)
4. Increase `MAX_RETRIES` if needed

---

### State File Corruption

**Cause:** Concurrent write access or disk full

**Solution:**
```bash
# Backup current state
cp state/STATE.md state/STATE.md.backup

# Reinitialize state files
kubectl exec -n live deployment/autonomous-agent -- \
  rm -f state/*.md

# Restart to recreate
kubectl rollout restart deployment/autonomous-agent -n live
```

---

## Integration

### Connecting to OpenClaw Orchestrator

The Autonomous Agent connects to other agents via OpenClaw:

```bash
# Via OpenClaw (port 8000)
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "autonomous_execution",
    "input": {
      "user_request": "Deploy new service version"
    }
  }'
```

### Direct Access

```bash
# Direct to autonomous-agent (port 8008)
curl -X POST http://localhost:8008/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Deploy new service version"
  }'
```

---

## Related Documentation

- [API Documentation](../api/autonomous-agent.md) - Complete API reference
- [OpenClaw Orchestrator](openclaw-orchestrator.md) - Service routing
- [Architecture](../architecture/overview.md) - System architecture
- [Monitoring](../observability.md) - Metrics and alerts

---

*Last Updated: March 2026*
*Autonomous Agent v1.0.0*
```

**Step 2: Commit**

```bash
git add docs/services/autonomous-agent.md
git commit -m "docs: add autonomous-agent service documentation

- Document Ralph Engine, GSD Orchestrator, Flow-Next Manager
- Include architecture diagram
- Add configuration reference
- Document deployment and monitoring
- Add troubleshooting guide
- Include state management details

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Update docs/index.md

**Files:**
- Modify: `docs/index.md:82-95` (Project Status table)

**Step 1: Add autonomous-agent to Project Status table**

Find the Music Generation row and add after it:

```markdown
| Music Generation | ✅ Operational | Port 8011 |
| Autonomous Agent | ✅ Operational | Port 8008 | Ralph Engine, GSD Orchestrator |
```

**Step 2: Commit**

```bash
git add docs/index.md
git commit -m "docs: add autonomous-agent to index Project Status table

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Update docs/api/endpoints.md

**Files:**
- Modify: `docs/api/endpoints.md` (add Autonomous Agent section after Music Generation)

**Step 1: Add Autonomous Agent section**

Find the Music Generation section (around line 956) and add after it:

```markdown
---

## Autonomous Agent

**Base URL:** `http://localhost:8008`

**API Docs:** [http://localhost:8008/docs](http://localhost:8008/docs)

### GET /execute/{task_id}

**Summary:** Get Task Status

**Operation ID:** `get_task_status_execute__task_id__get`

---

### GET /health

**Summary:** Health Check

**Operation ID:** `health_check_health_get`

---

### GET /metrics

**Summary:** Metrics

**Operation ID:** `metrics_metrics_get`

---

### POST /execute

**Summary:** Execute Task

**Operation ID:** `execute_task_execute_post`

---

### GET /status

**Summary:** Get Status

**Operation ID:** `get_status_status_get`

---
```

**Step 2: Commit**

```bash
git add docs/api/endpoints.md
git commit -m "docs: add autonomous-agent to API endpoint catalog

- Add 5 endpoints to catalog
- Include base URL and API docs link
- Add operation IDs

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Verify All Documentation

**Files:**
- All documentation files

**Step 1: Validate markdown links**

Run: `find docs -name "*.md" -exec grep -l "\[.*\](" {} \; | head -20`
Expected: Lists markdown files with links

**Step 2: Check for broken links**

Run: `grep -r "](../" docs/ | grep -v "README.md" | wc -l`
Expected: Count of relative links (should be reasonable)

**Step 3: Verify all new files exist**

Run: `ls -la docs/api/autonomous-agent.md docs/services/autonomous-agent.md`
Expected: Both files exist

**Step 4: Check git status**

Run: `git status`
Expected: All changes committed

**Step 5: Final commit**

```bash
# If any verification fixes needed
git add docs/
git commit -m "docs: verification fixes for autonomous-agent documentation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Push Documentation Updates

**Files:**
- None (git operation)

**Step 1: Push all documentation commits**

Run: `git push origin main`
Expected: All documentation commits pushed

**Step 2: Verify remote branch**

Run: `git log origin/main --oneline -10`
Expected: Shows latest documentation commits

**Commit:**
```bash
# Create final summary commit
echo "Documentation sync complete:
- Pushed 26 autonomous-agent implementation commits
- Added to SERVICE_STATUS.md
- Created API documentation
- Created service documentation
- Updated index and endpoint catalog" | \
git commit --allow-empty -m "docs: complete autonomous-agent documentation sync

Summary:
- 26 implementation commits pushed
- SERVICE_STATUS.md updated (8 → 9 services)
- API docs created (docs/api/autonomous-agent.md)
- Service docs created (docs/services/autonomous-agent.md)
- Index updated with Project Status entry
- Endpoint catalog updated with 5 endpoints

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Success Criteria

1. ✅ All 26 commits visible in GitHub repository
2. ✅ SERVICE_STATUS.md shows autonomous-agent as operational
3. ✅ API documentation complete with all 5 endpoints
4. ✅ Service documentation complete with architecture and ops info
5. ✅ Index and catalog link to new docs
6. ✅ No broken links or missing references

---

*End of Implementation Plan*

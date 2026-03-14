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

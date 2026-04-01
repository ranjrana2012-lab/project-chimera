# Claude Code Supervisory Orchestrator for Project Chimera

**Date:** 2026-04-01
**Status:** Design Approved
**Author:** Claude Code + User Collaboration
**Version:** 1.0

---

## Executive Summary

This document specifies the design for a Claude Code-based supervisory orchestrator for Project Chimera. The orchestrator sits above the existing Nemo Claw Orchestrator, providing system-wide health monitoring, automatic mode switching, and unified Ralph Loop management for both refactoring and show orchestration tasks.

**Key Design Decisions:**
- Non-invasive supervisory layer (preserves existing systems)
- Unified Ralph Loop (refactoring + orchestration)
- Automatic state-based mode switching (STANDBY, CHECKING, CONTROL)
- Reuse Nemo Claw's Privacy Router for LLM calls
- Web Dashboard + CLI operator interfaces
- Hybrid state persistence (files + Redis)
- Operator-configured error policies

**Target Timeline:** 12 weeks to production readiness

---

## Table of Contents

1. [Background](#1-background)
2. [Architecture Overview](#2-architecture-overview)
3. [Core Components](#3-core-components)
4. [Data Flow & Interactions](#4-data-flow--interactions)
5. [API & Endpoints](#5-api--endpoints)
6. [Testing Strategy](#6-testing-strategy)
7. [Implementation Phases](#7-implementation-phases)
8. [Risks & Mitigation](#8-risks--mitigation)
9. [Success Criteria](#9-success-criteria)

---

## 1. Background

### 1.1 Current State

Project Chimera is a comprehensive platform for creating live theatre experiences through coordinated AI services. The current architecture includes:

- **Nemo Claw Orchestrator** (port 8000): Production orchestrator for show operations
  - Agent routing and coordination
  - OpenShell policy enforcement
  - Privacy Router with GLM-4.7 First, GGUF models, local LLM fallback
  - 113 tests passing (79% coverage)

- **autonomous-agent service**: Ralph Loop-based refactoring system
  - Persistent execution via stop hooks
  - GSD orchestrator (Discuss→Plan→Execute→Verify)
  - File-based state (queue.txt, learnings.md, program.md)

- **13 microservices**: SceneSpeak, Captioning, BSL, Sentiment, Lighting, Safety, Operator Console, Music Generation, etc.

- **Quality Platform**: Test Orchestrator, SLO Gate, CI/CD Gateway, Prometheus, Grafana, Jaeger

### 1.2 Problem Statement

While the current architecture works well, there are gaps:

1. **No system-wide health monitoring**: Each service has health endpoints, but no unified monitoring
2. **No automatic mode switching**: Operators must manually manage show states
3. **Separate Ralph Loops**: Refactoring and orchestration use different control loops
4. **Limited error escalation**: No systematic approach to error handling and operator notification
5. **No unified operator interface**: Operators use multiple tools with no cohesive view

### 1.3 Solution Overview

Implement a Claude Code-based supervisory orchestrator that:

1. Sits above Nemo Claw (non-invasive)
2. Provides unified health monitoring across all services
3. Automatically switches operational modes based on show state
4. Consolidates Ralph Loop management
5. Implements operator-configured error policies
6. Provides Web Dashboard + CLI interfaces

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HUMAN OPERATOR                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────┐     │
│  │   Operator Console   │  │  Web Dashboard (New) │  │   Claude CLI │     │
│  │   (Show Controls)    │  │  (Orchestrator View) │  │ (Automation) │     │
│  └──────────┬───────────┘  └──────────┬───────────┘  └──────┬───────┘     │
└─────────────┼─────────────────────────┼─────────────────────┼──────────────┘
              │                         │                     │
              └─────────────────────────┼─────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│              CLAUDE CODE SUPERVISORY ORCHESTRATOR (New)                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Unified Ralph Loop Engine                        │   │
│  │  - Persistent execution via stop hooks                              │   │
│  │  - GSD: Discuss → Plan → Execute → Verify                          │   │
│  │  - Completion promises & retry backoff                              │   │
│  │  - State: DISABLED, STANDBY, CHECKING, PLANNING, ..., ESCALATED    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐  │
│  │  Health Monitor      │  │  Mode Controller      │  │  Task Queue     │  │
│  │  - /health sweeps    │  │  - Auto mode switch   │  │  - queue.txt    │  │
│  │  - Metrics queries   │  │  - State transitions  │  │  - Priority     │  │
│  │  - SLO gate checks   │  │  - Show state aware   │  │  - Retry logic  │  │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘  │
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐  │
│  │  Policy Engine       │  │  Error Handler       │  │  LLM Client     │  │
│  │  - Escalation rules  │  │  - Severity levels   │  │  - Nemo Claw    │  │
│  │  - Operator config   │  │  - Retry/backoff     │  │    Privacy Router│  │
│  │  - Approval gates    │  │  - Human escalation  │  │  - Model routing│  │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
        ┌───────────▼───────────┐ ┌────▼─────┐ ┌──────────▼──────────┐
        │   NEMO CLAW           │ │  REDIS   │ │  FILE STATE         │
        │   ORCHESTRATOR        │ │          │ │  /state/claude-orch/ │
        │   (Show Operations)   │ │ - Mode   │ │  - queue.txt        │
        │   - Agent routing     │ │ - Health │ │  - learnings.md     │
        │   - Policy enforcement│ │ - Tasks  │ │  - program.md       │
        │   - GGUF models       │ │          │ │  - state.json       │
        └───────────┬───────────┘ └──────────┘ └─────────────────────┘
                    │
        ┌───────────┴───────────┐ ┌────────────────────────────────┐
        │   CHIMERA SERVICES    │ │   QUALITY PLATFORM            │
        │   - SceneSpeak        │ │   - Test Orchestrator          │
        │   - Captioning        │ │   - SLO Gate                   │
        │   - BSL               │ │   - CI/CD Gateway              │
        │   - Sentiment         │ │   - Metrics (Prometheus)       │
        │   - Lighting/Sound    │ │   - Traces (Jaeger)            │
        │   - Safety Filter     │ └────────────────────────────────┘
        │   - Music Generation  │
        └───────────────────────┘
```

### 2.2 Operational Modes

The orchestrator supports four primary operational modes:

| Mode | Description | Trigger Behavior |
|------|-------------|------------------|
| **STANDBY** | Idle mode - occasional health checks, waiting for events | Default when no show active |
| **CHECKING** | Active health monitoring - sweeps all services, generates reports | Scheduled checks or manual trigger |
| **CONTROL** | Active orchestration - dispatches tasks, coordinates agents, manages show | Automatic when show active |
| **ESCALATED** | Error state - requires human intervention, all automation paused | Triggered by critical errors |

**Additional transient states:**
- DISABLED: Orchestrator not running
- PLANNING: Ralph Loop planning phase
- WAITING_FOR_APPROVAL: Task requires operator approval
- EXECUTING: Task execution in progress
- VERIFYING: Verifying task completion
- RETRY_BACKOFF: Waiting before retry
- PAUSED: Operator paused automation
- SHUTTING_DOWN: Graceful shutdown in progress

### 2.3 Design Principles

1. **Non-invasive**: Sits above existing systems, doesn't replace them
2. **Show-aware**: Mode switching based on show state
3. **Operator in control**: Configurable policies, approval gates
4. **Resilient**: Hybrid state, graceful degradation, recovery mechanisms
5. **Observable**: Comprehensive logging, metrics, tracing
6. **Testable**: 80%+ test coverage, chaos testing

---

## 3. Core Components

### 3.1 Unified Ralph Loop Engine

**Location:** `services/claude-orchestrator/internal/ralph/`

**Responsibilities:**
- Persistent execution via Claude Code stop hooks
- GSD lifecycle: Discuss → Plan → Execute → Verify
- Completion promise validation
- Retry backoff management
- State persistence

**Key Files:**
```
internal/ralph/
├── loop.go              # Main Ralph Loop controller
├── state.go             # State machine
├── gsd_orchestrator.go  # GSD pipeline
├── queue.go             # Task queue management
├── completion.go        # Completion promise validation
├── retry.go             # Retry/backoff logic
└── hooks.go             # Stop hook integration
```

**Interface:**
```go
type RalphLoop interface {
    Start() error
    Stop() error
    Pause() error
    Resume() error
    TriggerIteration() error
    GetStatus() RalphStatus
    AddTask(task Task) error
    GetQueue() []Task
}
```

### 3.2 Health Monitor

**Location:** `services/claude-orchestrator/internal/health/`

**Responsibilities:**
- Periodic health sweeps across all services
- SLO gate validation
- Metrics aggregation (Prometheus)
- Trace inspection (Jaeger)
- Health status reporting

**Key Files:**
```
internal/health/
├── monitor.go           # Health sweep orchestrator
├── checker.go           # Individual service health checker
├── slo_gate.go          # SLO validation
├── metrics.go           # Prometheus client
├── traces.go            # Jaeger client
└── reporter.go          # Health report generation
```

**Interface:**
```go
type HealthMonitor interface {
    Check(ctx context.Context) HealthReport
    CheckService(ctx context.Context, service string) ServiceHealth
    GetSLOStatus() SLOStatus
    GetMetrics() Metrics
    GetTraces(spanID string) Trace
}
```

### 3.3 Mode Controller

**Location:** `services/claude-orchestrator/internal/mode/`

**Responsibilities:**
- State machine transitions
- Show state awareness (via Nemo Claw)
- Automatic mode switching
- Mode-specific behavior

**Key Files:**
```
internal/mode/
├── controller.go        # Mode state machine
├── state_machine.go     # State transitions
├── show_tracker.go      # Show state monitoring
├── transitions.go       # Mode switch logic
└── policy.go            # Mode transition policies
```

**Interface:**
```go
type ModeController interface {
    GetCurrentMode() Mode
    TransitionTo(mode Mode) error
    ForceTransition(mode Mode) error
    GetTransitionHistory() []Transition
    SetTransitionPolicy(policy TransitionPolicy) error
}
```

### 3.4 Policy Engine

**Location:** `services/claude-orchestrator/internal/policy/`

**Responsibilities:**
- Operator-configured escalation policies
- Approval gate enforcement
- Action validation (ALLOW/DENY/ESCALATE)
- Policy persistence and reloading

**Key Files:**
```
internal/policy/
├── engine.go             # Policy evaluation engine
├── config.go             # Policy configuration loader
├── approval.go           # Approval gate management
├── validator.go          # Action validation
└── policies.yaml         # Policy configuration
```

**Policy Configuration Example:**
```yaml
escalation_policies:
  critical_services:
    - service: safety-filter
      on_failure: escalate_immediately
    - service: nemoclaw-orchestrator
      on_failure: retry_3x_then_escalate
  non_critical_services:
    - service: sentiment-agent
      on_failure: retry_5x_with_backoff
      backoff_duration: 30s

approval_gates:
  control_mode_during_show: required
  service_restart: required
  config_changes: required
  refactoring_during_show: denied

mode_transitions:
  standby_to_control:
    trigger: show_state_active
    approval_required: false
  control_to_standby:
    trigger: show_state_ended
    approval_required: false
  any_to_escalated:
    trigger: critical_error
    approval_required: false
```

**Interface:**
```go
type PolicyEngine interface {
    Evaluate(action Action) PolicyDecision
    RequireApproval(action Action) bool
    GetPolicy(policyID string) Policy
    UpdatePolicy(policy Policy) error
    ReloadPolicies() error
}
```

### 3.5 Error Handler

**Location:** `services/claude-orchestrator/internal/errorhandler/`

**Responsibilities:**
- Error severity classification
- Retry/backoff orchestration
- Human escalation
- Error recovery coordination

**Key Files:**
```
internal/errorhandler/
├── handler.go            # Error routing and classification
├── severity.go           # Severity levels
├── recovery.go           # Recovery strategies
├── escalation.go         # Human escalation logic
└── notifier.go           # Operator notification
```

**Interface:**
```go
type ErrorHandler interface {
    Handle(error Error) ErrorOutcome
    Classify(error Error) Severity
    Escalate(error Error) error
    Recover(error Error) error
    Notify(error Error) error
}
```

### 3.6 LLM Client (Nemo Claw Integration)

**Location:** `services/claude-orchestrator/internal/llm/`

**Responsibilities:**
- Delegate all LLM calls to Nemo Claw Privacy Router
- Model selection based on task type
- Fallback management
- Response parsing

**Key Files:**
```
internal/llm/
├── client.go             # Nemo Claw HTTP client
├── router.go             # Task → Model routing
├── fallback.go           # Fallback management
└── response.go           # Response parsing
```

**Interface:**
```go
type LLMClient interface {
    Generate(ctx context.Context, prompt string, options GenerateOptions) (string, error)
    Stream(ctx context.Context, prompt string, options GenerateOptions) (<-chan string, error)
    GetStatus() LLMStatus
    GetAvailableModels() []Model
}
```

### 3.7 State Persistence (Hybrid)

**Location:** `services/claude-orchestrator/internal/state/`

**Responsibilities:**
- File-based state (git-traceable)
- Redis-based state (real-time)
- Hybrid coordination

**File State (git-traceable):**
```
/state/claude-orchestrator/
├── queue.txt             # Task queue (Ralph Loop)
├── learnings.md          # Historical learnings
├── program.md            # Program constraints
└── state.json            # Current state snapshot
```

**Redis State (real-time):**
```
mode:current              # Current operational mode
health:status             # Aggregated health status
show:state                # Show state (from Nemo Claw)
tasks:pending             # Pending task queue
errors:active             # Active error tracking
```

**Key Files:**
```
internal/state/
├── file_store.go         # File-based persistence
├── redis_store.go        # Redis-based persistence
├── hybrid.go             # Hybrid persistence coordinator
└── snapshot.go           # State snapshot management
```

**Interface:**
```go
type StateStore interface {
    Get(key string) (interface{}, error)
    Set(key string, value interface{}) error
    Delete(key string) error
    Snapshot() error
    Restore() error
}
```

---

## 4. Data Flow & Interactions

### 4.1 Health Check Flow (CHECK mode)

```
Trigger: Scheduled check OR manual trigger

1. Mode Controller → Health Monitor
   POST /internal/health/check

2. Health Monitor → All Services (parallel)
   GET http://service:port/health/live
   GET http://service:port/health/ready
   Query Prometheus metrics
   Query Jaeger traces

3. Services → Health Monitor
   Aggregate responses

4. Health Monitor → Policy Engine
   Evaluate against policies

5. Health Monitor → Redis
   SET health:status

6. Health Monitor → Web Dashboard
   WebSocket push

7. Health Monitor → File State
   APPEND learnings.md
```

### 4.2 Mode Transition Flow (Automatic)

```
Trigger: Show state change OR scheduled check

1. Show Tracker → Nemo Claw
   GET /api/show/state

2. Show Tracker → Mode Controller
   POST /internal/mode/transition

3. Mode Controller → Policy Engine
   POST /internal/policy/evaluate

4. Mode Controller → State Machine
   UPDATE mode:current

5. Mode Controller → All Components
   Broadcast mode change

6. Mode Controller → Web Dashboard
   WebSocket push
```

### 4.3 Task Execution Flow (CONTROL mode)

```
Trigger: Operator command OR Ralph Loop task

1. Operator/Web Dashboard → Task Queue
   POST /internal/tasks/create

2. Task Queue → Policy Engine
   POST /internal/policy/evaluate

3. Task Queue → Ralph Loop
   state: WAITING_FOR_APPROVAL

4. Operator → Web Dashboard
   Approve task

5. Ralph Loop → Execute Phase
   a) Discuss: LLM call for approach
   b) Plan: Generate execution plan
   c) Execute: Execute plan steps
   d) Verify: Verify outcome

6. Ralph Loop → Task Queue
   UPDATE task status

7. Task Queue → File State
   APPEND learnings.md
   UPDATE queue.txt

8. Task Queue → Web Dashboard
   WebSocket push
```

### 4.4 Error Handling Flow

```
Trigger: Service failure OR SLO violation

1. Health Monitor → Error Handler
   POST /internal/error/report

2. Error Handler → Policy Engine
   POST /internal/policy/evaluate

3. Error Handler → Mode Controller
   POST /internal/mode/transition (to ESCALATED)

4. Error Handler → Notifier
   Send alerts

5. Error Handler → Ralph Loop
   PAUSE non-critical tasks

6. Error Handler → File State
   APPEND learnings.md

7. Operator → Web Dashboard / CLI
   Investigate and resolve

8. Operator → Error Handler
   POST /internal/error/{error_id}/resolve

9. Error Handler → Mode Controller
   POST /internal/mode/transition (to STANDBY)
```

---

## 5. API & Endpoints

### 5.1 Claude Code Orchestrator API

**Base URL:** `http://localhost:8010`

#### Health & Status
```
GET  /health/live                    # Liveness probe
GET  /health/ready                   # Readiness probe
GET  /health/status                  # Detailed status
GET  /health/slo                     # SLO gate status
```

#### Mode Control
```
GET  /mode/current                   # Current operational mode
POST /mode/transition                # Request mode transition
GET  /mode/history                   # Mode transition history
POST /mode/override                  # Operator override (emergency)
```

#### Task Management
```
GET  /tasks                          # List all tasks
POST /tasks                          # Create new task
GET  /tasks/{task_id}                # Get task details
POST /tasks/{task_id}/approve        # Approve task
POST /tasks/{task_id}/deny           # Deny task
DELETE /tasks/{task_id}              # Cancel task
```

#### Ralph Loop Control
```
GET  /ralph/status                   # Ralph Loop status
POST /ralph/pause                    # Pause Ralph Loop
POST /ralph/resume                   # Resume Ralph Loop
POST /ralph/iteration                # Trigger single iteration
GET  /ralph/queue                    # View task queue
```

#### Health Monitoring
```
POST /health/check                   # Trigger health check
GET  /health/report                  # Latest health report
GET  /health/history                 # Historical health data
GET  /health/service/{service}       # Specific service health
```

#### Policy Management
```
GET  /policies                       # List all policies
POST /policies/evaluate              # Evaluate action against policy
PUT  /policies/{policy_id}           # Update policy
POST /policies/reload                # Reload policy configuration
```

#### Error Management
```
GET  /errors                          # List active errors
GET  /errors/{error_id}              # Get error details
POST /errors/{error_id}/resolve      # Mark error as resolved
GET  /errors/history                 # Error history
```

### 5.2 Nemo Claw Integration Endpoints

**Base URL:** `http://localhost:8000`

```
GET  /api/show/state                 # Get current show state
POST /v1/orchestrate                 # Route skill request
GET  /skills                         # List available skills
POST /llm/generate                   # Generate LLM response
GET  /llm/status                     # LLM backend status
GET  /policy/rules                   # List active policies
```

### 5.3 WebSocket Events

**WS endpoint:** `ws://localhost:8010/ws/events`

```
mode_change                           # Mode transition
health_update                         # Health check results
task_created                          # New task created
task_updated                          # Task status change
task_completed                        # Task completed
error_reported                        # New error
error_resolved                        # Error resolved
show_state_change                     # Show state change
ralph_loop_iteration                  # Ralph Loop iteration
```

---

## 6. Testing Strategy

### 6.1 Unit Tests (Target: 80%+ coverage)

**Components to test:**
- Ralph Loop Engine (state machine, GSD, retry logic)
- Health Monitor (health checks, SLO gates)
- Mode Controller (transitions, show tracking)
- Policy Engine (evaluation, approval gates)
- Error Handler (classification, escalation)
- State Persistence (file/Redis operations)
- LLM Client (Nemo Claw integration)

### 6.2 Integration Tests

**Test Suites:**
- Ralph Loop Integration (GSD lifecycle, persistence)
- Health Monitoring Integration (end-to-end checks)
- Mode Control Integration (automatic transitions)
- Policy Engine Integration (approval workflows)
- Error Handling Integration (escalation flows)
- State Persistence Integration (hybrid coordination)
- Nemo Claw Integration (show state, LLM calls)

### 6.3 End-to-End Tests

**Critical Flows:**
- Health Check Cycle
- Mode Transition (Show Start)
- Task Execution with Approval
- Error Escalation
- Ralph Loop Persistence
- Refactoring Integration

### 6.4 Chaos Testing

**Failure Scenarios:**
- Service Failure During Show
- Redis Failure
- Nemo Claw Unavailability
- Network Partition
- Concurrent State Access

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- Project scaffold
- State persistence (hybrid)
- Health monitor (basic)
- Mode controller (basic)
- API foundation

### Phase 2: Ralph Loop Integration (Week 3-4)
- Ralph Loop Engine
- Task Queue
- Learnings System
- Program Constraints
- Autonomous Refactoring Integration

### Phase 3: Policy & Error Handling (Week 5-6)
- Policy Engine
- Error Handler
- Policy Configuration
- Notification System

### Phase 4: Nemo Claw Integration (Week 7-8)
- Nemo Claw Client
- Show State Tracker
- LLM Client
- Automatic Mode Switching

### Phase 5: Operator Interfaces (Week 9-10)
- Web Dashboard
- WebSocket Server
- CLI Tool
- Authentication

### Phase 6: Production Readiness (Week 11-12)
- Performance Optimization
- Security Hardening
- Chaos Testing
- Deployment Automation
- Monitoring & Observability
- Documentation

---

## 8. Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Unified Ralph Loop complexity | HIGH | Extensive testing, gradual migration, logical separation |
| Show state synchronization | HIGH | Redundant polling, fallback mechanisms, manual override |
| Nemo Claw dependency | MEDIUM | Circuit breaker, graceful degradation, cached state |
| State consistency (hybrid) | MEDIUM | Atomic operations, consistency checks, recovery procedures |
| Operator error | MEDIUM | Approval gates, audit logging, undo capabilities |
| Performance impact | LOW | Asynchronous operations, parallel health checks |
| Deployment complexity | LOW | Staged rollout, feature flags, rollback procedures |

---

## 9. Success Criteria

### 9.1 Functional Requirements
- [ ] Health checks can poll all services
- [ ] Mode can be switched manually via API
- [ ] State persists across restarts
- [ ] Automatic mode switching works based on show state
- [ ] Ralph Loop executes persistently
- [ ] GSD lifecycle works end-to-end
- [ ] Refactoring tasks complete successfully
- [ ] Policies enforce operator intent
- [ ] Errors are classified and escalated correctly
- [ ] Operators receive notifications
- [ ] Show state is tracked accurately
- [ ] LLM calls work through Nemo Claw

### 9.2 Non-Functional Requirements
- [ ] All tests passing (80%+ coverage)
- [ ] Performance meets SLOs
- [ ] Security audit passed
- [ ] Chaos tests passed
- [ ] Deployment automated
- [ ] Monitoring complete
- [ ] Documentation complete
- [ ] Operators trained

### 9.3 Production Readiness
- [ ] Staged rollout plan approved
- [ ] Feature flags configured
- [ ] Operator training completed
- [ ] Support procedures documented
- [ ] Rollback procedures tested

---

## Appendix A: Configuration Examples

### A.1 Environment Variables

```bash
# Service Configuration
SERVICE_NAME=claude-orchestrator
PORT=8010
HOST=0.0.0.0

# Nemo Claw Integration
NEMOCLAW_BASE_URL=http://localhost:8000
NEMOCLAW_TIMEOUT=30s

# State Persistence
REDIS_URL=redis://localhost:6379
STATE_DIR=/state/claude-orchestrator

# Health Monitoring
HEALTH_CHECK_INTERVAL=5m
HEALTH_CHECK_TIMEOUT=30s
SLO_GATE_URL=http://quality-platform:9000/slo-gate

# Ralph Loop
RALPH_LOOP_ENABLED=true
RALPH_MAX_ITERATIONS=0  # Unlimited
RALPH_STATE_DIR=/state/claude-orchestrator

# Policy Engine
POLICY_CONFIG_PATH=/config/policies.yaml
POLICY_RELOAD_INTERVAL=5m

# Error Handling
ERROR_RETENTION=7d
ERROR_ESCALATION_TIMEOUT=5m

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
LOG_OUTPUT=stdout
```

### A.2 Policy Configuration

See Section 3.4 for full policy configuration example.

---

## Appendix B: Deployment Architecture

```yaml
# docker-compose.yml excerpt
services:
  claude-orchestrator:
    build: ./services/claude-orchestrator
    ports:
      - "8010:8010"
    environment:
      - NEMOCLAW_BASE_URL=http://nemoclaw-orchestrator:8000
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./state/claude-orchestrator:/state/claude-orchestrator
      - ./config/policies.yaml:/config/policies.yaml
    depends_on:
      - nemoclaw-orchestrator
      - redis
    restart: unless-stopped

  web-dashboard:
    build: ./services/claude-dashboard
    ports:
      - "3000:3000"
    environment:
      - API_BASE_URL=http://claude-orchestrator:8010
      - WS_URL=ws://claude-orchestrator:8010/ws/events
    depends_on:
      - claude-orchestrator
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

---

**Document Status:** Ready for review
**Next Steps:**
1. User review and approval
2. Invoke writing-plans skill for implementation plan
3. Begin Phase 1 implementation

# Scene State Machine

**Version:** 1.0.0
**Date:** 2026-03-03
**Component:** OpenClaw Orchestrator - Scene Management

---

## Overview

The Scene State Machine manages the lifecycle of theatre scenes within Project Chimera. Each scene progresses through defined states with controlled transitions, supporting multi-scene orchestration with concurrent scene execution.

---

## State Diagram

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    │            ┌──────────┐             │
                    │            │   IDLE   │◄────────────┤
                    │            └─────┬────┘             │
                    │                  │                  │
                    │          create_scene()             │
                    │                  │                  │
                    │                  ▼                  │
                    │            ┌──────────┐             │
                    │            │  LOADING │             │
                    │            └─────┬────┘             │
                    │                  │                  │
                    │         load_complete               │
                    │         validation_ok               │
                    │                  │                  │
                    │                  ▼                  │
        ┌───────────┴──────┐   ┌──────────┐   ┌──────────┴─────────┐
        │                  │   │         │   │                    │
   ┌─────────┐        ┌─────────┐  │ ACTIVE │  ┌─────────┐    ┌─────────┐
   │  ERROR  │        │ PAUSED  │  │         │  │TRANSITION│    │COMPLETED│
   └─────────┘        └────┬────┘  └─────┬────┘  └────┬────┘    └────┬────┘
        ▲                  │             │            │              │
        │              pause()      activate()    transition()   complete()
        │                  │             │            │              │
        │                  └─────────────┴────────────┴──────────────┘
        │                                │
        │                         error/timeout
        │                                │
        └────────────────────────────────┘
                    │
                    │                recover()
                    │                     │
                    └─────────────────────┘
```

---

## States

### 1. IDLE
**Description:** Initial state. Scene exists but is not loaded or active.

**Attributes:**
- `scene_id`: Unique identifier
- `config`: Scene configuration (not yet validated)
- `created_at`: Timestamp

**Valid Transitions To:** LOADING

**Entry Actions:** None

**Exit Actions:** Begin loading scene resources

---

### 2. LOADING
**Description:** Scene resources are being loaded and validated.

**Attributes:**
- `loading_progress`: 0-100
- `loading_stage`: Current loading phase
- `validation_errors`: List of validation failures

**Valid Transitions To:** ACTIVE, ERROR

**Entry Actions:**
- Load scene configuration from storage
- Validate scene schema
- Preload assets (scripts, media, prompts)
- Initialize agent contexts

**Exit Actions:** Release loading resources

**Timeout:** 30 seconds → ERROR

---

### 3. ACTIVE
**Description:** Scene is live and processing audience input.

**Attributes:**
- `active_since`: Timestamp when scene became active
- `agent_states`: Dictionary of all agent states
- `audience_context`: Current audience state
- `dialogue_history`: Recent dialogue exchanges
- `metrics`: Performance metrics

**Valid Transitions To:** PAUSED, TRANSITION, COMPLETED, ERROR

**Entry Actions:**
- Start all agent loops
- Open WebSocket connections
- Begin Kafka consumption
- Send scene start notification

**Exit Actions:**
- Stop agent loops
- Close WebSocket connections
- Persist state for recovery

**Conditions:**
- All agents healthy
- Redis connection active
- Kafka consumer connected

---

### 4. PAUSED
**Description:** Scene is temporarily suspended (not active, but resumable).

**Attributes:**
- `paused_at`: Timestamp when paused
- `pause_reason`: Reason for pause
- `resume_capability`: Can this scene be resumed

**Valid Transitions To:** ACTIVE, COMPLETED, ERROR

**Entry Actions:**
- Suspend agent loops (keep connections)
- Notify all services of pause
- Save checkpoint state

**Exit Actions:**
- Resume agent loops
- Notify all services of resume

**Use Cases:**
- Manual pause by operator
- Technical issue requiring pause
- Scene intermission

---

### 5. TRANSITION
**Description:** Scene is transitioning to another scene (handoff in progress).

**Attributes:**
- `transition_type`: fade, cut, crossfade
- `target_scene_id`: Destination scene
- `transition_progress`: 0-100
- `handoff_complete`: Boolean

**Valid Transitions To:** ACTIVE (as new scene), COMPLETED, ERROR

**Entry Actions:**
- Initiate transition effect
- Begin agent state handoff
- Transfer audience context
- Fade out current scene audio/video

**Exit Actions:**
- Complete agent handoff
- Release previous scene resources
- Activate new scene

**Timeout:** 5 seconds → ERROR (fallback to cut)

**Transition Types:**
- **CUT:** Immediate switch (<100ms)
- **FADE:** Gradual fade out/in (2-3 seconds)
- **CROSSFADE:** Overlapping transition (3-5 seconds)

---

### 6. COMPLETED
**Description:** Scene has finished execution successfully.

**Attributes:**
- `completed_at`: Timestamp
- `completion_reason`: natural, manual, error_recovery
- `final_metrics`: Performance summary
- `archive_location`: Where scene data is archived

**Valid Transitions To:** None (terminal state)

**Entry Actions:**
- Stop all agent processes
- Archive scene data
- Generate completion report
- Notify operator console

**Terminal State:** Cannot transition from COMPLETED

---

### 7. ERROR
**Description:** Scene encountered an error and cannot continue.

**Attributes:**
- `error_code`: Unique error identifier
- `error_message`: Human-readable error
- `error_context`: Additional context (stack trace, etc.)
- `recoverable`: Boolean - can this error be recovered
- `retry_count`: Number of recovery attempts

**Valid Transitions To:** LOADING (if recoverable), COMPLETED

**Entry Actions:**
- Log error to audit trail
- Send alert to operator
- Save error state
- Notify dependent services

**Exit Actions:**
- Clear error state
- Attempt recovery logic

**Error Codes:**
- `E001`: Configuration validation failed
- `E002`: Agent initialization failed
- `E003`: Resource loading timeout
- `E004`: Agent health check failed
- `E005`: Transition timeout
- `E006`: Redis connection lost
- `E007`: Kafka consumer failed
- `E008`: Agent crash detected

---

## Transitions

### create_scene()
**Trigger:** Operator creates new scene via Console or API

**From:** IDLE
**To:** LOADING

**Conditions:**
- Scene config provided
- Scene ID unique
- Resource quota available

**Side Effects:**
- Generate scene ID
- Initialize scene metadata
- Reserve resources

---

### activate()
**Trigger:** Scene loading complete and validated

**From:** LOADING
**To:** ACTIVE

**Conditions:**
- All agents initialized
- Configuration valid
- No validation errors

**Side Effects:**
- Start agent loops
- Open connections
- Notify operator

---

### pause()
**Trigger:** Manual pause from Console or API

**From:** ACTIVE
**To:** PAUSED

**Conditions:**
- Scene is active
- No critical operation in progress

**Side Effects:**
- Suspend (not stop) agent processing
- Send pause notification
- Checkpoint state

---

### resume()
**Trigger:** Manual resume from Console or API

**From:** PAUSED
**To:** ACTIVE

**Conditions:**
- Scene is paused
- Resume capability enabled
- No blocking errors

**Side Effects:**
- Resume agent loops
- Send resume notification
- Clear pause flags

---

### transition()
**Trigger:** Scheduled time, event trigger, or manual command

**From:** ACTIVE, PAUSED
**To:** TRANSITION

**Conditions:**
- Target scene exists
- Target scene in LOADING or ACTIVE state
- Handoff possible

**Side Effects:**
- Initiate transition effect
- Transfer agent state
- Move audience context

---

### complete()
**Trigger:** Natural end, manual command, or error recovery

**From:** ACTIVE, PAUSED, ERROR
**To:** COMPLETED

**Conditions:**
- Scene finished (natural)
- Manual completion (operator)
- Unrecoverable error (after retries)

**Side Effects:**
- Stop all processes
- Archive data
- Generate report

---

### error()
**Trigger:** Any unhandled exception or validation failure

**From:** Any state except COMPLETED
**To:** ERROR

**Conditions:**
- Exception caught
- Validation failed
- Timeout occurred
- Health check failed

**Side Effects:**
- Log error
- Send alert
- Attempt recovery if possible

---

### recover()
**Trigger:** Manual operator intervention or automated retry

**From:** ERROR
**To:** LOADING

**Conditions:**
- Error is recoverable
- Retry count < max_retries (3)
- Underlying issue resolved

**Side Effects:**
- Clear error state
- Reload scene
- Resume from checkpoint if available

---

## Multi-Scene Orchestration

### Concurrent Scenes
The orchestrator supports multiple concurrent scenes, each with its own state machine instance.

**Rules:**
- Max 5 concurrent active scenes
- Only one scene can be in TRANSITION at a time
- Scene IDs must be unique
- Shared resources (Redis, Kafka) namespace-scoped by scene_id

### Scene Hierarchy
```
Performance (Container)
├── Scene 1 (ACTIVE)
├── Scene 2 (PAUSED)
├── Scene 3 (LOADING)
└── Scene 4 (IDLE)
```

### Global vs Local State
- **Global State:** Shared across all scenes (performance metrics, resource pool)
- **Local State:** Per-scene (dialogue history, agent states, audience context)

---

## Persistence

### Redis Keys
```
chimera:scene:{scene_id}:state         # Current state string
chimera:scene:{scene_id}:config        # Scene configuration JSON
chimera:scene:{scene_id}:checkpoint    # Recovery checkpoint
chimera:scene:{scene_id}:metrics       # Performance metrics
chimera:scene:{scene_id}:history       # State transition history
chimera:scene:registry                 # All active scene IDs
```

### TTL
- Active scenes: No TTL (persistent)
- Completed scenes: 7 days (then archive)
- Error scenes: 30 days (for debugging)

---

## Events

### State Change Events
Published to Kafka topic `scene.state.changed`:
```json
{
  "scene_id": "scene-001",
  "previous_state": "LOADING",
  "current_state": "ACTIVE",
  "timestamp": "2026-03-03T23:45:00Z",
  "trigger": "activate",
  "metadata": {}
}
```

### Error Events
Published to Kafka topic `scene.error`:
```json
{
  "scene_id": "scene-001",
  "error_code": "E004",
  "error_message": "Agent health check failed",
  "state": "ACTIVE",
  "recoverable": true,
  "timestamp": "2026-03-03T23:45:00Z"
}
```

---

## Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| State transition latency | <100ms | For direct transitions |
| Activate scene | <500ms | From LOADING to ACTIVE |
| Transition completion | <5s | For crossfade transitions |
| State persistence | <50ms | Redis write |
| Recovery from checkpoint | <2s | ERROR to ACTIVE |

---

## Security Considerations

- State transitions authenticated via JWT token
- Operator role required for manual transitions
- Audit log for all state changes
- Rate limiting on transition API (10/second)

---

## Future Enhancements

1. **Conditional Transitions:** Support for complex transition conditions
2. **State History Query:** API for querying past states
3. **Parallel Transitions:** Multiple scenes transitioning simultaneously
4. **Automated Recovery:** Self-healing from common errors
5. **State Visualization:** Real-time state machine visualization in Console

---

**Document Status:** ✅ Approved
**Next Task:** Task 2.1.2 - Define scene configuration schema

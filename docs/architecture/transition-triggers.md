# Scene Transition Trigger System

**Version:** 1.0.0
**Date:** 2026-03-04
**Component:** OpenClaw Orchestrator - Transition Management
**Status:** 🔄 Design Phase

---

## Overview

The Transition Trigger System enables automated and manual scene transitions within Project Chimera. Transitions can be triggered by time schedules, external events (Kafka), or manual operator intervention. The system handles trigger priority, conflict resolution, and ensures smooth handoffs between scenes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Transition Trigger System                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Time-Based │    │  Event-Based │    │    Manual    │               │
│  │   Triggers   │    │   Triggers   │    │   Triggers   │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                   │                        │
│         └───────────────────┼───────────────────┘                        │
│                             │                                            │
│                             ▼                                            │
│                    ┌─────────────────┐                                   │
│                    │  Trigger Queue  │                                   │
│                    │  (Priority)     │                                   │
│                    └────────┬────────┘                                   │
│                             │                                            │
│                             ▼                                            │
│                    ┌─────────────────┐                                   │
│                    │ Conflict Resolver│                                  │
│                    └────────┬────────┘                                   │
│                             │                                            │
│                             ▼                                            │
│                    ┌─────────────────┐                                   │
│                    │ Transition Exec │                                   │
│                    └────────┬────────┘                                   │
│                             │                                            │
│                             ▼                                            │
│                    ┌─────────────────┐                                   │
│                    │  State Machine  │                                   │
│                    └─────────────────┘                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Trigger Types

### 1. Time-Based Triggers

**Description:** Transitions triggered at scheduled times or durations.

#### 1.1 Scheduled Time Triggers

Transition at a specific timestamp (e.g., "2026-03-04T14:30:00Z").

**Configuration:**
```json
{
  "trigger_id": "tt-001",
  "type": "scheduled_time",
  "source_scene_id": "scene-001",
  "target_scene_id": "scene-002",
  "scheduled_time": "2026-03-04T14:30:00Z",
  "transition_type": "crossfade",
  "priority": 50,
  "enabled": true
}
```

**Use Cases:**
- Pre-planned show segments
- Time-synchronized performances
- Scheduled intermissions

#### 1.2 Duration Triggers

Transition after a scene has been active for a specified duration.

**Configuration:**
```json
{
  "trigger_id": "tt-002",
  "type": "duration",
  "source_scene_id": "scene-001",
  "target_scene_id": "scene-002",
  "duration_seconds": 300,
  "transition_type": "fade",
  "priority": 50,
  "enabled": true
}
```

**Use Cases:**
- Scene timeouts (max scene duration)
- Paced performance flow
- Automated progression

#### 1.3 Interval Triggers

Recurring transitions at fixed intervals.

**Configuration:**
```json
{
  "trigger_id": "tt-003",
  "type": "interval",
  "source_scene_pattern": "scene-*",
  "target_scene_sequence": ["scene-001", "scene-002", "scene-003"],
  "interval_seconds": 600,
  "transition_type": "crossfade",
  "priority": 40,
  "enabled": true
}
```

**Use Cases:**
- Rotating content scenes
- Automated showcase loops
- Background scene cycling

---

### 2. Event-Based Triggers

**Description:** Transitions triggered by Kafka events from other services.

#### 2.1 Audience Input Triggers

Transition based on audience response thresholds.

**Kafka Topic:** `audience.response.detected`

**Event Schema:**
```json
{
  "event_type": "audience_threshold_reached",
  "scene_id": "scene-001",
  "threshold_type": "positive_sentiment",
  "current_value": 0.85,
  "threshold": 0.80,
  "duration_seconds": 30,
  "timestamp": "2026-03-04T14:25:00Z",
  "suggested_target": "scene-002"
}
```

**Configuration:**
```json
{
  "trigger_id": "et-001",
  "type": "audience_threshold",
  "source_scene_id": "scene-001",
  "event_condition": {
    "topic": "audience.response.detected",
    "event_type": "audience_threshold_reached",
    "threshold_type": "positive_sentiment",
    "min_duration": 30
  },
  "target_scene_id": "scene-002",
  "transition_type": "fade",
  "priority": 70,
  "enabled": true
}
```

**Use Cases:**
- Sentiment-driven progression
- Audience achievement unlocks
- Interactive story branches

#### 2.2 Agent Health Triggers

Transition when an agent becomes unhealthy.

**Kafka Topic:** `agent.health.changed`

**Event Schema:**
```json
{
  "event_type": "agent_unhealthy",
  "scene_id": "scene-001",
  "agent_id": "scenespeak",
  "health_status": "unhealthy",
  "error_code": "AGENT_TIMEOUT",
  "timestamp": "2026-03-04T14:25:00Z"
}
```

**Configuration:**
```json
{
  "trigger_id": "et-002",
  "type": "agent_health",
  "source_scene_id": "scene-001",
  "event_condition": {
    "topic": "agent.health.changed",
    "event_type": "agent_unhealthy",
    "critical_agents": ["scenespeak", "sentiment"]
  },
  "target_scene_id": "scene-fallback",
  "transition_type": "cut",
  "priority": 90,
  "enabled": true
}
```

**Use Cases:**
- Automated fallback on failure
- Degraded mode activation
- Emergency scene switch

#### 2.3 Custom Event Triggers

Transition on arbitrary custom events.

**Kafka Topic:** `custom.transition.request`

**Event Schema:**
```json
{
  "event_type": "custom_transition",
  "source_scene_id": "scene-001",
  "target_scene_id": "scene-002",
  "transition_type": "crossfade",
  "metadata": {
    "reason": "Interactive choice completed",
    "choice_id": "choice-a"
  },
  "timestamp": "2026-03-04T14:25:00Z"
}
```

**Configuration:**
```json
{
  "trigger_id": "et-003",
  "type": "custom_event",
  "source_scene_id": "scene-001",
  "event_condition": {
    "topic": "custom.transition.request",
    "event_type": "custom_transition",
    "metadata_filter": {
      "choice_id": "choice-a"
    }
  },
  "target_scene_id": "scene-002",
  "transition_type": "crossfade",
  "priority": 60,
  "enabled": true
}
```

**Use Cases:**
- Interactive narrative choices
- External system integration
- Game-like progression

---

### 3. Manual Triggers

**Description:** Transitions initiated by human operators via API or Console.

#### 3.1 API Endpoint Triggers

REST API endpoint for manual transitions.

**Endpoint:** `POST /api/v1/scenes/{scene_id}/transition`

**Request Schema:**
```json
{
  "target_scene_id": "scene-002",
  "transition_type": "crossfade",
  "reason": "Manual operator transition",
  "operator_id": "operator-001",
  "metadata": {}
}
```

**Response Schema:**
```json
{
  "transition_id": "trans-001",
  "source_scene_id": "scene-001",
  "target_scene_id": "scene-002",
  "status": "initiated",
  "estimated_completion": "2026-03-04T14:25:05Z",
  "transition_type": "crossfade"
}
```

#### 3.2 Console Triggers

WebSocket-based manual transitions from Operator Console.

**WebSocket Message:**
```json
{
  "type": "transition_request",
  "source_scene_id": "scene-001",
  "target_scene_id": "scene-002",
  "transition_type": "fade",
  "operator_id": "operator-001",
  "request_id": "req-001"
}
```

**WebSocket Response:**
```json
{
  "type": "transition_response",
  "request_id": "req-001",
  "status": "approved",
  "transition_id": "trans-001",
  "message": "Transition initiated"
}
```

---

## Trigger Priority System

### Priority Levels

| Priority | Level      | Description                        | Precedence |
|----------|------------|------------------------------------|------------|
| 100      | CRITICAL   | Emergency/failover                 | Highest    |
| 90-99    | URGENT     | Agent health failures              |            |
| 80-89    | HIGH       | Audience safety events             |            |
| 70-79    | ELEVATED   | Audience threshold triggers        |            |
| 60-69    | NORMAL     | Custom events, scheduled           |            |
| 50-59    | STANDARD   | Duration-based triggers            |            |
| 40-49    | LOW        | Interval triggers                  |            |
| 0-39     | BACKGROUND  | Background/automation             | Lowest     |

### Priority Conflict Resolution

When multiple triggers are ready simultaneously:

1. **Sort by priority** (highest first)
2. **Within same priority:**
   - CRITICAL (90-100): Agent health > Safety
   - URGENT (80-89): Safety > Audience
   - Other: FIFO by trigger creation time
3. **Cancelled triggers:** Lower-priority triggers for the same source scene are cancelled

**Example:**
```
Scene A has pending triggers:
- Trigger 1: Duration timeout (Priority 50, created 14:00:00)
- Trigger 2: Agent unhealthy (Priority 90, created 14:05:00)

Resolution: Trigger 2 fires first (higher priority)
Trigger 1 is cancelled (same source scene)
```

---

## Trigger State Machine

```
┌──────────┐    enable()    ┌──────────┐
│  CREATED │───────────────>│  ENABLED │
└──────────┘                 └────┬─────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │  ARMED   │  │  PAUSED  │  │  TRIGGERED│
              └─────┬────┘  └──────────┘  └────┬─────┘
                    │                           │
                    │        fire()             │
                    └───────────────────────────┘
                                      │
                                      ▼
                               ┌──────────┐
                               │ COMPLETE │
                               └──────────┘
```

**States:**
- **CREATED:** Trigger defined but not active
- **ENABLED:** Trigger active and monitoring
- **ARMED:** Trigger condition met, ready to fire
- **PAUSED:** Temporarily disabled
- **TRIGGERED:** Trigger fired, transition in progress
- **COMPLETE:** Transition completed
- **CANCELLED:** Trigger cancelled (higher priority won)

---

## Data Models

### Trigger Configuration

```python
@dataclass
class TriggerConfig:
    """Base trigger configuration."""
    trigger_id: str
    type: TriggerType
    source_scene_id: str
    target_scene_id: str
    transition_type: TransitionType
    priority: int = 50
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### Time-Based Trigger

```python
@dataclass
class TimeTrigger(TriggerConfig):
    """Time-based trigger configuration."""
    time_type: TimeTriggerType  # SCHEDULED, DURATION, INTERVAL

    # For SCHEDULED
    scheduled_time: Optional[datetime] = None

    # For DURATION
    duration_seconds: Optional[int] = None

    # For INTERVAL
    interval_seconds: Optional[int] = None
    target_scene_sequence: Optional[List[str]] = None
```

### Event-Based Trigger

```python
@dataclass
class EventTrigger(TriggerConfig):
    """Event-based trigger configuration."""
    event_condition: EventCondition

@dataclass
class EventCondition:
    """Event matching conditions."""
    topic: str
    event_type: str
    metadata_filter: Optional[Dict[str, Any]] = None

    # For audience thresholds
    threshold_type: Optional[str] = None
    min_duration: Optional[int] = None

    # For agent health
    critical_agents: Optional[List[str]] = None
```

### Trigger State

```python
@dataclass
class TriggerState:
    """Current state of a trigger."""
    trigger_id: str
    state: TriggerStateType  # ENABLED, ARMED, TRIGGERED, COMPLETE, CANCELLED
    armed_at: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

---

## API Endpoints

### Trigger Management

#### List Triggers
```
GET /api/v1/triggers
Query Params: scene_id, type, state, enabled
```

#### Create Trigger
```
POST /api/v1/triggers
Body: TriggerConfig
```

#### Get Trigger
```
GET /api/v1/triggers/{trigger_id}
```

#### Update Trigger
```
PATCH /api/v1/triggers/{trigger_id}
Body: Partial TriggerConfig
```

#### Delete Trigger
```
DELETE /api/v1/triggers/{trigger_id}
```

#### Enable/Disable Trigger
```
POST /api/v1/triggers/{trigger_id}/enable
POST /api/v1/triggers/{trigger_id}/disable
```

### Manual Transitions

#### Initiate Transition
```
POST /api/v1/scenes/{scene_id}/transition
Body: {target_scene_id, transition_type, reason, operator_id}
```

#### Cancel Pending Transition
```
DELETE /api/v1/transitions/{transition_id}
```

#### Get Transition Status
```
GET /api/v1/transitions/{transition_id}
```

---

## Kafka Integration

### Consumer Topics

| Topic | Purpose | Handler |
|-------|---------|---------|
| `audience.response.detected` | Audience sentiment/input | AudienceTriggerHandler |
| `agent.health.changed` | Agent health status | HealthTriggerHandler |
| `custom.transition.request` | Custom events | CustomTriggerHandler |

### Producer Topics

| Topic | Purpose |
|-------|---------|
| `scene.transition.requested` | Transition initiated |
| `scene.transition.completed` | Transition finished |
| `scene.transition.failed` | Transition error |

---

## Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| Trigger evaluation latency | <10ms | For time-based checks |
| Event to trigger latency | <50ms | From Kafka consume |
| Manual trigger response | <100ms | API endpoint |
| Trigger state persistence | <20ms | Redis write |
| Priority sorting | O(n log n) | For n pending triggers |

---

## Error Handling

### Trigger Failures

| Error Type | Handling | Retry |
|------------|----------|-------|
| Target scene not found | Log error, mark failed | No |
| Invalid transition | Validation error | No |
| Redis persistence failure | Log warning, continue in memory | No |
| Kafka consumer failure | Reconnect with backoff | Yes (3x) |
| Transition timeout | Force CUT transition | No |

### Fallback Behavior

When a trigger fails:
1. Log error with full context
2. Mark trigger as FAILED
3. Send alert to operator
4. If CRITICAL priority, attempt fallback scene
5. Persist failure for analysis

---

## Security Considerations

- Manual transitions require JWT authentication with OPERATOR role
- Trigger creation requires ADMIN or OPERATOR role
- Audit log for all trigger state changes
- Rate limiting: 10 triggers per second per scene
- Input validation on all trigger configurations
- Sanitize Kafka event data before processing

---

## Testing Strategy

### Unit Tests
- Trigger configuration validation
- Priority sorting logic
- Condition matching for events
- State transitions

### Integration Tests
- End-to-end trigger flow
- Kafka event consumption
- API endpoint responses
- Redis persistence

### Scenario Tests
- Multiple simultaneous triggers
- Priority conflict resolution
- Agent failure fallback
- Manual override during automation

---

## Future Enhancements

1. **Conditional Triggers:** Complex boolean logic for trigger conditions
2. **Trigger Templates:** Reusable trigger configurations
3. **Trigger Chaining:** Output of one trigger inputs to another
4. **Machine Learning Triggers:** Adaptive triggers based on historical data
5. **Trigger Analytics:** Dashboard for trigger performance metrics

---

**Document Status:** 🔄 Draft - Pending Review
**Next Task:** Task 2.2.2 - Implement time-based transitions

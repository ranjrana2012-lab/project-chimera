# Nemo Claw Orchestrator Design Specification

**Project:** Project Chimera
**Component:** Nemo Claw Orchestrator (Replacement for OpenClaw Orchestrator)
**Date:** 2026-03-18
**Author:** Design Review
**Status:** Draft

---

## Executive Summary

This specification outlines the replacement of the current OpenClaw Orchestrator with NVIDIA Nemo Claw, an open-source stack that adds privacy and security controls to autonomous agent orchestration. The replacement leverages the user's DGX Spark GB0 ARM64 system for local Nemotron model inference while maintaining compatibility with existing Project Chimera agents.

### Key Objectives

1. **Security & Privacy**: Implement OpenShell policy-based guardrails for all agent interactions
2. **Hardware Optimization**: Leverage DGX Spark GB0 ARM64 for accelerated local inference
3. **Autonomous Capabilities**: Enable 24/7 self-evolving agents with safety controls
4. **Simplified Deployment**: Single-command deployment while preserving existing agent investments

### Success Criteria

- [ ] All 8 existing agents function with Nemo Claw orchestration
- [ ] 95% of LLM inference runs locally on DGX (Nemotron)
- [ ] OpenShell policies enforce content safety and data privacy
- [ ] Show state machine operates with WebSocket real-time updates
- [ ] Zero data loss during migration from OpenClaw

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Components](#2-components)
3. [Data Flow](#3-data-flow)
4. [Error Handling](#4-error-handling)
5. [Testing Strategy](#5-testing-strategy)
6. [Implementation Phases](#6-implementation-phases)
7. [API Changes](#7-api-changes)
8. [Deployment](#8-deployment)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEMO CLAW ORCHESTRATOR                           │
│                   (DGX Spark GB0 ARM64)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  OPEN SHELL RUNTIME                          │   │
│  │         Policy-Based Guardrails & Enforcement               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  PRIVACY ROUTER                              │   │
│  │     Intelligent LLM Backend Selection                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │   LOCAL      │  │   CLOUD      │  │  HYBRID      │      │   │
│  │  │  Nemotron    │  │  Fallback    │  │  Smart       │      │   │
│  │  │  (DGX GPU)   │  │  (Guarded)   │  │  Routing     │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AGENT COORDINATION LAYER                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            STATE MACHINE (Redis-backed)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Mapping

| Old (OpenClaw) | New (Nemo Claw) | Notes |
|----------------|-----------------|-------|
| FastAPI Orchestrator | Nemo Claw Core | New runtime |
| Direct LLM calls | Privacy Router | Local Nemotron |
| No policy layer | OpenShell Runtime | New safety layer |
| HTTP agent calls | Policy-filtered calls | Same endpoints, filtered |
| Show state machine | Redis-backed state | Enhanced persistence |

### 1.3 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Base Runtime** | NVIDIA Nemo Claw | Latest |
| **Policy Engine** | OpenShell | Built-in |
| **LLM Backend** | Nemotron (local) | ARM64-optimized |
| **API Framework** | FastAPI | 0.104+ |
| **State Store** | Redis | 7.x |
| **WebSocket** | FastAPI WebSocket | Built-in |
| **Monitoring** | OpenTelemetry | 1.x |

---

## 2. Components

### 2.1 OpenShell Policy Engine

**Purpose:** Enforce security policies and content filtering

**File:** `services/nemoclaw-orchestrator/policy/engine.py`

**Key Classes:**
```python
class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    SANITIZE = "sanitize"
    ESCALATE = "escalate"

@dataclass
class PolicyRule:
    name: str
    agent: str
    action: PolicyAction
    conditions: dict
    output_filter: bool = True

class PolicyEngine:
    async def check_input(self, agent, skill, input_data) -> PolicyResult
    async def filter_output(self, agent, response) -> dict
    async def sanitize_input(self, input_data) -> dict
```

**Default Policies:**
- Safety Filter: Always allow, highest priority
- SceneSpeak: Sanitize outputs, max length limits
- Autonomous Agent: Escalate high-complexity tasks
- Sentiment: Allow freely (read-only)

### 2.2 Privacy Router

**Purpose:** Route LLM calls to local Nemotron (95%) or guarded cloud (5%)

**File:** `services/nemoclaw-orchestrator/llm/privacy_router.py`

**Key Classes:**
```python
class LLMBackend(str, Enum):
    NEMOTRON_LOCAL = "nemotron_local"
    CLOUD_GUARDED = "cloud_guarded"
    FALLBACK = "fallback"

class PrivacyRouter:
    async def route(self, prompt: str, context: dict) -> LLMBackend
    async def generate(self, prompt: str, context: dict) -> str
```

**Routing Logic:**
1. Check policy for privacy requirements
2. Check DGX availability
3. Route to Nemotron if available (95% target)
4. Fallback to guarded cloud with PII stripping

### 2.3 Agent Coordinator

**Purpose:** Manage agent communication with policy filtering

**File:** `services/nemoclaw-orchestrator/agents/coordination.py`

**Key Classes:**
```python
class AgentCoordinator:
    async def call_agent(self, agent_name, skill, input_data) -> dict
    async def call_with_privacy_router(self, agent, skill, input) -> dict
    async def call_agent_http(self, agent, skill, input) -> dict
```

**Call Flow:**
1. Policy check (input)
2. Sanitize if required
3. Execute agent call (with privacy router if LLM)
4. Policy check (output)
5. Return filtered response

### 2.4 Agent Adapters

**Purpose:** Interface adapters for each existing agent

**File:** `services/nemoclaw-orchestrator/agents/adapters.py`

**Adapters:**
- `SceneSpeakAdapter` - LLM-dependent, uses Privacy Router
- `SentimentAdapter` - ML model, direct HTTP
- `CaptioningAdapter` - Whisper service, direct HTTP
- `BSLAdapter` - WebGL avatar, direct HTTP
- `AutonomousAdapter` - LLM-dependent, escalation required

### 2.5 State Machine

**Purpose:** Manage show state transitions

**File:** `services/nemoclaw-orchestrator/state/machine.py`

**States:**
```
IDLE → PRELUDE → ACTIVE → POSTLUDE → CLEANUP → IDLE
```

**Transitions:**
- Start show: IDLE → PRELUDE
- Duration elapsed: PRELUDE → ACTIVE
- Stop/end: ACTIVE → POSTLUDE
- Timeout: POSTLUDE → CLEANUP
- Complete: CLEANUP → IDLE

---

## 3. Data Flow

### 3.1 Show Lifecycle Flow

1. **Start Show**
   - Operator Console → POST /api/show/start
   - Policy check (allow/deny)
   - Create state in Redis (IDLE)
   - Transition to PRELUDE
   - Generate prelude via Nemotron
   - Broadcast via WebSocket

2. **Active Show**
   - Audience input via WebSocket
   - Policy sanitize input
   - Route to appropriate agent
   - Privacy Router (if LLM needed)
   - Output filter
   - Broadcast response

3. **End Show**
   - POST /api/show/end
   - Transition through POSTLUDE, CLEANUP
   - Archive state to Redis
   - Broadcast IDLE state

### 3.2 Agent Request Flow

```
Request → OpenShell Input Check
           ├── DENY → 403 Policy Violation
           ├── SANITIZE → Clean Input
           └── ALLOW → Route to Agent
               └── Requires LLM?
                   ├── Yes → Privacy Router → Nemotron (95%) / Cloud (5%)
                   └── No → Direct HTTP
           └── Response → OpenShell Output Check
               ├── DENY → Filtered Error
               ├── SANITIZE → Clean Output
               └── ALLOW → Return Result
```

### 3.3 WebSocket Updates

**Message Types:**
- `show_state` - State transitions
- `agent_response` - Agent outputs
- `sentiment_update` - Sentiment analysis
- `error` - Error messages

**All messages filtered by OpenShell before broadcast.**

---

## 4. Error Handling

### 4.1 Error Categories

| Error Type | HTTP Code | Retry | Fallback |
|------------|-----------|-------|----------|
| PolicyViolation | 403 | No | Block |
| AgentUnavailable | 503 | Yes (3x) | Cached response |
| LL RoutingError | 500 | Yes (2x) | Cloud fallback |
| StateTransitionError | 422 | No | Valid states list |
| CircuitBreakerOpen | 503 | No | Retry-After header |

### 4.2 Retry Strategy

- **Exponential backoff**: 1s, 2s, 4s delays
- **Max retries**: 3 for agent calls, 2 for LLM calls
- **Fallback mode**: Graceful degradation with cached responses

### 4.3 Circuit Breaker

- Trips after 5 consecutive failures
- Stays open for 60 seconds
- Half-open state for testing recovery

---

## 5. Testing Strategy

### 5.1 Test Coverage Targets

| Component | Unit | Integration | E2E | Target |
|-----------|------|-------------|-----|--------|
| Policy Engine | ✓✓✓ | ✓ | - | 95% |
| Privacy Router | ✓✓✓ | ✓ | - | 90% |
| Agent Coordinator | ✓✓ | ✓✓ | ✓ | 85% |
| State Machine | ✓✓✓ | ✓✓ | ✓ | 90% |
| WebSocket Manager | ✓✓ | ✓ | ✓✓ | 85% |
| API Endpoints | ✓ | ✓✓ | ✓✓ | 80% |

### 5.2 Test Structure

```
services/nemoclaw-orchestrator/tests/
├── unit/
│   ├── test_policy_engine.py
│   ├── test_privacy_router.py
│   ├── test_agent_coordinator.py
│   └── test_state_machine.py
├── integration/
│   ├── test_agent_flow.py
│   ├── test_show_lifecycle.py
│   └── test_websocket_updates.py
└── e2e/
    └── show-lifecycle.spec.ts (Playwright)
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Install Nemo Claw on DGX Spark GB0
- [ ] Set up OpenShell runtime
- [ ] Configure Nemotron local inference
- [ ] Create project structure

### Phase 2: Core Components (Week 3-4)
- [ ] Implement PolicyEngine with Chimera policies
- [ ] Implement PrivacyRouter with DGX routing
- [ ] Create agent adapters for all 8 agents
- [ ] Port state machine to Redis-backed

### Phase 3: API & WebSocket (Week 5-6)
- [ ] Implement FastAPI endpoints with policy filtering
- [ ] Port WebSocket manager with output filtering
- [ ] Implement show lifecycle APIs

### Phase 4: Testing & Migration (Week 7-8)
- [ ] Unit tests for all components
- [ ] Integration tests for agent communication
- [ ] E2E tests for show lifecycle
- [ ] Data migration from OpenClaw

### Phase 5: Deployment (Week 9)
- [ ] Production deployment on DGX
- [ ] Monitor performance and metrics
- [ ] Validate all agents functional
- [ ] Retire OpenClaw orchestrator

---

## 7. API Changes

### 7.1 Endpoints

Most endpoints remain compatible with OpenClaw:

| Endpoint | Change | Notes |
|----------|--------|-------|
| `GET /health/live` | No change | Health check |
| `GET /health/ready` | Enhanced | Includes Nemo Claw status |
| `POST /v1/orchestrate` | Enhanced | Policy-filtered |
| `GET /skills` | No change | Skill listing |
| `POST /api/show/start` | No change | Show control |
| `WebSocket /ws/show` | Enhanced | Filtered messages |

### 7.2 New Endpoints

- `GET /policy/rules` - List active policies
- `POST /policy/test` - Test input against policies
- `GET /llm/status` - Privacy Router status
- `GET /llm/backends` - Available LLM backends

### 7.3 Response Changes

All responses include policy metadata:

```json
{
  "result": {...},
  "policy": {
    "checked": true,
    "action": "sanitize",
    "rules_applied": ["profanity-filter", "length-limit"]
  },
  "llm_backend": "nemotron_local"
}
```

---

## 8. Deployment

### 8.1 Installation

```bash
# Install Nemo Claw
curl -fsSL https://nvidia.com/nemoclaw.sh | bash
nemoclaw onboard

# Configure for Project Chimera
cd services/nemoclaw-orchestrator
cp .env.example .env
# Edit .env with agent URLs and DGX config

# Install Python dependencies
pip install -r requirements.txt

# Start service
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 8.2 Docker Deployment

```dockerfile
# Dockerfile
FROM nvcr.io/nvidia/nemoclaw:latest-arm64

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.3 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEMOCLAW_MODE` | `local` | local | hybrid | cloud |
| `NEMOTRON_MODEL` | `nemotron-8b` | Local model name |
| `DGX_GPU_ID` | `0` | GPU device ID |
| `POLICY_STRICTNESS` | `medium` | low | medium | high |
| `REDIS_URL` | `redis://localhost:6379` | State store |

---

## Appendix A: Existing Agents Compatibility

All 8 existing agents remain compatible:

| Agent | Port | Changes Required |
|-------|------|------------------|
| SceneSpeak | 8001 | LLM calls via Privacy Router |
| Captioning | 8002 | No changes |
| BSL | 8003 | No changes |
| Sentiment | 8004 | No changes |
| Lighting/Sound/Music | 8005 | No changes |
| Safety Filter | 8006 | No changes |
| Operator Console | 8007 | WebSocket filtered |
| Music Generation | 8011 | No changes |

---

## Appendix B: Rollback Plan

If Nemo Claw deployment fails:

1. Stop Nemo Claw service
2. Start existing OpenClaw orchestrator
3. Verify all agents reconnect
4. Review logs for failure cause
5. Address issue and retry migration

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-18 | 0.1.0 | Initial design specification |

---

**Next Steps:**

1. Review and approve this specification
2. Create detailed implementation plan
3. Begin Phase 1: Foundation

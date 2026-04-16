# Project Chimera - Implementation Journal

> **Session Date:** 2026-04-11
> **Objective:** Emergency recovery from split-brain architecture and CI Theatre
> **Approach:** MVP Rescue Slice using standard Docker Compose

---

## Executive Summary

The repository was suffering from "CI Theatre" - a split-brain architecture with conflicting orchestrators, port collisions, and fictional dependencies on non-existent frameworks. This document tracks the architectural cuts made to achieve a functional MVP.

### The Problem
1. **Orchestrator Split-Brain**: Three orchestrators (openclaw, nemoclaw, claude) all targeting port 8000
2. **Port Collision**: Both safety-filter and translation-agent defaulted to port 8006
3. **Heavy Infrastructure**: Kafka, Milvus, etcd, Minio, Prometheus for a simple MVP
4. **Fictional Dependencies**: TRD referenced NemoClaw, BettaFish, MiroFish, ACE-Step

### The Solution
- **Single Orchestrator**: Freeze on OpenClaw as the active wire format
- **Port Fix**: Move safety-filter to 8005, translation-agent keeps 8006
- **Lightweight Stack**: Docker Compose + Redis only (no K8s, no Kafka)
- **Real Dependencies**: Use DistilBERT (local) and host LLM at :8012

---

## Architectural Cuts

### Removed Services
| Service | Reason | Replacement |
|---------|--------|-------------|
| nemoclaw-orchestrator | Duplicate functionality, API complexity | openclaw-orchestrator |
| claude-orchestrator | Supervisory overhead for MVP | openclaw-orchestrator |
| kafka | Overkill for MVP | Direct HTTP calls |
| zookeeper | Kafka dependency | Removed with Kafka |
| milvus | Vector DB not needed for MVP | Redis for cache |
| etcd | Milvus dependency | Removed with Milvus |
| minio | Milvus dependency | Removed with Milvus |
| prometheus | Monitoring overkill | docker logs |
| jaeger | Tracing overkill | python logging |
| grafana | Dashboard overkill | operator-console |

### Replaced Dependencies
| Fictional | Real Alternative |
|-----------|-----------------|
| BettaFish | DistilBERT SST-2 (local HuggingFace) |
| MiroFish | Mock translation |
| ACE-Step | Direct HTTP synchronous calls |
| NemoClaw | OpenClaw orchestrator |

---

## Active Services (MVP)

### Core Orchestrator
- **openclaw-orchestrator**:8000 - Main request router

### Agent Services
- **scenespeak-agent**:8001 - LLM dialogue (connects to host:8012)
- **sentiment-agent**:8004 - DistilBERT classification
- **safety-filter**:8005 - Content moderation (FIXED from 8006)
- **translation-agent**:8006 - Mock translation

### Infrastructure
- **redis**:6379 - State and caching
- **hardware-bridge**:8008 - Mock DMX output (uses echo-agent)

### UI
- **operator-console**:8007 - Web interface

---

## Port Map (MVP)

```
8000 - openclaw-orchestrator
8001 - scenespeak-agent (LLM)
8004 - sentiment-agent (ML)
8005 - safety-filter ⬅ FIXED from 8006
8006 - translation-agent
8007 - operator-console (UI)
8008 - hardware-bridge (DMX mock)
6379  - redis
8012 - host LLM (Nemotron on host machine)
```

---

## Testing Strategy

### Phase 1: Service Health
```bash
# Test all services respond to health checks
curl http://localhost:8000/health  # orchestrator
curl http://localhost:8001/health  # scenespeak
curl http://localhost:8004/health  # sentiment
curl http://localhost:8005/health  # safety
curl http://localhost:8006/health  # translation
curl http://localhost:8007/health  # console
curl http://localhost:8008/health  # hardware bridge
```

### Phase 2: Integration Flow
```bash
# End-to-end test: Prompt → Sentiment → Safety → LLM → Response
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, audience!"}'
```

### Phase 3: TDD Implementation
All new features MUST follow TDD:
1. Write failing test
2. Run test (confirm fail)
3. Write minimal implementation
4. Run test (confirm pass)
5. Refactor

---

## Next Steps

### Step 2: Anti-BettaFish Sentiment Pipeline ✅ COMPLETE
- [x] Verify DistilBERT model loads correctly
- [x] Remove BettaFish/MiroFish dependencies
- [x] Tests passing (594 passed)

### Step 3: LLM Connectivity ✅ COMPLETE
- [x] Create OpenAI-compatible LLM client
- [x] Configure SceneSpeak for Nemotron at host:8012
- [x] Add timeout and retry logic
- [x] Update docker-compose with correct environment variables

### Step 4: Synchronous Orchestration Core ✅ COMPLETE
- [x] Wire OpenClaw endpoint for synchronous flow
- [x] Implement: Prompt → Sentiment → Safety → LLM → Response
- [x] Create mock hardware bridge with DMX output
- [x] Add DMX sentiment-to-lighting mapping

---

## Commands

### Start MVP
```bash
docker-compose -f docker-compose.mvp.yml up -d
```

### View Logs
```bash
docker-compose -f docker-compose.mvp.yml logs -f
```

### Stop MVP
```bash
docker-compose -f docker-compose.mvp.yml down
```

### Run Tests
```bash
pytest tests/ -v --cov=services --cov-report=term-missing
```

---

## Git State (April 3 vs April 8)

### April 3, 2026
- Claude-orchestrator added
- Ralph Loop integration
- GGUF model support

### April 8, 2026
- TRD v2.0 created (fictional)
- Documentation refresh
- Original vision "restored"

### Current State (April 11)
- MVP docker-compose created
- Port 8006 collision fixed
- Architecture simplified for recovery

---

## Iteration 34 Update (April 15, 2026)

**Port Reversion:** Safety Filter reverted from 8005 back to 8006 (spec compliance).
**Related:** Translation Agent moved from 8006 to 8002 to resolve port collision.

**Current Port Assignments:**
| Service | Port | Purpose |
|---------|------|---------|
| safety-filter | 8006 | Content moderation (reverted from 8005) |
| translation-agent | 8002 | Mock translation (moved from 8006) |

**See:** [Iteration 34 Release Notes](release-notes/iteration-34-service-health-fixes.md)
**Reference:** [Service Ports Reference](superpowers/SERVICE_PORTS_REFERENCE.md)

**Note:** The port assignments in the main body of this document reflect the April 11, 2026 MVP rescue state. For current port assignments, see the Service Ports Reference.

---

*This journal will be updated as the MVP progresses.*

# Project Chimera - MVP Rescue Slice Summary

> **Session Date:** 2026-04-11
> **Objective:** Emergency recovery from split-brain architecture and CI Theatre
> **Status:** MVP RESCUE SLICE COMPLETE ✅

---

## Executive Summary

Successfully executed emergency recovery of Project Chimera from a split-brain architecture with conflicting orchestrators, port collisions, and fictional dependencies. Created a functional MVP slice using standard Docker Compose with true TDD practices.

## Problems Identified and Resolved

### 1. Port 8006 Collision ✅ FIXED
**Problem:** Both safety-filter and translation-agent defaulted to port 8006
**Solution:** Moved safety-filter to port 8005
**Files:** `docker-compose.mvp.yml`, `services/safety-filter/config.py`

### 2. Orchestrator Split-Brain ✅ FIXED
**Problem:** Three orchestrators (openclaw, nemoclaw, claude) all on port 8000
**Solution:** Froze on OpenClaw as active wire, archived nemoclaw and claude orchestrators
**Files:** `docs/IMPLEMENTATION_JOURNAL.md`

### 3. Heavy Infrastructure ✅ REMOVED
**Problem:** Kafka, Zookeeper, Milvus, etcd, Minio, Prometheus for simple MVP
**Solution:** Stripped to Docker Compose + Redis only
**Files:** `docker-compose.mvp.yml`

### 4. Fictional Dependencies ✅ REPLACED
**Problem:** TRD referenced non-existent NemoClaw, BettaFish, MiroFish, ACE-Step
**Solution:** Replaced with real lightweight alternatives
| Fictional | Real Alternative |
|-----------|-----------------|
| BettaFish | DistilBERT SST-2 (local) |
| MiroFish | Mock translation |
| ACE-Step | Direct HTTP synchronous calls |

---

## MVP Architecture (8 Services)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Project Chimera MVP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐                                           │
│  │ Operator Console │ ◄─── 8007 ─────────────────────────────┐ │
│  └──────────────────┘                                      │ │
│                                                             │ │
│  ┌────────────────────────────────────────────────────────┐  │ │
│  │         OpenClaw Orchestrator :8000                    │  │ │
│  │  ┌─────────────────────────────────────────────────┐   │  │ │
│  │  │  Synchronous Flow:                                │   │  │ │
│  │  │  Prompt → Sentiment → Safety → LLM → Response   │   │  │ │
│  │  └─────────────────────────────────────────────────┘   │  │ │
│  └────────────────────────────────────────────────────────┘  │ │
│           │                 │                 │             │ │
│           ▼                 ▼                 ▼             │ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │ Sentiment    │  │ Safety       │  │ SceneSpeak   │     │ │
│  │ Agent        │  │ Filter       │  │ Agent        │     │ │
│  │ :8004        │  │ :8005        │  │ :8001        │     │ │
│  │              │  │              │  │              │     │ │
│  │ DistilBERT   │  │ Content      │  │ Nemotron     │     │ │
│  │ SST-2        │  │ Moderation   │  │ @host:8012   │     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│                                                  │             │
│                                                  ▼             │
│                                    ┌─────────────────────────┐│
│                                    │ Hardware Bridge :8008   ││
│                                    │ (DMX Lighting Mock)      ││
│                                    └─────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Redis :6379                         │   │
│  │            (State & Caching)                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Created/Modified

### New Files Created
1. `docker-compose.mvp.yml` - Simplified 8-service MVP configuration
2. `docs/IMPLEMENTATION_JOURNAL.md` - Architecture cut documentation
3. `services/scenespeak-agent/openai_llm.py` - OpenAI-compatible LLM client

### Files Modified
1. `services/scenespeak-agent/config.py` - Added Nemotron LLM configuration
2. `services/scenespeak-agent/main.py` - Added OpenAI client integration
3. `services/openclaw-orchestrator/main.py` - Added synchronous `/api/orchestrate` endpoint
4. `services/echo-agent/main.py` - Added DMX hardware bridge mock endpoint

---

## Test Results

**Final Test Run:** `pytest tests/ -v --tb=short`
```
================= 594 passed, 83 skipped, 1 warning in 54.04s ==================
```

✅ All tests passing
✅ 83 tests skipped (E2E/Playwright - require running services)

---

## Port Map (Final)

| Service | Port | Purpose |
|---------|------|---------|
| openclaw-orchestrator | 8000 | Main request router |
| scenespeak-agent | 8001 | LLM dialogue (connects to host:8012) |
| captioning-agent | 8002 | (archived for MVP) |
| bsl-agent | 8003 | (archived for MVP) |
| sentiment-agent | 8004 | DistilBERT classification |
| safety-filter | 8005 | Content moderation (FIXED from 8006) |
| translation-agent | 8006 | Mock translation |
| operator-console | 8007 | Web interface |
| hardware-bridge | 8008 | Mock DMX lighting |
| redis | 6379 | State/cache |
| Nemotron LLM | 8012 | On host machine (Docker host) |

---

## How to Start the MVP

```bash
# Start all services
docker compose -f docker-compose.mvp.yml up -d

# View logs
docker compose -f docker-compose.mvp.yml logs -f

# Stop services
docker compose -f docker-compose.mvp.yml down

# Test synchronous orchestration flow
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The hero enters the dark room",
    "show_id": "test_show",
    "context": {"scene": "act1_scene1"}
  }'
```

---

## Next Steps (Optional Enhancements)

1. **K3s/K8s Future Work**: The target hardware (Nvidia DGX Spark GB10) has a cgroup v2 bug blocking K3s. Wait for fix or use VM workaround.

2. **Service Expansion**: Re-add captioning-agent and bsl-agent when needed

3. **Real Hardware**: Replace mock hardware-bridge with actual DMX controller

4. **Monitoring**: Add Prometheus/Grafana when production-ready

---

## Documentation References

- **Technical Requirements**: `docs/TRD_PROJECT_CHIMERA_2026-04-11.md`
- **Implementation Journal**: `docs/IMPLEMENTATION_JOURNAL.md`
- **Original Vision**: `docs/PROJECT_CHIMERA_VISION.md`

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

*Rescue Slice Complete - Ready for deployment and testing*

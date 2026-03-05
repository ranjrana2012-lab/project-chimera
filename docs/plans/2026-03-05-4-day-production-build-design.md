# 4-Day Production Build Design

**Date:** March 5, 2026
**Status:** Design Approved
**Timeline:** Thursday-Sunday, March 6-9, 2026
**Goal:** Build 10 production-ready services for Monday March 10 student demo

---

## Overview

Build 10 fully functional AI/Platform services in 4 days using a template-based factory approach. All services will be production-ready with Docker support, comprehensive testing, full observability, and integrated with OpenClaw Orchestrator.

**Approach:** Template-Based Factory - Create universal service template, then rapidly instantiate each service with unique business logic.

---

## Current State Assessment

### What Exists (Foundation)

| Component | State | Details |
|-----------|-------|---------|
| Platform Services | 70% Complete | quality-gate, cicd-gateway, monitoring, orchestrator, perf-optimizer |
| scenespeak-agent | 60% Complete | Has main.py, lora_adapter.py, metrics.py, tracing.py, tests/ |
| openclaw-orchestrator | 50% Complete | Has core/, persistence/, transitions/, validation/, tests/ |
| Other 8 agents | 10% Complete | Empty shells, no code |
| Infrastructure | 60% Complete | K8s manifests (Prometheus, AlertManager), Helm charts, 10 workflows |
| Dockerfiles | 0% | None exist |
| Integration | 0% | Services not wired together |

### Architecture (Per docs/reference/architecture.md)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROJECT CHIMERA - v0.4.0                          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        AI AGENTS (Ports 8001-8006)                    │
│  SceneSpeak(8001) Captioning(8002) BSL(8003) Sentiment(8004) LSM(8005) Safety(8006) │
└──────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────┐
│                      OPENCLAW ORCHESTRATOR (Port 8000)                │
│              Skill Router • Agent Coordinator • Event Manager          │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────┐
│              PLATFORM SERVICES (Ports 8010-8013)                       │
│  Dashboard(8010) TestOrch(8011) CI/CD(8012) QualityGate(8013)        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4-Day Implementation Plan

### Day 1 (Thursday, March 6) - Foundation & Template

**Goal:** Create production-ready service template and build OpenClaw Orchestrator

**Morning (4 hours):**
- Create universal service template with:
  - FastAPI structure with health endpoints (/health/live, /health/ready, /metrics)
  - OpenTelemetry tracing (per docs/architecture/008-opentelemetry.md)
  - Prometheus metrics (per monitoring docs)
  - Configuration management (environment variables)
  - Test framework setup (pytest, fixtures)

**Afternoon (4 hours):**
- Build OpenClaw Orchestrator (Port 8000):
  - Skill Router implementation
  - Agent Coordinator (REST client to all agents)
  - Event Manager (Kafka integration)
  - Health checks for all downstream services
  - Dockerfile (ARM64)

**Deliverables:**
- Service template in services/shared/template/
- OpenClaw Orchestrator fully functional
- All tests passing
- Docker image buildable

---

### Day 2 (Friday, March 7) - AI Agents (Part 1)

**Goal:** Build SceneSpeak, Captioning, and BSL agents

**SceneSpeak Agent (Port 8001):**
- Integrate existing code (main.py, lora_adapter.py)
- Add missing API endpoints per docs/api/scenespeak-agent.md
- Dockerfile (ARM64)
- Comprehensive tests
- Integration with GLM 4.7 API

**Captioning Agent (Port 8002):**
- FastAPI service with WebSocket support
- Whisper model integration
- Real-time transcription endpoint
- Dockerfile (ARM64)
- Tests

**BSL Agent (Port 8003):**
- Text-to-BSL gloss translation
- Avatar rendering service
- Dockerfile (ARM64)
- Tests

**Deliverables:**
- 3 AI agents fully functional
- All Docker images built
- Integration tests passing

---

### Day 3 (Saturday, March 8) - AI Agents (Part 2) + Console

**Goal:** Build Sentiment, LSM, Safety, and Operator Console

**Morning:**
- Sentiment Agent (Port 8004): DistilBERT + WorldMonitor sidecar
- Lighting-Sound-Music (Port 8005): DMX/sACN + audio control
- Safety Filter (Port 8006): Multi-layer ML moderation

**Afternoon:**
- Operator Console (Port 8007): FastAPI + WebSocket dashboard
  - Real-time metrics streaming
  - Alert display
  - Manual controls

**Deliverables:**
- 4 more agents fully functional
- Operator Console with live dashboard
- All Docker images built

---

### Day 4 (Sunday, March 9) - Integration + Testing + Demo Prep

**Morning:**
- Integration Testing:
  - End-to-end flow: OpenClaw → All agents
  - WebSocket connectivity (Operator Console)
  - Kafka event flow
  - Redis caching

**Afternoon:**
- Demo Preparation:
  - All services running in Docker/K8s
  - Monitoring dashboards (Grafana)
  - Tracing (Jaeger)
  - Smoke tests
  - Demo script

**Deliverables:**
- Full system integrated and tested
- Demo environment ready
- Documentation updated

---

## Technical Specifications

### Service Template Structure

```
services/<service>/
├── main.py                 # FastAPI with health endpoints
├── config.py               # Configuration with environment variables
├── models.py               # Pydantic models for requests/responses
├── service.py              # Core business logic
├── metrics.py              # Prometheus metrics
├── tracing.py              # OpenTelemetry setup
├── tests/
│   ├── test_main.py        # API endpoint tests
│   ├── test_service.py     # Business logic tests
│   └── conftest.py         # Test fixtures
├── Dockerfile              # Multi-stage ARM64 build
├── requirements.txt        # Service-specific dependencies
└── README.md               # Service documentation
```

### Standard main.py Structure

```python
from fastapi import FastAPI
from opentelemetry import trace
from prometheus_client import Counter, Histogram

app = FastAPI(
    title="{Service Name}",
    description="{Description per API docs}",
    version="1.0.0"
)

# Health Endpoints (required)
@app.get("/health/live")
async def liveness(): return {"status": "ok"}

@app.get("/health/ready")
async def readiness():
    # Check dependencies
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    # Prometheus metrics
    return Response(content=generate_metrics(), media_type="text/plain")

# Business Logic Endpoints (per API docs)
# ...
```

### Dockerfile (ARM64)

```dockerfile
FROM python:3.12-slim

# ARM64 specific
RUN apt-get update && apt-get install -y \
    gcc-aarch64-linux-gnu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE {PORT}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{PORT}"]
```

### AI Model Integration

| Service | Model | Integration |
|---------|-------|-------------|
| SceneSpeak | GLM 4.7 (Z.ai) | API client with retry logic |
| SceneSpeak | Local LLMs | Paths provided tomorrow |
| Captioning | Whisper | Local model via transformers |
| Sentiment | DistilBERT | Local model via transformers |
| Safety | ML Classifier | Train/fit framework |
| BSL | Rule-based + ML | Hybrid approach |

---

## Dependencies & Integration

### Dependency Graph

```
External APIs (Z.ai GLM 4.7, Local LLMs, Local Models)
        │
        ▼
    AI Agents (SceneSpeak, Captioning, BSL, Sentiment, LSM, Safety)
        │
        ▼
OpenClaw Orchestrator (Port 8000)
        │
        ▼
  Infrastructure (Redis, Kafka, Milvus)
```

### Integration Points

1. **OpenClaw → AI Agents (REST):** HTTP calls with timeout and retry
2. **Agent → Agent (Kafka Events):** Async event publishing
3. **All Services → Monitoring (OpenTelemetry):** Automatic tracing

---

## Error Handling & Monitoring

### Error Handling Strategy

```python
@app.post("/generate")
async def generate(request: GenerateRequest):
    with tracer.start_as_current_span("generate_dialogue") as span:
        try:
            result = await generate_dialogue(request.prompt)
            return result
        except APIError as e:
            span.record_exception(e)
            return await retry_generate(request)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
```

### Fallback Strategies

| Service | Primary | Fallback |
|---------|---------|----------|
| SceneSpeak | GLM 4.7 API | Local LLM |
| Captioning | Whisper | Cached results |
| Sentiment | DistilBERT | Rule-based |
| Safety | ML Model | Pattern match |

---

## Success Criteria

### Per Service Definition of Done

- [x] Code: Main.py with all API endpoints from docs/api/
- [x] Tests: 80%+ coverage, unit + integration tests
- [x] Docker: Dockerfile builds successfully on ARM64
- [x] Health: /health/live and /health/ready working
- [x] Metrics: /metrics endpoint with Prometheus metrics
- [x] Tracing: OpenTelemetry spans exported to Jaeger
- [x] Logging: Structured JSON logs
- [x] Documentation: README with usage examples
- [x] Integration: Works with OpenClaw Orchestrator

### Monday Demo Requirements (March 10, 2026)

**Before Students Arrive:**
- All 10 services running in Docker/K8s
- OpenClaw Orchestrator reachable at localhost:8000
- All agents health checks passing
- Operator Console dashboard showing live metrics
- Grafana dashboards loaded
- Jaeger tracing UI accessible

**Demo Flow (30 minutes):**
1. System Overview (5 min)
2. Orchestrator Demo (5 min)
3. AI Agents Demo (10 min)
4. Operator Console (5 min)
5. Observability (5 min)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM API downtime | Medium | High | Fallback to local models, caching |
| ARM64 compatibility | Medium | Medium | Test early, use compatible base images |
| Time overrun | High | High | Prioritize core services, stub non-essential |
| Integration failures | Medium | High | Test integration early, daily smoke tests |
| GPU resource limits | Low | Medium | Optimize model usage, batch processing |

### Daily Checkpoints

**Each day ends with:**
- All services running locally
- Docker images built
- Tests passing (>80%)
- Integration verified with OpenClaw

**Go/No-Go Checkpoints:**
- End of Day 1: Service template + OpenClaw working
- End of Day 2: First 3 agents integrated and tested
- End of Day 3: All agents building and responding
- End of Day 4: Full system demo ready

---

## Next Steps

### Immediate (Tomorrow When Local LLM Paths Provided)

1. Create the service template (shared infrastructure)
2. Set up AI model integrations:
   - GLM 4.7 API client
   - Local LLM loading code
   - Model path configuration
3. Begin Day 1 implementation:
   - Build OpenClaw Orchestrator
   - Set up Kafka, Redis, Milvus locally
   - Verify ARM64 Docker builds

### After Monday (Student Onboarding)

**Week of March 10-14:**
- Students complete Sprint 0 tasks
- Each student owns their service
- Daily standups, code reviews
- Begin Sprint 1 planning

**Sprint 1 (March 17-28):**
- Students enhance their services
- Add features they want
- Learn the codebase
- Present their improvements

---

## Hardware & Infrastructure

**Development Environment:**
- Nvidia DGX Spark GB10 - Arm64
- Eventually: 256GB memory cluster
- Local LLMs already downloaded
- Z.ai GLM 4.7 API access

**AI/ML Resources:**
- Z.ai - GLM 4.7 API
- Local LLMs (paths to be provided)
- GPU support for inference
- Model caching strategies

---

*Design Document - Project Chimera v0.4.0 - March 5, 2026*

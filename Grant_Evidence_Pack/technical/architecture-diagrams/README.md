# Architecture Diagrams - Evidence Pack

**Generated**: 2026-04-09
**Purpose**: Visual documentation of Project Chimera architecture

---

## Available Diagrams

| Diagram | Description | Format | Status |
|---------|-------------|--------|--------|
| [SERVICE_TOPOLOGY.md](SERVICE_TOPOLOGY.md) | Service connectivity and port mapping | Mermaid | ✅ Complete |
| [DATA_FLOW.md](DATA_FLOW.md) | Verified data flows vs. aspirational | Mermaid | ✅ Complete |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Docker/K8s deployment architecture | Mermaid | ✅ Complete |

---

## Quick Reference

### Service Ports
- **8000**: Nemo Claw Orchestrator
- **8001**: SceneSpeak Agent
- **8002**: Captioning Agent
- **8003**: BSL Agent
- **8004**: Sentiment Agent
- **8005**: Lighting/Sound/Music
- **8006**: Safety Filter
- **8007**: Operator Console

### Infrastructure Ports
- **3000**: Grafana
- **6379**: Redis
- **9092**: Kafka
- **9090**: Prometheus
- **11434**: Ollama
- **19530**: Milvus

### Legend
- **Solid Green Line (→)**: Verified working integration
- **Dashed Yellow Line (-->)**: Partially implemented / Not verified
- **Dotted Red Line (...)**: Aspirational / Not implemented

---

## Rendering Mermaid Diagrams

### Option 1: GitHub/GitLab (Native)
- View directly on GitHub/GitLab (auto-rendered)
- Requires: Mermaid syntax support in markdown

### Option 2: VS Code
- Install: Markdown Preview Mermaid Support extension
- Open: Cmd+Shift+V (Mac) / Ctrl+Shift+V (Windows)

### Option 3: Online Editor
- Visit: https://mermaid.live
- Copy/paste diagram code
- Export as PNG/SVG

### Option 4: CLI
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i SERVICE_TOPOLOGY.md -o topology.png
```

---

## Diagram Descriptions

### 1. SERVICE_TOPOLOGY.md

Shows the **service connectivity** and relationships:

- All 8 core services with health status
- External ML/AI dependencies (HuggingFace, Z.AI, Ollama)
- Infrastructure services (Redis, Kafka, Milvus, Prometheus, Grafana)
- Verified connections (solid lines)
- Aspirational connections (dashed lines)

**Key Findings**:
- ✅ All 8 services operational
- ✅ Sentiment → HuggingFace verified
- ✅ SceneSpeak → Z.AI verified
- ⚠️ End-to-end pipeline partially verified

### 2. DATA_FLOW.md

Documents the **data flow architecture**:

- User → Console → Orchestrator flow
- Sentiment analysis pipeline (DistilBERT)
- Dialogue generation pipeline (GLM-4.7)
- State management (Redis)
- Metrics collection (Prometheus)

**Key Findings**:
- ✅ Sentiment → Dialogue pipeline verified working
- ✅ WebSocket communication verified
- ✅ State management operational
- ⚠️ Async messaging (Kafka) not verified

### 3. DEPLOYMENT.md

Describes the **deployment infrastructure**:

- Docker container architecture
- Kubernetes manifests
- CI/CD pipeline
- Resource requirements
- Monitoring & observability

**Key Findings**:
- ✅ Docker deployment verified (10+ days uptime)
- ✅ K8s manifests available
- ✅ Health monitoring operational
- ✅ Metrics collection active

---

## Architecture Summary

### What Works (Verified)
- ✅ All 8 services running and healthy
- ✅ Sentiment analysis (DistilBERT ML)
- ✅ Dialogue generation (GLM-4.7 LLM)
- ✅ Service-to-service HTTP communication
- ✅ State management (Redis)
- ✅ Health monitoring (Prometheus/Grafana)

### What's Partial (Prototype/Incomplete)
- ⚠️ Safety filter (pattern matching only, not ML)
- ⚠️ BSL translation (dictionary-based, ~12 phrases)
- ⚠️ Captioning (infrastructure exists, not tested with audio)

### What's Not Verified
- ❌ End-to-end show workflow
- ❌ Kafka async messaging
- ❌ Milvus vector search
- ❌ Hardware integration (DMX lighting)

---

## Usage Examples

### Verify Service Health
```bash
# Check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    curl -s http://localhost:$port/health/live
done
```

### View Service Logs
```bash
# All services
docker ps --filter "name=chimera-"

# Specific service
docker logs chimera-sentiment -f
```

### Monitor Metrics
```bash
# Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Grafana
open http://localhost:3000
```

---

## Evidence Pack Integration

These diagrams complement:
- **Service Health Documentation**: `evidence/service-health/*.md`
- **API Integration Evidence**: `evidence/api-documentation/*.md`
- **Demonstration Scripts**: `evidence/scripts/*.sh`
- **Phase 1 Assessment**: `evidence/PHASE_1_DELIVERED.md`

---

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2026-04-09 | Initial architecture diagrams | Claude Code |

---

*Documentation Type: Architecture Diagrams*
*Evidence Source: Docker inspection, service testing, log analysis*
*Last Updated: 2026-04-09*

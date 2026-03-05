# Project Chimera Architecture

This document provides a comprehensive overview of the Project Chimera system architecture, including components, data flow, and design decisions.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Overview](#component-overview)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)
- [Scalability and Performance](#scalability-and-performance)
- [Security Architecture](#security-architecture)
- [Monitoring and Observability](#monitoring-and-observability)

## Overview

Project Chimera is a microservices-based AI theatre platform that creates live performances adapting in real-time to audience input. The system uses an event-driven architecture with centralized orchestration.

### Key Design Principles

1. **Modularity** - Each service has a single responsibility
2. **Scalability** - Services can scale independently
3. **Observability** - Comprehensive monitoring and tracing
4. **Safety** - Multi-layer content moderation and human oversight
5. **Accessibility** - Built-in captioning and BSL translation

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Client Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Web UI     │  │  Mobile App  │  │  Stage API   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼──────────────────┼──────────────────┼─────────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│                      API Gateway (Future)                          │
└────────────────────────────┬───────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│                   OpenClaw Orchestrator                            │
│                      (Control Plane)                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                   │
│  │   Skill    │  │  Pipeline  │  │    GPU     │                   │
│  │  Registry  │  │  Executor  │  │  Scheduler │                   │
│  └────────────┘  └────────────┘  └────────────┘                   │
└────┬─────────┬─────────┬─────────┬─────────┬─────────┬───────────┘
     │         │         │         │         │         │
     ▼         ▼         ▼         ▼         ▼         ▼
┌─────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│SceneSpeak│ │Caption│ │ BSL  │ │Sentiment│ │   LSM  │ │Safety  │
│  Agent   │ │ Agent │ │Agent │ │ Agent  │ │Service │ │Filter  │
└────┬─────┘ └───┬──┘ └───┬──┘ └───┬────┘ └────┬───┘ └────┬────┘
     │          │       │       │           │            │
     └──────────┴───────┴───────┴───────────┴────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                      Infrastructure Layer                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐     │
│  │  Redis  │  │  Kafka  │  │ Milvus  │  │   Kubernetes    │     │
│  │  Cache  │  │ Events  │  │ Vector  │  │     (k3s)       │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                      Monitoring Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ Prometheus  │  │   Grafana   │  │   Jaeger    │               │
│  │  Metrics    │  │ Dashboards  │  │   Tracing   │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

## Sidecar Pattern

Project Chimera uses the sidecar pattern for cross-cutting concerns and service augmentation. A sidecar container runs alongside the main application container in the same Pod, sharing resources and local communication.

### WorldMonitor Sidecar (v0.4.0)

The Sentiment Agent employs a WorldMonitor sidecar to provide real-time global context enrichment:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Pod                               │
│                  Sentiment Agent-xxxxx                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Main Container                                │    │
│  │     Sentiment Agent (Port 8004)                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │  FastAPI Application                           │    │    │
│  │  │  - Sentiment Analysis Engine                    │    │    │
│  │  │  - Context Enrichment Layer                     │    │    │
│  │  │  - News Sentiment Analyzer                      │    │    │
│  │  │  - REST API Endpoints                           │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │ localhost:8010                      │
│                           │ WebSocket                           │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Sidecar Container                             │    │
│  │     worldmonitor-sidecar (Port 8010)                    │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │  WorldMonitor Service                          │    │    │
│  │  │  - Global Events Stream                         │    │    │
│  │  │  - News Headlines Aggregator                    │    │    │
│  │  │  - Category Filtering                           │    │    │
│  │  │  - WebSocket Server                             │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
         │                              │
         │ Kubernetes Service            │ Kubernetes Service
         ▼                              ▼
  Sentiment Agent:8004           worldmonitor:8010
         │                              ▲
         └──────────────────────────────┘
              Cluster Communication
```

**Benefits of the Sidecar Pattern:**

1. **Separation of Concerns** - Global context fetching is isolated from sentiment analysis
2. **Independent Scaling** - Sidecar can be updated without changing the main service
3. **Local Communication** - Zero-latency communication via localhost
4. **Shared Lifecycle** - Sidecar starts/stops with the main container
5. **Resource Sharing** - Efficient use of Pod resources

**Communication Flow:**

```
1. Sentiment Agent starts
   │
   ▼
2. WorldMonitor sidecar starts
   │
   ▼
3. Sentiment Agent connects to ws://localhost:8010/ws
   │
   ▼
4. WorldMonitor streams global events via WebSocket
   │
   ▼
5. Sentiment Agent caches events (TTL: 300s)
   │
   ▼
6. API requests enriched with context from cache
```

**Environment Configuration:**

```yaml
env:
  # Main container
  - name: WORLDMONITOR_HOST
    value: localhost
  - name: WORLDMONITOR_PORT
    value: "8010"
  - name: SENTIMENT_CONTEXT_ENABLED
    value: "true"

  # Sidecar container
  - name: WORLDMONITOR_CATEGORIES
    value: "technology,business,entertainment,sports,science"
  - name: WORLDMONITOR_CACHE_TTL
    value: "300"
```

## Component Overview

### Core Services

#### OpenClaw Orchestrator

**Purpose:** Central control plane coordinating all skills and agents

**Responsibilities:**
- Skill registry and management
- Pipeline execution
- GPU resource scheduling
- Request routing and load balancing
- Health monitoring

**Technology:** FastAPI, Redis, Kafka

**Scale:** 2-3 replicas (GPU-enabled)

#### SceneSpeak Agent

**Purpose:** Real-time dialogue generation using local LLMs

**Responsibilities:**
- LLM inference (Llama 2 7B with LoRA adapters)
- Prompt management and composition
- Response caching
- Context building

**Technology:** PyTorch, Transformers, Redis

**Scale:** 1-2 replicas (GPU-enabled)

#### Captioning Agent

**Purpose:** Live speech-to-text with accessibility descriptions

**Responsibilities:**
- Audio transcription (OpenAI Whisper)
- Caption feed management
- Accessibility description generation

**Technology:** OpenAI Whisper, FastAPI

**Scale:** 2 replicas (CPU)

#### BSL-Text2Gloss Agent

**Purpose:** British Sign Language gloss notation translation

**Responsibilities:**
- Text-to-gloss translation
- Gloss notation formatting
- Sign language metadata

**Technology:** NLP libraries, translation models

**Scale:** 2 replicas (CPU)

#### Sentiment Agent

**Purpose:** Audience sentiment analysis from social media with WorldMonitor context integration

**Responsibilities:**
- Sentiment classification using DistilBERT SST-2
- Batch processing with trend analysis
- Social media integration
- **WorldMonitor Integration** (v0.4.0):
  - Real-time global context enrichment via WebSocket
  - News sentiment analysis
  - Context-aware sentiment scoring
  - Category-based event filtering
  - Context caching with TTL

**Technology:** Transformers, DistilBERT, FastAPI, WebSocket

**Scale:** 2 replicas (CPU) with WorldMonitor sidecar

**Sidecar Pattern:**
```
┌─────────────────────────────────────────────────────────────┐
│              Sentiment Agent Pod                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Sentiment Agent (8004)                    │  │
│  │  - Sentiment Analysis Engine                          │  │
│  │  - Context Enrichment Layer                          │  │
│  │  - News Sentiment Analyzer                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │ WebSocket                       │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          WorldMonitor Sidecar (8010)                   │  │
│  │  - Real-time global events                           │  │
│  │  - News headlines streaming                          │  │
│  │  - Category filtering                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Lighting, Sound & Music (LSM)

**Purpose:** Unified audio-visual control for theatrical experiences

**Responsibilities:**
- DMX/sACN lighting control with fixture management
- Sound effects playback with concurrent mixing (max 8 sounds)
- AI music generation using ACE-Step-1.5 models
- Coordinated cues for synchronized multi-media scenes
- WebSocket support for real-time generation and execution updates

**Technology:** FastAPI, ACE-Step-1.5, DMX/sACN libraries, WebSocket

**Scale:** 1 replica (GPU for music generation, hardware access for DMX)

**Note:** Consolidates Lighting Control, Music Generation, and Music Orchestration services

#### Safety Filter

**Purpose:** Multi-layer content moderation

**Responsibilities:**
- Word-based filtering
- ML-based content analysis
- Policy enforcement
- Review queue management

**Technology:** FastAPI, ML models

**Scale:** 2 replicas (CPU)

#### Music Generation (Integrated into LSM)

**Music functionality is now part of the Lighting, Sound & Music service (port 8005)**

**Features:**
- AI music generation using ACE-Step-1.5 models (base, sft, turbo, mlx)
- Model pool management with VRAM-aware loading
- Async generation with cancellation support
- Request routing with cache-first approach
- Redis caching with 7-day TTL
- Staged approval pipeline (marketing=auto, show=manual)
- WebSocket progress streaming
- MinIO storage for audio files

**Scale:** Handled by LSM service scaling

#### GitHub Student Automation

**Trust-Based Auto-Merge** - Students earn trust (3+ PRs = trusted)

**GitHub Actions Workflows**
- PR Validation (lint, test, coverage)
- Trust Check (query merged PRs)
- Auto-Merge (trusted contributors)
- Onboarding (Sprint 0 issues)

**CODEOWNERS** - Role-based review routing

**Branch Protection** - Required status checks and reviews

#### Operator Console

**Purpose:** Human oversight and approval interface

**Responsibilities:**
- Alert management
- Approval workflows
- System monitoring dashboard
- Manual intervention capabilities

**Technology:** FastAPI, WebSocket

**Scale:** 1 replica

### Infrastructure Components

#### k3s

Lightweight k3s distribution for development and production.

**Namespaces:**
- `live` - Production services
- `shared` - Infrastructure services
- `monitoring` - Observability stack

#### Redis

In-memory data store for caching and session management.

**Uses:**
- Response caching
- Session storage
- Pub/Sub for real-time updates

#### Kafka

Distributed event streaming platform.

**Topics:**
- `dialogue.events` - Generated dialogue
- `caption.events` - Live captions
- `sentiment.events` - Audience sentiment
- `safety.events` - Content moderation
- `lighting.events` - Stage automation

#### Milvus

Vector database for semantic search and retrieval.

**Uses:**
- Skill metadata indexing
- Context retrieval
- Similarity search

## Data Flow

### Performance Generation Flow

```
1. Audience Input
   │
   ▼
2. Sentiment Analysis (Sentiment Agent)
   │
   ▼
3. Context Building (Redis cache + Milvus)
   │
   ▼
4. Dialogue Generation (SceneSpeak Agent)
   │
   ▼
5. Safety Check (safety-filter)
   │
   ├── Unsafe ──► Review Queue ──► Operator Approval
   │
   └── Safe ──► Approval Gate
                  │
                  ▼
6. Stage Automation (lighting-control)
   │
   ▼
7. Output to Stage + Captions + BSL
```

### Captioning Flow

```
1. Audio Input
   │
   ▼
2. Speech-to-Text (Captioning Agent)
   │
   ▼
3. Accessibility Enhancement
   │
   ▼
4. Caption Feed Distribution
   │
   ├── Display Feed
   └── BSL Translation Feed
```

## Technology Stack

### Backend

- **Language:** Python 3.10+
- **Framework:** FastAPI 0.109+
- **Async:** asyncio, uvicorn

### AI/ML

- **LLM:** Llama 2 7B with LoRA adapters
- **Speech:** OpenAI Whisper
- **Sentiment:** RoBERTa-base-sentiment
- **Framework:** PyTorch 2.1+, Transformers 4.36+

### Infrastructure

- **Orchestration:** k3s
- **Messaging:** Apache Kafka
- **Caching:** Redis 7+
- **Vector DB:** Milvus 2.3+

### Monitoring

- **Metrics:** Prometheus
- **Dashboards:** Grafana
- **Tracing:** Jaeger
- **Logging:** Structured JSON logs

### Development

- **Language Server:** Python LSP
- **Formatting:** Black
- **Linting:** Ruff
- **Type Checking:** MyPy
- **Testing:** Pytest

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────┐
│         Development Machine             │
│  ┌─────────────────────────────────┐   │
│  │        k3s (Single Node)        │   │
│  │  ┌─────────────────────────┐    │   │
│  │  │   All Services (Dev)     │    │   │
│  │  └─────────────────────────┘    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Production Deployment

```
┌──────────────────────────────────────────────────────────┐
│                    Production Cluster                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Control   │  │   Worker   │  │   Worker   │        │
│  │   Plane    │  │  Node 1    │  │  Node 2    │        │
│  │            │  │  (GPU)     │  │  (CPU)     │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
```

### Namespaces

**live** - Production services
- OpenClaw Orchestrator
- SceneSpeak Agent
- All other agents

**shared** - Infrastructure
- Redis
- Kafka
- Milvus

**monitoring** - Observability
- Prometheus
- Grafana
- Jaeger

## Scalability and Performance

### Horizontal Scaling

Services can be scaled independently based on load:

```bash
# Scale SceneSpeak Agent
kubectl scale deployment/SceneSpeak Agent --replicas=3 -n live

# Scale Captioning Agent
kubectl scale deployment/Captioning Agent --replicas=4 -n live
```

### Resource Allocation

**GPU Services:**
- SceneSpeak: 1 GPU per replica
- OpenClaw: 1 GPU per replica (optional)

**CPU Services:**
- All other agents: CPU-optimized
- Default: 2 CPU, 4GB RAM per replica

### Performance Targets

- Dialogue generation: <3 seconds (p50), <5 seconds (p95)
- Captioning latency: <500ms
- API response: <100ms (p50)
- System availability: >99.5%

### Caching Strategy

- Response caching: Redis (TTL: 1 hour)
- Model caching: In-memory (GPU)
- Context caching: Milvus vector search

## Security Architecture

### Multi-Layer Safety

1. **Input Validation** - All inputs validated at API boundary
2. **Content Filtering** - Word-based + ML-based filtering
3. **Human Oversight** - Operator approval for critical actions
4. **Audit Logging** - All actions logged for review

### Access Control

- RBAC for Kubernetes
- JWT authentication for API access
- Network policies for service-to-service communication

### Data Protection

- Encryption at rest (Kubernetes secrets)
- Encryption in transit (TLS)
- No sensitive data in logs

## Monitoring and Observability

Project Chimera implements a comprehensive production observability platform with 4 core components: Alerting Foundation, Business Metrics, SLO Framework, and Distributed Tracing.

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY PLATFORM                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  AlertManager    │  │   Prometheus     │  │     Grafana      │ │
│  │  (Routing)       │  │   (Metrics)      │  │  (Dashboards)    │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│           │                     │                     │             │
│           │    ┌────────────────┴────────────────┐               │
│           │    │                                 │               │
│           ▼    ▼                                 ▼               │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              Business Metrics Dashboards              │        │
│  │  • Show Overview Dashboard                             │        │
│  │  • Dialogue Quality Dashboard                           │        │
│  │  • Audience Engagement Dashboard                        │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   SLO Framework  │  │   OpenTelemetry  │  │     Jaeger      │ │
│  │  (Reliability)   │  │   (Tracing)      │  │  (Analysis)     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│           │                     │                     │             │
│           ▼                     ▼                     ▼             │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              Quality Gate Deployment Blocking          │        │
│  └────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Alerting Foundation

**AlertManager** provides intelligent alert routing and notification management:

**Features:**
- Intelligent alert routing by severity
- Slack integration for real-time notifications
- Alert aggregation and deduplication
- Silence management for planned maintenance
- On-call rotation support

**Critical Alert Rules:**
- Service down (Pod not ready)
- High error rate (>5% over 5m)
- Elevated latency (p95 >5s over 5m)
- GPU exhaustion (>95% utilization)
- Safety filter trigger rate >10%

**Configuration:** `platform/monitoring/config/alert-rules-critical.yaml`

#### 2. Business Metrics

**Prometheus** collects metrics with **Grafana** dashboards for real-time visualization:

**Show Overview Dashboard:**
- Active show status
- Scene progression
- Audience engagement metrics
- System health indicators

**Dialogue Quality Dashboard:**
- Dialogue coherence score
- Lines generated per scene
- Token usage efficiency
- Cache hit rates

**Audience Engagement Dashboard:**
- Real-time sentiment score
- Emotion breakdown (joy, surprise, neutral, sadness, anger, fear)
- Engagement trends
- Social media mention volume

**Configuration:** `platform/monitoring/config/grafana-dashboards/`

#### 3. SLO Framework

Service Level Objectives with automated error budget tracking:

**SLO Targets:**
- OpenClaw: 99.9% (43.2min/month error budget)
- SceneSpeak: 99.5% (3.6hrs/month error budget)
- Captioning: 99.5% (3.6hrs/month error budget)
- BSL: 99% (7.2hrs/month error budget)
- Safety: 99.9% (43.2min/month error budget)
- Console: 99.5% (3.6hrs/month error budget)

**Error Budget Burn Rate:**
- Burn Rate 1x = On track
- Burn Rate 2x = Warning (5m threshold)
- Burn Rate 10x = Critical (1m threshold)

**Quality Gate:** Blocks deployments when:
- SLO compliance <95%
- Error budget remaining <10%

**Configuration:** `platform/monitoring/config/slo-*.yaml`

#### 4. Distributed Tracing

**OpenTelemetry** instrumentation across all services with **Jaeger** for analysis:

**Instrumentation Standard:**
- 10% sampling for production
- Consistent span attributes per service
- Rich business context (show_id, scene_number, tokens, etc.)

**Trace Analyzer Service:**
- CLI tool for trace analysis
- Service dependency mapping
- Performance bottleneck identification

**Scripts:**
- `scripts/analyze-trace.py` - Analyze specific trace
- `scripts/dependency-graph.py` - Generate dependency graph

### Metrics

#### System Metrics
- CPU, Memory, GPU utilization
- Network I/O
- Disk I/O

#### Application Metrics
- Request rate, latency, errors
- Cache hit rate
- Queue depths
- GPU utilization

#### Business Metrics
- Dialogue generation rate
- Caption accuracy
- Safety filter triggers
- Audience sentiment
- Show progression

### Tracing

Distributed tracing with Jaeger and OpenTelemetry for:
- Request flows across services
- Performance bottleneck identification
- Error root cause analysis
- Service dependency mapping

**Per-Service Span Attributes:**

**SceneSpeak Agent:**
- `show.id` - Show identifier
- `scene.number` - Scene number
- `adapter.name` - Adapter used
- `tokens.input` - Input token count
- `tokens.output` - Output token count
- `dialogue.lines_count` - Lines generated

**Captioning Agent:**
- `caption_latency_ms` - Caption processing latency

**BSL Agent:**
- `translation.request_id` - Translation request ID
- `sign_language` - Sign language variant

**Sentiment Agent:**
- `sentiment.score` - Sentiment value
- `audience.size` - Audience count

**Safety Filter:**
- `safety.action` - Action taken (allow/block/flag)
- `pattern.matched` - Pattern that matched
- `content.length` - Content length

### Logging

Structured JSON logs with:
- Correlation IDs (trace_id from OpenTelemetry)
- Timestamps (ISO 8601)
- Service name
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Contextual metadata

**Log Format:**
```json
{
  "timestamp": "2026-03-05T12:00:00Z",
  "level": "INFO",
  "service": "scenespeak-agent",
  "trace_id": "abc123def456",
  "span_id": "789ghi012",
  "message": "Dialogue generated successfully",
  "show_id": "show-2026-03-05",
  "scene_number": 3,
  "tokens_used": 450,
  "adapter": "gpt-4"
}
```

### Alerting

Alerts configured via AlertManager for:

**Critical Alerts (fire immediately):**
- Service down (Pod not Ready for >1m)
- High error rate (>5% over 5m)
- Elevated latency (p95 >5s over 5m)
- GPU exhaustion (>95% for >5m)
- Safety filter trigger rate >10%

**Warning Alerts (aggregated):**
- Elevated error rate (>1% over 15m)
- High memory usage (>80% for >10m)
- Cache miss rate spike (>50% increase)

**SLO Alerts (burn rate based):**
- Burn Rate 2x (5 minute threshold)
- Burn Rate 10x (1 minute threshold)
- Error budget <25% remaining
- Error budget <10% remaining (blocks deployment)

**Notification Channels:**
- Slack for real-time alerts
- Email for daily summaries
- Operator Console for active shows

### Quick Links

| Tool | URL | Credentials |
|------|-----|-------------|
| Grafana Dashboards | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| AlertManager | http://localhost:9093 | - |
| Jaeger UI | http://localhost:16686 | - |

### Related Documentation

- [Observability Guide](../observability.md) - Complete observability documentation
- [ADR-006: Production Observability Platform](../architecture/006-observability-platform.md) - Observability architecture
- [ADR-007: SLO Framework](../architecture/007-slo-framework.md) - SLO framework design
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md) - Tracing standard
- [Alerting Runbook](../runbooks/alerts.md) - Alert response procedures
- [SLO Handbook](../runbooks/slo-handbook.md) - SLO definitions and error budgets
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md) - Tracing guide

## Architecture Decision Records

For detailed discussions of architectural decisions, see:

- [ADR-001: Use k3s for Kubernetes](architecture/001-use-k3s.md)
- [ADR-002: FastAPI for Microservices](architecture/002-fastapi-services.md)
- [ADR-003: OpenClaw Skills Architecture](architecture/003-openclaw-skills.md)

## Future Enhancements

Planned architectural improvements:

1. **API Gateway** - Centralized API management
2. **Service Mesh** - Istio for advanced traffic management
3. **Event Sourcing** - CQRS pattern for events
4. **Multi-region Deployment** - Geographic distribution
5. **Advanced Caching** - CDN integration

---

For more information, see:
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Development Guide](DEVELOPMENT.md)

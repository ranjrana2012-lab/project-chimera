# Project Chimera - Full Implementation Design

**Version:** 1.0.0
**Date:** 2026-02-27
**Status:** Approved
**Audience:** Technical Lead, Development Team, Students
**Purpose:** Complete design for full implementation of Project Chimera as an open source framework

---

## Executive Summary

This document describes the complete implementation of Project Chimera, an AI-powered live theatre platform designed as an open source framework for universities worldwide. The system will be built by 60+ contributors over 6 months, with an initial MVP target of completion by Monday for student demonstration.

### Project Goals

1. **Create a working AI-powered live theatre system** for demonstration to students
2. **Build an extensible open source framework** that other universities can adopt
3. **Establish contribution workflows** using Trello (initial) → GitHub Projects (long-term)
4. **Enable student-created agents and skills** through modular architecture
5. **Document everything extensively** for 60+ contributors over 6 months

### Success Criteria

- [ ] All 8 core services deployed and functional
- [ ] End-to-end flow working: Audience Input → Sentiment → Dialogue → Safety → Output
- [ ] GPU services using real AI models (SceneSpeak)
- [ ] CPU services using real ML models (Sentiment, Captioning, BSL)
- [ ] Safety filtering active with configurable policies
- [ ] Operator console with override capabilities
- [ ] Monitoring dashboards showing live metrics
- [ ] Complete documentation for contributors
- [ ] Open source repository ready for external contributors

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Specifications](#2-component-specifications)
3. [Data Models & Event Schemas](#3-data-models--event-schemas)
4. [Configuration Management](#4-configuration-management)
5. [Testing Strategy](#5-testing-strategy)
6. [Monitoring & Observability](#6-monitoring--observability)
7. [Security Model](#7-security-model)
8. [Implementation Phases](#8-implementation-phases)
9. [Documentation Structure](#9-documentation-structure)
10. [Open Source Preparation](#10-open-source-preparation)

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Operator Console (Port 8007)            │
│                    Human oversight & approval                   │
│                  WebSocket: Real-time events                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw Orchestrator (Port 8000)            │
│              Skill routing, GPU scheduling, coordination         │
│         Kafka: Event producer/consumer | Redis: State          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ SceneSpeak   │    │  Sentiment   │    │  Captioning  │
│   (8001)     │    │   (8004)     │    │   (8002)     │
│   LLM + GPU  │    │  CPU Model   │    │  Whisper CPU │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
        ┌──────────────────┴───────────────────┐
        │                                      │
        ▼                                      ▼
┌──────────────┐                      ┌──────────────┐
│ Safety Filter│                      │   Lighting   │
│   (8006)     │                      │   (8005)     │
│  CPU Checks  │                      │  DMX/sACN    │
└──────┬───────┘                      └──────┬───────┘
       │                                     │
       ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│    BSL       │                    │   Shared     │
│  (8003)      │                    │   State      │
│ NLP Model    │                    │ Redis + Kafka│
└──────────────┘                    └──────────────┘
```

### 1.2 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Framework** | FastAPI | High-performance async APIs |
| **ML Framework** | PyTorch | Model inference |
| **LLM** | Mistral-7B-Instruct | Dialogue generation |
| **ASR** | OpenAI Whisper | Speech-to-text |
| **Sentiment** | DistilBERT | Emotion analysis |
| **Translation** | Helsinki-NLP OPUS | BSL gloss translation |
| **State Management** | Redis | Caching, pub/sub |
| **Event Streaming** | Kafka | Message bus |
| **Vector DB** | Milvus | Skill matching |
| **Orchestration** | Kubernetes | Container orchestration |
| **Monitoring** | Prometheus + Grafana | Metrics & dashboards |
| **Tracing** | Jaeger | Distributed tracing |
| **Container Runtime** | Docker | Service containers |
| **Local K8s** | k3s | Lightweight Kubernetes |

### 1.3 Service Dependencies

```
Operator Console
    ├── Reads from: All services (via Kafka)
    ├── Writes to: OpenClaw (overrides)
    └── Dependencies: Kafka, Redis

OpenClaw Orchestrator
    ├── Calls: All skill services
    ├── Reads from: Redis (skills, state)
    ├── Writes to: Kafka (events), Redis (state)
    └── Dependencies: Redis, Kafka, Milvus

SceneSpeak Agent
    ├── Reads from: Redis (prompts, cache)
    ├── Writes to: Kafka (events), Redis (cache)
    └── Dependencies: GPU, Redis, Kafka

Captioning Agent
    ├── Reads from: Redis (state)
    ├── Writes to: Kafka (events)
    └── Dependencies: Redis, Kafka

BSL-Text2Gloss Agent
    ├── Reads from: Redis (cache)
    ├── Writes to: Kafka (events), Redis (cache)
    └── Dependencies: Redis, Kafka

Sentiment Agent
    ├── Reads from: Kafka (audience input)
    ├── Writes to: Kafka (sentiment events), Redis (aggregated)
    └── Dependencies: Kafka, Redis

Lighting Control
    ├── Reads from: Kafka (scene cues), Redis (fixture state)
    ├── Writes to: DMX (sACN), Redis (state)
    └── Dependencies: Kafka, Redis, DMX network

Safety Filter
    ├── Reads from: Redis (policies)
    ├── Writes to: Kafka (audit), Redis (stats)
    └── Dependencies: Redis, Kafka
```

---

## 2. Component Specifications

### 2.1 OpenClaw Orchestrator

**Port:** 8000
**GPU:** 1x NVIDIA GPU (8GB VRAM)
**Resources:** 2-4 CPU, 8-16 GiB RAM

**Responsibilities:**
- Skill registration and discovery
- Request routing to skills
- GPU resource allocation and scheduling
- Policy engine for content approval
- Kafka event production/consumption
- Health monitoring of skills

**Key Modules:**
- `core/skill_registry.py` - Skill loading from ConfigMaps
- `core/router.py` - Request routing logic
- `core/gpu_scheduler.py` - GPU allocation tracking
- `core/policy_engine.py` - Content policy enforcement
- `core/kafka_producer.py` - Event publishing
- `core/kafka_consumer.py` - Event consumption

**API Endpoints:**
- `POST /v1/orchestrate` - Execute skill chain
- `GET /v1/skills` - List registered skills
- `GET /v1/skills/{skill}` - Get skill details
- `POST /v1/skills/register` - Register new skill
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.2 SceneSpeak Agent

**Port:** 8001
**GPU:** 1x NVIDIA GPU (8GB VRAM)
**Resources:** 4-8 CPU, 16-32 GiB RAM

**Responsibilities:**
- LLM-based dialogue generation
- LoRA adapter support for character voices
- Prompt template management
- Sentiment-aware generation
- Response caching

**Key Modules:**
- `core/llm_engine.py` - Model loading & inference
- `core/prompt_manager.py` - Prompt templates
- `core/lora_manager.py` - LoRA adapter loading
- `core/cache.py` - Response caching
- `core/sentiment_adapter.py` - Sentiment context
- `core/streamer.py` - WebSocket streaming

**Model:** Mistral-7B-Instruct-v0.2 (4-bit quantized)

**API Endpoints:**
- `POST /v1/generate` - Generate dialogue
- `GET /v1/prompts` - List prompt templates
- `GET /v1/prompts/{template}` - Get prompt template
- `GET /v1/lora-adapters` - List LoRA adapters
- `WS /stream` - WebSocket for streaming
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.3 Captioning Agent

**Port:** 8002
**GPU:** None (CPU inference)
**Resources:** 2-4 CPU, 4-8 GiB RAM

**Responsibilities:**
- Real-time speech-to-text
- Audio stream processing
- Timestamp generation
- WebSocket live caption feed

**Key Modules:**
- `core/whisper_engine.py` - Whisper model
- `core/audio_processor.py` - Audio stream handling
- `core/timestamp.py` - Timestamp generation
- `core/streamer.py` - WebSocket streaming

**Model:** OpenAI Whisper (base)

**API Endpoints:**
- `POST /v1/caption` - Caption audio file
- `POST /v1/stream/start` - Start captioning stream
- `POST /v1/stream/stop` - Stop captioning stream
- `WS /stream` - WebSocket for live captions
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.4 BSL-Text2Gloss Agent

**Port:** 8003
**GPU:** None (CPU inference)
**Resources:** 2 CPU, 4 GiB RAM

**Responsibilities:**
- English-to-BSL gloss translation
- Text preprocessing
- Translation model inference
- Gloss notation formatting
- Phrase caching

**Key Modules:**
- `core/translator.py` - Translation model
- `core/preprocessor.py` - Text preprocessing
- `core/gloss_formatter.py` - Gloss notation
- `core/cache.py` - Phrase caching

**Model:** Helsinki-NLP/opus-mt-en-ROMANCE (fine-tuned for BSL)

**API Endpoints:**
- `POST /v1/translate` - Translate text to BSL gloss
- `POST /v1/batch` - Batch translate
- `GET /v1/supported-languages` - List supported languages
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.5 Sentiment Agent

**Port:** 8004
**GPU:** None (CPU inference)
**Resources:** 4 CPU, 8 GiB RAM

**Responsibilities:**
- Real-time sentiment analysis
- Audience emotion detection
- Text preprocessing
- Sentiment aggregation
- Trend detection

**Key Modules:**
- `core/sentiment_model.py` - Sentiment model
- `core/preprocessor.py` - Text preprocessing
- `core/aggregator.py` - Sentiment aggregation
- `core/trend_detector.py` - Trend detection
- `core/kafka_consumer.py` - Audience input consumption

**Model:** distilbert-base-uncased-finetuned-sst-2-english

**API Endpoints:**
- `POST /v1/analyze` - Analyze sentiment
- `GET /v1/trends` - Get sentiment trends
- `GET /v1/current` - Get current aggregated sentiment
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.6 Lighting Control

**Port:** 8005
**GPU:** None
**Resources:** 0.5-1 CPU, 512 MiB - 2 GiB RAM

**Responsibilities:**
- DMX/sACN protocol implementation
- OSC message handling
- Scene preset management
- Fixture state management

**Key Modules:**
- `core/sacn_manager.py` - sACN protocol
- `core/osc_handler.py` - OSC messages
- `core/scene_manager.py` - Scene presets
- `core/fixture_state.py` - Redis state management
- `core/dmx_universe.py` - DMX universe management

**API Endpoints:**
- `POST /v1/lighting/set` - Set fixture values
- `GET /v1/scenes` - List scenes
- `POST /v1/scenes/activate` - Activate scene
- `GET /v1/fixtures` - List fixtures
- `GET /v1/fixtures/{id}/state` - Get fixture state
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.7 Safety Filter

**Port:** 8006
**GPU:** None
**Resources:** 1-2 CPU, 2-4 GiB RAM

**Responsibilities:**
- Profanity detection
- Content classification
- Hate speech detection
- Violence detection
- Audit logging

**Key Modules:**
- `core/profanity_detector.py` - Profanity filtering
- `core/content_classifier.py` - Content safety
- `core/audit_logger.py` - Kafka audit logging
- `core/threshold_manager.py` - Configurable thresholds

**API Endpoints:**
- `POST /v1/check` - Check content safety
- `GET /v1/policies` - List active policies
- `PUT /v1/policies` - Update policies
- `GET /v1/stats` - Safety statistics
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

### 2.8 Operator Console

**Port:** 8007
**GPU:** None
**Resources:** 1-2 CPU, 2-4 GiB RAM

**Responsibilities:**
- Human oversight interface
- Real-time event streaming
- Manual override controls
- Alert management
- Dashboard UI

**Key Modules:**
- `core/event_streamer.py` - WebSocket streaming
- `core/kafka_consumer.py` - Event consumption
- `core/alert_manager.py` - Alert management
- `core/override_handler.py` - Manual overrides

**Frontend:**
- `static/index.html` - Main dashboard
- `static/css/console.css` - Styles
- `static/js/console.js` - Dashboard logic

**API Endpoints:**
- `GET /` - Console UI
- `WS /events` - WebSocket for events
- `POST /v1/override` - Manual override
- `GET /v1/alerts` - List alerts
- `POST /v1/alerts/{id}/acknowledge` - Acknowledge alert
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

---

## 3. Data Models & Event Schemas

### 3.1 API Models

**Common Request/Response Models:**

```python
# Base models
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class Status(str, Enum):
    """Common status values"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime: float
    dependencies: Dict[str, str]

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

# OpenClaw models
class OrchestrationRequest(BaseModel):
    """Request for orchestration"""
    skills: list[str]
    input_data: Dict[str, Any]
    priority: Optional[int] = Field(default=100, ge=1, le=1000)
    timeout: Optional[int] = Field(default=30, ge=1, le=300)
    gpu_required: Optional[bool] = False

class OrchestrationResponse(BaseModel):
    """Response from orchestration"""
    request_id: str
    status: Status
    results: Dict[str, Any]
    execution_time_ms: float
    gpu_used: bool

# SceneSpeak models
class GenerationRequest(BaseModel):
    """Request for dialogue generation"""
    context: str = Field(..., min_length=1, max_length=1000)
    character: str
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    max_tokens: Optional[int] = Field(default=256, ge=1, le=1024)
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=2.0)

class GenerationResponse(BaseModel):
    """Response from dialogue generation"""
    request_id: str
    dialogue: str
    character: str
    sentiment_used: float
    tokens: int
    confidence: float
    from_cache: bool
    generation_time_ms: float

# Sentiment models
class SentimentRequest(BaseModel):
    """Request for sentiment analysis"""
    text: str = Field(..., min_length=1, max_length=5000)
    source: Optional[str] = "api"

class SentimentResponse(BaseModel):
    """Response from sentiment analysis"""
    sentiment_score: float  # -1.0 to 1.0
    confidence: float
    emotions: Dict[str, float]
    trend: Optional[str]  # "rising", "falling", "stable"

# Safety models
class SafetyRequest(BaseModel):
    """Request for safety check"""
    content: str = Field(..., min_length=1, max_length=10000)
    categories: Optional[list[str]] = None

class SafetyResponse(BaseModel):
    """Response from safety check"""
    decision: str  # "approved", "blocked", "flagged"
    reason: Optional[str] = None
    categories: Dict[str, bool]
    confidence: float
    requires_review: bool

# Lighting models
class LightingRequest(BaseModel):
    """Request to set lighting"""
    universe: int = Field(..., ge=1, le=512)
    fixtures: list[Dict[str, Any]]
    transition_time_ms: Optional[int] = Field(default=0, ge=0)

class SceneActivateRequest(BaseModel):
    """Request to activate a scene"""
    scene_name: str
    transition_time_ms: Optional[int] = Field(default=1000, ge=0)
```

### 3.2 Kafka Event Schemas

All Kafka events follow a standard envelope:

```python
class EventEnvelope(BaseModel):
    """Standard event envelope"""
    event_id: str  # UUID
    event_type: str
    event_version: str
    timestamp: datetime
    source_service: str
    correlation_id: Optional[str] = None
    data: Dict[str, Any]
```

**Event Types:**

| Event Type | Topic | Producer | Consumer |
|------------|-------|----------|----------|
| `audience.input.received` | `audience-input` | Console, External | Sentiment |
| `sentiment.analysis.completed` | `sentiment-analysis` | Sentiment | SceneSpeak, OpenClaw |
| `dialogue.generation.completed` | `dialogue-generation` | SceneSpeak | Safety, OpenClaw |
| `caption.generated` | `captioning` | Captioning | BSL, OpenClaw |
| `translation.completed` | `translation` | BSL | OpenClaw |
| `safety.check.completed` | `safety-check` | Safety | OpenClaw |
| `lighting.scene.changed` | `lighting-control` | Lighting | OpenClaw |
| `orchestration.skill.invoked` | `orchestration` | OpenClaw | Monitoring |
| `operator.override.initiated` | `operator-actions` | Console | OpenClaw, Safety |
| `error.occurred` | `error-events` | All | Monitoring |

### 3.3 Redis Data Structures

**Key Convention:** `chimera:{service}:{entity}:{id}`

**Example keys:**
- `chimera:openclaw:skills:*` - Skill registry
- `chimera:openclaw:gpu:allocations` - GPU allocations
- `chimera:scenespeak:cache:{hash}` - Response cache
- `chimera:sentiment:aggregated:current` - Current sentiment
- `chimera:lighting:active:scene` - Active scene

**Pub/Sub Channels:**
- `chimera:system:shutdown` - Graceful shutdown
- `chimera:events:sentiment` - Sentiment updates
- `chimera:events:dialogue` - New dialogue
- `chimera:events:safety` - Safety check results
- `chimera:events:lighting` - Lighting state changes

---

## 4. Configuration Management

### 4.1 Configuration Priority

1. Environment Variables (runtime overrides)
2. ConfigMap/Secret (Kubernetes)
3. .env file (local development)
4. config.py defaults (code defaults)

### 4.2 Configuration Files

**Base Configuration:**
- `configs/base/policies.yaml` - Content approval policies
- `configs/base/retention.yaml` - Data retention policies
- `configs/base/alerts.yaml` - Alert thresholds

**Service Configuration:**
- `configs/services/{service}/config.yaml` - Service-specific config

**Environment Overlays:**
- `configs/overlays/local/` - Local development
- `configs/overlays/dev/` - Development
- `configs/overlays/staging/` - Staging
- `configs/overlays/production/` - Production

### 4.3 Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Services
OPENCLAW_PORT=8000
SCENESPEAK_PORT=8001
CAPTIONING_PORT=8002
BSL_PORT=8003
SENTIMENT_PORT=8004
LIGHTING_PORT=8005
SAFETY_PORT=8006
CONSOLE_PORT=8007

# Infrastructure
REDIS_HOST=redis.shared.svc.cluster.local
REDIS_PORT=6379
KAFKA_BOOTSTRAP_SERVERS=kafka.shared.svc.cluster.local:9092
VECTOR_DB_HOST=vector-db.shared.svc.cluster.local
VECTOR_DB_PORT=19530

# GPU
GPU_ENABLED=true
CUDA_VISIBLE_DEVICES=0

# Models
SCENESPEAK_MODEL=mistralai/Mistral-7B-Instruct-v0.2
CAPTIONING_MODEL=openai/whisper-base
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
BSL_MODEL=Helsinki-NLP/opus-mt-en-ROMANCE

# Safety
SAFETY_AUTO_BLOCK_THRESHOLD=0.7
SAFETY_PROFANITY_FILTER_ENABLED=true

# Monitoring
JAEGER_HOST=jaeger.shared.svc.cluster.local
JAEGER_PORT=6831
JAEGER_SAMPLE_RATE=0.1
```

---

## 5. Testing Strategy

### 5.1 Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  5%
                    │   (Playwright)  │
                    ├─────────────────┤
                    │  Integration    │  20%
                    │     Tests       │
                    ├─────────────────┤
                    │   Unit Tests    │  75%
                    │    (pytest)     │
                    └─────────────────┘
```

### 5.2 Test Coverage Requirements

| Service | Unit | Integration | Load |
|---------|------|-------------|------|
| OpenClaw | 85% | Required | Required |
| SceneSpeak | 80% | Required | Required |
| Captioning | 80% | Required | Required |
| BSL | 75% | Required | Optional |
| Sentiment | 75% | Required | Optional |
| Lighting | 70% | Optional | Optional |
| Safety | 90% | Required | Required |
| Console | 70% | Optional | Optional |

### 5.3 Test Structure

```
tests/
├── unit/                    # 75% - Business logic
├── integration/             # 20% - Service communication
├── load/                    # Locust load tests
├── red-team/                # Security tests
├── accessibility/           # WCAG compliance
└── e2e/                     # End-to-end (Playwright)
```

---

## 6. Monitoring & Observability

### 6.1 Metrics

All services expose Prometheus metrics on `/metrics`:

- Counters: `*_total` (monotonically increasing)
- Gauges: `*_gauge` (point-in-time values)
- Histograms: `*_bucket`, `*_sum`, `*_count` (distributions)

**Key Metrics:**
- `http_requests_total` - HTTP request count
- `http_request_duration_seconds` - Request latency
- `*_errors_total` - Error count
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage

### 6.2 Dashboards

- **System Overview** - Service health, request rate, latency
- **AI Services** - Generation metrics, model stats
- **Resources** - CPU, memory, GPU usage

### 6.3 Alerting

Alerts configured in Prometheus for:
- Service down
- High error rate
- High latency
- High memory/CPU usage
- GPU memory high
- No dialogue generated
- High block rate

### 6.4 Tracing

Jaeger distributed tracing for:
- HTTP requests
- Skill invocations
- Model inference
- Kafka events
- Redis operations

---

## 7. Security Model

### 7.1 Security Layers

1. **Network Security** - Network policies, TLS
2. **Authentication** - JWT tokens, service accounts
3. **Input Validation** - Pydantic models
4. **Content Safety** - Safety filter
5. **Data Protection** - Encryption, PII redaction
6. **Operational Security** - Scanning, updates

### 7.2 Network Policies

Kubernetes NetworkPolicies enforce:
- Service-to-service communication rules
- Ingress restrictions
- Egress restrictions

### 7.3 Content Safety

Safety filter pipeline:
1. Word list check (profanity, slurs)
2. ML model check (BERT-based)
3. Aggregation
4. Decision (approve/block/flag)
5. Audit logging

---

## 8. Implementation Phases

### Phase 1: Infrastructure & Environment Setup (4-6 hours)

- Fix Docker permissions
- Configure k3s registry
- Run bootstrap
- Verify cluster health

### Phase 2: Core Service Implementations (20-25 hours)

- OpenClaw Orchestrator (6h)
- SceneSpeak Agent (5h)
- Captioning Agent (3h)
- BSL-Text2Gloss Agent (3h)
- Sentiment Agent (2h)
- Lighting Control (2h)
- Safety Filter (2h)
- Operator Console (2h)

### Phase 3: Integration & Testing (8-10 hours)

- Service integration
- End-to-end testing
- Load testing
- Security testing

### Phase 4: Observability & Polish (6-8 hours)

- Monitoring setup
- Grafana dashboards
- Documentation completion
- Demo preparation

### Phase 5: Open Source Preparation (4-6 hours)

- Repository cleanup
- GitHub setup
- Release preparation

**Total:** 42-55 hours

---

## 9. Documentation Structure

### 9.1 Documentation Taxonomy

```
docs/
├── README.md
├── CONTRIBUTING.md
├── GOVERNANCE.md
├── RELEASE.md
├── architecture/           # System architecture
├── api/                    # API documentation
├── guides/                 # How-to guides
├── runbooks/               # Operational procedures
├── plans/                  # Implementation plans
├── standards/              # Code & doc standards
└── training/               # Student materials
```

### 9.2 Documentation Standards

Every `.md` file includes:
- Header with title, version, date
- Purpose statement
- Audience level
- Prerequisites
- Table of contents (>500 words)
- Code examples with language tags
- See also/references
- Change history

---

## 10. Open Source Preparation

### 10.1 Repository Files

- `LICENSE` - MIT License
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community guidelines
- `SECURITY.md` - Security policy
- `README.md` - Project overview

### 10.2 GitHub Configuration

- Issue templates
- PR templates
- Branch protection rules
- CI/CD workflows
- Projects integration

### 10.3 Release Process

- Semantic versioning
- Changelog
- Release notes
- Tagging strategy

---

## Appendix A: Service Dependencies Matrix

| Service | Internal Deps | External Deps | GPU Required |
|---------|--------------|---------------|-------------|
| OpenClaw | All services | Redis, Kafka, Milvus | Yes |
| SceneSpeak | None | Redis, Kafka | Yes |
| Captioning | None | Redis, Kafka | No |
| BSL | None | Redis, Kafka | No |
| Sentiment | None | Redis, Kafka | No |
| Lighting | None | Redis, Kafka, DMX | No |
| Safety | None | Redis, Kafka | No |
| Console | All services | Redis, Kafka | No |

---

## Appendix B: Port Allocation

| Port | Service | Protocol |
|------|---------|----------|
| 8000 | OpenClaw Orchestrator | HTTP |
| 8001 | SceneSpeak Agent | HTTP |
| 8002 | Captioning Agent | HTTP |
| 8003 | BSL-Text2Gloss Agent | HTTP |
| 8004 | Sentiment Agent | HTTP |
| 8005 | Lighting Control | HTTP |
| 8006 | Safety Filter | HTTP |
| 8007 | Operator Console | HTTP |
| 3000 | Grafana | HTTP |
| 9090 | Prometheus | HTTP |
| 16686 | Jaeger | HTTP |
| 6379 | Redis | TCP |
| 9092 | Kafka | TCP |
| 19530 | Milvus | TCP |

---

## Appendix C: GPU Allocation

| GPU ID | Service | Allocation |
|--------|---------|------------|
| 0 | SceneSpeak | 8 GB |
| 0 | OpenClaw | 4 GB (shared) |

GPU scheduling via OpenClaw Orchestrator.

---

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-27 | 1.0.0 | Initial design document | Technical Lead |

---

**End of Design Document**

*This design is approved for implementation. Proceed to implementation plan creation.*

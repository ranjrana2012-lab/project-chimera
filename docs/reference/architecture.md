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

**Purpose:** Audience sentiment analysis from social media

**Responsibilities:**
- Sentiment classification
- Batch processing
- Social media integration

**Technology:** Transformers, RoBERTa

**Scale:** 2 replicas (CPU)

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

#### Kubernetes (k3s)

Lightweight Kubernetes distribution for development and production.

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
2. Sentiment Analysis (sentiment-agent)
   │
   ▼
3. Context Building (Redis cache + Milvus)
   │
   ▼
4. Dialogue Generation (scenespeak-agent)
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
2. Speech-to-Text (captioning-agent)
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

- **Orchestration:** Kubernetes (k3s)
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
kubectl scale deployment/scenespeak-agent --replicas=3 -n live

# Scale Captioning Agent
kubectl scale deployment/captioning-agent --replicas=4 -n live
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

### Metrics

**System Metrics:**
- CPU, Memory, GPU utilization
- Network I/O
- Disk I/O

**Application Metrics:**
- Request rate, latency, errors
- Cache hit rate
- Queue depths
- GPU utilization

**Business Metrics:**
- Dialogue generation rate
- Caption accuracy
- Safety filter triggers

### Tracing

Distributed tracing with Jaeger for:
- Request flows across services
- Performance bottleneck identification
- Error root cause analysis

### Logging

Structured JSON logs with:
- Correlation IDs
- Timestamps
- Service name
- Log levels
- Contextual metadata

### Alerting

Alerts configured for:
- High error rates
- Elevated latency
- Service unavailability
- GPU exhaustion
- Safety filter triggers

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

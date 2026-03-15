# LTX-2 + MiroFish Integration Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Project Chimera into a visual intelligence platform by integrating LTX-2 video generation and MiroFish agent swarm simulation

**Architecture:** Hybrid Visual Services Layer (local orchestration on DGX Spark + LTX-2 API video generation)

**Tech Stack:** FastAPI, LTX-2 API, MiroFish simulation engine, GraphRAG, Zep memory, FFmpeg, Kubernetes (K3s)

---

## Table of Contents

1. [Executive Summary](#section-1-executive-summary)
2. [System Architecture Overview](#section-1-system-architecture-overview)
3. [Component Design](#section-2-component-design)
4. [Integration & Data Flow](#section-3-integration--data-flow)
5. [Revenue Implementation](#section-4-revenue-implementation)
6. [Development Roadmap](#section-5-development-roadmap)
7. [Technical Specifications](#section-6-technical-specifications)
8. [Configuration & Deployment](#section-7-configuration--deployment)
9. [Documentation & Testing Strategy](#section-8-documentation--testing-strategy)

---

## Section 1: Executive Summary

### Vision

Transform Project Chimera from a text-centric orchestration platform into a **visual intelligence engine** that generates cinematic, monetizable video content from agent simulations. This integration combines:

- **LTX-2**: Lightricks' production-grade AI video generation (19B parameters, 4K@50fps, synchronized audio)
- **MiroFish**: Multi-agent swarm simulation engine with GraphRAG memory and Zep integration
- **DGX Spark**: NVIDIA Grace Blackwell GB10 SoC (128GB unified memory, ARM64)

### Strategic Value

**Differentiation:** Most AI platforms output text; Chimera + LTX-2 outputs video narratives

**Usability:** Executives consume 60-second videos faster than 40-page reports

**Monetization:** Video-enhanced intelligence products command 3-5x pricing premium

### Three Revenue Products

1. **Visual Intelligence Reports** ($500-2,000/report or $2,000-5,000/month subscription)
2. **Scenario Simulation Services** ($5,000-25,000/engagement)
3. **Social Narrative Modelling** ($1,500-5,000/analysis or $3,000-15,000/month retainer)

---

## Section 1: System Architecture Overview

### Visual Services Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Project Chimera - Visual Intelligence          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    CONSUMER AGENTS                          │   │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐  │   │
│   │  │ Sentiment Agent  │  │  Socials Agent   │  │  Director   │  │   │
│   │  │    (8004)        │  │     (8015)       │  │   Agent     │  │   │
│   │  └────────┬─────────┘  └────────┬─────────┘  └──────┬──────┘  │   │
│   └────────────┼─────────────────────┼─────────────────────┼───────┘   │
│                │                     │                     │           │
│   ┌────────────┼─────────────────────┼─────────────────────┼───────┐   │
│   │            ▼                     ▼                     ▼       │   │
│   │        ┌────────────────────────────────────────────────────┐ │   │
│   │        │              VISUAL SERVICES LAYER                │ │   │
│   │        │  ┌──────────────────┐  ┌──────────────────────┐   │ │   │
│   │        │  │  Visual Core     │  │  Simulation Engine   │   │ │   │
│   │        │  │     (8014)       │  │      (8016)          │   │ │   │
│   │        │  │                  │  │                      │   │ │   │
│   │        │  │ • LTX-2 Client   │  │ • MiroFish Core      │   │ │   │
│   │        │  │ • Prompt Factory │  │ • Agent Swarms       │   │ │   │
│   │        │  │ • LoRA Manager   │  │ • GraphRAG Memory    │   │ │   │
│   │        │  │ • Video Pipeline │  │ • Zep Integration    │   │ │   │
│   │        │  └────────┬─────────┘  └──────────┬───────────┘   │ │   │
│   │        │           │                       │              │ │   │
│   │        │  ┌────────▼───────────────────────▼──────────┐ │   │
│   │        │  │        Content Orchestrator (8017)        │ │   │
│   │        │  │  • Narrative Synthesis                    │ │   │
│   │        │  │  • Storyboard Generation                  │ │   │
│   │        │  │  • Scene Spec Creation                    │ │   │
│   │        │  └────────────────────────────────────────────┘ │   │
│   │        └────────────────────────────────────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   ORCHESTRATION LAYER                      │   │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐  │   │
│   │  │   OpenClaw       │  │  Autonomous      │  │  DeerFlow   │  │   │
│   │  │   Orchestrator   │  │     Agent        │  │  (Future)   │  │   │
│   │  │     (8000)       │  │      (8008)      │  │             │  │   │
│   │  └──────────────────┘  └──────────────────┘  └─────────────┘  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              EXTERNAL APIS + HARDWARE                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │   │
│   │  │  LTX-2 API   │  │  DGX Spark   │  │  Zep Cloud          │  │   │
│   │  │  (Cloud)     │  │  (Local)     │  │  (Memory)           │  │   │
│   │  └──────────────┘  └──────────────┘  └─────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Service Descriptions

| Service | Port | Purpose | Key Responsibilities |
|---------|------|---------|---------------------|
| **Visual Core** | 8014 | LTX-2 integration hub | API client, prompt engineering, LoRA management, video pipeline |
| **Simulation Engine** | 8016 | MiroFish agent swarms | Multi-agent simulation, GraphRAG, Zep memory, scenario generation |
| **Content Orchestrator** | 8017 | Narrative synthesis | Storyboard generation, scene specs, script creation |
| **Socials Agent** | 8015 | Social media intelligence | Platform monitoring, narrative tracking, video reports |

---

## Section 2: Component Design

### 2.1 Visual Core Service (Port 8014)

**Purpose:** Central hub for all LTX-2 video generation operations

**File Structure:**
```
services/visual-core/
├── main.py                    # FastAPI application
├── ltx_client.py              # LTX-2 API wrapper
├── prompt_factory.py          # Prompt engineering and templates
├── lora_manager.py            # LoRA training and management
├── video_pipeline.py          # FFmpeg post-processing, stitching
├── config.py                  # Configuration management
├── models.py                  # Pydantic models
├── metrics.py                 # Prometheus metrics
├── tracing.py                 # OpenTelemetry tracing
├── tests/
├── k8s-deployment.yaml
├── Dockerfile
└── requirements.txt
```

**Key Endpoints:**
```python
POST /api/v1/generate/text     # Text-to-Video
POST /api/v1/generate/image    # Image-to-Video
POST /api/v1/generate/audio    # Audio-to-Video
POST /api/v1/generate/batch     # Batch Generation
POST /api/v1/lora/train         # LoRA Training
POST /api/v1/video/extend       # Extend Video
POST /api/v1/video/retake       # Regenerate Segment
POST /api/v1/video/stitch       # Combine Clips
```

### 2.2 Simulation Engine (Port 8016)

**Purpose:** MiroFish agent swarm simulation with GraphRAG memory

**File Structure:**
```
services/simulation-engine/
├── main.py
├── mirofish/
│   ├── core.py                # MiroFish simulation engine
│   ├── agent.py               # Individual agent behavior
│   ├── swarm.py               # Agent swarm coordination
│   ├── graphrag.py            # GraphRAG implementation
│   └── memory.py              # Memory integration (Zep)
├── scenario/
│   ├── generator.py           # Scenario generation
│   └── templates.py           # Predefined scenario templates
├── config.py
├── models.py
├── tests/
├── k8s-deployment.yaml
└── requirements.txt
```

**Key Endpoints:**
```python
POST /api/v1/simulation/start     # Start simulation
GET  /api/v1/simulation/{id}/state # Get simulation state
POST /api/v1/simulation/{id}/advance # Advance simulation
POST /api/v1/simulation/{id}/pause   # Pause simulation
POST /api/v1/simulation/{id}/resume  # Resume simulation
GET  /api/v1/simulation/{id}/narrative # Get narrative
POST /api/v1/graph/build          # Build knowledge graph
```

### 2.3 Content Orchestrator (Port 8017)

**Purpose:** Convert simulation outputs into LTX-2 video scripts

**File Structure:**
```
services/content-orchestrator/
├── main.py
├── narrative/
│   ├── synthesizer.py        # Aggregate agent outputs
│   ├── storyboard.py         # Create shot-by-shot storyboards
│   └── script.py             # Generate final video scripts
├── scene/
│   ├── spec.py               # Scene specification format
│   ├── compiler.py           # Compile scene specs for LTX-2
│   └── templates.py          # Predefined scene templates
├── integration/
│   ├── simulation_client.py  # Connect to Simulation Engine
│   └── visual_client.py      # Connect to Visual Core
├── config.py
├── models.py
├── tests/
├── k8s-deployment.yaml
└── requirements.txt
```

**Key Endpoints:**
```python
POST /api/v1/narrative/generate   # Generate narrative from simulation
POST /api/v1/storyboard/create     # Create storyboard
POST /api/v1/scene/spec           # Create scene spec
POST /api/v1/pipeline/generate-video # End-to-end pipeline
```

### 2.4 Socials Agent (Port 8015)

**Purpose:** Social media monitoring, narrative tracking, and video report generation

**File Structure:**
```
services/socials-agent/
├── main.py
├── platforms/
│   ├── twitter.py              # Twitter/X monitoring
│   ├── reddit.py                # Reddit monitoring
│   ├── linkedin.py              # LinkedIn monitoring
│   └── base.py                  # Base platform interface
├── analysis/
│   ├── narrative.py             # Narrative tracking
│   ├── sentiment.py             # Sentiment over time
│   ├── virality.py              # Virality prediction
│   └── influence.py             # Influence mapping
├── reports/
│   ├── generator.py             # Video report generation
│   └── templates.py             # Report templates
├── config.py
├── models.py
├── tests/
├── k8s-deployment.yaml
└── requirements.txt
```

**Key Endpoints:**
```python
POST /api/v1/monitor/start        # Start platform monitoring
GET  /api/v1/monitor/{id}/results # Get monitoring results
POST /api/v1/analyze/narrative    # Analyze narrative
POST /api/v1/analyze/virality     # Predict virality
POST /api/v1/reports/generate     # Generate video report
POST /api/v1/simulate/social-scenario # Run social simulation
```

---

## Section 3: Integration & Data Flow

### Integration with Existing Services

**Enhanced Sentiment Agent:**
```python
# New endpoints in services/sentiment-agent/video/
POST /api/v1/video/briefing         # Generate video briefing
POST /api/v1/video/trend-analysis   # Generate trend analysis video
GET  /api/v1/video/{briefing_id}    # Get briefing status
```

**Autonomous Agent Integration:**
- Enhanced GSD Orchestrator with video generation support
- New `generate_video_output()` method for visual tasks
- Integration with Content Orchestrator for end-to-end pipelines

**OpenClaw Skill Registration:**
- `visual_briefing`: Video briefing generation
- `social_simulation`: Social narrative simulation
- `scenario_visualization`: Scenario visualization

### Complete Data Flow Example

**Use Case: Visual Intelligence Report**

```
1. USER REQUEST → "Analyze brand sentiment for 30 days"

2. DATA COLLECTION (Parallel)
   ├─ sentiment-agent:8004 → Sentiment analysis
   └─ socials-agent:8015 → Social monitoring

3. SIMULATION ENGINE :8016
   ├─ Create MiroFish scenario
   ├─ Run 200+ agent simulation (72 hours)
   └─ Return narrative outputs

4. CONTENT ORCHESTRATOR :8017
   ├─ Synthesize narrative
   ├─ Generate storyboard (8 scenes, 10s each)
   └─ Create scene specs

5. VISUAL CORE :8014
   ├─ Generate LTX-2 prompts
   ├─ Apply client LoRA
   ├─ Call LTX-2 API (parallel batch)
   └─ Receive 8 video clips

6. POST-PROCESSING
   ├─ Stitch clips (FFmpeg NVENC on DGX Spark)
   ├─ Add overlays (branding, captions)
   └─ Encode final output

7. DELIVERY
   └─ Upload to MinIO, generate CDN URL

TOTAL TIME: ~15-25 minutes
```

### DGX Spark Workload Distribution

**Local Execution (DGX Spark):**
- Agent orchestration (20GB)
- MiroFish simulation (45GB)
- LLM inference (20GB)
- Video cache (10GB)
- Working memory (15GB)
- System overhead (18GB)

**Cloud/API Execution:**
- LTX-2 video generation (primary)

---

## Section 4: Revenue Implementation

### Product Offerings

| Product | Target Customer | Price | Service Shape |
|---------|----------------|-------|---------------|
| Visual Intelligence Reports | Executives, Consultants | $500-2,000/report or $2,000-5,000/month | 60-90 sec video + PDF |
| Scenario Simulation Services | Risk Officers, Policy Teams | $5,000-25,000/engagement | Multi-scenario video package |
| Social Narrative Modelling | PR Agencies, Brands | $1,500-5,000/analysis or $3,000-15,000/month | Narrative video + predictions |

### Report Templates

```python
REPORT_TEMPLATES = {
    "executive_briefing": {
        "duration": 60,
        "scenes": ["intro", "insight", "data_viz", "trend", "conclusion"],
        "style": "professional",
        "pricing": {"single": "$500", "subscription": "$2,000/month"}
    },
    "deep_dive": {
        "duration": 90,
        "scenes": ["intro", "context", "analysis", "data_viz", "scenarios", "recommendations"],
        "style": "analytical",
        "pricing": {"single": "$1,000", "subscription": "$3,500/month"}
    },
    "comprehensive": {
        "duration": 120,
        "scenes": ["executive_summary", "market_analysis", "competitive", "data", "scenarios", "recommendations"],
        "style": "premium",
        "pricing": {"single": "$2,000", "subscription": "$5,000/month"}
    }
}
```

---

## Section 5: Development Roadmap

### Phase 1: Foundation (Weeks 1-3)

**Goal:** Basic LTX-2 integration and first working video

- Week 1: Visual Core Foundation
- Week 2: Sentiment Agent Enhancement
- Week 3: First Demo

**Milestone:** First working Visual Intelligence Report

### Phase 2: Social Intelligence (Weeks 4-7)

**Goal:** Social monitoring and narrative tracking

- Week 4: Socials Agent Foundation
- Week 5: Narrative Analysis
- Week 6: Social Video Reports
- Week 7: Socials Demo

**Milestone:** First Social Narrative Analysis video

### Phase 3: Simulation Engine (Weeks 8-11)

**Goal:** MiroFish agent swarm simulation

- Week 8: MiroFish Core
- Week 9: Memory and GraphRAG
- Week 10: Scenario Generation
- Week 11: Simulation Demo

**Milestone:** First working MiroFish simulation

### Phase 4: Content Orchestration (Weeks 12-14)

**Goal:** End-to-end pipeline

- Week 12: Content Orchestrator Service
- Week 13: Pipeline Integration
- Week 14: End-to-End Demo

**Milestone:** First Scenario Simulation Service demo

### Phase 5: Revenue Launch (Weeks 15-16)

**Goal:** Production-ready revenue products

- Week 15: Product Packaging
- Week 16: Launch

**Milestone:** Revenue-generating services live

---

## Section 6: Technical Specifications

### Visual Core Technology Stack

```python
# services/visual-core/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
aiofiles==23.2.1
ffmpeg-python==0.2.0
pillow==10.1.0
numpy==1.26.2
```

### LTX Client Implementation

Key classes: `LTXClient`, `LTXVideoRequest`, `LTXVideoResult`

### Prompt Factory

Templates: `CORPORATE_BRIEFING`, `DOCUMENTARY`, `SOCIAL_MEDIA`, `NEWS_REPORT`, `ANALYTICAL`

Methods: `build_prompt()`, `enhance_prompt_for_video()`

### Video Pipeline (FFmpeg on ARM64)

Key methods: `stitch_videos()`, `add_overlays()`, `generate_thumbnail()`

### Simulation Engine Technology Stack

```python
# services/simulation-engine/requirements.txt
fastapi==0.104.1
networkx==3.2.1
numpy==1.26.2
zep-cloud==0.10.0
opentelemetry-api==1.21.0
prometheus-client==0.19.0
```

### MiroFish Core Implementation

Key classes: `Agent`, `SimulationEngine`

Features: Agent decision-making, swarm coordination, GraphRAG knowledge graphs, Zep memory integration

---

## Section 7: Configuration & Deployment

### Kubernetes Deployment

All services follow standard patterns:
- ConfigMap for configuration
- Secret for sensitive data (API keys)
- Service (ClusterIP)
- Deployment with security contexts
- PersistentVolumeClaim for storage
- HorizontalPodAutoscaler for scaling

### Environment Variables

**Visual Core:**
```
LTX_API_KEY, LTX_API_BASE, LTX_MODEL_DEFAULT, MAX_CONCURRENT_REQUESTS,
CACHE_PATH, LORA_STORAGE_PATH, FFMPEG_PATH, OTLP_ENDPOINT
```

**Simulation Engine:**
```
MAX_AGENTS, TICK_INTERVAL, ZEP_API_KEY, STATE_PERSISTENCE, STATE_STORAGE_PATH
```

**Socials Agent:**
```
ENABLE_TWITTER, ENABLE_REDDIT, RATE_LIMIT_PER_MINUTE,
VISUAL_CORE_URL, SIMULATION_ENGINE_URL
```

### DGX Spark ARM64 Optimization

```bash
# Install ARM64 FFmpeg with NVENC
wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz

# Set performance tuning
export OMP_NUM_THREADS=20
export MALLOC_ARENA_MAX=8589934592
```

---

## Section 8: Documentation & Testing Strategy

### Documentation Structure

```
docs/
├── services/              # Service documentation
│   ├── visual-core/
│   ├── simulation-engine/
│   ├── socials-agent/
│   └── content-orchestrator/
├── products/              # Product guides
├── guides/                # Tutorials
├── architecture/          # Architecture docs
└── api/                   # API reference
```

### Testing Strategy

**Testing Pyramid:**
- E2E Tests: 10% (smoke tests)
- Integration Tests: 30%
- Unit Tests: 60%

**Test Coverage:**
- Unit tests for all core components
- Integration tests for service-to-service communication
- E2E tests for complete user workflows
- Performance tests for video generation
- Quality assurance tests for video outputs

---

## Approval & Next Steps

**Status:** Design approved - March 15, 2026

**Next Step:** Create implementation plan using superpowers:writing-plans

**Implementation:** Begin Phase 1 (Visual Core Foundation) immediately after plan creation

---

**Sources:**
- [LTX-2 Documentation](https://console.ltx.video)
- [MiroFish Research](https://github.com/mirofish)
- [Project Chimera Architecture](../architecture/overview.md)
- [DGX Spark Specifications](https://www.nvidia.com/en-us/data-center/products/grace-blackwell/)

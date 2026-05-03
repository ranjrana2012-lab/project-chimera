# Core AI Services

Overview of the AI agents and services that power Project Chimera.

## Services Overview

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| OpenClaw Orchestrator | 8000 | ✅ Production Ready | Central control plane |
| SceneSpeak Agent | 8001 | ✅ Production Ready | Dialogue generation |
| Captioning Agent | 8002 | ⚠️ Partial | Speech-to-text |
| BSL Translation Agent | 8003 | ⚠️ Partial | BSL gloss translation |
| Sentiment Agent | 8004 | ⚠️ Partial | Audience sentiment |
| **Lighting, Sound & Music** | **8005** | **✅ Production Ready** | **Unified audio-visual control** |
| Safety Filter | 8006 | ⚠️ Partial | Content moderation |
| Operator Console | 8007 | ✅ Production Ready | Human oversight |
| **Kimi vLLM Service** | **8012** | **✅ DGX Ready** | **Kimi K2.6 inference (INT4 quantized)** |
| **Kimi Super-Agent** | **50052** | **✅ DGX Ready** | **Hierarchical super-agent gRPC server** |

## Service Details

### OpenClaw Orchestrator (Port 8000)

**Purpose:** Central control plane coordinating all agents

**Key Features:**
- Skill routing and execution
- Agent coordination
- GPU resource scheduling
- Policy engine
- Kafka event streaming

**Health Check:**
```bash
curl http://localhost:8000/health/live
```

### SceneSpeak Agent (Port 8001)

**Purpose:** Real-time dialogue generation using local LLMs

**Key Features:**
- LLaMA-based dialogue generation
- LoRA adapter support
- Sentiment-aware generation
- Response caching

**Health Check:**
```bash
curl http://localhost:8001/health/live
```

### Captioning Agent (Port 8002)

**Purpose:** Live speech-to-text with accessibility

**Key Features:**
- OpenAI Whisper transcription
- WebSocket streaming
- Word-level timestamps
- Language auto-detection

**Status:** ⚠️ Partial - Needs minor fixes to response model

### BSL Translation Agent (Port 8003)

**Purpose:** British Sign Language gloss translation

**Key Features:**
- Text-to-gloss translation
- Non-manual marker annotation
- Gloss formatting standards

**Status:** ⚠️ Partial - Needs minor fixes to response model

### Sentiment Agent (Port 8004)

**Purpose:** Audience sentiment analysis from social media with WorldMonitor context integration

**Key Features:**
- DistilBERT SST-2 model
- Batch text processing
- Trend analysis
- Emotion detection
- **WorldMonitor Integration (v0.5.0)**:
  - Real-time global context enrichment
  - News sentiment analysis
  - Context-aware sentiment scoring
  - WebSocket-based context streaming
  - Category-based event filtering
  - Context caching with TTL

**Status:** ✅ Enhanced with WorldMonitor integration

**WorldMonitor Sidecar:**
- Port: 8010
- Connection: WebSocket (localhost:8010)
- Categories: technology, business, entertainment, sports
- Cache TTL: 300 seconds (5 minutes)

### Lighting, Sound & Music (Port 8005)

**Purpose:** Unified control for theatrical lighting, sound effects, and AI-generated music

**Key Features:**
- **Lighting Module:** DMX/sACN protocol support, OSC message handling, fixture management, fade control
- **Sound Module:** Sound effects library and playback, volume control and mixing, multi-track audio support
- **Music Module:** AI music generation using ACE-Step-1.5 models, track/playlist management, playback controls
- **Cues Module:** Coordinated multi-media scenes, timeline-based execution, scene presets, synchronization primitives

**API Endpoints:**
- `/health/live`, `/health/ready` - Health checks
- `/lighting/*` - DMX/sACN stage automation (9 endpoints)
- `/sound/*` - Sound effects and playback (9 endpoints)
- `/music/*` - AI generation and playback (12 endpoints + WebSocket)
- `/cues/*` - Coordinated scenes (12 endpoints + WebSocket)

**Health Check:**
```bash
curl http://localhost:8005/health/live
```

**Module Status:**
- Lighting: ✅ Active (DMX/sACN, OSC)
- Sound: ✅ Active (playback, mixing)
- Music: ✅ Active (ACE-Step-1.5 integrated)
- Cues: ✅ Active (coordinated execution)

### Safety Filter (Port 8006)

**Purpose:** Multi-layer content moderation

**Key Features:**
- Word-based filtering
- ML-based classification
- Multi-category filtering
- Audit logging

**Status:** ⚠️ Partial - Needs minor fixes to response model

### Operator Console (Port 8007)

**Purpose:** Human oversight interface

**Key Features:**
- Real-time WebSocket updates
- Alert management
- Approval workflow
- Dashboard UI

**Health Check:**
```bash
curl http://localhost:8007/health/live
```

### Kimi K2.6 Super-Agent Stack (DGX Spark GB10 Only)

**Purpose:** Hierarchical super-agent for complex AI workflows requiring long context reasoning, multimodal processing, or agentic coding capabilities.

**Components:**

#### Kimi vLLM Service (Port 8012)
- **Model:** Moonshot AI Kimi K2.6 (1T parameters, 32B active via MoE)
- **Quantization:** Native INT4 (~70GB VRAM)
- **Max Context:** 32,768 tokens
- **Purpose:** OpenAI-compatible API for inference

#### Kimi Super-Agent (Port 50052)
- **Protocol:** gRPC
- **Purpose:** Orchestrates delegation between Nemo Claw and Kimi K2.6
- **Delegation Triggers:**
  - **LONG_CONTEXT:** Requests >8K tokens
  - **MULTIMODAL:** Images, video, or audio content
  - **AGENTIC_CODING:** Keywords like "create agent", "write script"

**Health Checks:**
```bash
# vLLM service
curl http://localhost:8012/health

# Kimi super-agent (requires grpcurl)
grpcurl -plaintext localhost:50052 kimi.KimiSuperAgent/HealthCheck
```

**VRAM Allocation (128GB Total):**
| Component | VRAM Usage |
|-----------|------------|
| Kimi K2.6 (INT4) | ~70 GB |
| KV Cache | ~10 GB |
| Multimodal Processing | ~5 GB |
| Chimera Agents | ~10-20 GB |
| **Headroom** | ~23 GB |

**Status:** ✅ DGX Ready - Requires 128GB GPU VRAM (DGX Spark GB10 specification)

**Quick Start:**
```bash
# Download Kimi K2.6 model
./scripts/download-kimi-k26.sh

# Start vLLM service
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-vllm

# Wait for vLLM readiness
./scripts/wait-for-kimi.sh

# Start super-agent
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-super-agent

# Validate VRAM usage
./scripts/validate-kimi-vram.sh
```

**Related Documentation:**
- [Kimi K2.6 Design Spec](../superpowers/specs/2026-05-01-kimi-k26-super-agent-design.md)
- [Kimi K2.6 Quick Start](../guides/KIMI_QUICKSTART.md)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OpenClaw Orchestrator                      │
│              (Central Control Plane)                        │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┘
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
  SceneSpeak Captioning  BSL  Sentiment Lighting Safety  Operator
    Agent     Agent    Agent   Agent  Sound  Filter  Console
                                     & Music
                                         │
                                         ▼ (Complex Workflows)
                              ┌─────────────────────┐
                              │  Kimi K2.6 Super-Agent│
                              │  (DGX Spark GB10)     │
                              └──────────┬────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   Kimi K2.6 vLLM    │
                              │   (INT4, ~70GB VRAM) │
                              └─────────────────────┘
```

## Related Documentation

- [Lighting, Sound & Music Service](lighting-sound-music.md) - Unified audio-visual control
- [Architecture](../reference/architecture.md) - System architecture
- [API Reference](../reference/api.md) - Complete API docs
- [Quality Platform](quality-platform.md) - Testing infrastructure

## Service Migration Notes

**As of 2026-03-02**, the following services have been consolidated:

- **Lighting Control** → Merged into **Lighting, Sound & Music** (port 8005)
- **Music Generation** → Merged into **Lighting, Sound & Music** (port 8005)
- **Music Orchestration** → Merged into **Lighting, Sound & Music** (port 8005)

All functionality from these services has been preserved and enhanced in the new unified service.

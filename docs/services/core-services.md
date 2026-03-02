# Core AI Services

Overview of the 8 AI agents that power Project Chimera.

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

**Purpose:** Audience sentiment analysis from social media

**Key Features:**
- DistilBERT SST-2 model
- Batch text processing
- Trend analysis
- Emotion detection

**Status:** ⚠️ Partial - Needs minor fixes to response model

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

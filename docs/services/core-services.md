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
| Lighting Control | 8005 | ✅ Production Ready | DMX/sACN control |
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

### Lighting Control (Port 8005)

**Purpose:** DMX/sACN stage automation

**Key Features:**
- DMX/sACN protocol support
- OSC message handling
- Scene preset management
- Fade time control

**Health Check:**
```bash
curl http://localhost:8005/health/live
```

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
    Agent     Agent    Agent   Agent  Control Filter  Console
```

## Related Documentation

- [Architecture](../reference/architecture.md) - System architecture
- [API Reference](../reference/api.md) - Complete API docs
- [Quality Platform](quality-platform.md) - Testing infrastructure

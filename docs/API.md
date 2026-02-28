# Project Chimera API Documentation

Complete API reference for all Project Chimera services.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Common Patterns](#common-patterns)
- [Service APIs](#service-apis)
  - [OpenClaw Orchestrator](#openclaw-orchestrator)
  - [SceneSpeak Agent](#scenespeak-agent)
  - [Captioning Agent](#captioning-agent)
  - [BSL-Text2Gloss Agent](#bsl-text2gloss-agent)
  - [Sentiment Agent](#sentiment-agent)
  - [Lighting Control](#lighting-control)
  - [Safety Filter](#safety-filter)
  - [Operator Console](#operator-console)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [WebSocket APIs](#websocket-apis)

## Overview

Project Chimera exposes RESTful APIs for all services. Each service runs on a distinct port and provides health endpoints for monitoring.

### Base URLs

In the Kubernetes cluster, services are accessed via internal DNS:

```bash
# Services in the 'live' namespace
openclaw-orchestrator.live.svc.cluster.local:8000
scenespeak-agent.live.svc.cluster.local:8001
captioning-agent.live.svc.cluster.local:8002
bsl-text2gloss-agent.live.svc.cluster.local:8003
sentiment-agent.live.svc.cluster.local:8004
lighting-control.live.svc.cluster.local:8005
safety-filter.live.svc.cluster.local:8006
operator-console.live.svc.cluster.local:8007
```

For local development, services run on `localhost` with their respective ports.

### Versioning

All APIs are versioned using the `/api/v1/` prefix. Breaking changes will result in a new version (e.g., `/api/v2/`).

## Authentication

Currently, internal services communicate without authentication within the cluster. Future versions will implement:

- JWT-based authentication for external clients
- mTLS for service-to-service communication
- API keys for third-party integrations

## Common Patterns

### Health Endpoints

All services implement standard health endpoints:

```bash
GET /health/live    # Liveness probe
GET /health/ready   # Readiness probe
GET /health/startup # Startup probe (if applicable)
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Skill Invocation

Most services implement a standard `/invoke` endpoint for compatibility with the OpenClaw skill system:

```bash
POST /invoke
```

**Request:**
```json
{
  "input": {
    "key": "value"
  },
  "timeout_ms": 5000
}
```

**Response:**
```json
{
  "output": {
    "result": "value"
  },
  "metadata": {
    "cached": false,
    "latency_ms": 123
  }
}
```

## Service APIs

### OpenClaw Orchestrator

**Base URL:** `http://openclaw-orchestrator:8000`

Central control plane coordinating all skills and agents.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Orchestration

**POST /v1/orchestrate**

Execute orchestration through specified skills.

**Request:**
```json
{
  "pipeline": "sentiment_to_dialogue",
  "input": {
    "social_posts": ["Amazing performance!", "Love the characters!"]
  },
  "context": {
    "scene_id": "scene-001"
  },
  "timeout_ms": 5000
}
```

**Response:**
```json
{
  "status": "success",
  "output": {
    "proposed_lines": "CHARACTER: [Smiling warmly] Thank you so much for your wonderful response!",
    "stage_cues": ["[LIGHTING: Warm amber wash]"],
    "sentiment_summary": {
      "overall": "positive",
      "confidence": 0.92
    }
  },
  "metadata": {
    "pipeline_id": "sentiment_to_dialogue",
    "steps_executed": 2,
    "total_latency_ms": 850
  }
}
```

#### Skills Management

**GET /skills**

List all available skills.

**Response:**
```json
{
  "skills": [
    {
      "name": "scenespeak",
      "version": "1.0.0",
      "description": "Generates real-time dialogue for theatrical performances",
      "enabled": true,
      "endpoint": "http://scenespeak-agent:8001",
      "capabilities": ["dialogue_generation", "stage_cues"]
    },
    {
      "name": "sentiment",
      "version": "1.0.0",
      "description": "Analyzes audience sentiment from social media",
      "enabled": true,
      "endpoint": "http://sentiment-agent:8004",
      "capabilities": ["sentiment_analysis", "batch_processing"]
    }
  ],
  "total": 7
}
```

**GET /api/v1/skills/{name}**

Get metadata for a specific skill.

**Response:**
```json
{
  "name": "scenespeak",
  "version": "1.0.0",
  "description": "Generates real-time dialogue for theatrical performances",
  "enabled": true,
  "endpoint": "http://scenespeak-agent:8001",
  "capabilities": ["dialogue_generation", "stage_cues"],
  "config": {
    "model": "llama-2-7b",
    "max_tokens": 512,
    "temperature": 0.8
  }
}
```

**POST /api/v1/skills/{name}/enable**

Enable a skill.

**POST /api/v1/skills/{name}/disable**

Disable a skill.

**POST /api/v1/skills/reload**

Reload all skills from the skills directory.

#### Pipelines

**POST /api/v1/pipelines/execute**

Execute a pipeline of skills.

**Request:**
```json
{
  "steps": [
    {
      "skill_name": "sentiment",
      "input_mapping": {}
    },
    {
      "skill_name": "scenespeak",
      "input_mapping": {
        "sentiment": "sentiment_output"
      }
    }
  ],
  "input": {
    "social_posts": ["Amazing!", "Great!"]
  },
  "parallel": false
}
```

**GET /api/v1/pipelines/status/{id}**

Get pipeline execution status.

**POST /api/v1/pipelines/define**

Define a new pipeline.

**DELETE /api/v1/pipelines/{id}**

Delete a pipeline.

---

### SceneSpeak Agent

**Base URL:** `http://scenespeak-agent:8001`

Real-time dialogue generation using local LLMs.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Dialogue Generation

**POST /v1/generate**

Generate dialogue for a scene.

**Request:**
```json
{
  "scene_context": {
    "title": "Scene 1: The Meeting",
    "characters": ["ALICE", "BOB"],
    "setting": "A coffee shop",
    "current_situation": "Alice and Bob meet for the first time"
  },
  "dialogue_context": [
    {"character": "ALICE", "text": "Hi, I'm Alice.", "timestamp": "2024-01-01T12:00:00Z"}
  ],
  "sentiment_vector": {
    "overall": "positive",
    "energy": 0.8
  }
}
```

**Response:**
```json
{
  "proposed_lines": "BOB: [Smiling and standing up] Nice to meet you, Alice. I'm Bob. [Gestures to the empty chair] Please, have a seat. [LIGHTING: Soft warm light on table]",
  "stage_cues": [
    "[LIGHTING: Soft warm light on table]",
    "[SOUND: Gentle cafe ambiance]"
  ],
  "metadata": {
    "model": "llama-2-7b-scenespeak",
    "tokens_generated": 45,
    "prompt_tokens": 150
  },
  "cached": false,
  "latency_ms": 850
}
```

**POST /invoke**

Standard skill invocation endpoint.

---

### Captioning Agent

**Base URL:** `http://captioning-agent:8002`

Live speech-to-text with accessibility descriptions.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Transcription

**POST /api/v1/transcribe**

Transcribe audio using Whisper.

**Request:**
```json
{
  "audio_data": "base64-encoded-audio-data",
  "language": "en",
  "task": "transcribe",
  "timestamps": true,
  "vad_filter": true,
  "word_timestamps": false
}
```

**Response:**
```json
{
  "text": "Hello, welcome to the show. We're excited to have you here tonight.",
  "language": "en",
  "confidence": 0.96,
  "segments": [
    {
      "id": 0,
      "text": "Hello, welcome to the show.",
      "start": 0.0,
      "end": 2.5
    },
    {
      "id": 1,
      "text": "We're excited to have you here tonight.",
      "start": 2.5,
      "end": 5.8
    }
  ],
  "processing_time_ms": 450
}
```

**POST /api/v1/detect-language**

Detect the language of audio.

**Response:**
```json
{
  "language": "en",
  "confidence": 0.98
}
```

#### WebSocket Streaming

**WebSocket /api/v1/stream**

Real-time transcription streaming.

**Initial Message:**
```json
{
  "session_id": "optional-session-id",
  "language": "en",
  "sample_rate": 16000,
  "channels": 1
}
```

**Server Response:**
```json
{
  "status": "connected",
  "session_id": "sess-abc123"
}
```

**Client sends:** Binary audio chunks

**Server responds:**
```json
{
  "text": "Hello",
  "is_final": false,
  "timestamp": "2024-01-01T12:00:01Z"
}
```

---

### BSL-Text2Gloss Agent

**Base URL:** `http://bsl-text2gloss-agent:8003`

British Sign Language gloss notation translation.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Gloss Translation

**POST /api/v1/translate**

Translate text to BSL gloss notation.

**Request:**
```json
{
  "text": "Hello, how are you today?",
  "preserve_format": true,
  "include_metadata": true
}
```

**Response:**
```json
{
  "gloss": "HELLO YOU HOW TODAY?",
  "metadata": {
    "source_word_count": 6,
    "gloss_sign_count": 5,
    "non_manual_markers": ["bf", "q"]
  },
  "breakdown": [
    {"source": "Hello", "gloss": "HELLO", "markers": ["wave"]},
    {"source": "how are you", "gloss": "YOU HOW", "markers": ["q", "br"]},
    {"source": "today", "gloss": "TODAY", "markers": []}
  ]
}
```

**POST /invoke**

Standard skill invocation endpoint.

---

### Sentiment Agent

**Base URL:** `http://sentiment-agent:8004`

Audience sentiment analysis from social media.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Sentiment Analysis

**POST /api/v1/analyze**

Analyze sentiment of text.

**Request:**
```json
{
  "texts": [
    "This performance is absolutely amazing!",
    "I'm not sure about this scene...",
    "Best show I've ever seen!"
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "This performance is absolutely amazing!",
      "sentiment": "positive",
      "scores": {
        "positive": 0.95,
        "negative": 0.02,
        "neutral": 0.03
      },
      "confidence": 0.93
    }
  ],
  "summary": {
    "overall": "positive",
    "average_scores": {
      "positive": 0.65,
      "negative": 0.15,
      "neutral": 0.20
    }
  }
}
```

**POST /api/v1/analyze-batch**

Batch process multiple texts.

---

### Lighting Control

**Base URL:** `http://lighting-control:8005`

DMX/OSC stage automation.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Scene Management

**POST /v1/lighting/set**

Set a lighting scene.

**Request:**
```json
{
  "name": "warm_wash",
  "channels": {
    "1": 255,
    "2": 200,
    "3": 150,
    "4": 0
  },
  "osc_address": "/lighting/scene",
  "fade_time_ms": 1000
}
```

**Response:**
```json
{
  "status": "success",
  "scene": "warm_wash",
  "timestamp": "2024-01-01T12:00:00Z",
  "approval_required": true
}
```

**POST /api/v1/lighting/blackout**

Immediate blackout.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**GET /v1/lighting/state**

Get current lighting status.

**Response:**
```json
{
  "current_scene": "warm_wash",
  "channels": {
    "1": 255,
    "2": 200
  },
  "dmx_connected": true,
  "osc_connected": true
}
```

---

### Safety Filter

**Base URL:** `http://safety-filter:8006`

Multi-layer content moderation.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Content Filtering

**POST /api/v1/check**

Check content for safety issues.

**Request:**
```json
{
  "content": "The character should say something appropriate here.",
  "context": "family_show"
}
```

**Response:**
```json
{
  "safe": true,
  "confidence": 0.98,
  "flagged_categories": [],
  "filtered_content": "The character should say something appropriate here.",
  "review_required": false
}
```

#### Review Queue

**GET /api/v1/safety/review-queue**

Get items requiring human review.

**Response:**
```json
{
  "items": [
    {
      "id": "review-001",
      "content": "Original content...",
      "flagged_categories": ["inappropriate"],
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

**POST /api/v1/safety/review/{item_id}**

Submit review decision.

**Request:**
```json
{
  "decision": "approve"  // or "reject" or "modify"
}
```

---

### Operator Console

**Base URL:** `http://operator-console:8007`

Human oversight and approval interface.

#### Health Endpoints

```bash
GET /health/live
GET /health/ready
```

#### Alerts

**GET /api/v1/console/alerts**

Get active alerts.

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "severity": "warning",
      "source": "safety-filter",
      "message": "Content flagged for review",
      "timestamp": "2024-01-01T12:00:00Z",
      "requires_action": true
    }
  ]
}
```

#### Approvals

**GET /api/v1/console/approvals/pending**

Get pending approvals.

**Response:**
```json
{
  "items": [
    {
      "id": "approval-001",
      "type": "lighting_scene",
      "description": "Scene: dramatic_spotlight",
      "requester": "scenespeak-agent",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ]
}
```

**POST /api/v1/console/approvals/{id}**

Approve or reject an action.

**Request:**
```json
{
  "decision": "approve",
  "notes": "Approved for dramatic effect"
}
```

#### WebSocket Events

**WebSocket /api/v1/console/events**

Real-time console events.

**Server sends:**
```json
{
  "type": "alert",
  "data": {
    "severity": "warning",
    "message": "Content flagged"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Error Codes

All services return standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request |
| 401  | Unauthorized (future) |
| 403  | Forbidden (future) |
| 404  | Not Found |
| 422  | Validation Error |
| 429  | Rate Limited (future) |
| 500  | Internal Server Error |
| 503  | Service Unavailable |

**Error Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input: field is required",
    "details": {
      "field": "scene_context"
    }
  }
}
```

## Rate Limiting

Rate limiting is not currently enforced but will be added in future versions:

- Default: 100 requests per minute per IP
- WebSocket connections: 10 concurrent connections per IP

## WebSocket APIs

The following services offer WebSocket interfaces:

1. **Captioning Agent** - Real-time transcription streaming
2. **Operator Console** - Live event updates

### Connection Pattern

```javascript
const ws = new WebSocket('ws://captioning-agent:8002/api/v1/captioning/stream');

// Send configuration
ws.send(JSON.stringify({
  language: 'en',
  sample_rate: 16000
}));

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.text);
};

// Send audio chunks
ws.send(audioChunk);

// Close connection
ws.send('done');
```

---

For more information:
- [Architecture Documentation](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)
- [Deployment Guide](DEPLOYMENT.md)

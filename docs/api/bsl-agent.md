# BSL Agent API Documentation

**Version:** v0.5.0
**Base URL:** `http://localhost:8003`
**Service:** Text-to-BSL gloss translation with real-time avatar rendering

---

## Overview

The BSL Agent provides:
- Text to BSL (British Sign Language) gloss translation
- Real-time avatar rendering for sign language visualization
- Gesture library with caching
- Session-based avatar management

---

## Endpoints

### 1. Translate Text to BSL Gloss

Translate English text to BSL gloss notation.

**Endpoint:** `POST /api/v1/translate`

**Request Body:**

```json
{
  "text": "Hello, welcome to the theatre.",
  "format": "gloss",
  "include_facial_expressions": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | English text to translate |
| `format` | string | No | Output format: `gloss` or `json`. Default: `gloss` |
| `include_facial_expressions` | boolean | No | Include facial expressions. Default: true |

**Response (gloss format):**

```
HELLO WELCOME THEATRE.
^smile ^eyebrows-up
```

**Response (JSON format):**

```json
{
  "gloss": "HELLO WELCOME THEATRE.",
  "words": [
    {"word": "Hello", "gloss": "HELLO", "duration": 1.5},
    {"word": "welcome", "gloss": "WELCOME", "duration": 1.2},
    {"word": "to the theatre", "gloss": "THEATRE", "duration": 2.0}
  ],
  "facial_expressions": ["smile", "eyebrows-up"],
  "translation_time": 0.15
}
```

---

### 2. Batch Translate

Translate multiple texts at once.

**Endpoint:** `POST /api/v1/translate/batch`

**Request Body:**

```json
{
  "texts": [
    "Hello, welcome!",
    "How are you?",
    "Goodbye!"
  ],
  "format": "json"
}
```

**Response:**

```json
{
  "translations": [
    {"text": "Hello, welcome!", "gloss": "HELLO WELCOME"},
    {"text": "How are you?", "gloss": "HOW YOU"},
    {"text": "Goodbye!", "gloss": "GOODBYE"}
  ],
  "total_time": 0.3
}
```

---

### 3. List Available Formats

List supported output formats.

**Endpoint:** `GET /api/v1/formats`

**Response:**

```json
{
  "formats": [
    {
      "name": "gloss",
      "description": "Plain text gloss notation"
    },
    {
      "name": "json",
      "description": "Structured JSON with timing"
    }
  ]
}
```

---

### 4. Avatar: Sign Text

Queue text for avatar rendering and signing.

**Endpoint:** `POST /api/v1/avatar/sign`

**Request Body:**

```json
{
  "text": "Hello, welcome to the theatre!",
  "session_id": "user123"
}
```

**Response:**

```json
{
  "success": true,
  "avatar_id": "avatar_user123",
  "gestures_queued": 5,
  "state": "signing",
  "estimated_duration": 7.5
}
```

---

### 5. Avatar: Get State

Get current avatar rendering state.

**Endpoint:** `GET /api/v1/avatar/state`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session identifier |

**Example:**

```bash
curl "http://localhost:8003/api/v1/avatar/state?session_id=user123"
```

**Response:**

```json
{
  "state": "signing",
  "current_gesture": {
    "id": "gesture_abc123",
    "gloss": "WELCOME",
    "duration": 1.5,
    "both_hands": true,
    "facial_expression": "smile"
  },
  "queue_size": 3,
  "metrics": {
    "frames_rendered": 150,
    "avg_frame_time": 0.033,
    "dropped_frames": 0
  }
}
```

**States:**

| State | Description |
|-------|-------------|
| `idle` | Avatar is idle, waiting for input |
| `signing` | Avatar is currently signing |
| `transitioning` | Transitioning between gestures |
| `error` | Avatar encountered an error |

---

### 6. Avatar: List Active Avatars

List all active avatar instances.

**Endpoint:** `GET /api/v1/avatar/list`

**Response:**

```json
{
  "avatars": [
    {
      "id": "avatar_user123",
      "session_id": "user123",
      "state": "signing",
      "metrics": {
        "frames_rendered": 150,
        "avg_frame_time": 0.033
      }
    }
  ],
  "total": 1
}
```

---

### 7. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

### 8. Metrics

**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format.

---

## Configuration

The BSL Agent uses environment-based configuration with pydantic-settings. All configuration is loaded from environment variables or a `.env` file.

### Service Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `service_name` | string | `bsl-agent` | Service identifier for logging and metrics |
| `port` | integer | `8003` | HTTP server port |
| `log_level` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `environment` | string | `development` | Deployment environment (development, staging, production) |

### Avatar Rendering

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `avatar_model_path` | string | `/models/bsl_avatar` | Path to avatar model files |
| `avatar_resolution` | string | `1920x1080` | Video resolution (width x height) |
| `avatar_fps` | integer | `30` | Frames per second for avatar animation |
| `enable_facial_expressions` | boolean | `true` | Enable facial expression rendering |
| `enable_body_language` | boolean | `true` | Enable body language gestures |

### Translation

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `cache_ttl` | integer | `86400` | Translation cache TTL in seconds (24 hours) |

### OpenTelemetry

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `otlp_endpoint` | string | `http://localhost:4317` | OTLP gRPC endpoint for metrics and traces |

### Environment File Example

```bash
# Service
SERVICE_NAME=bsl-agent
PORT=8003
LOG_LEVEL=INFO
ENVIRONMENT=development

# Avatar Rendering
AVATAR_MODEL_PATH=/models/bsl_avatar
AVATAR_RESOLUTION=1920x1080
AVATAR_FPS=30
ENABLE_FACIAL_EXPRESSIONS=true
ENABLE_BODY_LANGUAGE=true

# Translation
CACHE_TTL=86400

# OpenTelemetry
OTLP_ENDPOINT=http://localhost:4317
```

## Examples

### Basic Translation

```bash
curl -X POST http://localhost:8003/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?"
  }'
```

### JSON Format with Facial Expressions

```bash
curl -X POST http://localhost:8003/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Nice to meet you",
    "format": "json",
    "include_facial_expressions": true
  }'
```

### Avatar Signing

```bash
# Queue text for signing
curl -X POST http://localhost:8003/api/v1/avatar/sign \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The performance will begin shortly",
    "session_id": "audience_member_1"
  }'

# Check avatar state
curl "http://localhost:8003/api/v1/avatar/state?session_id=audience_member_1"
```

---

## Gesture Format

BSL gestures include the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `gloss` | string | BSL gloss word |
| `duration` | float | Gesture duration in seconds |
| `both_hands` | boolean | Whether both hands are used |
| `dominant_hand` | string | `left` or `right` |
| `handshape` | string | Hand configuration (fist, open, etc.) |
| `orientation` | string | Palm orientation |
| `location` | string | Signing location on body |
| `facial_expression` | string | Non-manual marker |
| `body_language` | string | Body posture/lean |

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_TEXT",
    "message": "Text cannot be empty",
    "details": {}
  }
}
```

---

*Last Updated: March 2026*
*BSL Agent v0.4.0*

## Metrics

The BSL Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `bsl_active_sessions` | Gauge | - | Active BSL avatar rendering sessions |
| `bsl_gestures_rendered_total` | Counter | show_id | Total gestures rendered |
| `bsl_avatar_frame_rate` | Gauge | session_id | Avatar rendering FPS |
| `bsl_translation_latency_seconds` | Histogram | - | Time to translate text to BSL gloss |

### Tracing

The BSL Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)

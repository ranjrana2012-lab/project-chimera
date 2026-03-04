# BSL Agent API Documentation

**Version:** 3.0.0
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
*BSL Agent v3.0.0*

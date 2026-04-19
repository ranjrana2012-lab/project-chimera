# Project Chimera - API Documentation

## Overview

Project Chimera exposes RESTful APIs for all MVP services. This document provides comprehensive API reference for all endpoints.

## Base URLs

| Environment | Base URL |
|-------------|-----------|
| Development | `http://localhost:8000` (Orchestrator) |
| Services | `http://localhost:[port]` |
| Docker Internal | `http://[service-name]:[port]` |

## Common Response Format

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2026-04-19T12:00:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  },
  "timestamp": "2026-04-19T12:00:00Z"
}
```

## Health Endpoints

### All services provide health check endpoints:

| Service | Health Endpoint | Response Fields |
|---------|-----------------|-----------------|
| Orchestrator | `GET /health` | status, service, version |
| SceneSpeak | `GET /health` | status, service, model_available |
| Translation | `GET /health` | status, service, mock_mode |
| Sentiment | `GET /health` | status, service, model_loaded |
| Safety Filter | `GET /health/live` | status, service |
| Console | `GET /health` | status, service |
| Hardware Bridge | `GET /health` | status, service |

### Example

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "service": "openclaw-orchestrator",
  "version": "1.0.0"
}
```

## OpenClaw Orchestrator API (Port 8000)

### Endpoints

#### 1. Orchestrate Prompt

```http
POST /api/orchestrate
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "The audience is excited and cheering loudly!",
  "show_id": "test_show_001",
  "enable_sentiment": true,
  "enable_safety": true,
  "enable_translation": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "orchestration_id": "orch_12345",
    "prompt": "The audience is excited...",
    "sentiment": {
      "label": "positive",
      "confidence": 0.95
    },
    "dialogue": {
      "text": "What an amazing performance!",
      "speaker": "narrator"
    },
    "safety_check": {
      "safe": true,
      "policy": "family"
    }
  },
  "timestamp": "2026-04-19T12:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input
- `500 Internal Server Error` - Service error
- `503 Service Unavailable` - Dependency unavailable

#### 2. Generate Dialogue

```http
POST /api/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Create a dialogue for a dramatic scene",
  "show_id": "test_show_002",
  "characters": ["narrator", "protagonist"],
  "style": "dramatic"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "dialogue_id": "dlg_67890",
    "content": "NARRATOR: The storm rages outside...",
    "metadata": {
      "style": "dramatic",
      "length": 150
    }
  }
}
```

#### 3. Show Control

```http
POST /api/show/control
Content-Type: application/json
```

**Request Body:**
```json
{
  "show_id": "test_show_003",
  "action": "start",
  "scene_name": "opening_number"
}
```

**Actions:** `start`, `stop`, `pause`, `next_scene`

**Response:**
```json
{
  "status": "success",
  "data": {
    "show_id": "test_show_003",
    "status": "running",
    "current_scene": "opening_number"
  }
}
```

## SceneSpeak Agent API (Port 8001)

### Endpoints

#### 1. Generate Dialogue

```http
POST /api/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Create dialogue for a happy character",
  "context": "The show just ended successfully",
  "style": "conversational",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "text": "That was incredible! I can't believe we did it!",
    "model": "glm-4",
    "tokens_used": 45
  }
}
```

#### 2. Stream Dialogue (Server-Sent Events)

```http
POST /api/stream
Content-Type: application/json
```

**Request Body:** Same as `/api/generate`

**Response:** SSE stream with chunks

```bash
curl -N http://localhost:8001/api/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a story"}'
```

## Sentiment Agent API (Port 8004)

### Endpoints

#### 1. Analyze Sentiment

```http
POST /api/analyze
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "This is absolutely wonderful! Best day ever!",
  "language": "en"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "sentiment": "positive",
    "confidence": 0.92,
    "emotions": {
      "joy": 0.85,
      "excitement": 0.78
    },
    "model": "distilbert-sentiment"
  }
}
```

#### 2. Batch Analyze

```http
POST /api/batch
Content-Type: application/json
```

**Request Body:**
```json
{
  "texts": [
    "I love this show!",
    "This is terrible.",
    "It's okay, I guess."
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "results": [
      {"text": "I love this show!", "sentiment": "positive", "confidence": 0.95},
      {"text": "This is terrible.", "sentiment": "negative", "confidence": 0.98},
      {"text": "It's okay, I guess.", "sentiment": "neutral", "confidence": 0.75}
    ]
  }
}
```

## Safety Filter API (Port 8006)

### Endpoints

#### 1. Check Content Safety

```http
POST /v1/check
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "This is a family-friendly show.",
  "policy": "family"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "safe": true,
    "confidence": 0.99,
    "policy": "family",
    "categories": {
      "violence": false,
      "profanity": false,
      "sexual_content": false
    }
  }
}
```

#### 2. Filter Content

```http
POST /v1/filter
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Some inappropriate content here",
  "replacement": "***"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "filtered_content": "Some inappropriate content here",
    "replacements_made": 0,
    "original_safe": true
  }
}
```

## Translation Agent API (Port 8002)

### Endpoints

#### 1. Translate Text

```http
POST /translate
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Hello, welcome to the show!",
  "source_language": "en",
  "target_language": "es",
  "context": "performance"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "translated_text": "¡Hola, bienvenidos al espectáculo!",
    "source_language": "en",
    "target_language": "es",
    "confidence": 0.95,
    "mock_mode": true
  }
}
```

**Note:** Currently in mock mode - returns placeholder translations.

## Operator Console API (Port 8007)

### Endpoints

#### 1. Get Show Status

```http
GET /api/show/{show_id}/status
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "show_id": "test_show_001",
    "status": "running",
    "current_scene": "scene_2",
    "services": {
      "orchestrator": "healthy",
      "scenespeak": "healthy",
      "sentiment": "healthy"
    }
  }
}
```

#### 2. Control Show

```http
POST /api/show/control
Content-Type: application/json
```

**Request Body:**
```json
{
  "show_id": "test_show_001",
  "action": "start",
  "parameters": {
    "scene": "opening_number",
    "duration": 300
  }
}
```

**Actions:** `start`, `stop`, `pause`, `resume`, `next_scene`

## Error Codes Reference

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Fix request format |
| 401 | Unauthorized | Check API key |
| 404 | Not Found | Check endpoint URL |
| 422 | Validation Error | Fix request data |
| 500 | Server Error | Check service logs |
| 503 | Service Unavailable | Check dependencies |
| 504 | Gateway Timeout | Increase timeout |

## Rate Limiting

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 60 | 10 |
| Basic | 600 | 100 |
| Pro | 6000 | 1000 |

## WebSocket API (Planned)

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to Chimera WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Message Format

```json
{
  "type": "orchestration_update",
  "data": {
    "orchestration_id": "orch_12345",
    "status": "processing",
    "progress": 0.5
  }
}
```

## Testing APIs

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Orchestrate
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "show_id": "test"}'

# Sentiment analysis
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is wonderful!"}'
```

### Using Python

```python
import httpx

# Orchestrate
response = httpx.post(
    "http://localhost:8000/api/orchestrate",
    json={
        "prompt": "Test message",
        "show_id": "test_show"
    }
)
print(response.json())
```

### Using JavaScript

```javascript
// Fetch API
const response = await fetch('http://localhost:8000/api/orchestrate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: 'Test message',
    show_id: 'test_show'
  })
});
const data = await response.json();
console.log(data);
```

## SDK Examples (Planned)

Coming soon:
- Python SDK
- JavaScript SDK
- Go SDK

---

**Related Documentation:**
- `docs/DEVELOPER_SETUP.md` - Development guide
- `docs/CONFIGURATION.md` - Configuration guide
- `tests/TEST_SETUP.md` - Testing guide

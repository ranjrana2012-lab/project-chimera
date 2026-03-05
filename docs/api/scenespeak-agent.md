# SceneSpeak Agent API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8001`
**Service:** LLM-powered dialogue generation with LoRA adapter support

---

## Overview

SceneSpeak generates contextual dialogue for live theatre performances. It supports:
- Context-aware dialogue generation
- Sentiment-based tone adjustment
- LoRA adapter support for genre-specific styling
- Performance caching for reduced latency

---

## Authentication

Currently, no authentication is required for local development. Production deployment will require API keys.

---

## Endpoints

### 1. Generate Dialogue

Generate dialogue based on scene context and sentiment.

**Endpoint:** `POST /v1/generate`

**Request Body:**

```json
{
  "context": "Scene: A garden at sunset. Characters: ROMEO and JULIET.",
  "sentiment": 0.7,
  "max_tokens": 256,
  "temperature": 0.8,
  "adapter": "dramatic-theatre"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context` | string | Yes | Scene context and character information |
| `sentiment` | float | No | Sentiment value (-1.0 to 1.0). Default: 0.0 |
| `max_tokens` | integer | No | Maximum tokens to generate. Default: 256 |
| `temperature` | float | No | Sampling temperature (0.0 to 1.0). Default: 0.7 |
| `adapter` | string | No | LoRA adapter name to use |

**Response:**

```json
{
  "dialogue": "ROMEO: What light through yonder window breaks?",
  "metadata": {
    "tokens_used": 15,
    "generation_time": 0.12,
    "adapter": "dramatic-theatre",
    "model": "scenespeak-v3"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid request parameters |
| 500 | Internal server error |

---

### 2. List Available LoRA Adapters

List all available LoRA adapters for genre-specific dialogue styling.

**Endpoint:** `GET /v1/adapters`

**Response:**

```json
{
  "adapters": [
    {
      "name": "dramatic-theatre",
      "description": "Shakespearean dramatic dialogue",
      "loaded": true
    },
    {
      "name": "comedy",
      "description": "Light-hearted comedic dialogue",
      "loaded": false
    },
    {
      "name": "noir",
      "description": "Film noir hard-boiled dialogue",
      "loaded": false
    }
  ],
  "current_adapter": "dramatic-theatre"
}
```

---

### 3. Load LoRA Adapter

Load a specific LoRA adapter for use in dialogue generation.

**Endpoint:** `POST /v1/adapters/load`

**Request Body:**

```json
{
  "name": "comedy"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Adapter 'comedy' loaded successfully",
  "previous_adapter": "dramatic-theatre",
  "load_time": 0.45
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 404 | Adapter not found |
| 500 | Load failed |

---

### 4. Switch LoRA Adapters

Switch from one adapter to another.

**Endpoint:** `POST /v1/adapters/switch`

**Request Body:**

```json
{
  "from": "dramatic-theatre",
  "to": "comedy"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Switched from 'dramatic-theatre' to 'comedy'",
  "switch_time": 0.23
}
```

---

### 5. Benchmark Adapter

Benchmark adapter performance for comparison.

**Endpoint:** `POST /v1/adapters/benchmark`

**Request Body:**

```json
{
  "adapter": "comedy",
  "iterations": 10,
  "test_context": "Scene: A coffee shop. Two friends meet."
}
```

**Response:**

```json
{
  "adapter": "comedy",
  "avg_load_time": 0.42,
  "avg_generation_time": 0.15,
  "memory_usage_mb": 256,
  "iterations": 10
}
```

---

### 6. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

**Endpoint:** `GET /health/ready`

**Response:** `OK`

---

### 7. Metrics

**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format.

---

## Examples

### Basic Dialogue Generation

```bash
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Scene: A garden at sunset",
    "sentiment": 0.7
  }'
```

### Using LoRA Adapter

```bash
# Load adapter
curl -X POST http://localhost:8001/v1/adapters/load \
  -H "Content-Type: application/json" \
  -d '{"name": "noir"}'

# Generate with adapter
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Detective enters the dimly lit office",
    "adapter": "noir",
    "temperature": 0.9
  }'
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Sentiment must be between -1.0 and 1.0",
    "details": {}
  }
}
```

---

## Rate Limiting

Current limits (local development):
- 100 requests/minute per IP
- 1000 requests/minute total

---

*Last Updated: March 2026*
*SceneSpeak Agent v0.4.0*

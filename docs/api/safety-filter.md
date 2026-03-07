# Safety Filter API Documentation

**Version:** v0.5.0
**Base URL:** `http://localhost:8006`
**Service:** Multi-layer ML-based content moderation

---

## Overview

The Safety Filter provides three-layer content moderation:
1. **Pattern Matching** - Regex-based detection of known harmful patterns
2. **ML Classification** - Toxic/hateful/sexual/violent content classification
3. **Context-Aware Analysis** - Transformer-based conversation context understanding

---

## Endpoints

### 1. Check Content

Check content through all three filtering layers.

**Endpoint:** `POST /api/v1/check`

**Request Body:**

```json
{
  "content": "Test message for safety check",
  "user_id": "user123",
  "session_id": "session456",
  "conversation_history": [
    {"user": "Hello!"},
    {"assistant": "Hi there! How can I help?"}
  ],
  "context": {
    "source": "web",
    "platform": "chat"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Content to check |
| `user_id` | string | No | User identifier for audit |
| `session_id` | string | No | Session identifier for audit |
| `conversation_history` | array | No | Conversation turns for context |
| `context` | object | No | Additional metadata |

**Response:**

```json
{
  "action": "allow",
  "layer": "audit",
  "confidence": 1.0,
  "reason": "Content passed all safety checks",
  "matched_patterns": [],
  "model_predictions": {
    "toxic": 0.05,
    "hateful": 0.02,
    "sexual": 0.01,
    "violent": 0.03,
    "self-harm": 0.01
  },
  "timestamp": "2026-03-04T12:00:00Z"
}
```

**Actions:**

| Action | Description |
|--------|-------------|
| `allow` | Content is safe to display |
| `block` | Content must be blocked |
| `flag` | Content needs human review |
| `modify` | Content should be modified (censored) |

**Layers:**

| Layer | Description |
|-------|-------------|
| `pattern` | Blocked by pattern matching |
| `classification` | Flagged by ML classification |
| `context` | Flagged by context analysis |
| `audit` | Passed all checks |

---

### 2. Batch Check

Check multiple pieces of content.

**Endpoint:** `POST /api/v1/check/batch`

**Request Body:**

```json
{
  "items": [
    {"content": "First message"},
    {"content": "Second message"}
  ]
}
```

**Response:**

```json
{
  "results": [
    {
      "content": "First message",
      "action": "allow",
      "confidence": 1.0
    },
    {
      "content": "Second message",
      "action": "flag",
      "confidence": 0.75,
      "reason": "Flagged by classification: toxic (score: 0.78)"
    }
  ]
}
```

---

### 3. Filter Content

Filter content by replacing detected words with asterisks.

**Endpoint:** `POST /api/v1/filter`

**Request Body:**

```json
{
  "content": "Some message with bad words",
  "replacement_char": "*"
}
```

**Response:**

```json
{
  "original": "Some message with bad words",
  "filtered": "Some message with *** ****s",
  "replacements": 2
}
```

---

### 4. Get Statistics

Get filtering statistics.

**Endpoint:** `GET /api/v1/statistics`

**Response:**

```json
{
  "total_checked": 1000,
  "allowed": 950,
  "blocked": 30,
  "flagged": 20,
  "modified": 0,
  "allow_rate": 0.95,
  "block_rate": 0.03,
  "flag_rate": 0.02
}
```

---

### 5. Get Audit Log

Retrieve audit log entries.

**Endpoint:** `GET /api/v1/audit`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Maximum entries to return (default: 100) |
| `offset` | integer | Number of entries to skip (default: 0) |
| `user_id` | string | Filter by user ID |

**Example:**

```bash
curl "http://localhost:8006/api/v1/audit?limit=50&user_id=user123"
```

**Response:**

```json
{
  "entries": [
    {
      "timestamp": "2026-03-04T12:00:00Z",
      "content_hash": "abc123",
      "content_preview": "Test message...",
      "action": "allow",
      "confidence": 1.0,
      "reason": "Content passed all safety checks",
      "user_id": "user123",
      "session_id": "session456"
    }
  ],
  "total": 1000,
  "limit": 50,
  "offset": 0
}
```

---

### 6. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

### 7. Metrics

**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format.

---

## Examples

### Basic Check

```bash
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, how are you today?"
  }'
```

### Check with Conversation History

```bash
curl -X POST http://localhost:8006/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "content": "That sounds great!",
    "conversation_history": [
      {"user": "Hi there"},
      {"assistant": "Hello! How can I help you?"}
    ]
  }'
```

### Batch Check

```bash
curl -X POST http://localhost:8006/api/v1/check/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"content": "First message"},
      {"content": "Second message"},
      {"content": "Third message"}
    ]
  }'
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_CONTENT",
    "message": "Content cannot be empty",
    "details": {}
  }
}
```

---

## Configuration

The safety filter can be configured with:

| Setting | Default | Description |
|---------|---------|-------------|
| Pattern enabled | true | Enable pattern matching layer |
| Classification threshold | 0.7 | ML classification threshold |
| Context threshold | 0.6 | Context analysis threshold |
| Audit log enabled | true | Enable audit logging |
| Max audit entries | 10000 | Maximum audit log entries |

---

*Last Updated: March 2026*
*Safety Filter v0.4.0*

# Captioning Agent API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8002`
**Service:** Speech-to-text with real-time streaming

---

## Endpoints

### 1. Transcribe Audio

Transcribe audio file to text.

**Endpoint:** `POST /api/v1/transcribe`

**Request:** Multipart form data with audio file

```bash
curl -X POST http://localhost:8002/api/v1/transcribe \
  -F "audio=@audio.wav" \
  -F "language=en"
```

**Response:**

```json
{
  "text": "Hello, welcome to the theatre.",
  "language": "en",
  "confidence": 0.95,
  "duration": 2.5,
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.98},
    {"word": "welcome", "start": 0.6, "end": 1.2, "confidence": 0.94}
  ]
}
```

---

### 2. Detect Language

Detect language of audio or text.

**Endpoint:** `POST /api/v1/detect-language`

**Request Body:**

```json
{
  "text": "Bonjour, comment allez-vous?"
}
```

**Response:**

```json
{
  "language": "fr",
  "confidence": 0.98,
  "alternatives": [
    {"language": "es", "confidence": 0.02}
  ]
}
```

---

### 3. WebSocket: Real-time Streaming

Stream audio for real-time transcription.

**Endpoint:** `WS /api/v1/stream`

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8002/api/v1/stream');

// Send audio data
ws.send(binaryAudioData);

// Receive transcription
ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log(result.text);
};
```

**Response Format:**

```json
{
  "text": "partial transcription",
  "is_final": false,
  "confidence": 0.92
}
```

---

### 4. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

*Last Updated: March 2026*
*Captioning Agent v0.4.0*

## Metrics

The Captioning Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `captioning_latency_seconds` | Histogram | - | Time from speech to caption |
| `captioning_delivered_total` | Counter | show_id | Captions delivered |
| `captioning_accuracy_score` | Gauge | show_id | Accuracy score (0-1) |
| `captioning_active_users` | Gauge | - | Users viewing captions |

### Tracing

The Captioning Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)

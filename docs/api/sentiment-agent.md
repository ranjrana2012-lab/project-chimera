# Sentiment Agent API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8004`
**Service:** Audience emotion and sentiment analysis

---

## Endpoints

### 1. Analyze Sentiment

Analyze sentiment of a single text.

**Endpoint:** `POST /api/v1/analyze`

**Request Body:**

```json
{
  "text": "The audience seems excited and engaged!"
}
```

**Response:**

```json
{
  "sentiment": {
    "score": 0.75,
    "label": "positive"
  },
  "emotions": {
    "joy": 0.8,
    "surprise": 0.3,
    "neutral": 0.1,
    "sadness": 0.0,
    "anger": 0.0,
    "fear": 0.0
  },
  "confidence": 0.92
}
```

---

### 2. Batch Analyze

Analyze multiple texts.

**Endpoint:** `POST /api/v1/analyze-batch`

**Request Body:**

```json
{
  "texts": [
    "I love this performance!",
    "This is boring.",
    "I'm not sure how I feel."
  ]
}
```

**Response:**

```json
{
  "results": [
    {"text": "I love this performance!", "score": 0.9, "label": "positive"},
    {"text": "This is boring.", "score": -0.7, "label": "negative"},
    {"text": "I'm not sure how I feel.", "score": 0.0, "label": "neutral"}
  ],
  "average_score": 0.07
}
```

---

### 3. Get Sentiment Trend

Get sentiment trend over time.

**Endpoint:** `GET /api/v1/trend`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `window` | string | Time window: `1m`, `5m`, `15m`, `1h` |

**Example:**

```bash
curl "http://localhost:8004/api/v1/trend?window=5m"
```

**Response:**

```json
{
  "trend": "rising",
  "current_score": 0.6,
  "change": "+0.3",
  "data_points": [
    {"timestamp": "2026-03-04T11:55:00Z", "score": 0.3},
    {"timestamp": "2026-03-04T12:00:00Z", "score": 0.6}
  ]
}
```

---

### 4. Get Aggregate Sentiment

Get aggregated sentiment statistics.

**Endpoint:** `GET /api/v1/aggregate`

**Response:**

```json
{
  "average": 0.45,
  "count": 150,
  "distribution": {
    "positive": 80,
    "neutral": 50,
    "negative": 20
  }
}
```

---

### 5. Get Emotion Aggregates

Get aggregated emotion breakdown.

**Endpoint:** `GET /api/v1/emotions`

**Response:**

```json
{
  "emotions": {
    "joy": 0.65,
    "surprise": 0.20,
    "neutral": 0.10,
    "sadness": 0.03,
    "anger": 0.01,
    "fear": 0.01
  },
  "dominant": "joy"
}
```

---

### 6. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

*Last Updated: March 2026*
*Sentiment Agent v0.4.0*

## Configuration

The Sentiment Agent uses environment-based configuration with pydantic-settings.

### Service Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `sentiment-agent` | Service identifier for logging and tracing |
| `PORT` | integer | `8004` | HTTP server port |
| `HOST` | string | `0.0.0.0` | Server bind address |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Model Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `USE_ML_MODEL` | boolean | `false` | Enable DistilBERT model for enhanced sentiment analysis |
| `MODEL_PATH` | string | `null` | Path to DistilBERT model files (optional) |
| `MODEL_CACHE_DIR` | string | `./models_cache` | Directory for cached model files |

### Processing Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_TEXT_LENGTH` | integer | `10000` | Maximum text length to process (characters) |
| `BATCH_SIZE` | integer | `32` | Maximum batch size for processing multiple texts |

### OpenTelemetry Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OTLP_ENDPOINT` | string | `http://localhost:4317` | OpenTelemetry protocol endpoint |
| `ENABLE_TRACING` | boolean | `true` | Enable distributed tracing |

## Metrics

The Sentiment Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sentiment_audience_avg` | Gauge | show_id, time_window | Average audience sentiment |
| `sentiment_emotion_joy_total` | Counter | show_id | Joy emotion count |
| `sentiment_emotion_surprise_total` | Counter | show_id | Surprise emotion count |
| `sentiment_emotion_neutral_total` | Counter | show_id | Neutral emotion count |
| `sentiment_emotion_sadness_total` | Counter | show_id | Sadness emotion count |
| `sentiment_emotion_anger_total` | Counter | show_id | Anger emotion count |
| `sentiment_emotion_fear_total` | Counter | show_id | Fear emotion count |
| `sentiment_analysis_queue_size` | Gauge | - | Texts awaiting analysis |
| `sentiment_analysis_duration_seconds` | Gauge | - | Analysis time |

### Tracing

The Sentiment Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)

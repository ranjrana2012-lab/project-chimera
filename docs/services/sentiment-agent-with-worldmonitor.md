# Sentiment Agent with WorldMonitor Integration

The Sentiment Agent analyzes audience sentiment from social media posts and live feedback, now enhanced with WorldMonitor integration for real-time global context and news sentiment analysis.

## Overview

The Sentiment Agent (port 8004) provides sophisticated sentiment analysis capabilities that are now enriched with:

- **Real-time global context** from WorldMonitor sidecar service
- **News sentiment analysis** for understanding current events impact
- **Context-aware sentiment scoring** that considers global events
- **Enhanced response models** with contextual metadata

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Sentiment Agent (8004)                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Sentiment Analysis Engine                  │  │
│  │  - DistilBERT SST-2 model                                    │  │
│  │  - Batch processing                                          │  │
│  │  - Trend analysis                                            │  │
│  │  - Emotion detection                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                   │                                 │
│  ┌────────────────────────────────▼─────────────────────────────┐  │
│  │              Context Enrichment Layer                        │  │
│  │  - Context Builder                                           │  │
│  │  - WebSocket Client                                          │  │
│  │  - Cache Manager                                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                   │                                 │
│  ┌────────────────────────────────▼─────────────────────────────┐  │
│  │            News Sentiment Analyzer                           │  │
│  │  - Headline analysis                                         │  │
│  │  - Event impact scoring                                     │  │
│  │  - Category-based filtering                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   WorldMonitor Sidecar (8010)                       │
│  - Real-time global events                                        │
│  - News headlines                                                 │
│  - Category filtering                                             │
│  - WebSocket streaming                                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Context Enrichment

The Sentiment Agent automatically enriches sentiment analysis with global context:

```python
# Automatic context enrichment
{
  "texts": ["Amazing performance!"],
  "include_context": true  # Default: true
}

# Response includes context
{
  "results": [...],
  "context": {
    "global_events": [
      {
        "event_id": "evt_123",
        "headline": "Tech breakthrough announced",
        "sentiment": "positive",
        "categories": ["technology"]
      }
    ],
    "news_sentiment": {
      "overall": "positive",
      "by_category": {
        "technology": 0.85,
        "entertainment": 0.72
      }
    }
  }
}
```

### 2. News Sentiment Analysis

Analyze sentiment of news headlines and events:

```python
# News sentiment endpoint
POST /api/v1/news-sentiment

{
  "headlines": [
    "New AI model revolutionizes healthcare",
    "Economic concerns rise globally"
  ],
  "categories": ["technology", "business"]
}

# Response
{
  "results": [
    {
      "headline": "New AI model revolutionizes healthcare",
      "sentiment": "positive",
      "score": 0.92,
      "category": "technology"
    }
  ],
  "overall_sentiment": "positive",
  "category_summary": {
    "technology": {
      "sentiment": "positive",
      "average_score": 0.92
    }
  }
}
```

### 3. Context API

Retrieve current context from WorldMonitor:

```python
# Get all context
GET /api/v1/context

# Get context by category
GET /api/v1/context?category=technology

# Force refresh
GET /api/v1/context?refresh=true

# Response
{
  "events": [
    {
      "event_id": "evt_123",
      "timestamp": "2026-03-03T12:00:00Z",
      "headline": "Tech breakthrough announced",
      "description": "Major advancement in quantum computing",
      "categories": ["technology", "science"],
      "severity": "high",
      "sentiment": "positive"
    }
  ],
  "metadata": {
    "total_events": 1,
    "last_updated": "2026-03-03T12:00:00Z",
    "cache_age_seconds": 45
  }
}
```

### 4. Context Statistics

Get statistics about context data:

```python
GET /api/v1/context/stats

# Response
{
  "statistics": {
    "total_events": 15,
    "by_category": {
      "technology": 5,
      "business": 3,
      "entertainment": 4,
      "sports": 3
    },
    "by_severity": {
      "high": 2,
      "medium": 8,
      "low": 5
    },
    "sentiment_distribution": {
      "positive": 8,
      "neutral": 5,
      "negative": 2
    }
  },
  "cache_info": {
    "last_updated": "2026-03-03T12:00:00Z",
    "cache_age_seconds": 45,
    "using_cached": true
  }
}
```

## Configuration

### Environment Variables

```bash
# WorldMonitor Integration
WORLDMONITOR_ENABLED=true
WORLDMONITOR_HOST=localhost
WORLDMONITOR_PORT=8010
WORLDMONITOR_RECONNECT_DELAY=5.0

# Context Configuration
CONTEXT_CACHE_TTL=300
CONTEXT_CATEGORIES=technology,business,entertainment,sports
CONTEXT_MAX_EVENTS=100

# News Sentiment
NEWS_SENTIMENT_ENABLED=true
NEWS_SENTIMENT_BATCH_SIZE=10
NEWS_SENTIMENT_CATEGORIES=technology,business,entertainment,sports
```

### Configuration File

```yaml
# config/sentiment-agent.yaml
worldmonitor:
  enabled: true
  host: ${WORLDMONITOR_HOST:-localhost}
  port: ${WORLDMONITOR_PORT:-8010}
  reconnect_delay: ${WORLDMONITOR_RECONNECT_DELAY:-5.0}
  timeout: 30.0

context:
  enabled: true
  cache_ttl: ${CONTEXT_CACHE_TTL:-300}
  categories:
    - technology
    - business
    - entertainment
    - sports
  max_events: ${CONTEXT_MAX_EVENTS:-100}

news_sentiment:
  enabled: true
  batch_size: ${NEWS_SENTIMENT_BATCH_SIZE:-10}
  categories:
    - technology
    - business
    - entertainment
    - sports
  use_context: true

sentiment:
  model: distilbert-base-uncased-finetuned-sst-2-english
  batch_size: 32
  max_length: 512
  device: cpu
```

## Usage Examples

### Basic Sentiment Analysis

```python
import requests

# Analyze sentiment
response = requests.post(
    "http://sentiment-agent:8004/api/v1/analyze",
    json={
        "texts": [
            "This performance is absolutely amazing!",
            "I'm not sure about this scene..."
        ]
    }
)

data = response.json()
print(data["results"])
```

### Sentiment Analysis with Context

```python
# Include global context in analysis
response = requests.post(
    "http://sentiment-agent:8004/api/v1/analyze",
    json={
        "texts": ["The tech references feel very timely!"],
        "include_context": true
    }
)

data = response.json()
print(data["context"])  # Global events context
```

### News Sentiment Analysis

```python
# Analyze news headlines
response = requests.post(
    "http://sentiment-agent:8004/api/v1/news-sentiment",
    json={
        "headlines": [
            "AI breakthrough transforms healthcare",
            "Markets show volatility"
        ],
        "categories": ["technology", "business"]
    }
)

data = response.json()
print(data["category_summary"])
```

### Get Current Context

```python
# Retrieve current global context
response = requests.get(
    "http://sentiment-agent:8004/api/v1/context"
)

data = response.json()
for event in data["events"]:
    print(f"{event['headline']} - {event['sentiment']}")
```

### Filter Context by Category

```python
# Get only technology events
response = requests.get(
    "http://sentiment-agent:8004/api/v1/context?category=technology"
)

data = response.json()
print(f"Technology events: {len(data['events'])}")
```

## Deployment Guide

### Kubernetes Deployment

The Sentiment Agent is deployed with WorldMonitor as a sidecar:

```yaml
# k8s/sentiment-agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-agent
  namespace: live
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sentiment-agent
  template:
    metadata:
      labels:
        app: sentiment-agent
    spec:
      containers:
      - name: sentiment-agent
        image: ghcr.io/project-chimera/sentiment-agent:v0.4.0
        ports:
        - containerPort: 8004
        env:
        - name: WORLDMONITOR_ENABLED
          value: "true"
        - name: WORLDMONITOR_HOST
          value: "localhost"
        - name: WORLDMONITOR_PORT
          value: "8010"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi

      - name: worldmonitor-sidecar
        image: ghcr.io/project-chimera/worldmonitor:v0.4.0
        ports:
        - containerPort: 8010
        env:
        - name: WM_CATEGORIES
          value: "technology,business,entertainment,sports"
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
```

### Docker Compose (Local Development)

```yaml
# docker-compose.yml
services:
  sentiment-agent:
    build: ./services/sentiment-agent
    ports:
      - "8004:8004"
    environment:
      - WORLDMONITOR_ENABLED=true
      - WORLDMONITOR_HOST=worldmonitor
      - WORLDMONITOR_PORT=8010
    depends_on:
      - worldmonitor

  worldmonitor:
    build: ./services/worldmonitor
    ports:
      - "8010:8010"
    environment:
      - WM_CATEGORIES=technology,business,entertainment,sports
```

### Health Checks

```bash
# Liveness probe
curl http://sentiment-agent:8004/health/live

# Readiness probe
curl http://sentiment-agent:8004/health/ready

# With context check
curl http://sentiment-agent:8004/health/ready
# Returns 200 when WorldMonitor connection is established
```

## API Endpoints

### Sentiment Analysis

- `POST /api/v1/analyze` - Analyze sentiment of text
- `POST /api/v1/analyze-batch` - Batch sentiment analysis
- `POST /api/v1/analyze-with-context` - Analyze with global context

### News Sentiment

- `POST /api/v1/news-sentiment` - Analyze news headlines sentiment
- `GET /api/v1/news-sentiment/stats` - Get news sentiment statistics

### Context API

- `GET /api/v1/context` - Get current global context
- `GET /api/v1/context/stats` - Get context statistics
- `GET /api/v1/context/categories` - List available categories

### Health

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (includes WorldMonitor status)

## Monitoring

### Metrics

The Sentiment Agent exposes metrics for monitoring:

- `sentiment_requests_total` - Total sentiment analysis requests
- `sentiment_latency_seconds` - Sentiment analysis latency
- `context_cache_hits` - Context cache hits
- `context_cache_misses` - Context cache misses
- `worldmonitor_connection_status` - WorldMonitor connection status (1=connected, 0=disconnected)
- `news_sentiment_requests_total` - News sentiment analysis requests

### Prometheus Example

```promql
# Sentiment analysis rate
rate(sentiment_requests_total[5m])

# Average latency
rate(sentiment_latency_seconds_sum[5m]) / rate(sentiment_latency_seconds_count[5m])

# WorldMonitor connection status
worldmonitor_connection_status

# Context cache hit rate
context_cache_hits / (context_cache_hits + context_cache_misses)
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest services/sentiment-agent/tests/

# Run context tests
pytest services/sentiment-agent/tests/test_context_enrichment.py

# Run news sentiment tests
pytest services/sentiment-agent/tests/test_news_sentiment.py
```

### Integration Tests

```bash
# Test WorldMonitor integration
pytest services/sentiment-agent/tests/integration/test_worldmonitor_integration.py

# Test end-to-end with context
pytest services/sentiment-agent/tests/integration/test_context_flow.py
```

## Troubleshooting

### WorldMonitor Connection Issues

If WorldMonitor is not connected:

1. Check WorldMonitor is running:
   ```bash
   curl http://worldmonitor:8010/health
   ```

2. Check WebSocket connection:
   ```bash
   # Check logs for connection errors
   kubectl logs sentiment-agent -n live | grep -i websocket
   ```

3. Verify configuration:
   ```bash
   # Check environment variables
   kubectl exec sentiment-agent -n live -- env | grep WORLDMONITOR
   ```

### Context Not Updating

If context is stale:

1. Force refresh:
   ```bash
   curl "http://sentiment-agent:8004/api/v1/context?refresh=true"
   ```

2. Check cache TTL:
   ```bash
   curl http://sentiment-agent:8004/api/v1/context/stats
   ```

3. Verify WorldMonitor is sending events:
   ```bash
   # Check WorldMonitor logs
   kubectl logs deployment/sentiment-agent -c worldmonitor-sidecar -n live
   ```

## Related Documentation

- [Core Services](core-services.md) - All AI services overview
- [API Reference](../reference/api.md) - Complete API documentation
- [Architecture](../reference/architecture.md) - System architecture
- [WorldMonitor Usage Guide](../guides/worldmonitor-context-usage.md) - Usage examples

# WorldMonitor + Sentiment Agent Integration Design

**Date:** 2026-03-03
**Status:** ✅ Approved
**Version:** 1.0.0

---

## Overview

Integrate WorldMonitor's comprehensive global intelligence platform into the sentiment agent using a **sidecar pattern**, enabling:

1. **Context Enrichment** - Automatic global context in sentiment responses
2. **News Sentiment Analysis** - Analyze sentiment of aggregated news feeds
3. **Standalone WorldMonitor Features** - Dedicated context endpoints

This integration enhances the sentiment agent with real-time global situational awareness while maintaining the existing sentiment analysis capabilities.

---

## Architecture

### Sidecar Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Pod                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │   Sentiment Agent        │  │   WorldMonitor Sidecar   │ │
│  │   (Python/FastAPI)       │  │   (Node.js)              │ │
│  │                          │  │                          │ │
│  │  Port 8004               │  │  Port 3001               │ │
│  │  - Sentiment Analysis    │  │  - News Aggregation      │ │
│  │  - Context Enrichment    │◄─┤  - Global Intelligence   │ │
│  │  - New Endpoints         │  │  - AI Summarization      │ │
│  │  - WebSocket Client      │┼─►│  - WebSocket Server      │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│                                              │               │
│                                    Shared Volume/Redis        │
└─────────────────────────────────────────────────────────────┘
```

### Communication Flow

1. **WorldMonitor Sidecar** aggregates data from 100+ news sources
2. **WebSocket** pushes real-time context updates to Sentiment Agent
3. **Sentiment Agent** enriches responses with cached global context
4. **Redis** provides shared caching for fast lookups

---

## Components

### Sentiment Agent (Enhanced)

**Existing:**
- DistilBERT SST-2 sentiment analysis
- Emotion detection
- Trend analysis
- OpenClaw skill support

**New:**
- WebSocket client for real-time context from WorldMonitor
- Context enrichment layer for automatic response enhancement
- News sentiment analyzer using existing model on WorldMonitor feeds
- Dedicated context API endpoints

### WorldMonitor Sidecar

**Core Features:**
- News aggregation from 100+ sources (geopolitical, tech, finance, happy news)
- Country Instability Index (CII) calculation
- Threat classification (keyword, ML, LLM)
- Real-time event tracking (conflicts, disasters, markets)
- AI-powered summarization and forecasting

**Data Layers:**
- Active conflicts and protests
- Natural disasters
- Military bases and movements
- Cyber threat IOCs
- Undersea cables and pipelines
- Market and crypto data
- 16 languages with RTL support

### Shared Storage (Redis)

- Cached context data (5-minute TTL)
- News archive for sentiment analysis
- Configuration for data sources

---

## Data Flow

### Real-time Context Flow (WebSocket)

```
WorldMonitor Sidecar                          Sentiment Agent
     │                                                │
     │  [1] Aggregate news from 100+ sources          │
     │  [2] Calculate CII scores                      │
     │  [3] Classify threats                          │
     │                                                │
     │  [4] Push context update ─────────────────────►│  [5] Update context cache
     │     WebSocket: {                                │     [6] Enrich next sentiment
     │       type: "context_update",                   │         response with new context
     │       data: {                                   │
     │         cii_scores: {...},                      │
     │         threats: [...],                         │
     │         major_events: [...]                     │
     │       }                                         │
     │     }                                           │
```

### Sentiment Analysis with Context

```
Client                   Sentiment Agent              WorldMonitor
  │                           │                          │
  │ POST /api/v1/analyze       │                          │
  │ {text: "Amazing show!"}    │                          │
  │───────────────────────────►│                          │
  │                           │ [1] Analyze sentiment     │
  │                           │ [2] Enrich with cached    │
  │                           │     context from WS       │
  │                           │ [3] Return response:      │
  │◄──────────────────────────│ {                        │
  │   sentiment: {             │   sentiment: {...},      │
  │     label: "positive",     │   context: {             │
  │     confidence: 0.95       │     cii_score: 35,       │
  │   },                       │     major_events: [...],  │
  │   context: {               │     relevant_news: [...]  │
  │     cii_score: 35,         │   }                      │
  │     summary: "Low..."      │ }                        │
  │   }                       │                          │
```

---

## API Design

### Enhanced Sentiment Endpoints

```python
POST /api/v1/analyze
{
  "text": "The audience loves this performance!",
  "include_context": true  # NEW - defaults to true
}

Response:
{
  "sentiment": {
    "label": "positive",
    "confidence": 0.95
  },
  "context": {  # NEW
    "global_cii": 35,
    "country_summary": {
      "GB": {"score": 25, "trend": "stable"},
      "US": {"score": 40, "trend": "rising"}
    },
    "active_threats": [
      {"level": "low", "type": "civil_unrest", "location": "London"}
    ],
    "relevant_events": [
      {"type": "economic", "summary": "Markets up 2%..."}
    ],
    "last_updated": "2026-03-03T12:00:00Z"
  }
}
```

### New Context Endpoints

```python
# Global context
GET /api/v1/context/global
Response: {global_cii, active_threats, major_events, summary}

# Country-specific context
GET /api/v1/context/country/{code}
Response: {country_cii, recent_events, news_summary, instability_factors}

# Real-time context stream
WebSocket /api/v1/context/stream
Server sends: {type: "context_update", data: {...}}
```

### New News Sentiment Endpoint

```python
POST /api/v1/news/sentiment
{
  "sources": ["bbc", "reuters"],
  "categories": ["geopolitical"],
  "hours": 24
}

Response: {
  "analyzed_articles": 45,
  "average_sentiment": "neutral",
  "sentiment_distribution": {...},
  "top_positive": [...],
  "top_negative": [...]
}
```

---

## Deployment

### Kubernetes Pod Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sentiment-agent-lsm
  namespace: chimera
spec:
  containers:
  # Main Sentiment Agent
  - name: sentiment-agent
    image: ghcr.io/project-chimera/sentiment-agent:v0.4.0
    ports:
    - containerPort: 8004
      name: http
    env:
    - name: WORLDMONITOR_SIDECAR_URL
      value: "http://localhost:3001"
    - name: REDIS_HOST
      value: "redis.shared.svc.cluster.local"
    volumeMounts:
    - name: shared-cache
      mountPath: /app/shared

  # WorldMonitor Sidecar
  - name: worldmonitor-sidecar
    image: ghcr.io/project-chimera/worldmonitor-sidecar:v1.0.0
    ports:
    - containerPort: 3001
      name: http
    env:
    - name: WS_BROADCAST_URL
      value: "ws://sentiment-agent:8004/api/v1/context/stream"
    - name: REDIS_HOST
      value: "redis.shared.svc.cluster.local"
    volumeMounts:
    - name: shared-cache
      mountPath: /app/shared

  volumes:
  - name: shared-cache
    emptyDir: {}
```

### Docker Compose (Local Development)

```yaml
services:
  sentiment-agent:
    build: ./services/sentiment-agent
    ports: ["8004:8004"]
    environment:
      - WORLDMONITOR_SIDECAR_URL=http://worldmonitor:3001
    depends_on:
      - worldmonitor
      - redis

  worldmonitor:
    build: ./services/worldmonitor-sidecar
    ports: ["3001:3001"]
    environment:
      - WS_BROADCAST_URL=ws://sentiment-agent:8004/api/v1/context/stream
      - REDIS_HOST=redis
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

---

## Error Handling & Fallbacks

### WebSocket Connection Failures

```python
if not worldmonitor_connected:
    # Use cached context from Redis
    context = await redis.get("context:cache")
    # Stale context is better than no context
    response["context"] = context
    response["context"]["stale"] = True
    # Attempt reconnection in background
    background_tasks.add_task(reconnect_sidecar)
```

### Sidecar Unavailable

```python
if context_fetch_failed:
    return {
        "sentiment": {...},  # Still provide sentiment
        "context": {
            "status": "unavailable",
            "message": "Global context temporarily unavailable",
            "cached_at": "2026-03-03T11:30:00Z"
        }
    }
```

### Memory & Resource Limits

- MAX_CONTEXT_CACHE_SIZE = 100 (last 100 context updates)
- MAX_NEWS_ARTICLES = 1000
- LRU eviction when limits reached

---

## Configuration

### Environment Variables

```bash
# WorldMonitor Sidecar Integration
WORLDMONITOR_SIDECAR_URL=http://localhost:3001
WORLDMONITOR_WS_ENDPOINT=ws://localhost:3001/context/stream
CONTEXT_ENRICHMENT_ENABLED=true
CONTEXT_CACHE_TTL=300

# Redis (Shared Cache)
REDIS_HOST=redis.shared.svc.cluster.local
REDIS_PORT=6379
REDIS_CONTEXT_KEY=worldmonitor:context
REDIS_NEWS_KEY=worldmonitor:news

# Context Enrichment Settings
CONTEXT_INCLUDE_CII=true
CONTEXT_INCLUDE_THREATS=true
CONTEXT_INCLUDE_EVENTS=true
CONTEXT_INCLUDE_NEWS_SUMMARY=true
DEFAULT_CONTEXT_COUNTRY=GB

# News Sentiment Analysis
NEWS_SENTIMENT_ENABLED=true
NEWS_SENTIMENT_MAX_ARTICLES=500
NEWS_SENTIMENT_CATEGORIES=geopolitical,tech,finance
```

---

## Testing Strategy

### Unit Tests

- `test_context_enrichment_positive_sentiment()`
- `test_context_enrichment_with_high_threat_level()`
- `test_context_cache_invalidation()`
- `test_websocket_context_update_handling()`
- `test_news_sentiment_aggregation()`

### Integration Tests

- `test_sentiment_agent_receives_context_updates()`
- `test_sentiment_with_context_enrichment_e2e()`
- `test_news_sentiment_analysis_e2e()`
- `test_websocket_stream_context_updates()`

### Performance Targets

- Context enrichment adds <50ms to sentiment response
- WebSocket context updates propagate within 100ms
- Sidecar can handle 100 concurrent connections
- Memory usage: <2GB total (sentiment + sidecar)

---

## Documentation & Migration

### New Documentation Files

```
docs/services/sentiment-agent-with-worldmonitor.md
docs/services/sentiment-agent/API.md
docs/plans/2026-03-03-worldmonitor-integration.md (implementation)
docs/guides/worldmonitor-context-usage.md
```

### Updated Existing Docs

- `docs/services/core-services.md`
- `docs/reference/api.md`
- `docs/reference/architecture.md`
- `CHANGELOG.md`

### Migration Path

1. **Phase 1:** Build WorldMonitor sidecar container
2. **Phase 2:** Add WebSocket client to sentiment agent
3. **Phase 3:** Implement context enrichment layer
4. **Phase 4:** Add new context and news sentiment endpoints
5. **Phase 5:** Deploy integrated pod, update documentation
6. **Phase 6:** Monitor performance, optimize

---

## Success Criteria

- [x] Design approved
- [ ] WorldMonitor sidecar container built
- [ ] WebSocket communication working
- [ ] Context enrichment functional
- [ ] New endpoints operational
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Deployed to Kubernetes
- [ ] Performance targets met

---

**Status:** ✅ Design Approved - Ready for Implementation Planning

# Performance-First Optimization for Production Readiness - Design Spec

**Date:** April 19, 2026
**Type:** Performance Optimization
**Timeline:** 3 weeks
**Target:** Self-hosted university/organization infrastructure

---

## Overview & Goals

**Objective:** Optimize Project Chimera MVP for production deployment on university infrastructure with <5 second response times for end-to-end flows.

**Success Criteria:**
- Multi-agent coordination latency reduced to <5 seconds (currently higher)
- Translation agent activated with real API (currently mock)
- ML models pre-loaded on startup (eliminates 30-60s cold start)
- Production deployment scripts ready for university infrastructure
- Performance monitoring dashboard operational

**Scope:**
- Focus on MVP services (8 core services)
- Target deployment: Self-hosted university/organization infrastructure
- Timeline: 2-3 weeks

**Out of Scope (deferred to later phases):**
- Advanced security features (authentication, rate limiting)
- Full monitoring stack (Prometheus/Grafana advanced setup)
- CI/CD pipeline automation
- Disaster recovery procedures

---

## Architecture & Components

### Current Architecture (Bottlenecks Identified)

```
Operator Console (8007)
       ↓
OpenClaw Orchestrator (8000)
   ↓ ↓ ↓ ↓ ↓ ↓ ↓
SceneSpeak  Safety  Sentiment  Trans  Hardware  Dashboard  Health
(8001)      (8006)   (8004)    (8002)  (8008)    (8013)     (8012)
```

**Performance Bottlenecks:**
1. Synchronous orchestration - Orchestrator waits for each agent sequentially
2. No connection pooling - New HTTP connection per request
3. ML model cold start - DistilBERT loads on first request
4. Mock translation - No actual API integration
5. No request caching - Repeated computations for similar inputs

### Optimized Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Performance Layer (New)                         │
│  • Connection Pool Manager (shared across services)        │
│  • Request Cache (Redis-based)                              │
│  • ML Model Pre-loader (service startup)                    │
│  • Async Task Queue (background processing)                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
    Same MVP Services (with optimized communication)
```

### New Components

#### 1. Connection Pool Manager
**File:** `services/shared/connection_pool.py`

Manages persistent HTTP connections between services. Reuses connections to eliminate TCP handshake overhead.

#### 2. Request Cache
**File:** `services/shared/cache.py`

Redis-based caching for service responses with appropriate TTLs:
- Sentiment: 5-minute TTL (audience mood changes)
- Translation: 1-hour TTL (content doesn't change)
- SceneSpeak: No cache (creative generation varies)

#### 3. ML Model Pre-loader
**File:** Service startup hooks in each agent

Loads ML models during service startup or Docker build. Health endpoint blocks until `model_loaded: true`.

#### 4. Parallel Orchestration
**File:** `services/openclaw-orchestrator/orchestrator.py`

Uses `asyncio.gather()` for concurrent agent calls instead of sequential execution.

#### 5. Translation Agent Activation
**File:** `services/translation-agent/config.py`

Configures real translation API (Google Translate) to replace mock mode.

---

## Data Flow & Optimizations

### Optimized Flow

```
User Request → Orchestrator
    ↓ (check cache)
Cache hit? → Return cached result (if available)
    ↓ (parallel requests via connection pool)
┌─────────────┬─────────────┬─────────────┐
↓             ↓             ↓             ↓
Sentiment    SceneSpeak    Safety        Translation
(100-200ms)  (2-5s LLM)    (50-100ms)    (real API)
    └─────────────┴─────────────┴─────────────┘
                ↓ (async aggregation)
        Orchestrator combines results
                ↓
            Response
Target time: <5 seconds
```

### Key Optimizations

1. **Parallel Agent Calls** - Independent agents run concurrently
2. **Smart Caching Strategy** - Cache keys based on content hash
3. **Connection Pooling** - 5-10 persistent connections per service
4. **ML Model Pre-loading** - Models loaded during Docker build/startup

---

## Implementation Components

### Component 1: Connection Pool Manager

```python
class ConnectionPoolManager:
    """Manages persistent HTTP connections between services."""

    def __init__(self, max_connections: int = 10):
        self.pools = {}
        self.max_connections = max_connections

    async def get_connection(self, service_url: str):
        """Get or create a pooled connection."""
        if service_url not in self.pools:
            self.pools[service_url] = HTTPConnectionPool(
                service_url, max_connections=self.max_connections
            )
        return self.pools[service_url]
```

### Component 2: Request Cache

```python
class RequestCache:
    """Redis-based caching for service responses."""

    def cache_key(self, prompt: str, show_id: str, agent: str) -> str:
        """Generate cache key."""
        return f"{agent}:{show_id}:{hashlib.md5(prompt.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[dict]:
        """Get cached response."""
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None

    async def set(self, key: str, value: dict, ttl: int):
        """Cache response with TTL."""
        self.redis.setex(key, ttl, json.dumps(value))
```

### Component 3: ML Model Pre-loader

```python
@app.on_event("startup")
async def preload_model():
    """Pre-load ML model on service startup."""
    global model, tokenizer, model_loaded

    logger.info("Loading DistilBERT model...")
    model = DistilBERTForSequenceClassification.from_pretrained(
        "distilbert-base-uncased-finetuned-sst-2-english"
    )
    tokenizer = DistilBERTTokenizerFast.from_pretrained(
        "distilbert-base-uncased-finetuned-sst-2-english"
    )

    # Warm up with sample input
    _ = model.predict(["Sample input"])

    model_loaded = True
    logger.info("Model loaded and ready")

@app.get("/health")
async def health():
    """Health check that blocks until model is loaded."""
    return {
        "status": "healthy" if model_loaded else "initializing",
        "model_loaded": model_loaded
    }
```

### Component 4: Parallel Orchestration

```python
async def orchestrate_parallel(prompt: str, show_id: str, options: dict):
    """Orchestrate agents in parallel for better performance."""

    tasks = []

    if options.get("enable_sentiment"):
        tasks.append(call_sentiment_agent(prompt))

    if options.get("enable_safety"):
        tasks.append(call_safety_agent(prompt))

    if options.get("enable_translation"):
        tasks.append(call_translation_agent(prompt, "en"))

    # LLM generation is the bottleneck, call it separately
    dialogue = await call_scenespeak_agent(prompt, show_id)

    # Wait for all fast agents to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "dialogue": dialogue,
        "sentiment": results[0] if options.get("enable_sentiment") else None,
        "safety": results[1] if options.get("enable_safety") else None,
        "translation": results[2] if options.get("enable_translation") else None
    }
```

### Component 5: Translation Agent Activation

```python
class TranslationConfig:
    API_PROVIDER = "google"
    GOOGLE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    DEFAULT_SOURCE = "en"
    DEFAULT_TARGET = "es"
    CACHE_TTL = 3600  # 1 hour
    GOOGLE_API_URL = "https://translation.googleapis.com/language/translate/v2"
```

---

## Testing Strategy

### Performance Testing

**File:** `tests/performance/test_optimization_targets.py`

Key tests:
- `test_end_to_end_under_5_seconds` - Full orchestration in <5s
- `test_ml_model_preloaded` - First request <1s (not 30s)
- `test_cache_hit_performance` - Cache hits in <100ms
- `test_parallel_agent_calls` - Parallel faster than sequential

### Integration Tests

**File:** `tests/integration/test_performance_optimizations.py`

Key tests:
- Connection pooling reuses connections
- Real translation API returns actual translations
- Cache invalidation works correctly

### Load Testing Updates

**File:** `tests/load/locustfile.py` (enhanced)

Monitors p95 response times and fails if >5 seconds.

---

## Deployment & Operations

### Production Deployment Script

**File:** `scripts/deploy-production.sh`

Automated deployment including:
1. Pre-deployment health checks
2. Docker Compose build and start
3. Service health verification
4. ML model readiness checks
5. Smoke tests

### Systemd Service Files

**File:** `scripts/systemd/project-chimera.service`

Enables auto-start on boot for university infrastructure.

### Monitoring Script

**File:** `scripts/monitor-performance.sh`

Continuously monitors response times and alerts on degradation.

### Performance Dashboard

**File:** `scripts/monitor/grafana-dashboard.json`

Grafana dashboard showing:
- Response time (p95)
- Requests per second
- Cache hit rate
- Connection pool utilization

---

## Timeline & Milestones

### Week 1: Performance Optimizations

**Day 1-2:** Connection Pooling
- Implement `ConnectionPoolManager`
- Update all services to use connection pools
- Unit tests for connection pooling

**Day 3-4:** ML Model Pre-loading
- Implement startup hooks
- Update health endpoints
- Integration tests for model loading

**Day 5:** Parallel Orchestration
- Refactor orchestrator to use `asyncio.gather()`
- Integration tests for parallel flows

**Week 1 Deliverables:**
- ✅ Connection pooling operational
- ✅ ML models pre-loaded on startup
- ✅ Parallel agent calls reducing latency by 50%+

### Week 2: Cache & Translation Activation

**Day 1-2:** Request Caching
- Implement `RequestCache` class
- Add caching to agents
- Cache invalidation tests

**Day 3-4:** Translation API Integration
- Configure Google Translate API
- Replace mock mode
- Integration tests

**Day 5:** Performance Testing
- Load tests with Locust (50 concurrent users)
- Benchmark against targets
- Fix regressions

**Week 2 Deliverables:**
- ✅ Request caching operational
- ✅ Translation agent using real API
- ✅ Load test baseline established

### Week 3: Production Deployment

**Day 1-2:** Deployment Scripts
- Create `deploy-production.sh`
- Create systemd service files
- Test deployment on staging

**Day 3:** Monitoring Setup
- Prometheus metrics endpoint
- Grafana dashboard
- Performance monitoring script

**Day 4:** Documentation & Runbook
- `PRODUCTION_RUNBOOK.md`
- Troubleshooting guides
- Rollback procedures

**Day 5:** Final Testing & Deployment
- Full test suite execution
- Deploy to production
- 24-hour monitoring
- Team handover

**Week 3 Deliverables:**
- ✅ Production deployment automated
- ✅ Monitoring dashboard operational
- ✅ Complete runbook and documentation

---

## Risks & Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| ML model loading fails silently | High | Medium | Health endpoint blocks until ready; monitoring alerts if not ready after 2 minutes |
| Connection pool exhaustion | Medium | Low | Configurable pool sizes; pool overflow creates new connections; monitoring on pool utilization |
| Cache stampede on startup | Low | Medium | Graceful degradation on cache miss; staggered service startup |
| Translation API rate limits | Medium | Medium | Rate limiting and queueing; cache results; fallback to mock if quota exceeded |
| Parallel execution increases load | Medium | Low | Load testing before deployment; horizontal scaling with Docker Compose scale option |

### Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| University firewall blocks ports | High | Low | Document required ports; provide alternative port config; firewall whitelist guide |
| Insufficient resources (RAM/CPU) | High | Medium | Document minimum requirements (8GB RAM, 4 CPU cores); scaling recommendations |
| No dedicated operations team | Medium | High | Comprehensive runbook and automation; training session included |

---

## Files to Create/Modify

### New Files (15)
1. `services/shared/connection_pool.py`
2. `services/shared/cache.py`
3. `services/shared/__init__.py`
4. `scripts/deploy-production.sh`
5. `scripts/stop-production.sh`
6. `scripts/monitor-performance.sh`
7. `scripts/systemd/project-chimera.service`
8. `scripts/monitor/grafana-dashboard.json`
9. `tests/performance/test_optimization_targets.py`
10. `tests/integration/test_performance_optimizations.py`
11. `docs/PRODUCTION_RUNBOOK.md`
12. `docs/superpowers/specs/2026-04-19-performance-optimization-design.md` (this file)

### Modified Files (8)
1. `services/openclaw-orchestrator/orchestrator.py` - Parallel execution
2. `services/sentiment-agent/main.py` - Model pre-loading
3. `services/scenespeak-agent/main.py` - Model pre-loading
4. `services/translation-agent/config.py` - Real API config
5. `services/translation-agent/main.py` - Real API calls
6. `docker-compose.mvp.yml` - Add Redis if not present
7. `tests/load/locustfile.py` - Performance assertions
8. `.env.example` - Add translation API key

---

## Acceptance Criteria

### Performance Targets
- [ ] End-to-end orchestration: <5 seconds (p95)
- [ ] First request time: <1 second (all services)
- [ ] Cache hit response: <100ms
- [ ] Translation agent: Real API working (not mock)

### Deployment Targets
- [ ] Automated deployment script works
- [ ] All services auto-start on boot
- [ ] Health checks pass within 2 minutes of startup
- [ ] Performance dashboard operational

### Testing Targets
- [ ] All performance tests passing
- [ ] Load test: 50 concurrent users, p95 <5s
- [ ] Integration tests: 100% pass rate
- [ ] E2E tests: All journeys passing

---

**Next Step:** After design approval, create detailed implementation plan using writing-plans skill.

**Status:** Ready for user review

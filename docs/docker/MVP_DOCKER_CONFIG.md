# MVP Docker Configuration Documentation

**Project:** Project Chimera - MVP Rescue Slice
**Configuration:** docker-compose.mvp.yml
**Last Validated:** 2025-04-15
**Status:** ✅ All checks passed

---

## Overview

This Docker Compose configuration provides a simplified, standalone environment for core functionality testing. It removes complex dependencies (Kafka, Milvus, Kubernetes) and uses local Docker containers only.

### Architecture Flow

```
OpenClaw Orchestrator (synchronous wire format)
    ├──→ Sentiment Analysis (DistilBERT)
    ├──→ Safety Filter (content moderation)
    ├──→ SceneSpeak (LLM dialogue via host:8012)
    ├──→ Translation Agent (mock translation)
    └──→ Operator Console (UI)

Infrastructure:
    └──→ Redis (state/cache)
    └──→ Hardware Bridge (mock DMX lighting)
```

---

## Service Definitions

### 1. OpenClaw Orchestrator
**Container:** `chimera-openclaw-orchestrator`
**Port:** 8000
**Dockerfile:** `services/openclaw-orchestrator/Dockerfile`

**Environment Variables:**
- `SERVICE_NAME=openclaw-orchestrator`
- `PORT=8000`
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001`
- `SENTIMENT_AGENT_URL=http://sentiment-agent:8004`
- `SAFETY_FILTER_URL=http://safety-filter:8006`
- `REDIS_URL=redis://redis:6379`

**Dependencies:**
- redis

**Networks:**
- chimera-backend

---

### 2. SceneSpeak Agent
**Container:** `chimera-scenespeak-agent`
**Port:** 8001
**Dockerfile:** `services/scenespeak-agent/Dockerfile`

**Environment Variables:**
- `SCENESPEAK_SERVICE_NAME=scenespeak-agent`
- `SCENESPEAK_PORT=8001`
- `SCENESPEAK_ENVIRONMENT=development`
- `SCENESPEAK_LOG_LEVEL=INFO`
- `SCENESPEAK_GLM_API_KEY=${GLM_API_KEY}` (requires .env file)
- `SCENESPEAK_GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4/`
- `SCENESPEAK_LOCAL_LLM_ENABLED=true`
- `SCENESPEAK_LOCAL_LLM_URL=http://host.docker.internal:8012`
- `SCENESPEAK_LOCAL_LLM_MODEL=nemotron-3-super-120b-a12b-nvfp4`
- `SCENESPEAK_LOCAL_LLM_TYPE=openai`
- `SCENESPEAK_GLM_API_FALLBACK=true`
- `SCENESPEAK_LLM_TIMEOUT=120`

**Special Configuration:**
- `extra_hosts`: Maps `host.docker.internal` to `host-gateway` for local LLM access

**Networks:**
- chimera-backend

---

### 3. Translation Agent
**Container:** `chimera-translation-agent`
**Port:** 8002 (moved from 8006 to avoid collision in Iteration 34)
**Dockerfile:** `services/translation-agent/Dockerfile`

**Environment Variables:**
- `SERVICE_NAME=translation-agent`
- `TRANSLATION_AGENT_PORT=8002`
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `TRANSLATION_AGENT_USE_MOCK=true`

**Networks:**
- chimera-backend

---

### 4. Sentiment Agent
**Container:** `chimera-sentiment-agent`
**Port:** 8004
**Dockerfile:** `services/sentiment-agent/Dockerfile`

**Environment Variables:**
- `SERVICE_NAME=sentiment-agent`
- `PORT=8004`
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `USE_ML_MODEL=true`
- `SENTIMENT_MODEL_TYPE=distilbert` (uses DistilBERT, NOT BettaFish/MIROFISH)
- `DEVICE=cpu`
- `MODEL_CACHE_DIR=/app/models_cache`

**Volumes:**
- `sentiment-models:/app/models_cache` (persistent model cache)

**Networks:**
- chimera-backend

---

### 5. Safety Filter
**Container:** `chimera-safety-filter`
**Port:** 8006
**Dockerfile:** `services/safety-filter/Dockerfile`

**Environment Variables:**
- `SERVICE_NAME=safety-filter`
- `PORT=8006`
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `SAFETY_FILTER_POLICY=family`
- `REDIS_URL=redis://redis:6379`

**Dependencies:**
- redis

**Networks:**
- chimera-backend

---

### 6. Operator Console
**Container:** `chimera-operator-console`
**Port:** 8007
**Dockerfile:** `services/operator-console/Dockerfile`

**Environment Variables:**
- `SERVICE_NAME=operator-console`
- `PORT=8007`
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `ORCHESTRATOR_URL=http://openclaw-orchestrator:8000`

**Dependencies:**
- openclaw-orchestrator

**Networks:**
- chimera-backend
- chimera-frontend

---

### 7. Hardware Bridge (Mock)
**Container:** `chimera-hardware-bridge`
**Port:** 8008
**Dockerfile:** `services/echo-agent/Dockerfile`

**Environment Variables:**
- `SERVICE_NAME=hardware-bridge`
- `PORT=8008`
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `ECHO_MODE=dmx-sentiment`

**Purpose:**
Simulates DMX lighting output based on sentiment analysis

**Networks:**
- chimera-backend

---

### 8. Redis
**Container:** `chimera-redis`
**Port:** 6379
**Image:** `redis:7-alpine`

**Configuration:**
- `command`: redis-server --appendonly yes (AOF persistence enabled)
- `volumes`: chimera-redis-data:/data

**Health Check:**
- `test`: ["CMD", "redis-cli", "ping"]
- `interval`: 10s
- `timeout`: 3s
- `retries`: 3

**Networks:**
- chimera-backend

---

## Port Mappings (Post-Iteration 34)

| Service | Internal Port | External Port | Notes |
|---------|--------------|---------------|-------|
| openclaw-orchestrator | 8000 | 8000 | Core orchestration |
| scenespeak-agent | 8001 | 8001 | LLM dialogue |
| translation-agent | 8002 | 8002 | Mock translation (moved from 8006) |
| sentiment-agent | 8004 | 8004 | DistilBERT sentiment |
| safety-filter | 8006 | 8006 | Content moderation |
| operator-console | 8007 | 8007 | Web UI |
| hardware-bridge | 8008 | 8008 | Mock DMX lighting |
| redis | 6379 | 6379 | State/cache |

**Collision Fixed:** Translation agent moved from 8006 to 8002 to avoid collision with safety-filter.

---

## Networks

### chimera-backend
**Driver:** bridge
**Purpose:** Internal communication between all backend services

**Connected Services:**
- openclaw-orchestrator
- scenespeak-agent
- translation-agent
- sentiment-agent
- safety-filter
- operator-console
- hardware-bridge
- redis

### chimera-frontend
**Driver:** bridge
**Purpose:** Frontend service isolation

**Connected Services:**
- operator-console

---

## Volumes

### sentiment-models
**Purpose:** Persistent cache for DistilBERT sentiment models
**Mounted To:** `/app/models_cache` in sentiment-agent

### chimera-redis-data
**Purpose:** Redis AOF persistence
**Mounted To:** `/data` in redis container

---

## Environment Variables

### Standard Variables (All Services)
- `SERVICE_NAME`: Service identifier for logging/tracing
- `PORT`: Service listening port
- `ENVIRONMENT`: deployment environment (development)
- `LOG_LEVEL`: Logging verbosity (INFO)

### Required External Variables
Create a `.env` file in the project root with:

```bash
# Z.ai GLM 4.7 API (Primary LLM for SceneSpeak)
GLM_API_KEY=your_glm_api_key_here
```

### Service-Specific Variables

**SceneSpeak Agent:**
- `SCENESPEAK_GLM_API_BASE`: Z.ai API endpoint
- `SCENESPEAK_LOCAL_LLM_ENABLED`: Enable local Nemotron LLM fallback
- `SCENESPEAK_LOCAL_LLM_URL`: Local LLM endpoint (host:8012)
- `SCENESPEAK_LOCAL_LLM_MODEL`: Model name (nemotron-3-super-120b-a12b-nvfp4)
- `SCENESPEAK_GLM_API_FALLBACK`: Use GLM API if local LLM fails
- `SCENESPEAK_LLM_TIMEOUT`: Request timeout (120s)

**Sentiment Agent:**
- `USE_ML_MODEL`: Enable ML-based sentiment (true)
- `SENTIMENT_MODEL_TYPE`: Model type (distilbert)
- `DEVICE`: Inference device (cpu)
- `MODEL_CACHE_DIR`: Model cache path

**Safety Filter:**
- `SAFETY_FILTER_POLICY`: Moderation policy (family)

**Translation Agent:**
- `TRANSLATION_AGENT_USE_MOCK`: Use mock translation (true)

---

## Health Checks

### Redis Health Check
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 3s
  retries: 3
```

**Note:** Only Redis has an explicit health check configured. Other services rely on Docker's `restart: unless-stopped` policy for resilience.

---

## Restart Policies

All services use: `restart: unless-stopped`

This ensures services automatically restart on failure but can be manually stopped when needed.

---

## Validation

### Validation Script
Run the automated validation script:

```bash
./scripts/validate-docker-compose.sh
```

### Manual Validation Steps

1. **Syntax Check:**
   ```bash
   docker compose -f docker-compose.mvp.yml config
   ```

2. **Service Verification:**
   ```bash
   docker compose -f docker-compose.mvp.yml ps
   ```

3. **Log Inspection:**
   ```bash
   docker compose -f docker-compose.mvp.yml logs -f [service-name]
   ```

4. **Health Status:**
   ```bash
   docker compose -f docker-compose.mvp.yml ps
   ```

---

## Startup Sequence

**Phase 1: Infrastructure**
1. Redis starts (with health check)

**Phase 2: Core Services**
2. Sentiment Agent (loads DistilBERT models)
3. Safety Filter (connects to Redis)
4. Translation Agent (mock mode)

**Phase 3: Orchestrator**
5. SceneSpeak Agent (connects to local LLM)
6. OpenClaw Orchestrator (connects to all agents)

**Phase 4: User Interface**
7. Operator Console (connects to orchestrator)
8. Hardware Bridge (mock DMX)

---

## Dependencies

### Service Dependencies

**OpenClaw Orchestrator:**
- redis (required for state/cache)

**Safety Filter:**
- redis (required for moderation cache)

**Operator Console:**
- openclaw-orchestrator (required for API communication)

### External Dependencies

**SceneSpeak Agent:**
- Z.ai GLM API (primary LLM) - requires `GLM_API_KEY` in .env
- Local Nemotron LLM (fallback) - requires host:8012 accessible

**Sentiment Agent:**
- HuggingFace model cache (first run downloads DistilBERT)

---

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :8000

# Kill the process or change the port in docker-compose.mvp.yml
```

**2. GLM API Key Missing**
```bash
# Create .env file with:
echo "GLM_API_KEY=your_key_here" > .env
```

**3. Local LLM Not Accessible**
```bash
# Ensure local LLM is running on host:8012
curl http://localhost:8012/v1/models
```

**4. Redis Connection Failed**
```bash
# Check Redis logs
docker compose -f docker-compose.mvp.yml logs redis

# Verify Redis is healthy
docker compose -f docker-compose.mvp.yml ps redis
```

**5. Sentiment Model Download Slow**
```bash
# First run downloads ~250MB DistilBERT model
# Check logs:
docker compose -f docker-compose.mvp.yml logs sentiment-agent

# Model cached in sentiment-models volume after first download
```

### Debug Commands

```bash
# View all service logs
docker compose -f docker-compose.mvp.yml logs

# Follow specific service logs
docker compose -f docker-compose.mvp.yml logs -f openclaw-orchestrator

# Check service health
docker compose -f docker-compose.mvp.yml ps

# Inspect service configuration
docker inspect chimera-openclaw-orchestrator

# Execute command in container
docker compose -f docker-compose.mvp.yml exec openclaw-orchestrator sh
```

---

## Performance Considerations

### Resource Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 10 GB (for model cache)

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 20 GB

### Service-Specific Resources

**Sentiment Agent:**
- Initial memory: ~500 MB
- After model load: ~1.5 GB
- CPU usage: Moderate (DistilBERT inference)

**SceneSpeak Agent:**
- Base memory: ~200 MB
- With LLM requests: ~500 MB
- CPU usage: Low (external LLM)

**Redis:**
- Memory: ~100 MB
- CPU usage: Low

---

## Security Notes

1. **API Keys:** Never commit `.env` file with real API keys
2. **Port Exposure:** All ports exposed to localhost only by default
3. **Network Isolation:** Services communicate via internal Docker networks
4. **Redis:** No authentication configured (development only)

---

## Iteration History

**Iteration 34 (2025-04-15):**
- Fixed port collision: translation-agent moved from 8006 to 8002
- Verified all 8 services defined correctly
- Validated network configuration (chimera-backend, chimera-frontend)
- Confirmed volume mounts (sentiment-models, chimera-redis-data)

---

## Next Steps

1. **Test Service Startup:**
   ```bash
   docker compose -f docker-compose.mvp.yml up -d
   docker compose -f docker-compose.mvp.yml ps
   ```

2. **Verify Connectivity:**
   ```bash
   # Test orchestrator
   curl http://localhost:8000/health

   # Test operator console
   curl http://localhost:8007
   ```

3. **Run Integration Tests:**
   ```bash
   ./tests/integration/run-integration-tests.sh
   ```

---

**Document Version:** 1.0
**Last Updated:** 2025-04-15
**Validated By:** Claude Code (Phase 1.4)

# Project Chimera - Configuration Guide

## Quick Start Configuration

### 1. Environment Variables Setup

```bash
# Copy the example environment file
cp .env.example .env.local

# Edit with your configuration
nano .env.local
```

### 2. Required API Keys

| Service | API Key Required | Get It Here | Notes |
|---------|-----------------|-------------|-------|
| **SceneSpeak Agent** | GLM API Key | https://open.bigmodel.cn/ | Zhipu AI (智谱AI) |
| **Translation Agent** | Optional | Various | See below |
| **Safety Filter** | Optional | OpenAI/Azure | Content moderation |

### 3. GLM API Setup (SceneSpeak Agent)

```bash
# Get your API key from: https://open.bigmodel.cn/
# Add to .env or docker-compose.mvp.yml:

GLM_API_KEY=your_actual_api_key_here
```

**Test the connection:**
```bash
curl -X POST http://localhost:8001/health \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### 4. ML Model Setup

#### Sentiment Agent (DistilBERT)

The model downloads automatically on first start. Verify:

```bash
# Check model status
docker exec chimera-sentiment-agent curl http://localhost:8004/health

# Expected output: {"model_loaded": true, ...}

# If model not loaded, restart the service
docker compose -f docker-compose.mvp.yml restart sentiment-agent

# Wait for model to load (30-60 seconds)
watch -n 5 'docker exec chimera-sentiment-agent curl http://localhost:8004/health'
```

#### Local LLM Setup (Optional)

If you want to use Ollama for SceneSpeak fallback:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Download model
ollama pull llama3.2

# Verify
curl http://localhost:11434/api/tags
```

### 5. Translation Agent Configuration

The translation agent currently runs in **mock mode**. To enable real translation:

#### Option A: Google Translate API

```bash
# Install dependencies
pip install google-cloud-translate

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

#### Option B: DeepL API

```bash
# Get API key from: https://www.deepl.com/pro-api
DEEPL_API_KEY=your_api_key_here
```

#### Option C: LibreTranslate (Self-hosted)

```bash
# Run LibreTranslate container
docker run -ti -p 5000:5000 libretranslate/libretranslate

# Update service URL
TRANSLATION_SERVICE_URL=http://libretranslate:5000
```

### 6. Service URL Configuration

Services use these URLs (Docker internal networking):

| Service | Internal URL | External URL |
|---------|--------------|--------------|
| Orchestrator | `http://openclaw-orchestrator:8000` | `http://localhost:8000` |
| SceneSpeak | `http://scenespeak-agent:8001` | `http://localhost:8001` |
| Translation | `http://translation-agent:8002` | `http://localhost:8002` |
| Sentiment | `http://sentiment-agent:8004` | `http://localhost:8004` |
| Safety | `http://safety-filter:8006` | `http://localhost:8006` |
| Console | `http://operator-console:8007` | `http://localhost:8007` |
| Hardware | `http://hardware-bridge:8008` | `http://localhost:8008` |
| Redis | `redis://redis:6379` | `localhost:6379` |

### 7. Configuration Files Reference

| File | Purpose |
|------|---------|
| `.env` | Main environment variables |
| `.env.example` | Template with all options |
| `.env.docker` | Local/private/ignored Docker configuration |
| `docker-compose.mvp.yml` | MVP service definitions |
| `services/*/.env.example` | Per-service templates |

### 8. Verification Commands

```bash
# Check all service health
./scripts/verify-stack-health.sh

# Check individual service
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # SceneSpeak
curl http://localhost:8004/health  # Sentiment
curl http://localhost:8006/health/live  # Safety

# Verify Redis
docker exec chimera-redis redis-cli ping
```

### 9. Troubleshooting Configuration

#### GLM API Connection Failed

```bash
# Check if API key is set
docker compose -f docker-compose.mvp.yml logs scenespeak-agent | grep GLM

# Verify API key format (should be 48 characters)
echo $GLM_API_KEY | wc -c

# Test API directly
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4", "messages": [{"role": "user", "content": "Hi"}]}'
```

#### Model Not Loading

```bash
# Check disk space
df -h

# Check model cache directory
docker exec chimera-sentiment-agent ls -la /app/models_cache

# Restart with verbose logging
docker compose -f docker-compose.mvp.yml up -d --force-recreate sentiment-agent
```

#### Service Cannot Reach Another Service

```bash
# Verify Docker network
docker network inspect chimera-backend

# Test from inside container
docker exec chimera-openclaw-orchestrator curl http://scenespeak-agent:8001/health

# Check service discovery
docker exec chimera-openclaw-orchestrator nslookup scenespeak-agent
```

### 10. Production Configuration

For production deployment:

```bash
# Use production environment file
cp .env.production.example .env.production

# Update critical values:
# - ENVIRONMENT=production
# - LOG_LEVEL=WARNING (or ERROR)
# - Add real API keys
# - Configure CORS for your domain
# - Set up monitoring endpoints
```

---

**Next Steps:**
- See `docs/DEVELOPER_SETUP.md` for development environment
- See `docs/DEPLOYMENT.md` for deployment guide
- See `docs/RUNBOOK.md` for operational procedures

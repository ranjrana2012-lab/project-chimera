# BettaFish & MiroFish Integration - Quick Start Guide

This guide helps you deploy and integrate BettaFish (public opinion analysis) and MiroFish-Offline (swarm intelligence simulation) with Project Chimera.

## ⚠️ LICENSE WARNINGS

### BettaFish - GPL-2.0
**COMMERCIAL USE PROHIBITED** - This integration is for R&D/academic use only.

### MiroFish - AGPL-3.0
**NETWORK USE IS DISTRIBUTION** - Source code must be available to all network users.

## Prerequisites

### Hardware Requirements
- **RAM**: 32GB+ recommended (16GB minimum)
- **GPU**: NVIDIA GPU with 12-16GB+ VRAM (optional but recommended)
- **Storage**: 100GB+ NVMe SSD

### Software Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (for GPU support)
- Git

### API Keys Required
1. **Search API**: Tavily (https://www.tavily.com/) - $5/month
2. **LLM API**: OpenAI-compatible (OpenAI, DeepSeek, Kimi, etc.)

## Quick Start

### Step 1: Clone and Configure BettaFish

```bash
cd /home/ranj/Project_Chimera/integrations/bettafish

# Create environment file
cp .env.template .env

# Edit and replace CHANGE_ME_* placeholders
nano .env
```

**Required configuration in `.env`:**
```bash
# Database
DB_PASSWORD=your_secure_password

# Search API
TAVILY_API_KEY=tvly-your-key-here

# LLM API (minimum 3 engines)
INSIGHT_ENGINE_API_KEY=sk-your-key
INSIGHT_ENGINE_BASE_URL=https://api.openai.com/v1
INSIGHT_ENGINE_MODEL_NAME=gpt-4o-mini

MEDIA_ENGINE_API_KEY=sk-your-key
MEDIA_ENGINE_BASE_URL=https://api.openai.com/v1
MEDIA_ENGINE_MODEL_NAME=gpt-4o-mini

QUERY_ENGINE_API_KEY=sk-your-key
QUERY_ENGINE_BASE_URL=https://api.openai.com/v1
QUERY_ENGINE_MODEL_NAME=gpt-4o-mini

REPORT_ENGINE_API_KEY=sk-your-key
REPORT_ENGINE_BASE_URL=https://api.openai.com/v1
REPORT_ENGINE_MODEL_NAME=gpt-4o
```

### Step 2: Start BettaFish

```bash
cd /home/ranj/Project_Chimera/integrations/bettafish

# Build and start
docker-compose -f docker-compose.security.yml up -d --build

# Check logs
docker-compose -f docker-compose.security.yml logs -f bettafish

# Access UI (from this machine only)
# Open http://127.0.0.1:5000 in browser
```

### Step 3: Clone and Configure MiroFish

```bash
cd /home/ranj/Project_Chimera/integrations/mirofish

# Create environment file
cp .env.template .env

# Edit and set Neo4j password
nano .env
```

**Required configuration in `.env`:**
```bash
NEO4J_PASSWORD=your_secure_graph_password
```

### Step 4: Start MiroFish

```bash
cd /home/ranj/Project_Chimera/integrations/mirofish

# Build and start
docker-compose -f docker-compose.security.yml up -d --build

# Wait for services to start (60-90 seconds)
docker-compose -f docker-compose.security.yml logs -f

# Pull required models
docker exec mirofish-ollama ollama pull qwen2.5:14b
docker exec mirofish-ollama ollama pull nomic-embed-text

# Access UI
# Open http://127.0.0.1:3000 in browser
```

### Step 5: Start Opinion Pipeline (Chimera Integration)

```bash
cd /home/ranj/Project_Chimera

# Start the opinion pipeline service
docker-compose up -d opinion-pipeline-agent

# Check status
curl http://localhost:8020/health/live
```

## Data Flow

```
User Query
    ↓
BettaFish (Web Scraping → Multi-Agent Analysis)
    ↓
Markdown Report
    ↓
MiroFish (GraphRAG → Swarm Simulation)
    ↓
Prediction Data
    ↓
Opinion Pipeline Service
    ↓
Project Chimera Services
```

## API Endpoints

### Opinion Pipeline Service

```bash
# Get service status
curl http://localhost:8020/api/v1/status

# Trigger BettaFish analysis
curl -X POST http://localhost:8020/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze public opinion on AI safety",
    "platforms": ["twitter", "reddit"],
    "time_range": "7d",
    "max_results": 100
  }'

# Get analysis status
curl http://localhost:8020/api/v1/analysis/{analysis_id}

# Trigger MiroFish simulation
curl -X POST http://localhost:8020/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "report_path": "./integrations/bettafish/reports/analysis_xxx.md",
    "agent_count": 10,
    "simulation_rounds": 3,
    "prediction_goal": "What will be the public reaction?"
  }'

# Get latest sentiment (enriched)
curl http://localhost:8020/api/v1/latest/sentiment
```

## Smoke Test

### Test BettaFish

1. Open http://127.0.0.1:5000
2. Enter query: "Analyze recent discussions about AI safety"
3. Wait for report generation (10-15 minutes)
4. Check `./integrations/bettafish/final_reports/` for output

### Test MiroFish

1. Open http://127.0.0.1:3000
2. Upload a BettaFish markdown report
3. Configure: 5 agents, 2 rounds
4. Run simulation
5. Check results in Neo4j Browser (http://127.0.0.1:7474)

### Test Integration

```bash
# 1. Trigger analysis
ANALYSIS=$(curl -s -X POST http://localhost:8020/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "platforms": ["news"], "time_range": "7d"}' \
  | jq -r '.analysis_id')

# 2. Check status
curl http://localhost:8020/api/v1/analysis/$ANALYSIS

# 3. Trigger simulation (after analysis complete)
SIMULATION=$(curl -s -X POST http://localhost:8020/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"report_path": "./integrations/bettafish/final_reports/test.md", "agent_count": 5, "simulation_rounds": 2, "prediction_goal": "Test prediction"}' \
  | jq -r '.simulation_id')

# 4. Check simulation
curl http://localhost:8020/api/v1/simulation/$SIMULATION
```

## Stopping Services

```bash
# Stop BettaFish
cd ~/Project_Chimera/integrations/bettafish
docker-compose -f docker-compose.security.yml down

# Stop MiroFish
cd ~/Project_Chimera/integrations/mirofish
docker-compose -f docker-compose.security.yml down

# Stop Opinion Pipeline
cd ~/Project_Chimera
docker-compose down opinion-pipeline-agent
```

## Troubleshooting

### BettaFish Issues

**Problem**: Container fails to start
```bash
# Check logs
docker-compose -f docker-compose.security.yml logs bettafish

# Common issue: Missing API keys
# Solution: Verify .env file has all required API keys
```

**Problem**: Web scraping blocked
```bash
# Solution: Use proxy or rate limiting
# Add to .env:
RATE_LIMIT_REQUESTS_PER_MINUTE=10
```

### MiroFish Issues

**Problem**: Out of memory
```bash
# Solution: Use smaller model
# Edit .env:
LLM_MODEL_NAME=qwen2.5:7b

# Or increase memory limit in docker-compose.security.yml
```

**Problem**: GPU not detected
```bash
# Check GPU
nvidia-smi

# Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# If GPU unavailable, Ollama will use CPU (slower)
```

### Integration Issues

**Problem**: Cannot reach BettaFish/MiroFish from Opinion Pipeline
```bash
# Check services are running
docker ps | grep -E "bettafish|mirofish|opinion"

# Check network connectivity
docker exec chimera-opinion-pipeline curl http://bettafish:5000
```

## Resources

- **BettaFish**: https://github.com/666ghj/BettaFish
- **MiroFish-Offline**: https://github.com/nikmcfly/MiroFish-Offline
- **Project Chimera**: https://github.com/ranjrana2012-lab/project-chimera
- **Tavily API**: https://www.tavily.com/
- **Ollama Models**: https://ollama.com/library

## Support

For issues with:
- **BettaFish**: Check `integrations/bettafish/SECURITY_LICENSE_NOTICE.md`
- **MiroFish**: Check `integrations/mirofish/SECURITY_LICENSE_NOTICE.md`
- **Integration**: Check `docs/BETTAfish_MIROFISH_INTEGRATION_PLAN.md`

---

**Remember**: This is R&D/academic software only. Commercial use is prohibited.

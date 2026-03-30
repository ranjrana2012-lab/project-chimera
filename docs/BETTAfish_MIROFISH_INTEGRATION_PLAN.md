# Implementation Plan: BettaFish, MiroFish-Offline & OpenClaw Integration with Project Chimera

## Overview

This plan integrates three external AI systems with Project Chimera to create a comprehensive public opinion analysis and predictive sentiment pipeline:

1. **BettaFish** - Multi-agent public opinion analysis system that crawls social platforms
2. **MiroFish-Offline** - Swarm intelligence prediction engine using GraphRAG and thousands of LLM agents
3. **OpenClaw** - Multi-platform chat bot framework (already integrated via openclaw-orchestrator)

**Data Pipeline:** BettaFish (public opinion data) → MiroFish (predictive simulations) → sentiment-agent (enriched analysis) → OpenClaw (real-time reporting)

---

## Executive Summary

**Objective:** Integrate experimental multi-agent AI systems for public opinion analysis and swarm-based sentiment prediction into Project Chimera's entertainment platform.

**Complexity:** HIGH
**Estimated Effort:** 40-60 hours
**Risk Level:** HIGH (licensing, resource consumption, experimental software)

**Critical Constraint:** Both BettaFish (GPL-2.0, commercial use prohibited) and MiroFish (AGPL-3.0) have restrictive licenses that **prohibit commercial deployment**. This integration is **R&D ONLY**.

---

## Current Architecture

### Project Chimera (Existing)

```
┌─────────────────────────────────────────────────────────────┐
│                    Project Chimera                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │sentiment-agent│  │captioning-agent│  │bsl-agent    │    │
│  └───────┬───────┘  └──────────────┘  └──────────────┘    │
│          │                                                │
│  ┌───────▼──────────┐  ┌──────────────┐                   │
│  │openclaw-orchestrator│  │nemoclaw-orchestrator│           │
│  └───────────────────┘  └──────────────┘                   │
│                                                              │
│  Infrastructure: Redis, Kafka, Milvus, Neo4j                     │
└─────────────────────────────────────────────────────────────┘
```

### Target Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Extended Chimera                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Opinion Pipeline Layer (NEW)                          │   │
│  │                                                          │   │
│  │  ┌────────────┐    ┌────────────┐    ┌───────────┐  │   │
│  │  │ BettaFish  │───→│ MiroFish    │───→│Opinion API │  │   │
│  │  │ (isolated) │    │ (isolated)  │    │(NEW)      │  │   │
│  │  └──────┬─────┘    └──────┬───────┘    └───────┬───┘   │
│  │         │                │                   │        │   │
│  │         ▼                ▼                   ▼        │   │
│  │    (Markdown report)  (Neo4j Graph)      (Prediction)│   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │        │
│  ┌───────────────────────▼──────────────────────────┐   │
│  │             sentiment-agent (ENHANCED)              │   │
│  │                                                      │   │
│  │  • Enriched sentiment predictions               │   │
│  │  • Public opinion context                     │   │
│  │  • Swarm simulation insights                    │   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                              │
│  ┌───────────────────────┐  ┌──────────────────────────┐ │
│  │   OpenClaw Bots (NEW)  │  │    Existing Chimera       │ │ │
│  │                          │  │    Services               │ │ │
│  │  • Public opinion feeds  │  │                          │ │ │
│  │  • Prediction alerts   │  │                          │ │ │
│  └────────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Infrastructure Preparation (6-8 hours)

#### 1.1 Create Integration Directory Structure

**Objective:** Establish isolated sandbox directories for BettaFish and MiroFish.

**Actions:**
```bash
cd /home/ranj/Project_Chimera
mkdir -p integrations/bettafish/{data,logs,reports}
mkdir -p integrations/mirofish/{data,graphs,logs}
mkdir -p services/opinion-pipeline-agent
```

#### 1.2 Create Isolated Docker Networks

**Objective:** Prevent resource conflicts and ensure security isolation.

**File:** `docker-compose.override.yml`

```yaml
# New isolated networks
networks:
  bettafish-isolated:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.28.0.0/16

  mirofish-isolated:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.29.0.0/16
```

**Acceptance Criteria:**
- [ ] Networks created and verified with `docker network ls`
- [ ] No routing between isolated networks and chimera-backend

#### 1.3 Hardware Resource Audit

**Objective:** Verify system capacity for heavy workloads.

**Checklist:**
```bash
# RAM check (need 32GB+ for MiroFish)
free -h

# GPU check (need 12-16GB VRAM for qwen2.5:14b)
nvidia-smi

# Storage check (need 100GB+ NVMe)
df -h /home/ranj
```

---

### Phase 2: BettaFish Deployment (8-10 hours)

#### 2.1 Clone and Configure BettaFish

**Repository:** https://github.com/666ghj/BettaFish

**Actions:**
```bash
cd integrations/bettafish
git clone https://github.com/666ghj/BettaFish.git .
cp .env.example .env
chmod 600 .env
```

**Security Hardening - Dockerfile:**

```dockerfile
# Add before EXPOSE directive
RUN groupadd --gid 1000 betta_group && \
    useradd --uid 1000 --gid betta_group --create-home betta_user
RUN chown -R betta_user:betta_group /app /ms-playwright
USER betta_user
```

**Port Binding Security - docker-compose.yml:**

```yaml
ports:
  - "127.0.0.1:5000:5000"  # Loopback only
  - "127.0.0.1:8501:8501"
  - "127.0.0.1:8502:8502"
  - "127.0.0.1:8503:8503"
```

#### 2.2 Environment Configuration

**File:** `integrations/bettafish/.env`

```bash
# Core Configuration
HOST=127.0.0.1
PORT=5000

# PostgreSQL Database
DB_DIALECT=postgresql
DB_HOST=db
DB_PORT=5432
DB_USER=bettafish
DB_PASSWORD=CHANGE_ME_BETTA_PASSWORD
DB_NAME=bettafish
DB_CHARSET=utf8mb4

# Search API (Tavily for Western/Global)
SEARCH_TOOL_TYPE=TavilyAPI
TAVILY_API_KEY=CHANGE_ME_TAVILY_API_KEY

# Agent LLM Configuration
INSIGHT_ENGINE_API_KEY=CHANGE_ME_OPENAI_API_KEY
INSIGHT_ENGINE_BASE_URL=https://api.openai.com/v1
INSIGHT_ENGINE_MODEL_NAME=gpt-4o-mini

MEDIA_ENGINE_API_KEY=${INSIGHT_ENGINE_API_KEY}
MEDIA_ENGINE_BASE_URL=${INSIGHT_ENGINE_BASE_URL}
MEDIA_ENGINE_MODEL_NAME=gpt-4o-mini

QUERY_ENGINE_API_KEY=${INSIGHT_ENGINE_API_KEY}
QUERY_ENGINE_BASE_URL=${INSIGHT_ENGINE_BASE_URL}
QUERY_ENGINE_MODEL_NAME=gpt-4o-mini

REPORT_ENGINE_API_KEY=${INSIGHT_ENGINE_API_KEY}
REPORT_ENGINE_BASE_URL=${INSIGHT_ENGINE_BASE_URL}
REPORT_ENGINE_MODEL_NAME=gpt-4o-mini

FORUM_ENGINE_API_KEY=${INSIGHT_ENGINE_API_KEY}
FORUM_ENGINE_BASE_URL=${INSIGHT_ENGINE_BASE_URL}
FORUM_ENGINE_MODEL_NAME=gpt-4o-mini
```

**Acceptance Criteria:**
- [ ] All API keys use CHANGE_ME_ placeholders
- [ ] All ports bind to 127.0.0.1
- [ ] Non-root user configured in Dockerfile

#### 2.3 Deploy BettaFish Stack

**Actions:**
```bash
cd integrations/bettafish
docker compose up -d --build
docker compose logs -f bettafish
```

**Verification:**
```bash
# Check health
curl http://127.0.0.1:5000/health

# Verify UI access
xdg-open http://127.0.0.1:5000  # Should show BettaFish UI
```

---

### Phase 3: MiroFish-Offline Deployment (10-12 hours)

#### 3.1 Clone and Configure MiroFish-Offline

**Repository:** https://github.com/nikmcfly/MiroFish-Offline

**Actions:**
```bash
cd integrations/mirofish
git clone https://github.com/nikmcfly/MiroFish-Offline.git .
cp .env.example .env
chmod 600 .env
```

**Security Hardening - Add to each Dockerfile:**

```dockerfile
# Add non-root user
RUN groupadd --gid 1000 miro_group && \
    useradd --uid 1000 --gid miro_group --create-home miro_user
RUN chown -R miro_user:miro_group /app
USER miro_user
```

**Port Binding Security:**

```yaml
ports:
  - "127.0.0.1:3000:3000"   # MiroFish UI
  - "127.0.0.1:5001:5001"   # Backend API
  - "127.0.0.1:7474:7474"   # Neo4j Browser
  - "127.0.0.1:11434:11434" # Ollama API
```

#### 3.2 GPU Configuration for Ollama

**File:** `docker-compose.yml` (add to ollama service)

```yaml
services:
  ollama:
    image:ollama/ollama:latest
    container_name:mirofish-ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ollama_data:/root/.ollama
```

#### 3.3 Environment Configuration

**File:** `integrations/mirofish/.env`

```bash
# LLM Configuration (Local Ollama)
LLM_API_KEY=ollama
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL_NAME=qwen2.5:14b

# Embedding Configuration
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://ollama:11434

# Neo4j Graph Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=CHANGE_ME_NEO4J_PASSWORD

# OASIS Framework
OPENAI_API_BASE_URL=http://ollama:11434/v1
OPENAI_API_KEY=ollama
```

**Acceptance Criteria:**
- [ ] All passwords use CHANGE_ME_ placeholders
- [ ] All ports bind to 127.0.0.1
- [ ] GPU reservations configured

#### 3.4 Deploy MiroFish Stack

**Actions:**
```bash
cd integrations/mirofish
docker compose up -d --build

# Wait for services to stabilize
sleep 60

# Pull required models
docker exec mirofish-ollama ollama pull qwen2.5:14b
docker exec mirofish-ollama ollama pull nomic-embed-text
```

**Verification:**
```bash
# Check Neo4j connection
curl http://127.0.0.1:7474

# Verify MiroFish UI
xdg-open http://127.0.0.1:3000
```

---

### Phase 4: Opinion Pipeline Service (8-10 hours)

#### 4.1 Create Opinion Pipeline Orchestrator

**File:** `services/opinion-pipeline-agent/Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install shared requirements first
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir services/shared/requirements.txt

# Install service dependencies
COPY services/opinion-pipeline-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/opinion-pipeline-agent/ . .

# Copy shared module
COPY services/shared/ /app/shared/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8020/health/live')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]
```

#### 4.2 Create Opinion Pipeline Service

**File:** `services/opinion-pipeline-agent/main.py`

```python
"""
Opinion Pipeline Orchestrator

Bridges BettaFish outputs and MiroFish inputs, providing
enriched sentiment data to Chimera services.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Add shared module to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.middleware import SecurityHeadersMiddleware, configure_cors, setup_rate_limit_error_handler

app = FastAPI(
    title="Opinion Pipeline Service",
    description="Orchestrates BettaFish and MiroFish for sentiment enrichment",
    version="1.0.0"
)

# Security middleware
configure_cors(app)
app.add_middleware(SecurityHeadersMiddleware)
setup_rate_limit_error_handler(app)

# Configuration
BETTAFISH_REPORT_PATH = Path(os.environ.get("BETTAFISH_REPORT_PATH", "./integrations/bettafish/reports"))
MIROFISH_API_URL = os.environ.get("MIROFISH_API_URL", "http://127.0.0.1:5001")
CHIMERA_SENTIMENT_API = os.environ.get("CHIMERA_SENTIMENT_API", "http://sentiment-agent:8004")

# Global state
latest_analysis: Optional[Dict[str, Any]] = None
simulation_active: bool = False


class OpinionAnalysisRequest(BaseModel):
    """Request public opinion analysis."""
    query: str
    platforms: list[str] = ["twitter", "reddit", "news"]
    time_range: str = "7d"  # e.g., "7d", "30d"
    max_results: int = 100


class SimulationRequest(BaseModel):
    """Request swarm simulation based on BettaFish report."""
    report_path: str
    agent_count: int = 10
    simulation_rounds: int = 3
    prediction_goal: str


@app.get("/health/live")
async def liveness():
    """Liveness probe."""
    return {"status": "alive"}


@app.post("/api/v1/analyze")
async def trigger_analysis(request: OpinionAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Trigger BettaFish analysis and return asynchronously.

    Process:
    1. Submit query to BettaFish
    2. Monitor progress
    3. Store generated report
    4. Return analysis ID for later retrieval
    """
    analysis_id = f"analysis_{asyncio.get_event_loop().time()}"

    # Queue background task
    background_tasks.add_task(
        run_bettafish_analysis,
        analysis_id,
        request.query,
        request.platforms,
        request.time_range
    )

    return {
        "analysis_id": analysis_id,
        "status": "pending",
        "estimated_time_minutes": 15
    }


async def run_bettafish_analysis(
    analysis_id: str,
    query: str,
    platforms: list[str],
    time_range: str
):
    """Run BettaFish analysis in background."""
    # TODO: Implement actual BettaFish API call
    # This would involve calling BettaFish's REST API
    pass


@app.post("/api/v1/simulate")
async def trigger_simulation(request: SimulationRequest):
    """
    Upload BettaFish report to MiroFish for swarm simulation.

    Process:
    1. Read BettaFish markdown report
    2. Submit to MiroFish as seed document
    3. Configure simulation parameters
    4. Trigger swarm simulation
    5. Return simulation ID
    """
    # Validate report exists
    report_path = Path(request.report_path)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    # Read report content
    report_content = report_path.read_text()

    # Submit to MiroFish
    # TODO: Implement MiroFish API call
    simulation_id = f"sim_{asyncio.get_event_loop().time()}"

    return {
        "simulation_id": simulation_id,
        "status": "processing",
        "estimated_time_minutes": 30
    }


@app.get("/api/v1/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get BettaFish analysis status and results."""
    # TODO: Implement status check
    return {
        "analysis_id": analysis_id,
        "status": "pending",
        "progress": 0
    }


@app.get("/api/v1/simulation/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get MiroFish simulation status and results."""
    # TODO: Implement status check
    return {
        "simulation_id": simulation_id,
        "status": "pending",
        "progress": 0
    }


@app.get("/api/v1/latest/sentiment")
async def get_latest_sentiment():
    """
    Get latest enriched sentiment data.

    Returns:
    - BettaFish public opinion analysis
    - MiroFish swarm predictions
    - Chimera sentiment-agent baseline
    """
    global latest_analysis

    if latest_analysis is None:
        raise HTTPException(status_code=404, detail="No analysis available")

    # Fetch current sentiment from Chimera
    # TODO: Call sentiment-agent API

    return latest_analysis


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)
```

#### 4.3 Create Requirements File

**File:** `services/opinion-pipeline-agent/requirements.txt`

```txt
# FastAPI and web framework
fastapi>=0.104.0
uvicorn[standard]>=0.23.0
pydantic>=2.5.0
python-multipart>=0.0.6

# HTTP client
httpx>=0.25.0
aiohttp>=3.8.0

# Shared dependencies
slowapi>=0.1.9
structlog>=2.4.0

# Monitoring
prometheus-client>=0.19.0
opentelemetry-api>=1.22.0
opentelemetry-sdk>=1.22.0
```

#### 4.4 Update Docker Compose

**File:** `docker-compose.yml` (add service)

```yaml
opinion-pipeline-agent:
  build:
    context: .
    dockerfile: services/opinion-pipeline-agent/Dockerfile
  container_name: chimera-opinion-pipeline
  ports:
    - "127.0.0.1:8020:8020"
  environment:
    - BETTAFISH_REPORT_PATH=./integrations/bettafish/reports
    - MIROFISH_API_URL=http://127.0.0.1:5001
    - CHIMERA_SENTIMENT_API=http://sentiment-agent:8004
    - LOG_LEVEL=INFO
    - ENVIRONMENT=production
  volumes:
    - ./integrations/bettafish/reports:/app/reports:ro
  networks:
    - chimera-backend
    - bettafish-isolated
    - mirofish-isolated
  restart: unless-stopped
  depends_on:
    sentiment-agent:
      condition: service_healthy
```

---

### Phase 5: Sentiment Agent Integration (6-8 hours)

#### 5.1 Add Public Opinion Enrichment Endpoint

**File:** `services/sentiment-agent/main.py`

```python
from typing import Optional, Dict, Any
import httpx

# Add new endpoint
@app.get("/api/v1/sentiment/enriched")
async def get_enriched_sentiment(
    content_id: str,
    include_public_opinion: bool = False
):
    """
    Get enriched sentiment analysis including public opinion context.

    Args:
        content_id: Content identifier (video ID, show ID, etc.)
        include_public_opinion: Whether to include BettaFish/MiroFish data
    """
    base_sentiment = await analyze_sentiment(content_id)

    result = {
        "content_id": content_id,
        "base_sentiment": base_sentiment,
        "enriched_data": None
    }

    if include_public_opinion:
        # Fetch from opinion pipeline
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"http://opinion-pipeline-agent:8020/api/v1/latest/sentiment",
                    timeout=10.0
                )
                if response.status_code == 200:
                    result["enriched_data"] = response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch opinion data: {e}")

    return result
```

---

### Phase 6: OpenClaw Bot Integration (4-6 hours)

#### 6.1 Create Public Opinion Reporting Bot

**File:** `services/openclaw-orchestrator/bots/opinion_reporter.py`

```python
"""
OpenClaw Bot: Public Opinion Reporter

Reports public opinion analysis and predictions
via Telegram/Discord during live shows.
"""

from typing import Optional
import httpx
import asyncio

OPINION_API_URL = "http://opinion-pipeline-agent:8020"

class OpinionReporterBot:
    """Bot that reports public opinion insights."""

    async def get_daily_summary(self) -> Optional[str]:
        """Get daily opinion summary formatted for chat."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{OPINION_API_URL}/api/v1/latest/sentiment",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return format_opinion_summary(data)
            except Exception as e:
                print(f"Failed to fetch opinion data: {e}")
        return None

    async def get_prediction_alert(self) -> Optional[str]:
        """Get prediction alerts from MiroFish simulations."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{OPINION_API_URL}/api/v1/simulation/latest",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return format_prediction_alert(data)
            except Exception as e:
                print(f"Failed to fetch simulation data: {e}")
        return None

def format_opinion_summary(data: dict) -> str:
    """Format opinion data for chat display."""
    # TODO: Implement formatting logic
    return f"📊 Public Opinion Summary:\n{data}"

def format_prediction_alert(data: dict) -> str:
    """Format prediction alert for chat display."""
    # TODO: Implement alert logic
    return f"⚠️ Prediction Alert:\n{data}"
```

#### 6.2 Register Bot with OpenClaw Orchestrator

**File:** `services/openclaw-orchestrator/main.py` (add bot registration)

```python
from bots.opinion_reporter import OpinionReporterBot

# Register the bot
orchestrator.register_bot("opinion_reporter", OpinionReporterBot())
```

---

### Phase 7: Security Hardening (4-6 hours)

#### 7.1 Apply Security Hardening to New Stacks

**For both BettaFish and MiroFish:**

1. **Non-root containers** - Already specified in Phase 2 & 3
2. **Loopback-only binding** - Already specified in Phase 2 & 3
3. **Change ME placeholders** - All credentials use CHANGE_ME_

#### 7.2 Create .env Templates

**File:** `integrations/bettafish/.env.production.template`

```bash
# Production template - DO NOT USE IN DEVELOPMENT
HOST=127.0.0.1
PORT=5000
DB_PASSWORD=CHANGE_ME_BETTA_PASSWORD_PRODUCTION
TAVILY_API_KEY=CHANGE_ME_TAVILY_API_KEY
INSIGHT_ENGINE_API_KEY=CHANGE_ME_OPENAI_API_KEY_PRODUCTION
# ... rest of configuration
```

**File:** `integrations/mirofish/.env.production.template`

```bash
# Production template - DO NOT USE IN DEVELOPMENT
NEO4J_PASSWORD=CHANGE_ME_NEO4J_PASSWORD_PRODUCTION
LLM_MODEL_NAME=qwen2.5:14b
# ... rest of configuration
```

#### 7.3 Add Disclaimer to Documentation

**File:** `integrations/README.md`

```markdown
# ⚠️ IMPORTANT: Licensing Restrictions

## BettaFish - GPL-2.0 with Commercial Prohibition

**COMMERCIAL USE OR PROFIT-MAKING ACTIVITIES ARE STRICTLY PROHIBITED**

This integration is for:
- ✅ Academic research
- ✅ Educational purposes
- ✅ Internal non-profit R&D
- ❌ Commercial SaaS products
- ❌ Profit-generating services
- ❌ Client-facing intelligence services

## MiroFish - AGPL-3.0 Copyleft

**NETWORK USE IS DISTRIBUTION**

If you modify MiroFish and provide it over a network (even internally),
you MUST make the complete modified source code publicly available under AGPL-3.0.

## Deployment Requirements

1. **Run in isolated sandbox** - Both systems must be in separate Docker networks
2. **127.0.0.1 binding only** - No public network exposure
3. **Secure credentials** - All API keys use CHANGE_ME_ placeholders
4. **Resource monitoring** - Monitor RAM/CPU to prevent OOM
5. **Legal review required** - Before any deployment, consult legal counsel
```

---

### Phase 8: Testing & Validation (8-10 hours)

#### 8.1 BettaFish Smoke Test

**Objective:** Verify BettaFish can crawl and generate reports.

**Test Query:**
```
"Analyze public reaction to a hypothetical product announcement from the past month.
Keep scope limited to avoid aggressive scraping."
```

**Validation:**
- [ ] BettaFish UI accessible at http://127.0.0.1:5000
- [ ] Query agent initiates search
- [ ] Forum agents engage in debate
- [ ] Report generated in `integrations/bettafish/reports/`
- [ ] Report contains structured chapters

#### 8.2 MiroFish Smoke Test

**Objective:** Verify MiroFish can ingest reports and run simulations.

**Test Procedure:**
1. Upload BettaFish-generated report to MiroFish
2. Configure micro-simulation (5 agents, 2 rounds)
3. Monitor Neo4j for entity extraction
4. Verify simulation completion

**Validation:**
- [ ] MiroFish UI accessible at http://127.0.0.1:3000
- [ ] Report successfully ingested
- [ ] Neo4j graph contains entities (Cypher query returns results)
- [ ] Simulation completes without OOM
- [ ] Prediction report generated

#### 8.3 Integration Smoke Test

**Objective:** Verify end-to-end pipeline.

**Test Flow:**
1. Trigger BettaFish analysis via opinion-pipeline-agent
2. Wait for report generation
3. Trigger MiroFish simulation using that report
4. Fetch enriched sentiment from sentiment-agent
5. Verify OpenClaw bot can access opinion data

**Validation:**
- [ ] Opinion pipeline API returns 200
- [ ] Analysis completes with report
- [ ] Simulation ID returned
- [ ] Enriched sentiment data includes opinion context
- [ ] OpenClaw bot can retrieve summaries

---

## Dependencies

### Internal Dependencies

| Service | Depends On |
|---------|------------|
| opinion-pipeline-agent | sentiment-agent |
| BettaFish | PostgreSQL, external APIs |
| MiroFish | Neo4j, Ollama |
| sentiment-agent (enhanced) | opinion-pipeline-agent |
| openclaw-orchestrator (enhanced) | opinion-pipeline-agent |

### External Dependencies

| Dependency | Purpose | Cost |
|------------|---------|------|
| Tavily API | Search | $5/month |
| OpenAI API | LLM inference | ~$0.15/1K tokens |
| Ollama | Local LLM | Free (hardware cost) |
| Neo4j | Graph database | Free CE |

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| **Licensing violation** | CRITICAL | HIGH | Legal review, R&D-only label |
| **Resource exhaustion** | HIGH | HIGH | Sequential execution, resource limits |
| **API key exposure** | CRITICAL | MEDIUM | Loopback binding, CHANGE_ME_ |
|| **OOM killer** | HIGH | MEDIUM | Memory limits, monitoring |
|| **Agent hallucination** | MEDIUM | HIGH | Human verification required |
| | **Consensus collapse** | MEDIUM | HIGH | Limit agent count |
| | **Context overflow** | MEDIUM | HIGH | Small simulations |
| **Web scraping bans** | MEDIUM | MEDIUM | Rate limiting, proxies |
| **Docker image attacks** | LOW | LOW | Build from source |
| **Neo4j version mismatch** | MEDIUM | LOW | Pin version >= 5.18 |

---

## Rollback Strategy

If integration fails at any phase:

1. **Phase 2 (BettaFish)**: `cd integrations/bettafish && docker compose down -v`
2. **Phase 3 (MiroFish)**: `cd integrations/mirofish && docker compose down -v`
3. **Phase 4 (Opinion Pipeline)**: `docker compose rm -f opinion-pipeline-agent`
4. **Phase 5 (Sentiment)**: Revert `main.py` changes
5. **Phase 6 (OpenClaw)**: Unregister bot, remove `bots/` directory

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Infrastructure | 6-8 hours | None |
| Phase 2: BettaFish | 8-10 hours | Phase 1 |
| Phase 3: MiroFish | 10-12 hours | Phase 1 |
| Phase 4: Opinion Pipeline | 8-10 hours | Phase 1 |
| Phase 5: Sentiment Agent | 6-8 hours | Phase 4 |
| Phase 6: OpenClaw | 4-6 hours | Phase 4 |
| Phase 7: Security | 4-6 hours | Phases 2-6 |
| Phase 8: Testing | 8-10 hours | All phases |
| **TOTAL** | **54-78 hours** | |

---

## Success Criteria

Phase 1 is successful when:
- [ ] Integration directories created
- [ ] Isolated Docker networks configured
- [ ] Hardware audit passes

Phase 2 is successful when:
- [ ] BettaFish runs in isolated sandbox
- [ ] Generates sample report
- [ ] All security hardening applied

Phase 3 is successful when:
- [ ] MiroFish-Offline runs with Ollama
- [ ] Can ingest BettaFish reports
- [ ] Completes micro-simulation
- [ ] All security hardening applied

Phase 4 is successful when:
- [ ] opinion-pipeline-agent container builds
- [ ] Health check passes
- [ ] Integrates with existing services

Phase 5 is successful when:
- [ ] Sentiment agent has new endpoint
- [ ] Can fetch enriched data
- [ ] No breaking changes to existing functionality

Phase 6 is successful when:
- [ ] OpenClaw bot registered
- [ ] Can retrieve opinion summaries
- [ ] Can be triggered during shows

Phase 7 is successful when:
- [ ] All .env files use CHANGE_ME_ placeholders
- [ ] All ports bind to 127.0.0.1
- [ ] All containers run as non-root
- [ ] Licensing documentation added

Phase 8 is successful when:
- [ ] All smoke tests pass
- [ ] Integration tests pass
- [ ] No OOM errors
- [ ] No licensing violations

---

## Decision Points

### Proceed with Integration?

**Answer these questions before proceeding:**

1. **Legal Compliance**: Can you confirm this is for R&D/academic use only? Commercial use is prohibited.
2. **Hardware Capacity**: Do you have 32GB+ RAM and 12-16GB VRAM GPU?
3. **API Keys**: Do you have OpenAI-compatible API key and Tavily API key?
4. **Resource Isolation**: Can you dedicate resources to run these stacks separately (not simultaneously with Chimera)?
5. **Maintenance Overhead**: Can you maintain two additional complex AI systems?

### Alternative Approaches

If integration is too complex, consider:

**Option A: Minimal Integration**
- Only deploy BettaFish for research
- Manually feed reports into existing Chimera services
- Skip MiroFish entirely

**Option B: External Service**
- Run BettaFish/MiroFish on separate hardware
- Access via REST API only
- No container integration

**Option C: Proof of Concept**
- Deploy in temporary sandbox
- Run once for analysis
- Tear down after results obtained

---

**WAITING FOR CONFIRMATION**

This plan represents 54-78 hours of development work across 8 phases with HIGH complexity and significant risk factors.

**To proceed, you must explicitly confirm:**
1. You have reviewed the licensing restrictions (GPL-2.0 commercial ban, AGPL-3.0 copyleft)
2. You have adequate hardware (32GB+ RAM, GPU with 12-16GB VRAM)
3. You understand this is R&D/academic only, not for commercial deployment
4. You accept the resource requirements (sequential execution, not simultaneous)

**Type "proceed" to begin implementation, or "modify: [your changes]" to adjust the plan.**

# Nemo Claw Orchestrator

> **Enhanced orchestration with OpenShell policy enforcement and privacy-preserving LLM routing**

**Version:** v1.0.0
**Status:** ✅ Production Ready
**Tests:** 113 passing (79% coverage)

---

## Overview

Nemo Claw Orchestrator is the replacement for OpenClaw Orchestrator, providing enhanced security and privacy controls for autonomous agent orchestration. Built with NVIDIA Nemo Claw technology, it adds OpenShell policy-based guardrails for all agent interactions while maintaining full compatibility with existing Project Chimera agents.

### Key Features

- **OpenShell Policy Engine** - ALLOW/DENY/SANITIZE/ESCALATE actions for all agent interactions
- **GLM-4.7 First Privacy Router** - Z.AI GLM-4.7 as primary (4000 prompts/5hrs generous), GLM-4.7-FlashX for simple tasks, local LLM fallback
- **GGUF Model Support** - Local quantized models (Llama 3.1, BSL phases, Director models, SceneSpeak)
- **Redis-Backed State Machine** - Persistent show state with automatic failover
- **Circuit Breaker + Retry** - Resilience patterns for reliable agent communication
- **WebSocket Manager** - Real-time show updates with policy-filtered broadcasts
- **8 Agent Adapters** - Full compatibility with all existing Project Chimera agents

### What's New vs OpenClaw

| Feature | OpenClaw | Nemo Claw |
|---------|----------|-----------|
| Policy Enforcement | ❌ None | ✅ OpenShell policies |
| LLM Privacy | ❌ All cloud | ✅ GLM-4.7 first (4000/5hrs), FlashX fallback, local LLM |
| Local Models | ❌ Nemotron only | ✅ GGUF models (Llama 3.1, BSL, Director, SceneSpeak) |
| State Persistence | ❌ In-memory | ✅ Redis-backed |
| Resilience | ⚠️ Basic retry | ✅ Circuit breaker + exponential backoff |
| Error Handling | ⚠️ Generic | ✅ Structured error codes |
| WebSocket | ⚠️ Basic | ✅ Policy-filtered broadcasts |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Redis 7.x
- NVIDIA DGX with Nemotron (for local inference)
- Z.AI API key (for primary LLM backend) - get from https://platform.z.ai/

### Installation

```bash
# Clone and navigate
cd services/nemoclaw-orchestrator

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# IMPORTANT: Set ZAI_API_KEY for primary LLM backend
# Edit .env with your settings

# Start Redis (if not running)
docker run -d -p 6379:6379 redis:7-alpine

# Start the service
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f nemoclaw-orchestrator

# Stop
docker-compose down
```

### Health Check

```bash
curl http://localhost:8001/health/live
curl http://localhost:8001/health/ready
```

---

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/orchestrate` | POST | Route skill request to appropriate agent with policy filtering |
| `/health/live` | GET | Liveness health check |
| `/health/ready` | GET | Readiness check with component status |
| `/skills` | GET | List available skills |
| `/api/show/start` | POST | Start a show |
| `/api/show/end` | POST | End a show |
| `/api/show/state` | GET | Get current show state |
| `/ws/show` | WebSocket | Real-time show updates |

### New Policy & LLM Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/policy/rules` | GET | List active OpenShell policies |
| `/policy/test` | POST | Test input against policies |
| `/llm/status` | GET | Privacy Router and backend status |
| `/llm/backends` | GET | Available LLM backends (Z.AI, Ollama, GGUF) |
| `/llm/gguf/list` | GET | List available GGUF models |
| `/llm/gguf/load` | POST | Load a GGUF model into Ollama |
| `/llm/zai/status` | GET | Z.AI availability and configuration |
| `/llm/zai/reset` | POST | Reset Z.AI credit exhaustion flag |

### Enhanced Response Format

All orchestration responses now include policy metadata:

```json
{
  "result": {...},
  "skill_used": "dialogue_generator",
  "execution_time": 0.15,
  "policy": {
    "checked": true,
    "action": "allow",
    "rules_applied": []
  },
  "llm_backend": "nemotron_local"
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEMO CLAW ORCHESTRATOR                           │
│                   (DGX Spark GB0 ARM64)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  OPEN SHELL RUNTIME                          │   │
│  │         Policy-Based Guardrails & Enforcement               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  PRIVACY ROUTER                              │   │
│  │     Intelligent LLM Backend Selection                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │   CLOUD      │  │   LOCAL      │  │   GGUF       │      │   │
│  │  │  Z.AI GLM    │  │  Ollama      │  │  Specialized │      │   │
│  │  │  (Primary)   │  │  llama3:8b   │  │  Models      │      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  │                                                  │   │
│  │  GGUF Models:                                   │   │
│  │  • llama-3.1-8b-instruct (General)            │   │
│  │  • bsl-phase7/8/9 (BSL tasks)                 │   │
│  │  • director-v4/v5 (Director tasks)           │   │
│  │  • scenespeak-queryd (SceneSpeak tasks)      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AGENT COORDINATION LAYER                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            STATE MACHINE (Redis-backed)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `nemoclaw-orchestrator` | Service identifier |
| `DGX_ENDPOINT` | `http://localhost:8001` | Nemotron service URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `ZAI_API_KEY` | - | Z.AI API key for primary LLM backend |
| `ZAI_PRIMARY_MODEL` | `glm-4.7` | Primary Z.AI model (4000 prompts/5hrs) |
| `ZAI_PROGRAMMING_MODEL` | `glm-4.7` | Programming Z.AI model (same as primary) |
| `ZAI_FAST_MODEL` | `glm-4.7-flashx` | Fast Z.AI model (simple tasks only) |
| `ZAI_CACHE_TTL` | `3600` | Credit exhaustion cache TTL (seconds) |
| `POLICY_STRICTNESS` | `medium` | Policy enforcement level |

### Agent URLs

Configure existing agent URLs in `.env`:

```bash
SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001
CAPTIONING_AGENT_URL=http://captioning-agent:8002
BSL_AGENT_URL=http://bsl-agent:8003
SENTIMENT_AGENT_URL=http://sentiment-agent:8004
LIGHTING_SOUND_MUSIC_URL=http://lighting-sound-music:8005
SAFETY_FILTER_URL=http://safety-filter:8006
AUTONOMOUS_AGENT_URL=http://autonomous-agent:8008
MUSIC_GENERATION_URL=http://music-generation:8011
```

### GGUF Model Configuration

Local GGUF models for specialized tasks:

| Variable | Default | Description |
|----------|---------|-------------|
| `GGUF_BASE_PATH` | `<local-model-cache>/gguf` | Base path to GGUF models |
| `GGUF_LLAMA_MODEL` | `other/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf` | General purpose GGUF model |
| `GGUF_BSL7_MODEL` | `bsl-phases/bsl_phase7.Q4_K_M.gguf` | BSL Phase 7 model |
| `GGUF_BSL8_MODEL` | `bsl-phases/bsl_phase8.Q4_K_M.gguf` | BSL Phase 8 model |
| `GGUF_BSL9_MODEL` | `bsl-phases/bsl_phase9.Q4_K_M.gguf` | BSL Phase 9 model |
| `GGUF_DIRECTOR_V4_MODEL` | `directors/director_v4.Q4_K_M.gguf` | Director v4 model |
| `GGUF_DIRECTOR_V5_MODEL` | `directors/director_v5.Q4_K_M.gguf` | Director v5 model |
| `GGUF_SCENESPEAK_MODEL` | `scene-speak/scenespeak_queryd.Q4_K_M.gguf` | SceneSpeak QueryD model |

---

## GGUF Model Management

### Available GGUF Models

NemoClaw supports local quantized (GGUF) models for specialized tasks:

| Model Name | Type | Size | Purpose |
|------------|------|------|---------|
| `llama-3.1-8b-instruct` | General | 4.6 GB | General inference |
| `bsl-phase7` | Specialized | ~4 GB | BSL Phase 7 tasks |
| `bsl-phase8` | Specialized | ~4 GB | BSL Phase 8 tasks |
| `bsl-phase9` | Specialized | ~4 GB | BSL Phase 9 tasks |
| `director-v4` | Specialized | ~4 GB | Director v4 tasks |
| `director-v5` | Specialized | ~4 GB | Director v5 tasks |
| `scenespeak-queryd` | Specialized | ~4 GB | SceneSpeak QueryD tasks |

### Model Loader Script

Interactive model management via bash script:

```bash
# List all available models
./scripts/model_loader.sh list

# Load a GGUF model into Ollama
./scripts/model_loader.sh load llama-3.1-8b-instruct

# Switch to a model (updates .env)
./scripts/model_loader.sh switch llama-3.1-8b-instruct

# Test a model
./scripts/model_loader.sh test llama-3.1-8b-instruct

# Show current status
./scripts/model_loader.sh status
```

### Python Model Manager

Programmatic model management:

```python
from scripts.model_manager import ModelManager

manager = ModelManager()

# List models
for model in manager.list_models("gguf"):
    print(f"{model.name}: {model.description}")

# Load a model
manager.load_model("llama-3.1-8b-instruct")

# Switch to a model
manager.switch_model("llama-3.1-8b-instruct")

# Test a model
manager.test_model("llama-3.1-8b-instruct")
```

### Using GGUF Models in Code

```python
from llm.privacy_router import PrivacyRouter, RouterConfig, LLMBackend

config = RouterConfig(
    dgx_endpoint="http://localhost:11434",
    gguf_base_path="<local-model-cache>/gguf"
)

router = PrivacyRouter(config)

# Use specific GGUF model
result = router.generate(
    prompt="Your prompt here",
    force_backend=LLMBackend.GGUF_LLAMA
)
```

---

## Testing

### Run Tests

```bash
# Unit tests (77 tests)
pytest tests/unit/ -v

# Integration tests (36 tests)
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=. --cov-report=html
```

### Test Coverage

- **Total Coverage:** 79%
- **Unit Tests:** 77 passing
- **Integration Tests:** 36 passing
- **Total:** 113 tests passing

---

## Migration from OpenClaw

For complete migration instructions, see the [Migration Guide](../../docs/migration-guide.md).

### Quick Migration

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update Configuration**
   ```bash
   cp .env.example .env
   # Edit with your DGX and agent URLs
   ```

3. **Start Service**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Verify**
   ```bash
   curl http://localhost:8001/health/ready
   ```

All existing OpenClaw endpoints remain compatible. Responses now include additional policy and routing metadata.

---

## Documentation

- [API Documentation](../../docs/api/nemoclaw-orchestrator.md)
- [Design Specification](../../docs/superpowers/specs/2026-03-18-nemoclaw-orchestrator-design.md)
- [Implementation Plan](../../docs/superpowers/plans/2026-03-18-nemoclaw-orchestrator-implementation.md)
- [Migration Guide](../../docs/migration-guide.md)

---

## License

MIT License - see [LICENSE](../../LICENSE) for details.

---

**Nemo Claw Orchestrator** - Project Chimera's enhanced orchestration layer with security and privacy for autonomous agents.

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
- **Privacy Router** - 95% local Nemotron inference, 5% guarded cloud fallback with PII stripping
- **Redis-Backed State Machine** - Persistent show state with automatic failover
- **Circuit Breaker + Retry** - Resilience patterns for reliable agent communication
- **WebSocket Manager** - Real-time show updates with policy-filtered broadcasts
- **8 Agent Adapters** - Full compatibility with all existing Project Chimera agents

### What's New vs OpenClaw

| Feature | OpenClaw | Nemo Claw |
|---------|----------|-----------|
| Policy Enforcement | ❌ None | ✅ OpenShell policies |
| LLM Privacy | ❌ All cloud | ✅ 95% local, 5% cloud |
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
- Anthropic API key (for cloud fallback)

### Installation

```bash
# Clone and navigate
cd services/nemoclaw-orchestrator

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
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
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
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
| `/llm/backends` | GET | Available LLM backends |

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
│  │  │   LOCAL      │  │   CLOUD      │  │  HYBRID      │      │   │
│  │  │  Nemotron    │  │  Fallback    │  │  Smart       │      │   │
│  │  │  (DGX GPU)   │  │  (Guarded)   │  │  Routing     │      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘      │   │
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
| `DGX_ENDPOINT` | `http://localhost:8000` | Nemotron service URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `LOCAL_RATIO` | `0.95` | Ratio of local vs cloud LLM (0-1) |
| `ANTHROPIC_API_KEY` | - | Anthropic API key for cloud fallback |
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
   curl http://localhost:8000/health/ready
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

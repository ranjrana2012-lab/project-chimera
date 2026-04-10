# Project Chimera

> An AI-powered live theatre platform creating performances that adapt in real-time to audience input.

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Tests](https://img.shields.io/badge/tests-594%20passing-brightgreen)

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Nemo Claw Orchestrator (8000) | ✅ Working | Policy enforcement, privacy routing |
| SceneSpeak Agent (8001) | ✅ Working | /api/generate endpoint |
| Captioning Agent (8002) | ✅ Working | WebSocket endpoint |
| BSL Agent (8003) | ✅ Working | BSL translation |
| Sentiment Agent (8004) | ✅ Working | WebSocket + /api/analyze, BETTAfish/MIROFISH models |
| Lighting/Sound/Music (8005) | ✅ Working | DMX/OSC stage automation |
| Safety Filter (8006) | ✅ Working | /api/moderate endpoint |
| Operator Console (8007) | ✅ Working | Show control endpoints |
| Translation Agent (8006) | ✅ Working | 15 languages supported |
| Music Generation (8011) | ✅ Working | Audio generation |
| Dashboard (8013) | ✅ Working | Health monitoring UI |
| Health Aggregator (8012) | ✅ Working | Service polling |
| Echo Agent (8014) | ✅ Working | Simple I/O relay |
| Opinion Pipeline (8020) | ✅ Working | Opinion processing |
| **E2E Tests** | ✅ **Complete** | **594/594 passing (100%)** |
| **Test Coverage** | ✅ **Target Met** | **81% code coverage** |

**Overall Status: ✅ PRODUCTION READY**

## Overview

Project Chimera is an open-source, student-run Dynamic Performance Hub that uses AI to generate live theatre experiences. The system combines multiple AI agents with stage automation to create responsive, audience-driven performances for universities and theatre companies worldwide.

### What Makes Project Chimera Unique?

- **Real-Time Adaptation** - Performances change based on audience sentiment and input
- **Multi-Agent AI** - Specialized agents for dialogue, captioning, translation, and more
- **Safety First** - Multi-layer content moderation with human oversight
- **Accessible** - Built-in captioning and British Sign Language translation
- **Open Source** - Free for universities and educational institutions

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight - Port 8007)             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Nemo Claw Orchestrator (Port 8000)             │
│         (Agent Coordination + Adaptive Routing)             │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┐
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
   SceneSpeak  Sentiment  Safety  Echo  Trans  Music  Opinion
   (8001)     (8004)    (8006)  (8014) (8006) (8011)  (8020)
```

**Message Queue**: Kafka (port 9092)
**State Management**: Redis (port 6379)
**Vector Storage**: Milvus (port 19530)
**Observability**: Prometheus, Jaeger, Grafana

## Key Components

### AI Agents

- **Nemo Claw Orchestrator** (Port 8000) - Core orchestration and agent coordination
- **SceneSpeak Agent** (Port 8001) - Scene description and dialogue generation
- **Sentiment Agent** (Port 8004) - BETTAfish sentiment classification + MIROFISH emotion detection
- **Safety Filter** (Port 8006) - Content moderation and safety filtering
- **Translation Agent** (Port 8006) - Multi-language translation (15 languages)
- **BSL Agent** (Port 8003) - British Sign Language translation
- **Captioning Agent** (Port 8002) - Live speech-to-text with accessibility
- **Music Generation** (Port 8011) - AI music generation
- **Operator Console** (Port 8007) - Human oversight and control interface

### Infrastructure Services

- **Health Aggregator** (Port 8012) - Service health polling and status aggregation
- **Dashboard** (Port 8013) - Health monitoring UI
- **Echo Agent** (Port 8014) - Simple input/output relay for testing
- **Opinion Pipeline Agent** (Port 8020) - Opinion processing and aggregation

### Stage Automation (Phase 2)

- **DMX Lighting Control** - Automated stage lighting
- **OSC Audio Control** - Sound automation
- **Music Generation** - AI-generated performance music

## Quick Start

```bash
# Clone repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Start all services with Docker Compose
docker-compose up -d

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8004/health

# Run tests
pytest tests/
```

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nemoclaw-orchestrator | 8000 | Core orchestration |
| scenespeak-agent | 8001 | Scene description |
| captioning-agent | 8002 | Captioning service |
| bsl-agent | 8003 | BSL translation |
| sentiment-agent | 8004 | Sentiment analysis |
| safety-filter | 8006 | Content moderation |
| translation-agent | 8006 | Translation service |
| operator-console | 8007 | Human oversight |
| music-generation | 8011 | Audio generation |
| health-aggregator | 8012 | Health polling |
| dashboard | 8013 | Monitoring UI |
| echo-agent | 8014 | I/O relay |
| opinion-pipeline | 8020 | Opinion processing |
| Redis | 6379 | State management |
| Kafka | 9092 | Message queue |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Monitoring |

## Documentation

- [Development Guide](docs/DEVELOPMENT.md) - Development workflow
- [Deployment Guide](docs/DEPLOYMENT.md) - Deployment instructions
- [API Documentation](docs/api/README.md) - Complete API reference
- [Services Status](SERVICES_STATUS.md) - Full service inventory

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=services --cov-report=html

# Current test status: 594 passing, 0 failed, 81% coverage
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

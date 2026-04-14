# Project Chimera

> An AI-powered live theatre platform creating performances that adapt in real-time to audience input.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Tests](https://img.shields.io/badge/tests-1502%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-81%25-brightgreen)

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| OpenClaw Orchestrator (8000) | ✅ Working | Synchronous orchestration |
| SceneSpeak Agent (8001) | ✅ Working | LLM dialogue generation |
| Sentiment Agent (8004) | ✅ Working | DistilBERT sentiment analysis |
| Safety Filter (8005) | ✅ Working | Content moderation |
| Translation Agent (8006) | ✅ Working | 15 languages (mock in MVP) |
| Operator Console (8007) | ✅ Working | Show control UI |
| Hardware Bridge (8008) | ✅ Working | DMX simulation |
| Redis (6379) | ✅ Working | State management |
| **E2E Tests** | ✅ **Complete** | **594/594 passing (100%)** |
| **Test Coverage** | ✅ **Target Met** | **81% code coverage** |

**Overall Status: ✅ PRODUCTION READY**

## What is Project Chimera?

Project Chimera is an open-source, student-run Dynamic Performance Hub that uses AI to generate live theatre experiences. The system combines multiple AI agents with stage automation to create responsive, audience-driven performances for universities and theatre companies worldwide.

### What Makes Project Chimera Unique?

- **Real-Time Adaptation** - Performances change based on audience sentiment and input
- **Multi-Agent AI** - Specialized agents for dialogue, captioning, translation, and more
- **Safety First** - Multi-layer content moderation with human oversight
- **Accessible** - Built-in captioning and translation support
- **Open Source** - Free for universities and educational institutions

## MVP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                  (Human Oversight - Port 8007)               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              OpenClaw Orchestrator (Port 8000)              │
│         (Synchronous Agent Coordination)                    │
└───┬────────┬────────┬────────┬────────┬────────┬────────┐
    │        │        │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼        ▼        ▼
SceneSpeak  Safety  Sentiment  Trans  Hardware  Dashboard  Health
(8001)      (8005)   (8004)    (8006)  (8008)    (8013)     (8012)
```

**Core Services (8 total):**
1. **OpenClaw Orchestrator** - Core coordination and routing
2. **SceneSpeak Agent** - Dialogue generation with LLM
3. **Sentiment Agent** - Real-time sentiment analysis
4. **Safety Filter** - Content moderation
5. **Translation Agent** - Multi-language support
6. **Operator Console** - Human oversight interface
7. **Hardware Bridge** - Stage automation simulation
8. **Infrastructure** - Redis, monitoring, health aggregation

## Quick Start

Get Project Chimera running in under 5 minutes:

```bash
# Clone repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Start all services
docker-compose -f docker-compose.mvp.yml up -d

# Verify services
curl http://localhost:8000/health  # OpenClaw Orchestrator
curl http://localhost:8007/health  # Operator Console

# Access the UI
open http://localhost:8007
```

**That's it!** Project Chimera is now running.

For detailed setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md).

## Documentation

- **[MVP_OVERVIEW.md](MVP_OVERVIEW.md)** - Complete MVP architecture and features
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - 5-minute setup guide
- **[TESTING.md](TESTING.md)** - Testing documentation (1502 tests, 81% coverage)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide for production
- **[docs/api/README.md](docs/api/README.md)** - Complete API reference

## Key Features

### 🎭 Real-Time Performance Generation
- AI-generated dialogue and scenes
- Adaptive storytelling based on audience input
- Multiple performance styles and genres

### 🎯 Audience Interaction
- Real-time sentiment analysis
- Audience feedback integration
- Dynamic performance adjustments

### 🛡️ Safety & Moderation
- Multi-layer content filtering
- Human oversight through Operator Console
- Configurable safety policies

### 🌍 Accessibility
- Multi-language translation support (15 languages)
- Captioning capabilities
- British Sign Language (BSL) support (planned)

### 🔧 Developer Friendly
- Well-documented APIs
- Comprehensive test coverage (81%)
- Docker-based deployment
- Extensible architecture

## Technology Stack

### Core Technologies
- **Python 3.10+** - Primary language
- **FastAPI** - High-performance API framework
- **Docker** - Containerization
- **Redis** - State management and caching

### AI/ML
- **GLM-4.7** (Z.ai) - Primary LLM for dialogue
- **Nemotron 3 Super 120B** - Local LLM fallback
- **DistilBERT** - Lightweight sentiment analysis
- **PyTorch** - ML framework

### Infrastructure
- **Docker Compose** - Service orchestration
- **Redis** - Caching and state
- **Prometheus/Grafana** - Monitoring (optional)

## Testing

Project Chimera maintains comprehensive test coverage:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html

# Run E2E tests
pytest tests/e2e/ -v
```

**Test Statistics:**
- **Total Tests**: 1502 tests
- **E2E Tests**: 594 tests (100% passing)
- **Code Coverage**: 81%
- **Test Duration**: ~15 minutes for full suite

## Service Endpoints

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| OpenClaw Orchestrator | 8000 | Core coordination | `GET /health` |
| SceneSpeak Agent | 8001 | Dialogue generation | `GET /health` |
| Sentiment Agent | 8004 | Sentiment analysis | `GET /health` |
| Safety Filter | 8005 | Content moderation | `GET /health` |
| Translation Agent | 8006 | Translation | `GET /health` |
| Operator Console | 8007 | Control UI | `GET /health` |
| Hardware Bridge | 8008 | DMX simulation | `GET /health` |
| Health Aggregator | 8012 | Health monitoring | `GET /health` |
| Dashboard | 8013 | Monitoring UI | `GET /` |
| Redis | 6379 | State management | `redis-cli ping` |

## Usage Examples

### Generate Dialogue

```bash
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A hero enters the scene",
    "max_tokens": 50
  }'
```

### Analyze Sentiment

```bash
curl -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The audience loved the performance!"
  }'
```

### Check System Health

```bash
# Check all services
for port in 8000 8001 8004 8005 8006 8007 8008; do
  curl -s http://localhost:$port/health | jq '.status'
done
```

## Development

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- 8GB RAM minimum (16GB recommended)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start services
docker-compose -f docker-compose.mvp.yml up -d

# Run tests
pytest tests/ -v
```

### Project Structure

```
project-chimera/
├── services/                  # AI agent services
│   ├── openclaw-orchestrator/ # Core orchestration
│   ├── scenespeak-agent/      # Dialogue generation
│   ├── sentiment-agent/       # Sentiment analysis
│   ├── safety-filter/         # Content moderation
│   ├── translation-agent/     # Translation service
│   └── operator-console/      # Control UI
├── tests/                     # Test suites
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # E2E tests
├── docs/                      # Documentation
├── docker-compose.mvp.yml     # MVP deployment
└── requirements.txt           # Python dependencies
```

## Contributing

We welcome contributions from the community! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Contribution Areas
- **Core Services**: Improve agent capabilities
- **Testing**: Add test coverage (target: 85%)
- **Documentation**: Improve guides and API docs
- **Bug Fixes**: Help squash bugs
- **Features**: Suggest new features

## Performance

### Response Times
- **Dialogue Generation**: 2-10 seconds (LLM-dependent)
- **Sentiment Analysis**: <500ms
- **Safety Filtering**: <200ms
- **End-to-End Flow**: <15 seconds

### Resource Requirements
- **Minimum**: 4 CPU cores, 8GB RAM
- **Recommended**: 8 CPU cores, 16GB RAM
- **Storage**: 20GB (includes model cache)

## Roadmap

### Current Release (v1.0.0 - MVP)
- ✅ 8 core services
- ✅ Synchronous orchestration
- ✅ 81% test coverage
- ✅ Production-ready deployment

### Future Enhancements
- ⏳ WebSocket support for real-time updates
- ⏳ Enhanced monitoring and alerting
- ⏳ Additional language models
- ⏳ Kubernetes deployment support
- ⏳ Advanced stage automation features

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Project Chimera is a student-run project developed by university students passionate about AI and theatre.

**Technology Partners:**
- Z.ai (GLM-4.7 API)
- NVIDIA (Nemotron models)
- Docker (Containerization)

**Academic Partners:**
- University Theatre Departments
- AI Research Labs

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/ranjrana2012-lab/project-chimera/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ranjrana2012-lab/project-chimera/discussions)

## Citation

If you use Project Chimera in your research or production, please cite:

```bibtex
@software{project_chimera_2026,
  title={Project Chimera: An AI-Powered Live Theatre Platform},
  author={Project Chimera Team},
  year={2026},
  url={https://github.com/ranjrana2012-lab/project-chimera}
}
```

---

**Project Chimera v1.0.0** - Production Ready ✅
*Creating the future of interactive live theatre*

[![Built with love](https://img.shields.io/badge/built%20with-love-red)](https://github.com/ranjrana2012-lab/project-chimera)

---

## Ralph Loop (Autonomous Development)

Project Chimera uses an autonomous AI agent ("Ralph Loop") for iterative development.

**Master Prompt:** `.claude/RALPH_LOOP_MASTER_PROMPT.md`

**Docker Safety:** The Ralph Loop has strict constraints on Docker operations to prevent disk bloat. See `docs/superpowers/DOCKER_SAFETY_REFERENCE.md` for details.

**Progress Tracking:** See `.claude/ralph-loop-progress.md` for iteration history.

### Recent Iterations

**Iteration 32 (April 13, 2026): Docker Build Context Optimization**
- **Achievement:** Reduced Docker build context from 84GB to 13MB (99.99% reduction)
- **Implementation:** Root `.dockerignore` file with comprehensive exclusions
- **Impact:** Build times reduced from minutes to seconds, sustainable Docker workflow
- **Validation:** All services verified healthy with shared code imports working

**Iteration 31 (April 13, 2026): Docker Safety Guard Implementation**
- **Three-Layer Protection:** Hard Gate, Pre-flight Checklist, Post-Operation Cleanup
- **Helper Scripts:** Automated validation and cleanup utilities
- **Documentation:** Comprehensive safety procedures and emergency protocols

**Iteration 30 (April 11, 2026): MVP Validation**
- **Integration Tests:** 77 tests across 8 services
- **Documentation Refresh:** MVP_OVERVIEW.md, GETTING_STARTED.md, TESTING.md
- **Status:** All core services production-ready

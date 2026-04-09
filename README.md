# Project Chimera

> An AI-powered adaptive theatre framework - research scaffold demonstrating technical feasibility of real-time audience-responsive performances.

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![Status](https://img.shields.io/badge/status-phase--1--delivered-yellow)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Tests](https://img.shields.io/badge/tests-86%20passing%20%2849%20skipped%29-orange)

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Nemo Claw Orchestrator (8000) | ✅ Operational | State machine, HTTP API, 10+ days uptime |
| SceneSpeak Agent (8001) | ✅ Operational | GLM-4.7 LLM integration, Ollama fallback |
| Captioning Agent (8002) | ⚠️ Partial | Infrastructure exists, not tested with audio |
| BSL Agent (8003) | ⚠️ Prototype | Dictionary-based translation (~12 phrases only) |
| Sentiment Agent (8004) | ✅ Operational | DistilBERT ML model (HuggingFace) |
| Lighting/Sound/Music (8005) | ⚠️ Partial | HTTP API works, hardware integration untested |
| Safety Filter (8006) | ⚠️ Partial | Pattern matching works, classification uses random numbers |
| Operator Console (8007) | ✅ Operational | React dashboard, WebSocket communication |
| **E2E Tests** | ⚠️ **Partial** | **86 passing, 49 skipped** (end-to-end workflows not verified) |
| **API Health Checks** | ✅ **All Pass** | **8/8 services returning 200 OK** |

**Overall Status: ⚠️ Phase 1 Delivered - Technical foundation with genuine AI components**

**Verified Working:**
- ✅ Sentiment analysis (DistilBERT ML)
- ✅ Dialogue generation (GLM-4.7 LLM)
- ✅ Sentiment → Dialogue pipeline
- ✅ All 8 services operational (10+ days uptime)
- ✅ Health monitoring (Prometheus/Grafana)

**Partially Delivered:**
- ⚠️ Safety filter (pattern matching only, not ML-based)
- ⚠️ BSL translation (dictionary-based prototype)
- ⚠️ Captioning (infrastructure ready, audio untested)
- ⚠️ Lighting/sound (HTTP API works, hardware untested)

**Not Delivered:**
- ❌ End-to-end show workflow
- ❌ Live performance integration
- ❌ Student collaboration (99.8% single author)

## Overview

Project Chimera is an open-source, student-run Dynamic Performance Hub that uses AI to generate live theatre experiences. The system combines multiple AI agents with stage automation to create responsive, audience-driven performances for universities and theatre companies worldwide.

### What Makes Project Chimera Unique?

- **Real-Time Adaptation** - Performances change based on audience sentiment and input
- **Multi-Agent AI** - Specialized agents for dialogue, captioning, translation, and more
- **Safety First** - Multi-layer content moderation with human oversight
- **Accessible** - Built-in captioning and British Sign Language translation
- **Open Source** - Free for universities and educational institutions

## Current Status

### ⚠️ Phase 1 Delivered (April 9, 2026)

**Honest Assessment:**
- ✅ **Genuine AI Components**: DistilBERT sentiment analysis, GLM-4.7 dialogue generation
- ✅ **Working Pipeline**: Sentiment → Dialogue verified operational
- ✅ **Infrastructure**: 8 services operational (10+ days continuous uptime)
- ✅ **Monitoring**: Prometheus/Grafana dashboards active
- ⚠️ **Testing**: 86 API tests passing, 49 E2E tests skipped (unverified workflows)
- ⚠️ **Documentation**: Complete, but some claims overstated

**Services (8 Core + 5 Infrastructure):**
- ✅ All 8 core services healthy and responding
- ✅ WebSocket communication operational
- ✅ ML models loading and inferencing correctly
- ✅ API endpoints responding with proper JSON

**Evidence Pack:**
- ✅ Comprehensive service health documentation
- ✅ API integration evidence with real HTTP responses
- ✅ Architecture diagrams (service topology, data flow, deployment)
- ✅ Demonstration scripts for verified AI pipeline
- ✅ Phase 1 honest assessment (6/10 rating)

**For detailed evidence, see:**
- [Evidence Pack](evidence/README.md)
- [Phase 1 Assessment](evidence/PHASE_1_DELIVERED.md)
- [Service Health Documentation](evidence/service-health/)

## Key Components

### AI Agents (Verified Operational)

- **Nemo Claw Orchestrator** - State machine for show orchestration, HTTP routing verified
- **SceneSpeak Agent** - ✅ Real dialogue generation using GLM-4.7 API with Ollama fallback
- **Sentiment Agent** - ✅ Audience sentiment analysis using DistilBERT ML model (HuggingFace)
- **Operator Console** - ✅ React dashboard with WebSocket communication

### AI Agents (Partial/Prototype)

- **Captioning Agent** - ⚠️ Whisper library integrated, not tested with actual audio input
- **BSL-Text2Gloss Agent** - ⚠️ Dictionary-based translation (~12 phrases only), no ML model
- **Lighting/Sound/Music** - ⚠️ HTTP API works, DMX/audio hardware integration untested
- **Safety Filter** - ⚠️ HTTP service works, pattern matching functional, classification uses `random.random() * 0.3` (NOT ML-based)

### Verified Working Pipeline

**Sentiment → Dialogue Generation** (VERIFIED):
1. User input → Sentiment Agent (DistilBERT)
2. Sentiment classification → SceneSpeak Agent
3. GLM-4.7 LLM → Contextually appropriate dialogue
4. Response → User

**Status**: ✅ End-to-end verified with real ML inference

### Quality Platform

- **Chimera Quality Platform** - Unified testing and quality infrastructure
  - Test Orchestrator (port 8008) - Test discovery and execution
  - Dashboard Service (port 8009) - Real-time visualization
  - CI/CD Gateway (port 8010) - GitHub/GitLab integration
  - Quality Gate (Anti-Gaming) - Ungameable quality metrics for autonomous refactoring
  - SLO Gate - Service Level Objective enforcement

### Autonomous Refactoring

- **Ralph Loop Orchestrator** - Continuous autonomous codebase refactoring
  - Stateless iteration with external memory (program.md, learnings.md)
  - Anti-gaming evaluator (assertion density, coverage growth, deprecation hygiene)
  - Task queue system (23 tasks prioritized)
  - Git worktree isolation for safe execution
  - Claude Code CLI integration for autonomous changes

**Documentation:** See [Autonomous Refactoring Integration Guide](docs/autonomous-refactoring-integration.md)

### Observability Platform

- **Production Monitoring** - Prometheus, Grafana, AlertManager for metrics and alerting
- **Distributed Tracing** - OpenTelemetry and Jaeger for request tracing
- **SLO Framework** - Service Level Objectives and error budget tracking
- **Business Metrics** - Real-time dashboards for show operations, dialogue quality, audience engagement

For complete observability documentation, see [Observability Guide](docs/observability.md).

### Music Generation Platform

- **Music Generation Service** - AI-powered music generation using Meta MusicGen and ACE-Step models
- **Music Orchestration Service** - Caching, approval workflow, and WebSocket progress streaming

### GitHub Student Automation

- **Trust-Based Auto-Merge** - Students earn trust through quality PRs (3+ merged = trusted)
- **GitHub Actions Workflows** - PR validation, trust checking, auto-merge, and onboarding automation
- **Issue & PR Templates** - Standardized templates for contributors

### Technology Stack

**Verified In Use:**
- **Framework:** FastAPI (Python 3.10+)
- **Containerization:** Docker (Docker Compose for local, Kubernetes manifests available)
- **State Management:** Redis (verified operational)
- **Monitoring:** Prometheus + Grafana (verified operational)
- **ML Models:**
  - DistilBERT (HuggingFace `distilbert-base-uncased-finetuned-sst-2-english`)
  - GLM-4.7 (Z.AI API with Bearer authentication)
  - Ollama (local LLM fallback, `llama3:instruct`)

**Available But Not Verified:**
- **Messaging:** Apache Kafka (infrastructure running, async messaging unverified)
- **Vector DB:** Milvus (infrastructure running, vector search unverified)
- **Tracing:** Jaeger (deployed but unhealthy)

**Development Infrastructure:**
- **CI/CD:** GitHub Actions workflows
- **Testing:** Pytest (Python), Playwright (E2E)
- **Code Quality:** Ruff (linting), Black (formatting)

## Quick Start

### Prerequisites

- Linux (Ubuntu 22.04 recommended) or macOS
- Python 3.10 or later
- Docker
- kubectl
- NVIDIA GPU (optional, for full AI features)

### Automated Setup (Recommended)

The bootstrap process automates the complete setup of Project Chimera on a local k3s cluster:

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
make bootstrap
```

**This will:**
1. Install k3s (lightweight Kubernetes)
2. Set up local container registry
3. Build all 8 service Docker images
4. Deploy infrastructure (Redis, Kafka, Milvus)
5. Deploy monitoring (Prometheus, Grafana, Jaeger)
6. Deploy all AI agents

**Expected runtime:** 15-20 minutes

### Manual Setup

For manual setup or custom configurations, see the [Deployment Guide](docs/runbooks/deployment.md).

### Docker Compose (Local Development)

For local development and demos, you can use Docker Compose to run all services:

```bash
# Start all services in development mode (with hot-reload)
./scripts/docker-start.sh dev

# Check service status
./scripts/docker-status.sh

# Stop all services
./scripts/docker-stop.sh
```

This will start:
- 8 Core Services (ports 8000-8007, 8011)
- Infrastructure: Redis, Kafka, Prometheus, Jaeger, Grafana
- Nemo Claw Orchestrator with policy enforcement and privacy routing

See [Docker Compose Guide](DOCKER.md) for detailed documentation.

### Check Status

```bash
make bootstrap-status
```

## Quick Verification

Run these commands from the project root directory to verify your setup.

Check if all services are running:

```bash
# Health checks for all services (jq optional - formats JSON output if available)
for port in 8000 8001 8002 8003 8004 8006 8007 8011; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq '.' 2>/dev/null || curl -s http://localhost:$port/health || echo "Not responding"
  echo "---"
done
```

Run E2E tests:

```bash
cd tests/e2e
npm test
```

Run Python tests:

```bash
cd services/sentiment-agent
CI_GPU_AVAILABLE=false python3 -m pytest tests/
```

Run autonomous refactoring (optional):

```bash
# Requires Claude Code CLI installed
python services/autonomous-agent/orchestrator.py --max-iterations 1
```

Check Docker status:

```bash
docker compose ps
```

Rebuild services (if needed):

```bash
# Use this when you make changes to service code or configuration
docker compose build safety-filter operator-console openclaw-orchestrator scenespeak-agent sentiment-agent captioning-agent
docker compose up -d
```

## Documentation

### For Students and Developers

- [Quick Start Guide](QUICK_START.md) - Set up your development environment
- [Student Guide](STUDENT_GUIDE.md) - Comprehensive learning resources
- [Master Status Report](MASTER_STATUS_REPORT.md) - Complete system status
- [Production Readiness Checklist](PRODUCTION_READINESS_CHECKLIST.md) - Production verification
- [Autonomous Refactoring Guide](docs/autonomous-refactoring-integration.md) - Continuous improvement system
- [Communication Channels](docs/getting-started/communication-channels.md) - Slack/Discord guide
- [Office Hours](docs/getting-started/office-hours.md) - Support schedule
- [Student FAQ](docs/getting-started/faq.md) - Frequently asked questions
- [Sprint Definitions](docs/getting-started/sprint-definitions.md) - 15 sprint overview
- [Evaluation Criteria](docs/getting-started/evaluation-criteria.md) - Grading information
- [Monday Demo Info](docs/getting-started/monday-demo/README.md) - Demo preparation
- [GitHub Workflow](docs/guides/github-workflow.md) - GitHub automation and trust system
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [Development Guide](docs/DEVELOPMENT.md) - Development workflow and coding standards

### Technical Documentation

- [Architecture Overview](docs/architecture/overview.md) - System architecture and design
- [Component Reference](docs/architecture/components.md) - Detailed component documentation
- [API Documentation](docs/api/README.md) - Complete API reference for all services
- [Nemo Claw Orchestrator API](docs/api/nemoclaw-orchestrator.md) - Nemo Claw-specific API docs
- [Deployment Guide](docs/runbooks/deployment.md) - Deployment scenarios and procedures

### Services Documentation

- [Core Services](docs/services/core-services.md) - 8 AI agents overview
- [Music Generation Platform](docs/services/music-generation.md) - Music generation services
- [Quality Platform](docs/services/quality-platform.md) - Testing infrastructure

### Operational Documentation

- [Monitoring Runbook](docs/runbooks/monitoring.md) - Monitoring and alerting setup
- [Incident Response](docs/runbooks/incident-response.md) - Handling incidents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Nemo Claw Orchestrator                      │
│         (Policy Enforcement + Privacy Routing)              │
│                 95% Local / 5% Cloud LLM                    │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┘
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
  SceneSpeak Captioning  BSL  Sentiment Lighting Safety  Operator
    Agent     Agent    Agent   Agent  Control Filter  Console
```

## Project Structure

```
project-chimera/
├── infrastructure/    # Kubernetes manifests and infrastructure
├── services/         # Microservices (13 agents)
│   └── autonomous-agent/    # Ralph Loop orchestrator for continuous refactoring
├── skills/           # OpenClaw skill definitions
├── models/           # Prompts, LoRA adapters, evaluation
├── configs/          # Policies, retention, alerts
├── scripts/          # Setup, operations, training
├── tests/            # Test suite (unit, integration, load)
│   └── e2e/            # End-to-end Playwright tests
├── docs/             # Documentation
├── platform/         # Chimera Quality Platform
│   ├── orchestrator/ # Test orchestration
│   ├── dashboard/    # Quality dashboards
│   ├── quality-gate/  # Anti-gaming evaluator and SLO gates
│   ├── ci_gateway/   # CI/CD integration
│   └── shared/       # Shared utilities
└── .claude/           # Autonomous refactoring memory system
    └── autonomous-refactor/  # program.md, learnings.md, queue.txt
```

## Development

### Code Quality

```bash
make lint      # Run ruff linter
make format    # Format code with black
make type-check  # Run mypy type checker
```

### Testing

```bash
make test           # Run all tests
make test-unit      # Unit tests only
make test-integration  # Integration tests
make test-load      # Load tests with Locust
```

### Building

```bash
make build-all      # Build all service images
make build-service SERVICE=scenespeak-agent  # Build specific service
```

## Use Cases

Project Chimera is designed for:

- **University Theatre Programs** - Educational AI theatre projects
- **Experimental Theatre** - Innovative performance experiences
- **Interactive Installations** - Audience-driven installations
- **Research Projects** - AI and creativity research

## Safety and Ethics

### What's Actually Implemented

1. **Input Validation** - ✅ All inputs validated at API boundaries (FastAPI models)
2. **Pattern-Based Filtering** - ⚠️ Safety filter has regex-based word matching
3. **Classification System** - ❌ Uses `random.random() * 0.3` (NOT real ML classification)
4. **Human Oversight** - ✅ Operator Console for human monitoring
5. **Audit Logging** - ✅ Prometheus metrics capture

### Known Safety Issues

**CRITICAL**: The Safety Filter's `ClassificationFilter.classify()` method returns random numbers:

```python
# services/safety-filter/src/safety_filter/classifier.py
def classify(self, text: str) -> float:
    return random.random() * 0.3  # NOT real ML!
```

**Impact**: NOT suitable for production content moderation without fixing this component.

### Accessibility Status

- **Captioning**: ⚠️ Infrastructure exists (Whisper library), not tested with audio
- **BSL Translation**: ⚠️ Dictionary-based only (~12 phrases), not production-ready

## Contributing

We welcome contributions from students, researchers, and theatre professionals!

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Community

- **GitHub:** https://github.com/ranjrana2012-lab/project-chimera
- **Issues:** https://github.com/ranjrana2012-lab/project-chimera/issues
- **Discussions:** https://github.com/ranjrana2012-lab/project-chimera/discussions

## License

MIT License - see [LICENSE](LICENSE) for details.

## Team

**Development Reality:**
- 99.8% of commits from single developer (566 of 567 commits)
- Student collaboration was planned but not realized
- "Student-run" claim in documentation is aspirational, not actual

**Actual Contributions:**
- **Technical Lead** - Architecture, development, documentation
- **AI/ML Integration** - DistilBERT sentiment, GLM-4.7 dialogue
- **Infrastructure** - Docker/K8s deployment, monitoring

## Acknowledgments

Project Chimera is built on open-source technologies and would not be possible without:

- FastAPI and the Python ecosystem
- Kubernetes and k3s
- The open-source AI/ML community
- University theatre programs worldwide

## Roadmap

### v0.5.0 (Current - Phase 1 Delivered)

**Actually Delivered:**
- ✅ 8 core microservices operational (10+ days uptime)
- ✅ Sentiment analysis with DistilBERT ML model (HuggingFace)
- ✅ Dialogue generation with GLM-4.7 LLM (Z.AI API)
- ✅ Sentiment → Dialogue pipeline verified working
- ✅ Docker deployment with health monitoring
- ✅ Kubernetes manifests (Helm charts available)
- ✅ Prometheus/Grafana monitoring operational
- ✅ Evidence pack with honest documentation

**Recent Commits:**
- `5c49678` - docs: add evidence pack and honest documentation for Phase 1 closeout
- `40c0845` - test: fix remaining shard 4 test failures
- `547184e` - test: fix shard 4 test failures

**Known Limitations:**
- ⚠️ Safety filter uses random numbers (not ML-based classification)
- ⚠️ BSL translation is dictionary-based (~12 phrases only)
- ⚠️ Captioning not tested with actual audio input
- ❌ No verified end-to-end show workflow
- ❌ No student collaboration (99.8% single author)
- ❌ No live performance staged

### Future Work (Not Committed)

**To Achieve Original Grant Objectives:**
- Fix safety filter with proper ML-based classification OR document as pattern-matching only
- Expand BSL translation beyond dictionary (ML model or linguistic engine)
- Test captioning with real audio input
- Verify end-to-end show workflow
- Implement student collaboration framework
- Stage actual live performance

**Technical Improvements:**
- Complete E2E integration testing (currently 49 tests skipped)
- Hardware integration for DMX lighting and audio control
- Kafka async messaging verification
- Milvus vector search implementation

---

**Project Chimera** - An AI-powered live theatre platform for universities worldwide.

For questions, support, or to get involved, please [open an issue](https://github.com/ranjrana2012-lab/project-chimera/issues) or [start a discussion](https://github.com/ranjrana2012-lab/project-chimera/discussions).

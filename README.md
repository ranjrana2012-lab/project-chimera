# Project Chimera

> An AI-powered live theatre platform creating performances that adapt in real-time to audience input.

![Version](https://img.shields.io/badge/version-0.4.0-blue)
![Status](https://img.shields.io/badge/status-alpha-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)

## Overview

Project Chimera is an open-source, student-run Dynamic Performance Hub that uses AI to generate live theatre experiences. The system combines multiple AI agents with stage automation to create responsive, audience-driven performances for universities and theatre companies worldwide.

### What Makes Project Chimera Unique?

- **Real-Time Adaptation** - Performances change based on audience sentiment and input
- **Multi-Agent AI** - Specialized agents for dialogue, captioning, translation, and more
- **Safety First** - Multi-layer content moderation with human oversight
- **Accessible** - Built-in captioning and British Sign Language translation
- **Open Source** - Free for universities and educational institutions

## Key Components

### AI Agents

- **OpenClaw Orchestrator** - Central control plane coordinating all agents
- **SceneSpeak Agent** - Real-time dialogue generation using local LLMs
- **Captioning Agent** - Live speech-to-text with accessibility descriptions
- **BSL-Text2Gloss Agent** - British Sign Language gloss notation translation
- **Sentiment Agent** - Audience sentiment analysis enhanced with WorldMonitor global intelligence for context-enriched responses
- **Lighting Control** - DMX/OSC stage automation
- **Safety Filter** - Multi-layer content moderation
- **Operator Console** - Human oversight and approval interface

### Quality Platform

- **Chimera Quality Platform** - Unified testing and quality infrastructure
  - Test Orchestrator (port 8008) - Test discovery and execution
  - Dashboard Service (port 8009) - Real-time visualization
  - CI/CD Gateway (port 8010) - GitHub/GitLab integration

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

- **Framework:** FastAPI (Python 3.10+)
- **Orchestration:** Kubernetes (k3s)
- **Messaging:** Apache Kafka
- **Caching:** Redis
- **Vector DB:** Milvus
- **Monitoring:** Prometheus + Grafana + Jaeger
- **AI/ML:** PyTorch, Transformers, OpenAI Whisper, Meta MusicGen

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
git clone https://github.com/project-chimera/project-chimera.git
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

For manual setup or custom configurations, see the [Deployment Guide](docs/reference/runbooks/deployment.md).

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
- 8 Core Services (ports 8000-8007)
- Infrastructure: Redis, Kafka, Prometheus, Jaeger, Grafana

See [Docker Compose Guide](DOCKER.md) for detailed documentation.

### Check Status

```bash
make bootstrap-status
```

## Documentation

### For Students and Developers

- [Quick Start Guide](docs/getting-started/quick-start.md) - Set up your development environment
- [Student Roles](docs/getting-started/roles.md) - Component ownership details
- [Communication Channels](docs/getting-started/communication-channels.md) - Slack/Discord guide
- [Office Hours](docs/getting-started/office-hours.md) - Support schedule
- [Student FAQ](docs/getting-started/faq.md) - Frequently asked questions
- [Sprint Definitions](docs/getting-started/sprint-definitions.md) - 15 sprint overview
- [Evaluation Criteria](docs/getting-started/evaluation-criteria.md) - Grading information
- [Monday Demo Info](docs/getting-started/monday-demo/) - Demo preparation
- [GitHub Workflow](docs/guides/github-workflow.md) - GitHub automation and trust system
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [Development Guide](docs/DEVELOPMENT.md) - Development workflow and coding standards

### Technical Documentation

- [Architecture Overview](docs/reference/architecture.md) - System architecture and design
- [API Documentation](docs/reference/api.md) - Complete API reference for all services
- [Deployment Guide](docs/reference/runbooks/deployment.md) - Deployment scenarios and procedures

### Services Documentation

- [Core Services](docs/services/core-services.md) - 8 AI agents overview
- [Music Generation Platform](docs/services/music-generation.md) - Music generation services
- [Quality Platform](docs/services/quality-platform.md) - Testing infrastructure

### Operational Documentation

- [Monitoring Runbook](docs/reference/runbooks/monitoring.md) - Monitoring and alerting setup
- [Incident Response](docs/reference/runbooks/incident-response.md) - Handling incidents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OpenClaw Orchestrator                      │
│              (Central Control Plane)                        │
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
├── services/         # Microservices (8 agents)
├── skills/           # OpenClaw skill definitions
├── models/           # Prompts, LoRA adapters, evaluation
├── configs/          # Policies, retention, alerts
├── scripts/          # Setup, operations, training
├── tests/            # Test suite (unit, integration, load)
├── docs/             # Documentation
├── platform/         # Chimera Quality Platform
│   ├── orchestrator/ # Test orchestration
│   ├── dashboard/    # Quality dashboards
│   ├── ci_gateway/   # CI/CD integration
│   └── shared/       # Shared utilities
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

Project Chimera includes multiple safety layers:

1. **Input Validation** - All inputs validated at API boundaries
2. **Content Filtering** - Word-based + ML-based filtering
3. **Human Oversight** - Operator approval for critical actions
4. **Audit Logging** - All actions logged for review
5. **Accessibility** - Built-in captioning and BSL translation

## Contributing

We welcome contributions from students, researchers, and theatre professionals!

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Community

- **GitHub:** https://github.com/project-chimera/project-chimera
- **Issues:** https://github.com/project-chimera/project-chimera/issues
- **Discussions:** https://github.com/project-chimera/project-chimera/discussions

## License

MIT License - see [LICENSE](LICENSE) for details.

## Team

Project Chimera is maintained by university students and faculty:

- **Technical Lead** - Architecture and technical direction
- **AI/ML Specialist** - Machine learning and model training
- **Infrastructure Engineer** - Kubernetes and deployment
- **Frontend Developer** - User interfaces and experiences
- **QA/Accessibility Specialist** - Quality and accessibility

## Acknowledgments

Project Chimera is built on open-source technologies and would not be possible without:

- FastAPI and the Python ecosystem
- Kubernetes and k3s
- The open-source AI/ML community
- University theatre programs worldwide

## Roadmap

### v0.4.0 (Current - March 2026)

- WorldMonitor integration for enhanced sentiment analysis
- Global context enrichment for real-time audience feedback
- WebSocket-based context streaming
- Category-based event filtering

### v0.5.0 (Planned)

- Complete service fixes (Captioning, BSL, Safety)
- Multi-scene support
- Enhanced accessibility features

### v1.0.0 (Future)

- Production-ready deployment
- Cloud deployment guides
- Public performances

---

**Project Chimera** - An AI-powered live theatre platform for universities worldwide.

For questions, support, or to get involved, please [open an issue](https://github.com/project-chimera/project-chimera/issues) or [start a discussion](https://github.com/project-chimera/project-chimera/discussions).

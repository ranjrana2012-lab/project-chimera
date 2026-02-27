# Project Chimera

> An AI-powered live theatre platform that creates performances adapting in real-time to audience input.

**Version:** 0.1.0
**Status:** Alpha Development

## Overview

Project Chimera is a student-run Dynamic Performance Hub that uses AI to generate live theatre experiences. The system combines multiple AI agents with stage automation to create responsive, audience-driven performances.

### Key Components

- **OpenClaw Orchestrator** - Central control plane coordinating all agents
- **SceneSpeak Agent** - Real-time dialogue generation using local LLMs
- **Captioning Agent** - Live speech-to-text with accessibility descriptions
- **BSL-Text2Gloss Agent** - British Sign Language gloss notation translation
- **Sentiment Agent** - Audience sentiment analysis from social media
- **Lighting Control** - DMX/OSC stage automation
- **Safety Filter** - Multi-layer content moderation
- **Operator Console** - Human oversight and approval interface

## Quick Start

### Prerequisites

- Linux (Ubuntu 22.04 recommended)
- Python 3.10 or later
- Docker
- kubectl
- NVIDIA GPU (optional, for OpenClaw and SceneSpeak)

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

For detailed setup instructions, see [Student Quick Start Guide](Student_Quick_Start.md).

### Manual Setup

See [Bootstrap Setup Guide](docs/runbooks/bootstrap-setup.md) for manual setup steps.

### Check Status

```bash
make bootstrap-status
```

## Documentation

### For Students

- [Student Quick Start Guide](Student_Quick_Start.md) - Setup your development environment
- [Student Role Assignments](docs/STUDENT_ROLES.md) - Component ownership details

### Technical Documentation

- [Technical Requirements](TRD_Project_Chimera.md)
- [Implementation Documentation](docs/plans/IMPLEMENTATION_DOCUMENTATION.md) - How the scaffold was built
- [Architecture Decisions](docs/architecture/)
- [API Documentation](docs/api/)
- [Operational Runbooks](docs/runbooks/)
- [Backlog](Backlog_Project_Chimera.md)

## Project Structure

```
project-chimera/
├── infrastructure/    # Kubernetes manifests and infrastructure
├── services/         # Microservices
├── skills/           # OpenClaw skill definitions
├── models/           # Prompts, LoRA adapters, evaluation
├── configs/          # Policies, retention, alerts
├── scripts/          # Setup, operations, training
├── tests/            # Test suite
└── docs/             # Documentation
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

## Contributing

This is a student project. Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Team

- Technical Lead
- AI/ML Specialist
- Infrastructure Engineer
- Frontend Developer
- QA/Accessibility Specialist

---

**Project Chimera** © 2026 University Technical Theatre Team

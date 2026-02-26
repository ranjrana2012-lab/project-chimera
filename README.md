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

- Python 3.10 or later
- Docker and Docker Compose
- Kubernetes cluster (k3s recommended for local)
- NVIDIA GPU (for OpenClaw and SceneSpeak)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/project-chimera/project-chimera.git
   cd project-chimera
   ```

2. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start local development stack**
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```

5. **Run tests**
   ```bash
   make test
   ```

### Kubernetes Deployment

1. **Build Docker images**
   ```bash
   make build-all
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -k infrastructure/kubernetes/overlays/dev
   ```

3. **Check deployment status**
   ```bash
   kubectl get pods -n live
   kubectl get pods -n shared
   ```

## Documentation

- [Technical Requirements](docs/trd/TRD_Project_Chimera.md)
- [Architecture Decisions](docs/architecture/)
- [API Documentation](docs/api/)
- [Operational Runbooks](docs/runbooks/)

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

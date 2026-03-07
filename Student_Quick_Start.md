# Student Quick Start Guide - Project Chimera

**Version:** 1.0.0
**Last Updated:** March 2026
**Target Audience:** New students joining Project Chimera

---

## Table of Contents

1. [Welcome to Project Chimera](#welcome-to-project-chimera)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Starting the System](#starting-the-system)
5. [Understanding the Architecture](#understanding-the-architecture)
6. [Common Development Tasks](#common-development-tasks)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Port Reference](#port-reference)
10. [Getting Help](#getting-help)

---

## Welcome to Project Chimera

Project Chimera is a dynamic performance hub that orchestrates multiple AI agents to create interactive theatrical experiences. This guide will help you get started quickly.

### What You'll Be Working With

- **AI Agents**: SceneSpeak, Captioning, BSL (British Sign Language), Sentiment Analysis
- **Platform Services**: Orchestrator, Lighting/Sound/Music, Safety Filter, Operator Console
- **Tech Stack**: Python, FastAPI, Docker, Redis, Kafka, Milvus Vector DB
- **Monitoring**: Prometheus, Grafana, Jaeger

---

## Prerequisites

### Hardware Requirements

- **Minimum**: 8GB RAM, 20GB free disk space
- **Recommended**: 16GB RAM, 50GB free disk space
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional but recommended)

### Software Requirements

#### Linux (Ubuntu/Debian)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y git curl wget vim build-essential

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA drivers (if you have GPU)
sudo apt-get install -y nvidia-driver-535
```

#### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop
open /Applications/Docker.app

# Install Python 3.11+
brew install python@3.11
```

#### Verify Installation

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version

# Check Git
git --version

# Check GPU (if applicable)
nvidia-smi
```

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/project-chimera.git
cd project-chimera

# Check current branch
git branch
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env

# Minimum required settings:
# - GPU setup (if available)
# - API keys (if using external services)
```

### 3. Download Models

```bash
# Run model download script
python scripts/download-models.sh

# Or download manually for each service
docker-compose run --rm scenespeak-agent python -c "from transformers import AutoModel; AutoModel.from_pretrained('gpt-2')"
```

### 4. Build Services

```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build scenespeak-agent

# This may take 10-20 minutes on first build
```

---

## Starting the System

### Start All Services

```bash
# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Verify Services are Running

```bash
# Quick health check
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8011; do
    echo "Checking port $port..."
    curl -s http://localhost:$port/health && echo "✓ Healthy" || echo "✗ Unhealthy"
done
```

### Access Service Documentation

```
Orchestrator:    http://localhost:8000/docs
SceneSpeak:      http://localhost:8001/docs
Captioning:      http://localhost:8002/docs
BSL:             http://localhost:8003/docs
Sentiment:       http://localhost:8004/docs
Lighting:        http://localhost:8005/docs
Safety:          http://localhost:8006/docs
Console:         http://localhost:8007
Grafana:         http://localhost:3000
Prometheus:      http://localhost:9090
Jaeger:          http://localhost:16686
```

---

## Understanding the Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Operator Console                        │
│                    (Dashboard + Oversight)                   │
└────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │ OpenClaw         │
                    │ Orchestrator     │
                    │ (Port 8000)      │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌─────▼──────┐    ┌─────▼──────┐
    │SceneSpeak│        │ Sentiment  │    │  Music     │
    │  Agent   │        │  Agent     │    │ Generation │
    │ (8001)   │        │  (8004)    │    │  (8011)    │
    └────┬─────┘        └─────┬──────┘    └────────────┘
         │                   │
    ┌────▼────┐        ┌─────▼──────┐
    │Captioning│       │    BSL     │
    │ Agent   │        │   Agent    │
    │ (8002)  │        │  (8003)    │
    └─────────┘        └────────────┘
```

### Key Components

#### OpenClaw Orchestrator (Port 8000)
- **Purpose**: Central coordinator for all agents
- **Key Features**: Skill routing, event management, state management
- **Documentation**: [services/openclaw-orchestrator/README.md](services/openclaw-orchestrator/README.md)

#### SceneSpeak Agent (Port 8001)
- **Purpose**: Generate dialogue for theatrical performances
- **Key Features**: LLM-based text generation, character personality
- **Documentation**: [services/scenespeak-agent/README.md](services/scenespeak-agent/README.md)

#### Captioning Agent (Port 8002)
- **Purpose**: Convert speech to text in real-time
- **Key Features**: Whisper model integration, streaming support
- **Documentation**: [services/captioning-agent/README.md](services/captioning-agent/README.md)

#### BSL Agent (Port 8003)
- **Purpose**: Generate British Sign Language glosses
- **Key Features**: Text-to-sign translation, avatar rendering
- **Documentation**: [services/bsl-agent/README.md](services/bsl-agent/README.md)

#### Sentiment Agent (Port 8004)
- **Purpose**: Analyze audience sentiment
- **Key Features**: ML-based sentiment classification, real-time analysis
- **Documentation**: [services/sentiment-agent/README.md](services/sentiment-agent/README.md)

#### Lighting/Sound/Music Service (Port 8005)
- **Purpose**: Control stage lighting and sound
- **Key Features**: DMX/sACN control, audio playback
- **Documentation**: [services/lighting-sound-music/README.md](services/lighting-sound-music/README.md)

#### Safety Filter (Port 8006)
- **Purpose**: Moderate content for safety
- **Key Features**: Multi-layer filtering, configurable rules
- **Documentation**: [services/safety-filter/README.md](services/safety-filter/README.md)

#### Operator Console (Port 8007)
- **Purpose**: Dashboard for operators
- **Key Features**: WebSocket monitoring, control interface
- **Documentation**: [services/operator-console/README.md](services/operator-console/README.md)

---

## Common Development Tasks

### Test an API Endpoint

```bash
# Get health status
curl http://localhost:8000/health

# Generate dialogue
curl -X POST http://localhost:8001/api/v1/dialogue \
  -H "Content-Type: application/json" \
  -d '{
    "character": "Hamlet",
    "context": "To be or not to be",
    "sentiment": "melancholic"
  }'

# Analyze sentiment
curl -X POST http://localhost:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is absolutely wonderful!"
  }'
```

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f scenespeak-agent

# Last 100 lines
docker-compose logs --tail=100 orchestrator
```

### Restart a Service

```bash
# Restart specific service
docker-compose restart scenespeak-agent

# Rebuild and restart
docker-compose up -d --build scenespeak-agent
```

### Enter a Container

```bash
# Enter bash shell
docker-compose exec scenespeak-agent bash

# Run Python in container
docker-compose exec scenespeak-agent python -c "print('Hello')"

# Check environment
docker-compose exec scenespeak-agent env
```

---

## Testing

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test specific service
pytest services/scenespeak-agent/tests/

# Test specific file
pytest services/scenespeak-agent/tests/test_main.py

# Test specific function
pytest services/scenespeak-agent/tests/test_main.py::test_health
```

### Run Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_orchestrator_flow.py
```

---

## Troubleshooting

### Service Won't Start

**Symptom**: Service exits immediately

**Solutions**:
1. Check port conflicts: `lsof -i :8000-8011`
2. Check logs: `docker-compose logs [service]`
3. Verify .env file exists: `cat .env`
4. Check for GPU issues (if applicable): `nvidia-smi`

### GPU Not Available

**Symptom**: CUDA errors, slow inference

**Solutions**:
1. Verify GPU: `nvidia-smi`
2. Check CUDA: `nvcc --version`
3. Fallback to CPU: Add `DEVICE=cpu` to .env
4. Check Docker GPU support: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

### Model Download Failed

**Symptom**: Service fails on first start

**Solutions**:
1. Check internet connectivity
2. Download manually: `python scripts/download-models.sh`
3. Verify cache permissions: `ls -la ~/.cache/huggingface/`
4. Check disk space: `df -h`

### Docker Build Fails

**Symptom**: docker-compose build errors

**Solutions**:
1. Clear cache: `docker system prune -a`
2. Check disk space: `df -h`
3. Verify architecture (ARM64): `uname -m`
4. Build without cache: `docker-compose build --no-cache`

### Slow Performance

**Symptom**: Services respond slowly

**Solutions**:
1. Check resources: `docker stats`
2. Check GPU usage: `nvidia-smi`
3. Reduce batch size in .env
4. Use CPU fallback if GPU issues

### More Troubleshooting

For more detailed troubleshooting, see:
- [Main Troubleshooting Guide](docs/runbooks/troubleshooting.md)
- [Docker Troubleshooting](docs/runbooks/docker-troubleshooting.md)

---

## Port Reference

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| Orchestrator | 8000 | Central coordinator | `/health` |
| SceneSpeak | 8001 | Dialogue generation | `/health` |
| Captioning | 8002 | Speech-to-text | `/health` |
| BSL | 8003 | Sign language gloss | `/health` |
| Sentiment | 8004 | Sentiment analysis | `/health` |
| Lighting | 8005 | Stage automation | `/health` |
| Safety | 8006 | Content moderation | `/health` |
| Console | 8007 | Operator dashboard | `/health` |
| Grafana | 3000 | Metrics visualization | `/api/health` |
| Prometheus | 9090 | Metrics collection | `/-/healthy` |
| Jaeger | 16686 | Distributed tracing | `/` |

---

## Common Commands Cheat Sheet

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart [service-name]

# View logs
docker-compose logs -f [service-name]

# Check status
docker-compose ps
```

### Development

```bash
# Create feature branch
git checkout -b feature/[name]

# Run tests
pytest

# Format code
black services/

# Lint code
pylint services/

# Build and start
docker-compose up -d --build
```

### Troubleshooting

```bash
# Check ports
lsof -i :8000

# Check GPU
nvidia-smi

# Check disk space
df -h

# Check Docker stats
docker stats

# Clean Docker cache
docker system prune -a
```

---

## Getting Help

### Documentation

- **Main Documentation**: [docs/README.md](docs/README.md)
- **Architecture**: [docs/architecture/README.md](docs/architecture/README.md)
- **API Documentation**: [docs/api/README.md](docs/api/README.md)
- **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Quick Reference

- **Commands**: [docs/getting-started/quick-reference.md](docs/getting-started/quick-reference.md)
- **Troubleshooting**: [docs/runbooks/troubleshooting.md](docs/runbooks/troubleshooting.md)
- **Docker Issues**: [docs/runbooks/docker-troubleshooting.md](docs/runbooks/docker-troubleshooting.md)

### Community Support

- **GitHub Issues**: [github.com/your-org/project-chimera/issues](https://github.com/your-org/project-chimera/issues)
- **Discussions**: [github.com/your-org/project-chimera/discussions](https://github.com/your-org/project-chimera/discussions)
- **Slack**: #project-chimera channel

### Office Hours

- **Schedule**: Check [docs/getting-started/office-hours.md](docs/getting-started/office-hours.md)
- **Location**: Zoom link in team calendar
- **Format**: Open Q&A and code review

---

## Next Steps

1. **Explore the Architecture**: Read [docs/architecture/diagrams.md](docs/architecture/diagrams.md)
2. **Set Up Your Development Environment**: Follow [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
3. **Pick Your First Task**: Check GitHub issues labeled `good-first-issue`
4. **Join the Team**: Introduce yourself in the #project-chimera Slack channel
5. **Attend Standups**: Join daily standups to sync with the team

---

## Additional Resources

### Learning Resources

- **FastAPI**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **Docker**: [https://docs.docker.com/get-started/](https://docs.docker.com/get-started/)
- **Python Async**: [https://docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)
- **Pytest**: [https://docs.pytest.org/](https://docs.pytest.org/)

### Project Resources

- **Project Board**: [GitHub Projects](https://github.com/your-org/project-chimera/projects)
- **CI/CD Pipeline**: [GitHub Actions](https://github.com/your-org/project-chimera/actions)
- **Demo Videos**: [docs/demo/](docs/demo/)
- **Architecture Decisions**: [docs/architecture/](docs/architecture/)

---

**Welcome to Project Chimera! We're excited to have you on the team.** 🚀

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Maintainers**: Project Chimera Team

# Project Chimera - Developer Onboarding Guide

**Version:** 1.0.0
**Last Updated:** April 9, 2026
**Target Audience:** New developers joining Project Chimera

---

## Welcome to Project Chimera! 🎭

Project Chimera is an AI-powered adaptive live theatre framework that combines emotion detection, adaptive dialogue generation, and hardware control to create responsive theatrical experiences.

This guide will help you get started with the codebase, understand the architecture, and contribute effectively.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Architecture](#architecture)
4. [Codebase Tour](#codebase-tour)
5. [Development Workflow](#development-workflow)
6. [Coding Standards](#coding-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Common Tasks](#common-tasks)
9. [Resources](#resources)

---

## Project Overview

### What is Project Chimera?

Project Chimera creates **adaptive live theatre experiences** by:
- Analyzing audience emotional state using ML (DistilBERT)
- Generating adaptive dialogue responses (GLM-4.7)
- Controlling DMX lighting and audio systems in real-time
- Providing British Sign Language (BSL) translation for accessibility

### Project Phases

**Phase 1** (Complete): Local-First AI Framework
- Proof-of-concept adaptive AI system
- Sentiment analysis and adaptive routing
- Comparison mode (adaptive vs non-adaptive)

**Phase 2** (Foundation Complete): Hardware Integration
- DMX lighting control service
- Audio system control service
- BSL avatar service
- Monitoring and safety features

### Technology Stack

- **Language:** Python 3.12+
- **Web Framework:** FastAPI
- **ML Models:** DistilBERT, GLM-4.7
- **Hardware Protocols:** DMX512
- **Containerization:** Docker, Docker Compose
- **Testing:** pytest, pytest-asyncio
- **Monitoring:** Prometheus, Grafana
- **CI/CD:** GitHub Actions

---

## Development Environment Setup

### Prerequisites

- Python 3.12 or higher
- Git
- Docker (for containerized services)
- Make (optional, for convenience scripts)

### 1. Clone the Repository

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
```

### 2. Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install base dependencies
pip install --upgrade pip
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install Phase 2 services dependencies
pip install -e ".[phase2]"

# Or install everything
pip install -e ".[all]"
```

### 4. Verify Installation

```bash
# Run Phase 1 core
python -m services.operator_console.chimera_core --help

# Run tests
pytest tests/ -v

# Check service health (if services are running)
curl http://localhost:8001/health  # DMX Controller
curl http://localhost:8002/health  # Audio Controller
curl http://localhost:8003/health  # BSL Avatar Service
```

### 5. Configure Environment

Create a `.env` file in the project root:

```bash
# API Keys (for Phase 1)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Service Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development

# Phase 2 Configuration
DMX_UNIVERSE=1
DMX_REFRESH_RATE=44
AUDIO_MAX_VOLUME_DB=-6
```

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Audience Input                          │
│                  (Speech, Sentiment)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Chimera Core (Orchestrator)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Sentiment Analysis (DistilBERT)                       │ │
│  │  ↓                                                      │ │
│  │  Adaptive Routing Engine                                │ │
│  │  ↓                                                      │ │
│  │  Dialogue Generation (GLM-4.7)                         │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼────────┐ ┌──▼──────────┐ ┌▼──────────────┐
│ DMX Controller │ │ Audio       │ │ BSL Avatar    │
│                │ │ Controller  │ │ Service       │
│ - Lighting     │ │ - Volume    │ │ - Translation │
│ - Scenes       │ │ - Tracks    │ │ - Gestures    │
│ - Emergency    │ │ - Mute      │ │ - Avatar      │
└───────┬────────┘ └──┬──────────┘ └▼──────────────┘
        │              │              │
└────────┼──────────────┼──────────────┘
         │              │
    ┌────▼──────────────▼────┐
    │   Hardware Output      │
    │ - Lights               │
    │ - Speakers             │
    │ - Displays (BSL)       │
    └────────────────────────┘
```

### Service Communication

**Phase 1 (Chimera Core):**
- Monolithic architecture for simplicity
- Direct ML model integration
- File-based configuration

**Phase 2 (Hardware Services):**
- Microservices architecture
- REST API communication
- Independent deployment
- Health monitoring

### Data Flow

1. **Input**: Audience speech/text → Sentiment analysis
2. **Processing**: Adaptive routing → Dialogue generation
3. **Output**: Hardware control signals → Physical response
4. **Feedback**: System state → Adaptive adjustments

---

## Codebase Tour

### Directory Structure

```
project-chimera/
├── docs/                           # Documentation
│   ├── DEVELOPER_ONBOARDING_GUIDE.md
│   ├── SECURITY_DOCUMENTATION.md
│   └── DEPLOYMENT_AND_OPERATIONS_GUIDE.md
├── services/
│   ├── operator-console/           # Phase 1: Main orchestrator
│   │   └── chimera_core.py         # Core adaptive logic
│   ├── sentiment-agent/            # Sentiment analysis service
│   ├── openclaw-orchestrator/      # Alternative orchestrator
│   ├── claude-orchestrator/        # Claude-based orchestrator
│   │
│   ├── dmx-controller/             # Phase 2: DMX lighting control
│   │   ├── dmx_controller.py       # Main service
│   │   ├── tests/                  # Service tests
│   │   ├── examples/               # Usage examples
│   │   └── Dockerfile              # Container definition
│   │
│   ├── audio-controller/           # Phase 2: Audio control
│   │   ├── audio_controller.py     # Main service
│   │   ├── tests/
│   │   ├── examples/
│   │   └── Dockerfile
│   │
│   └── bsl-avatar-service/         # Phase 2: BSL translation
│       ├── bsl_avatar_service.py   # Main service
│       ├── tests/
│       ├── examples/
│       └── Dockerfile
│
├── tests/
│   ├── integration/                # Integration tests
│   ├── performance/                # Performance benchmarks
│   └── e2e/                        # End-to-end tests
│
├── monitoring/
│   ├── prometheus.yml              # Prometheus config
│   ├── alerting_rules.yml          # Alert definitions
│   └── grafana/                    # Grafana dashboards
│
├── .github/
│   └── workflows/                  # CI/CD pipelines
│       └── phase2-tests.yml
│
└── pyproject.toml                  # Project configuration
```

### Key Files to Understand

**For Phase 1 Development:**
- `services/operator-console/chimera_core.py` - Core adaptive logic
- `services/sentiment-agent/sentiment_agent/models.py` - ML models
- `services/openclaw-orchestrator/` - Alternative orchestrator

**For Phase 2 Development:**
- `services/dmx-controller/dmx_controller.py` - Lighting control
- `services/audio-controller/audio_controller.py` - Audio control
- `services/bsl-avatar-service/bsl_avatar_service.py` - BSL translation

**For Testing:**
- `tests/integration/test_phase2_integration.py` - Service integration
- `tests/performance/benchmark_phase2.py` - Performance benchmarks

---

## Development Workflow

### 1. Branch Strategy

```bash
# Main branch (stable)
main

# Feature branches
feature/your-feature-name
fix/bug-fix-name
hotfix/critical-fix

# Example
git checkout -b feature/add-new-lighting-scene
```

### 2. Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and test
pytest tests/ -v

# 3. Commit changes
git add .
git commit -m "feat: add new lighting scene feature"

# 4. Push to remote
git push origin feature/my-feature

# 5. Create pull request
gh pr create --title "Add new lighting scene feature"
```

### 3. Code Review Process

1. **Self-Review**: Review your own changes first
2. **Automated Checks**: Ensure CI/CD passes
3. **Peer Review**: Request review from team member
4. **Address Feedback**: Make requested changes
5. **Approval**: Merge after approval

### 4. Testing Before Commit

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html

# Run specific test
pytest tests/integration/test_phase2_integration.py -v

# Run performance benchmarks
python tests/performance/benchmark_phase2.py
```

---

## Coding Standards

### Python Style Guide

Follow PEP 8 with these exceptions:

**Line Length:**
- Preferred: 88 characters (Black default)
- Maximum: 100 characters

**Imports:**
```python
# Standard library
import os
import sys
from dataclasses import dataclass

# Third-party
import pytest
from fastapi import FastAPI

# Local imports
from services.dmx_controller import DMXController
```

**Naming Conventions:**
```python
# Classes: PascalCase
class DMXController:
    pass

# Functions/Variables: snake_case
def calculate_volume_level():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_VOLUME_DB = -6

# Private: _leading_underscore
def _internal_function():
    pass
```

### Documentation Standards

**Docstrings (Google Style):**
```python
def calculate_adaptive_response(
    sentiment_score: float,
    context: Dict[str, Any],
) -> str:
    """Calculate adaptive response based on sentiment.

    Args:
        sentiment_score: Audience sentiment score (-1.0 to 1.0)
        context: Additional context for response generation

    Returns:
        Adaptive dialogue response text

    Raises:
        ValueError: If sentiment_score is out of range
    """
    if not -1.0 <= sentiment_score <= 1.0:
        raise ValueError("Sentiment score must be between -1.0 and 1.0")
    # Implementation...
```

**Comments:**
- Use comments to explain **why**, not **what**
- Keep comments up-to-date
- Use TODO/FIXME for temporary notes

```python
# Good: Explains why
# Using exponential backoff to prevent API rate limiting
time.sleep(2 ** attempt)

# Bad: Obvious
# Increment counter
counter += 1
```

### Error Handling

```python
# Specific exceptions
try:
    result = api_call()
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    # Handle connection error
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    # Handle value error
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    # Handle unexpected error

# Always provide context
raise ValueError(f"Invalid channel value: {value}. Must be 0-255")
```

### Type Hints

```python
from typing import List, Dict, Optional, Union

def process_fixtures(
    fixtures: List[Fixture],
    config: Dict[str, Any],
    dry_run: bool = False,
) -> Optional[Dict[str, Any]]:
    """Process fixtures with optional dry run."""
    pass
```

---

## Testing Guidelines

### Test Organization

```
tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests (slower, real components)
├── performance/       # Performance benchmarks
└── e2e/              # End-to-end tests (slowest, full system)
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
from services.dmx_controller import DMXController, Fixture

class TestDMXController:
    """Test DMX Controller functionality."""

    @pytest.fixture
    def controller(self):
        """Create test controller instance."""
        return DMXController(universe=1, refresh_rate=44)

    @pytest.fixture
    def sample_fixture(self):
        """Create sample fixture for testing."""
        return Fixture(
            id="test_fixture",
            name="Test Fixture",
            start_address=1,
            channel_count=3,
        )

    def test_add_fixture(self, controller, sample_fixture):
        """Test adding fixture to controller."""
        controller.add_fixture(sample_fixture)
        assert "test_fixture" in controller.fixtures
        assert controller.fixture_count == 1

    def test_emergency_stop(self, controller, sample_fixture):
        """Test emergency stop functionality."""
        controller.add_fixture(sample_fixture)
        controller.emergency_stop()
        assert controller.state == ControllerState.EMERGENCY_STOP
```

### Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Critical paths covered
- **E2E Tests**: Main user flows covered

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=services --cov-report=html

# Specific test file
pytest tests/dmx_controller/tests/test_dmx_controller.py -v

# Specific test
pytest tests/ -k "test_emergency_stop" -v
```

---

## Common Tasks

### Adding a New Service

1. **Create service directory:**
```bash
mkdir services/new-service
cd services/new-service
```

2. **Create service file:**
```python
# new_service.py
from fastapi import FastAPI

app = FastAPI(title="New Service")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

3. **Create tests:**
```python
# tests/test_new_service.py
import pytest
from fastapi.testclient import TestClient
from new_service import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
```

4. **Add Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8004
CMD ["uvicorn", "new_service:app", "--host", "0.0.0.0", "--port", "8004"]
```

### Adding Monitoring to a Service

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter(
    'service_requests_total',
    'Total requests',
    ['method', 'endpoint']
)

request_duration = Histogram(
    'service_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest())

# Use in endpoints
@app.get("/api/endpoint")
async def endpoint():
    with request_duration.labels('GET', '/api/endpoint').time():
        request_count.labels('GET', '/api/endpoint').inc()
        # Your code here
```

### Debugging Tips

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use Python debugger:**
```python
import pdb; pdb.set_trace()
```

**Check service logs:**
```bash
docker-compose logs -f service-name
```

**Test API endpoints:**
```bash
curl http://localhost:8001/api/status
curl -X POST http://localhost:8002/api/emergency_mute
```

---

## Resources

### Documentation

- **Project README**: `README.md`
- **API Documentation**: See individual service READMEs
- **Security Guide**: `docs/SECURITY_DOCUMENTATION.md`
- **Deployment Guide**: `docs/DEPLOYMENT_AND_OPERATIONS_GUIDE.md`

### Internal Resources

- **Code Examples**: `services/*/examples/`
- **Test Examples**: `tests/*/`
- **Configuration Templates**: `services/docker-compose.*.yml`

### External Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pytest Docs**: https://docs.pytest.org/
- **Docker Docs**: https://docs.docker.com/
- **Prometheus Docs**: https://prometheus.io/docs/

### Getting Help

1. **Check documentation first** - Most answers are in the docs
2. **Search existing issues** - Someone may have solved it
3. **Ask in team chat** - For quick questions
4. **Create GitHub issue** - For bugs or feature requests

---

## Next Steps

1. **Set up your environment** (see above)
2. **Read the code** - Start with `chimera_core.py`
3. **Run the tests** - Familiarize yourself with test patterns
4. **Make a small change** - Fix a typo or add a simple feature
5. **Contribute** - Submit your first pull request!

---

## Welcome Aboard! 🚀

We're excited to have you join Project Chimera. Remember:
- Start small and iterate
- Ask questions when stuck
- Test your changes thoroughly
- Document your code
- Have fun creating adaptive theatre experiences!

**Quick Reference:**
- Tests: `pytest tests/ -v`
- Format: `black .`
- Lint: `ruff check .`
- Type check: `mypy .`

---

**Questions?** Don't hesitate to reach out to the team!

*Last Updated: April 9, 2026*

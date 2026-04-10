# Project Chimera Development Guide

This guide covers setting up a development environment and contributing to Project Chimera.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Workflow](#development-workflow)
- [Code Organization](#code-organization)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)

## Quick Start

### Fastest Path to Hacking

```bash
# Clone and bootstrap
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera
make bootstrap

# Start developing
make dev
```

This sets up a complete development environment with all services running locally.

## Prerequisites

### Required Software

- **Python:** 3.12 or later (tested with 3.12+)
- **Git:** 2.30+
- **Docker:** 24.0+
- **Docker Compose:** 2.20+
- **pytest:** 7.0+ (for testing)

### Recommended Tools

- **IDE:** VS Code with Python extension
- **Code Formatting:** Black, Ruff
- **Type Checking:** MyPy
- **Testing:** Pytest

### Optional (for full features)

- **NVIDIA GPU:** With CUDA 12.x
- **Poetry:** For dependency management
- **pre-commit:** For git hooks

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera
```

### 2. Create Virtual Environment

```bash
# Using venv
python3 -m venv .venv
source .venv/bin/activate

# Or using poetry (if installed)
poetry install
```

### 3. Install Dependencies

```bash
# Install base dependencies
make install-deps

# Or manually
pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

Key settings to configure:

```bash
# Enable development features
APP_ENV=development
APP_DEBUG=true

# GPU support (if available)
OPENCLAW_GPU_ENABLED=true
SCENESPEAK_GPU_ENABLED=true

# Development ports
OPENCLAW_PORT=8000
SCENESPEAK_PORT=8001
```

### 5. Start Development Environment

```bash
# Start all services
make dev

# Or start specific service
cd services/openclaw-orchestrator
python -m src.main
```

### 6. Verify Setup

```bash
# Check all services are running
make bootstrap-status

# Test API
curl http://localhost:8000/health/live
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code following our [coding standards](#coding-standards).

### 3. Test Locally

```bash
# Run tests
make test

# Run linter
make lint

# Format code
make format
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Organization

### Directory Structure

```
project-chimera/
├── services/                       # Microservices
│   ├── nemoclaw-orchestrator/      # Core orchestrator (port 8000)
│   ├── scenespeak-agent/           # Scene description (port 8001)
│   ├── sentiment-agent/            # BETTAfish/MIROFISH models (port 8004)
│   ├── safety-filter/              # Content moderation (port 8006)
│   ├── operator-console/           # Human oversight (port 8007)
│   ├── music-generation/           # Audio generation (port 8011)
│   ├── health-aggregator/          # Service polling (port 8012)
│   ├── dashboard/                  # Health monitoring UI (port 8013)
│   ├── echo-agent/                 # I/O relay (port 8014) ✅ NEW
│   ├── translation-agent/          # Translation (port 8006) ✅ NEW
│   ├── shared/                     # Shared modules (resilience, tracing, etc.)
│   └── orchestration/              # Orchestration patterns
├── tests/                          # Test suite (594 tests passing)
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── resilience/                 # Resilience pattern tests
├── docs/                           # Documentation
├── docker-compose.yml              # Full stack deployment
└── scripts/                        # Utility scripts
```

### Service Structure

Each service follows a consistent structure:

```
service-name/
├── src/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration
│   ├── models/              # Pydantic models
│   ├── core/                # Business logic
│   └── routes/              # API routes
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_core.py
│   └── test_routes.py
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

### Adding a New Service

1. Create service directory
2. Add base structure
3. Implement models and routes
4. Add tests
5. Create Dockerfile
6. Add to infrastructure manifests
7. Update documentation

## Testing

### Test Structure

Tests are organized by type:

```
tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests (slower, real deps)
├── load/              # Load tests (performance)
├── red-team/          # Security tests
└── accessibility/     # Accessibility tests
```

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=services --cov-report=html

# Current test status (April 10, 2026)
# 594 tests passing ✅
# 0 tests failing ✅
# 81% code coverage ✅
# 83 tests skipped (require running services)
```

### Test Coverage Targets

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| Shared modules | 80% | 81% | ✅ Exceeded |
| Services | 75% | TBD | In Progress |
| Overall | 80% | 81% | ✅ Target Met |

### Writing Tests

```python
# tests/unit/services/test_scenespeak_agent.py

import pytest
from services.scenespeak_agent.core import LLMEngine


class TestLLMEngine:
    """Test suite for LLMEngine."""

    @pytest.fixture
    def engine(self, mock_model):
        """Create test engine with mocked model."""
        return LLMEngine(model_path="test-model")

    @pytest.mark.asyncio
    async def test_generate_dialogue(self, engine):
        """Test dialogue generation."""
        result = await engine.generate(
            prompt="Hello",
            max_tokens=10
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_invalid_input(self, engine):
        """Test with invalid input."""
        with pytest.raises(ValueError):
            engine.generate("", max_tokens=10)
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_function():
    """Unit test."""

@pytest.mark.integration
def test_integration():
    """Integration test."""

@pytest.mark.red_team
def test_security():
    """Security test."""

@pytest.mark.accessibility
def test_accessibility():
    """Accessibility test."""
```

## Debugging

### Local Service Debugging

#### Using VS Code

1. Install Python extension
2. Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
      ],
      "cwd": "${workspaceFolder}/services/openclaw-orchestrator",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

#### Using pdb

```python
import pdb; pdb.set_trace()  # Set breakpoint
```

Or use ipdb for better experience:

```bash
pip install ipdb
```

### Kubernetes Debugging

#### Port Forward to Local

```bash
# Forward service port
kubectl port-forward -n live svc/SceneSpeak Agent 8001:8001

# Now debug locally
curl http://localhost:8001/health/live
```

#### Debug Running Pods

```bash
# Get shell in pod
kubectl exec -it -n live deployment/SceneSpeak Agent -- bash

# View logs
kubectl logs -f -n live deployment/SceneSpeak Agent

# View logs for all containers
kubectl logs -f -n live <pod-name> --all-containers=true
```

### Common Debugging Commands

```bash
# Check service connectivity
kubectl get pods -n live
kubectl get svc -n live
kubectl describe pod <pod-name> -n live

# Check resource usage
kubectl top pods -n live
kubectl top nodes

# Check events
kubectl get events -n live --sort-by='.lastTimestamp'
```

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:

- **Line length:** 100 characters
- **Imports:** Grouped (stdlib, third-party, local)
- **Docstrings:** Google style
- **Type hints:** Required for all functions

### Code Formatting

```bash
# Format code
make format

# Check formatting
make lint
```

### Commit Messages

Use conventional commits:

```
feat: add new dialogue caching mechanism
fix: handle empty input in captioning service
docs: update API documentation
refactor: simplify LLM engine interface
test: add tests for sentiment analysis
```

### Code Review Checklist

- [ ] Tests pass locally
- [ ] Code is formatted
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No sensitive data included

## Common Tasks

### Adding a New API Endpoint

```python
# services/your-service/src/routes/new_feature.py

from fastapi import APIRouter
from ..models.request import NewRequest
from ..models.response import NewResponse

router = APIRouter(prefix="/v1/new-feature", tags=["new-feature"])

@router.post("/action", response_model=NewResponse)
async def new_action(request: NewRequest):
    """Description of endpoint."""
    # Implementation
    pass
```

### Adding a New Service

1. Create service structure
2. Add models in `src/models/`
3. Add core logic in `src/core/`
4. Add routes in `src/routes/`
5. Create `src/main.py`
6. Add tests
7. Create Dockerfile
8. Add to infrastructure

### Testing Locally with Kubernetes

```bash
# Build local image
docker build -t chimera-test:local services/your-service

# Load into k3s
kubectl image load chimera-test:local

# Deploy test pod
kubectl run test-pod --image=chimera-test:local -n live
```

### Working with Skills

Skills are defined in the `skills/` directory. Each skill has:

```
skills/skill-name/
├── SKILL.md              # Skill documentation
├── skill.py              # Skill implementation
└── requirements.txt      # Skill dependencies
```

### Adding Monitoring

Add Prometheus metrics:

```python
from prometheus_client import Counter, Histogram

request_counter = Counter(
    'requests_total',
    'Total requests',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration'
)
```

### ML Model Integration

**Sentiment Agent** uses BETTAfish and MIROFISH models:

```python
# services/sentiment-agent/src/sentiment_agent/core.py

from transformers import pipeline

# BETTAfish model for sentiment classification
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="bettafish/sentiment-classifier",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# MIROFISH model for emotion detection
emotion_pipeline = pipeline(
    "text-classification",
    model="mirofish/emotion-detector",
    return_all_scores=True
)
```

For ML model setup, see `services/sentiment-agent/README.md`.

## IDE Setup

### VS Code

Install extensions:
- Python
- Pylance
- Docker
- Kubernetes
- YAML

Recommended settings:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true,
  "editor.rulers": [100]
}
```

### PyCharm

1. Open project as PyCharm project
2. Configure Python interpreter (use venv)
3. Enable Black plugin
4. Configure pytest runner

## Troubleshooting

### Common Development Issues

#### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

#### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Docker Build Failures

```bash
# Clean build
docker system prune -af

# Build without cache
docker build --no-cache -t test:local .
```

---

For more information:
- [Contributing Guidelines](CONTRIBUTING.md)
- [API Documentation](reference/api.md)
- [Architecture Overview](reference/architecture.md)

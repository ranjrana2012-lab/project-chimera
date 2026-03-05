# Development Guide

**Version:** 0.4.0
**Last Updated:** March 2026

---

## Overview

This guide covers development workflows, coding standards, testing practices, and contribution guidelines for Project Chimera.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing Guide](#testing-guide)
6. [Debugging](#debugging)
7. [Contributing](#contributing)
8. [Code Review](#code-review)

---

## Getting Started

### Prerequisites

- **Python:** 3.10 or later
- **Docker:** 20.10+
- **kubectl:** Matching cluster version
- **k3s:** For local development
- **Git:** For version control

### Local Development Setup

#### 1. Clone and Bootstrap

```bash
# Clone the repository
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera

# Run automated bootstrap
make bootstrap
```

#### 2. Install Development Dependencies

```bash
# Install Python development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

#### 3. Verify Setup

```bash
# Check all services are running
make bootstrap-status

# Run tests
make test

# Run linting
make lint
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Docker (ms-azuretools.vscode-docker)
- YAML (redhat.vscode-yaml)
- GitLens (eamodio.gitlens)

Configuration (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

---

## Development Workflow

### Feature Development

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write code following coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test locally:**
   ```bash
   # Run linters
   make lint

   # Run tests
   make test

   # Run type checking
   make mypy
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   gh pr create --title "feat: your feature" --body "Description"
   ```

### Commit Message Conventions

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(scenespeak): add dialogue caching

Add Redis-based caching for generated dialogue to improve
performance and reduce LLM API calls.

Closes #123
```

```
fix(safety): correct pattern matching bug

Fixed bug in safety filter where certain patterns were
not being matched correctly. Added test case.

Fixes #456
```

---

## Project Structure

```
project-chimera/
├── services/                    # Core AI services
│   ├── scenespeak-agent/        # Dialogue generation
│   ├── captioning-agent/        # Speech-to-text
│   ├── bsl-agent/              # BSL translation
│   ├── sentiment-agent/        # Sentiment analysis
│   ├── lighting-service/       # Stage lighting
│   ├── safety-filter/          # Content moderation
│   ├── operator-console/       # Dashboard
│   └── openclaw-orchestrator/  # Central coordinator
├── platform/                    # Platform services
│   ├── monitoring/             # Prometheus, Grafana, AlertManager
│   ├── quality-gate/           # SLO-based deployment gate
│   ├── cicd-gateway/           # GitHub/GitLab integration
│   ├── dashboard/              # Quality dashboard
│   ├── perf-optimizer/         # Performance optimization
│   ├── deployment/             # Helm charts, manifests
│   └── orchestrator/           # OpenClaw skills
├── docs/                       # Documentation
│   ├── api/                    # API documentation
│   ├── architecture/           # Architecture decisions (ADRs)
│   ├── runbooks/               # Operational procedures
│   ├── getting-started/        # Onboarding guides
│   └── observability.md        # Observability overview
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── scripts/                    # Utility scripts
│   ├── bootstrap/              # Setup scripts
│   ├── fix/                    # Documentation fix scripts
│   └── audit/                  # Validation scripts
└── platform/                   # Kubernetes manifests
    ├── monitoring/             # Monitoring stack
    └── deployment/             # Service deployments
```

---

## Coding Standards

### Python Style Guide

Follow PEP 8 with these modifications:

**Line Length:**
- Soft limit: 100 characters
- Hard limit: 120 characters

**Imports:**
```python
# Standard library imports
import asyncio
from dataclasses import dataclass

# Third-party imports
import fastapi
from pydantic import BaseModel

# Local imports
from services.common import config
from services.scenespeak import generator
```

**Naming Conventions:**
```python
# Modules: lowercase_with_underscores
import scenespeak_generator

# Classes: CapWords
class DialogueGenerator:
    pass

# Functions/Variables: lowercase_with_underscores
def generate_dialogue():
    max_length = 100

# Constants: UPPER_CASE_WITH_UNDERSCORES
MAX_TOKENS = 2048
DEFAULT_ADAPTER = "gpt-4"
```

**Type Hints:**
```python
from typing import List, Optional
from pydantic import BaseModel

def generate_dialogue(
    prompt: str,
    adapter: str = "gpt-4",
    max_tokens: Optional[int] = None
) -> DialogueResponse:
    """Generate dialogue from prompt.

    Args:
        prompt: Input prompt for generation
        adapter: LLM adapter to use
        max_tokens: Maximum tokens to generate

    Returns:
        DialogueResponse with generated text and metadata
    """
    pass
```

### API Design

**REST API Conventions:**

```python
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/scenespeak", tags=["scenespeak"])

@router.post("/generate", response_model=DialogueResponse, status_code=status.HTTP_200_OK)
async def generate_dialogue(request: DialogueRequest):
    """Generate dialogue from prompt.

    Raises:
        HTTPException: 400 if request invalid
        HTTPException: 500 if generation fails
    """
    try:
        response = await generator.generate(request.prompt)
        return response
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Endpoint Naming:**
- Use nouns, not verbs: `/api/v1/scenespeak/generate` not `/api/v1/scenespeak/generateDialogue`
- Use plural for collections: `/api/v1/scenespeak/dialogues` not `/api/v1/scenespeak/dialogue`
- Use kebab-case: `/api/v1/slo-compliance` not `/api/v1/sloCompliance`

---

## Testing Guide

### Test Structure

```
tests/
├── unit/                       # Unit tests
│   ├── services/
│   │   ├── scenespeak/
│   │   ├── captioning/
│   │   └── safety/
│   └── platform/
│       ├── monitoring/
│       └── quality-gate/
├── integration/                # Integration tests
│   ├── test_api_endpoints.py
│   └── test_service_integration.py
└── e2e/                        # End-to-end tests
    └── test_full_show_flow.py
```

### Writing Tests

**Unit Tests:**
```python
import pytest
from services.scenespeak.generator import DialogueGenerator

@pytest.fixture
def generator():
    return DialogueGenerator(adapter="test")

def test_generate_dialogue_basic(generator):
    """Test basic dialogue generation."""
    request = DialogueRequest(prompt="Hello world")
    response = generator.generate(request)

    assert response.text is not None
    assert len(response.text) > 0
    assert response.adapter == "test"

@pytest.mark.parametrize("adapter,expected", [
    ("gpt-4", "gpt-4"),
    ("claude", "claude"),
])
def test_adapter_selection(generator, adapter, expected):
    """Test adapter selection."""
    generator.adapter = adapter
    assert generator.adapter == expected
```

**Async Tests:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generate_dialogue_endpoint():
    """Test dialogue generation API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/scenespeak/generate",
            json={"prompt": "Test prompt"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "tokens_used" in data
```

**Integration Tests:**
```python
import pytest
from databases import Database

@pytest.fixture
async def db():
    database = Database("postgresql://test:test@localhost/test_db")
    await database.connect()
    yield database
    await database.disconnect()

@pytest.mark.asyncio
async def test_dialogue_persistence(db):
    """Test dialogue persistence to database."""
    await db.execute("INSERT INTO dialogues ...")
    result = await db.fetch_one("SELECT * FROM dialogues ...")
    assert result is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/services/scenespeak/test_generator.py

# Run with coverage
pytest --cov=services --cov-report=html

# Run only unit tests
pytest tests/unit/ -m "not integration"

# Run only integration tests
pytest tests/integration/ -m "integration"

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Test Coverage

Target coverage levels:
- **Unit tests:** 80%+ coverage
- **Integration tests:** Critical paths covered
- **E2E tests:** Main user flows covered

```bash
# Generate coverage report
pytest --cov=services --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## Debugging

### Local Debugging

**Python Debugger (pdb):**
```python
import pdb; pdb.set_trace()

# Or use ipdb if installed
import ipdb; ipdb.set_trace()
```

**VS Code Debugging:**

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "services.scenespeak.main:app",
        "--host", "localhost",
        "--port", "8001",
        "--reload"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

### Kubernetes Debugging

**Port Forwarding:**
```bash
# Forward service to local port
kubectl port-forward svc/scenespeak-agent 8001:8001 -n live

# Now access at http://localhost:8001
curl http://localhost:8001/health
```

**Remote Debugging:**
```bash
# Exec into container
kubectl exec -it <pod-name> -n live -- /bin/bash

# View logs
kubectl logs <pod-name> -n live --follow

# Check multiple containers in pod
kubectl logs <pod-name> -c container-name -n live --follow
```

### Common Debugging Scenarios

**Service Not Responding:**
1. Check if pod is running: `kubectl get pods -n live`
2. Check pod logs: `kubectl logs <pod-name> -n live`
3. Check service endpoints: `kubectl get endpoints -n live`
4. Port forward and test locally

**High Memory Usage:**
1. Check resource usage: `kubectl top pods -n live`
2. Describe pod for limits: `kubectl describe pod <pod-name> -n live`
3. Check for memory leaks in application logs

**Database Connection Issues:**
1. Check database pod: `kubectl get pods -n database`
2. Test connection: `kubectl run -it --rm debug --image=postgres -- psql -h postgres <dbname>`
3. Check connection string in pod: `kubectl exec -it <pod-name> -- env | grep DATABASE`

---

## Contributing

### Pull Request Process

1. **Fork and branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes:**
   - Follow coding standards
   - Add tests
   - Update documentation

3. **Test thoroughly:**
   ```bash
   make lint
   make test
   ```

4. **Commit with clear message:**
   ```bash
   git commit -m "feat: add your feature"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature
   gh pr create --title "feat: your feature"
   ```

### PR Checklist

Before submitting PR, ensure:

- [ ] Code follows style guide (ruff, black pass)
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts
- [ ] PR description clearly explains changes
- [ ] Linked to relevant issue

### Getting Feedback

**Code Review:** Request review from:
- Component owner (for service-specific changes)
- Technical lead (for architecture changes)
- Documentation team (for doc changes)

**Discussions:** Use GitHub Discussions for:
- Design proposals
- Questions about implementation
- Architecture decisions

---

## Code Review

### Review Criteria

**Code Quality:**
- Follows coding standards
- Clear and readable
- Properly commented (complex logic only)
- No hardcoded values

**Testing:**
- Tests cover new functionality
- Tests cover edge cases
- Tests are well-structured
- Coverage maintained

**Documentation:**
- API docs updated
- README updated if needed
- Runbooks updated for operational changes
- ADR created for architectural decisions

### Review Process

1. **Automated checks pass:**
   - CI/CD pipeline green
   - All tests passing
   - Linting clean

2. **Reviewer feedback:**
   - Address all comments
   - Make requested changes
   - Push updates to branch

3. **Approval and merge:**
   - At least one approval required
   - Auto-merge for trusted contributors
   - Squash merge for clean history

### Review Response Etiquette

- **Be respectful:** Constructive feedback only
- **Be responsive:** Address comments promptly
- **Be grateful:** Reviewers volunteer their time
- **Explain, don't defend:** Help reviewers understand

---

## Additional Resources

- [Contributing Guide](CONTRIBUTING.md) - Contribution guidelines
- [Documentation Contribution Guide](docs/contributing/documentation.md) - Docs-specific guide
- [Testing Guide](docs/runbooks/testing-guide.md) - Comprehensive testing
- [Architecture Documentation](docs/architecture/) - System design
- [API Documentation](docs/api/) - Service APIs

---

**Need help?** Check our [FAQ](docs/getting-started/faq.md) or join [office hours](docs/getting-started/office-hours.md).

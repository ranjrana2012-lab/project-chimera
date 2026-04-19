# Project Chimera - Developer Setup Guide

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.20+ | Service orchestration |
| Python | 3.12+ | Service development |
| Git | 2.30+ | Version control |
| Make | 4.0+ | Build automation |

### Optional Software

| Software | Purpose |
|----------|---------|
| Ollama | Local LLM development |
| VS Code | Recommended IDE |
| Postman | API testing |
| Redis CLI | Cache debugging |

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/Project_Chimera.git
cd Project_Chimera
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env.local

# Edit with your configuration
nano .env.local
```

**Minimum required settings:**
```bash
# Required for SceneSpeak agent
GLM_API_KEY=your_api_key_here  # Get from https://open.bigmodel.cn/

# Optional - for local LLM fallback
LOCAL_LLM_ENABLED=true
LOCAL_LLM_URL=http://host.docker.internal:11434
```

### 3. Start Development Stack

```bash
# Start MVP services
docker compose -f docker-compose.mvp.yml up -d

# Verify services are healthy
./scripts/wait-for-services.sh
./scripts/verify-stack-health.sh
```

### 4. Install Development Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio httpx websockets

# Install pre-commit hooks (if configured)
pip install pre-commit
pre-commit install
```

## Project Structure

```
Project_Chimera/
├── services/                    # Microservices
│   ├── openclaw-orchestrator/   # Core orchestration service
│   ├── scenespeak-agent/        # LLM dialogue agent
│   ├── sentiment-agent/         # Sentiment analysis
│   ├── safety-filter/           # Content moderation
│   ├── translation-agent/       # Translation service
│   ├── operator-console/        # Web UI
│   └── hardware-bridge/         # DMX simulation
├── shared/                      # Shared libraries
│   ├── models/                  # Pydantic models
│   └── resilience/              # Resilience patterns
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   ├── integration/mvp/         # Integration tests
│   └── e2e/                     # E2E tests
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── monitoring/                  # Monitoring configs
└── docker-compose.mvp.yml       # MVP orchestration
```

## Development Workflow

### 1. Make Changes

```bash
# Edit service code
cd services/openclaw-orchestrator
nano main.py
```

### 2. Test Changes

```bash
# Run unit tests
pytest tests/ -v

# Run integration tests
pytest tests/integration/mvp/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### 3. Build & Restart

```bash
# Rebuild specific service
docker compose -f docker-compose.mvp.yml up -d --build openclaw-orchestrator

# View logs
docker compose -f docker-compose.mvp.yml logs -f openclaw-orchestrator
```

### 4. Verify

```bash
# Check health
curl http://localhost:8000/health

# Run full test suite
./scripts/verify-stack-health.sh
```

## Service Development

### Creating a New Service

1. **Create service directory:**
```bash
mkdir services/my-service
cd services/my-service
```

2. **Create basic structure:**
```
my-service/
├── Dockerfile
├── requirements.txt
├── main.py
├── config.py
└── tests/
    └── test_main.py
```

3. **Create Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8010

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
```

4. **Create main.py:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="My Service")

class HealthResponse(BaseModel):
    status: str
    service: str

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", service="my-service")
```

5. **Add to docker-compose.mvp.yml:**
```yaml
my-service:
  build:
    context: .
    dockerfile: services/my-service/Dockerfile
  ports:
    - "8010:8010"
  environment:
    - SERVICE_NAME=my-service
    - PORT=8010
  networks:
    - chimera-backend
  restart: unless-stopped
```

6. **Test service:**
```bash
docker compose -f docker-compose.mvp.yml up -d my-service
curl http://localhost:8010/health
```

## Testing Guidelines

### Unit Tests

```python
# tests/unit/test_my_service.py
import pytest
from services.my_service.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Integration Tests

```python
# tests/integration/mvp/test_my_service.py
import pytest
import httpx

@pytest.fixture
def service_url():
    return "http://my-service:8010"

def test_service_communication(service_url):
    response = httpx.get(f"{service_url}/health")
    assert response.status_code == 200
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit only
pytest tests/unit/ -v

# Integration only
pytest tests/integration/mvp/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific test file
pytest tests/integration/mvp/test_service_communication.py -v

# Specific test
pytest tests/::test_health_check -v
```

## Debugging

### Local Development

```bash
# Run service in debug mode
cd services/openclaw-orchestrator
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With debugger
python -m pdb main.py
```

### Docker Debugging

```bash
# View logs
docker compose -f docker-compose.mvp.yml logs -f openclaw-orchestrator

# Exec into container
docker exec -it chimera-openclaw-orchestrator bash

# Check environment
docker exec chimera-openclaw-orchestrator env

# Test from inside container
docker exec chimera-openclaw-orchestrator curl http://scenespeak-agent:8001/health
```

### Common Issues

**Issue:** Service cannot connect to another service
```bash
# Check network
docker network inspect chimera-backend

# Test DNS resolution
docker exec chimera-openclaw-orchestrator nslookup scenespeak-agent

# Verify service is running
docker compose -f docker-compose.mvp.yml ps scenespeak-agent
```

**Issue:** ML model not loading
```bash
# Check model cache
docker exec chimera-sentiment-agent ls -la /app/models_cache

# Check disk space
df -h

# Restart service
docker compose -f docker-compose.mvp.yml restart sentiment-agent
```

**Issue:** Port already in use
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port in .env
OPENCLAW_ORCHESTRATOR_PORT=8001
```

## Code Style

We use:
- **black** for code formatting
- **isort** for import sorting
- **ruff** for linting

```bash
# Install tools
pip install black isort ruff

# Format code
black services/
isort services/

# Lint code
ruff check services/

# Auto-fix issues
ruff check --fix services/
```

## Git Workflow

### Branch Naming

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/documentation-update` - Documentation
- `refactor/component-name` - Refactoring

### Commit Messages

```
type: description

optional body

type: feat, fix, docs, refactor, test, chore
```

Examples:
```
feat: add sentiment analysis endpoint

Add new /api/analyze endpoint to sentiment-agent that accepts
text input and returns sentiment classification with confidence score.

Closes #123
```

### Pull Request Process

1. Create feature branch
2. Make changes and commit
3. Run tests locally
4. Push to GitHub
5. Create pull request
6. Wait for CI checks to pass
7. Request review
8. Address feedback
9. Merge when approved

## Useful Commands

### Quick Actions

```bash
# Start everything
docker compose -f docker-compose.mvp.yml up -d

# Stop everything
docker compose -f docker-compose.mvp.yml down

# Restart everything
docker compose -f docker-compose.mvp.yml restart

# View logs
docker compose -f docker-compose.mvp.yml logs -f

# Clean rebuild
docker compose -f docker-compose.mvp.yml down
docker compose -f docker-compose.mvp.yml build --no-cache
docker compose -f docker-compose.mvp.yml up -d
```

### Service-Specific

```bash
# Restart specific service
docker compose -f docker-compose.mvp.yml restart sentiment-agent

# Rebuild specific service
docker compose -f docker-compose.mvp.yml up -d --build sentiment-agent

# View specific service logs
docker compose -f docker-compose.mvp.yml logs -f sentiment-agent

# Exec into specific service
docker exec -it chimera-sentiment-agent bash
```

## Getting Help

### Documentation

- `docs/CONFIGURATION.md` - Configuration guide
- `docs/OPERATIONAL_READINESS.md` - Operations guide
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/RUNBOOK.md` - Troubleshooting runbook
- `docs/API.md` - API documentation
- `tests/TEST_SETUP.md` - Testing guide

### Resources

- FastAPI docs: https://fastapi.tiangolo.com/
- Docker docs: https://docs.docker.com/
- pytest docs: https://docs.pytest.org/

### Team Communication

- Slack: #chimera-dev
- Issues: https://github.com/your-org/Project_Chimera/issues
- Wiki: https://github.com/your-org/Project_Chimera/wiki

---

**Next:** Read `docs/CONFIGURATION.md` to configure your development environment.

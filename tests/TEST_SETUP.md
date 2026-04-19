# Project Chimera - Test Setup Guide

## Overview

Project Chimera uses a multi-tier testing approach:
- **Unit Tests**: Individual service components
- **Integration Tests**: Service-to-service communication
- **E2E Tests**: Complete user workflows

## Prerequisites

### Local Development

```bash
# Install Python dependencies
pip install pytest pytest-asyncio pytest-cov httpx websockets docker

# Install Redis CLI (for health checks)
sudo apt-get install redis-tools  # Ubuntu/Debian
brew install redis                 # macOS
```

### Docker Services

```bash
# Start MVP services
docker compose -f docker-compose.mvp.yml up -d

# Wait for services to be healthy
./scripts/wait-for-services.sh

# Verify all services are healthy
./scripts/verify-stack-health.sh
```

## Running Tests

### Unit Tests

Run unit tests for individual services:

```bash
# Orchestrator
cd services/openclaw-orchestrator
pytest tests/ -v

# Scenespeak Agent
cd services/scenespeak-agent
pytest tests/ -v

# All services (from project root)
pytest services/*/tests/ -v
```

### Integration Tests

Test service-to-service communication:

```bash
# MVP integration tests
pytest tests/integration/mvp/ -v

# Specific test file
pytest tests/integration/mvp/test_service_communication.py -v

# With coverage
pytest tests/integration/mvp/ -v --cov=services --cov-report=html
```

### E2E Tests

Test complete user workflows:

```bash
# All MVP user journeys
pytest tests/e2e/test_mvp_user_journeys.py -v

# Specific journey
pytest tests/e2e/test_mvp_user_journeys.py::TestMVPUserJourneys::test_journey_1_prompt_to_dialogue_with_checks -v
```

## Test Organization

```
tests/
├── unit/                    # Unit tests for shared modules
│   ├── shared/
│   │   ├── models/
│   │   └── resilience/
│   └── services/
├── integration/
│   └── mvp/                 # MVP integration tests
│       ├── conftest.py
│       ├── test_service_communication.py
│       ├── test_service_health.py
│       ├── test_orchestrator_flow.py
│       └── ...
└── e2e/                     # End-to-end tests
    ├── conftest.py
    └── test_mvp_user_journeys.py
```

## Service Endpoints

| Service | Port | Health Endpoint |
|---------|------|-----------------|
| OpenClaw Orchestrator | 8000 | `/health` |
| SceneSpeak Agent | 8001 | `/health` |
| Translation Agent | 8002 | `/health` |
| Sentiment Agent | 8004 | `/health` |
| Safety Filter | 8006 | `/health/live` |
| Operator Console | 8007 | `/health` |
| Hardware Bridge | 8008 | `/health` |
| Redis | 6379 | `redis-cli ping` |

## CI/CD Testing

### GitHub Actions

- **`.github/workflows/mvp-tests.yml`**: MVP-focused test suite
- **`.github/workflows/automated-tests.yml`**: All automated tests
- **`.github/workflows/e2e-tests.yml`**: E2E user journey tests

### Running CI Locally

```bash
# Install act (GitHub Actions runner)
brew install act  # macOS
# or download from https://github.com/nektos/act

# Run MVP tests workflow
act -j mvp-tests

# Run integration tests
act -j integration-tests
```

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker compose -f docker-compose.mvp.yml ps

# View service logs
docker compose -f docker-compose.mvp.yml logs [service-name]

# Restart services
docker compose -f docker-compose.mvp.yml restart
```

### Test Timeouts

```bash
# Increase timeout for specific tests
pytest tests/integration/mvp/ -v --timeout=60

# Run with verbose output to see where tests hang
pytest tests/e2e/test_mvp_user_journeys.py -vv -s
```

### ML Model Loading Issues

```bash
# Check if models are downloaded
docker exec chimera-sentiment-agent ls -la /app/models_cache

# Re-download models if needed
./scripts/download-sentiment-model.sh
```

## Coverage Reporting

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run only integration tests
pytest -m "integration" -v

# List all markers
pytest --markers
```

## Debugging Failed Tests

```bash
# Stop on first failure
pytest tests/ -x -v

# Drop into debugger on failure
pytest tests/ -vv --pdb

# Show local variables on failure
pytest tests/ -vv -l
```

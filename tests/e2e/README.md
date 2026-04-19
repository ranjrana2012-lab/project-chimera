# Project Chimera - E2E User Journey Tests

## Overview

End-to-end tests that verify complete user workflows through the MVP system.

## Test Suites

### TestMVPUserJourneys

Core user journey tests that verify real-world usage patterns:

1. **Journey 1: Prompt to Dialogue with Checks** - Tests the full flow from user prompt through sentiment analysis, dialogue generation, and safety filtering
2. **Journey 2: Scene Coordination** - Verifies operator console can trigger scenes through the orchestrator to hardware bridge
3. **Journey 3: Translation Workflow** - Tests translation request processing and response formatting
4. **Journey 4: Show Lifecycle** - Validates show creation, activation, and deactivation workflows
5. **Journey 5: Multi-Agent Coordination** - Tests orchestrator coordinating multiple agents (sentiment, scenespeak, safety)
6. **Journey 6: Error Handling** - Verifies graceful error handling for invalid requests
7. **Journey 7: Redis Persistence** - Confirms data persistence across Redis operations
8. **Journey 8: Health Monitoring** - Validates all services report health status correctly

### TestE2EScenarios

Additional edge case and stress tests:

1. **Sentiment Analysis Pipeline** - Tests complete sentiment analysis workflow
2. **Safety Filter Pipeline** - Tests content safety checking workflow
3. **Concurrent Requests** - Validates system handles multiple simultaneous requests

## Running the Tests

### Prerequisites

- Docker services running: `docker compose -f docker-compose.mvp.yml up -d`
- Python 3.12+ with pytest: `pip install pytest httpx redis`

### Execute All Tests

```bash
# Start services first
docker compose -f docker-compose.mvp.yml up -d

# Wait for services to be healthy
./scripts/wait-for-services.sh

# Run E2E tests
pytest tests/e2e/test_mvp_user_journeys.py -v
```

### Run Specific Test

```bash
pytest tests/e2e/test_mvp_user_journeys.py::TestMVPUserJourneys::test_journey_1_prompt_to_dialogue_with_checks -v
```

### Run with Coverage

```bash
pytest tests/e2e/test_mvp_user_journeys.py --cov=services --cov-report=term-missing
```

## Test Design Principles

These E2E tests follow these principles:

1. **User-Focused**: Tests verify complete user workflows, not individual components
2. **Resilient**: Tests handle partial failures gracefully (timeouts, connection errors)
3. **Realistic**: Uses actual service endpoints and data flow
4. **Isolated**: Each test is independent and can run in any order
5. **Fast**: Uses short timeouts to avoid long waits during failures

## Service Endpoints Tested

| Service | Base URL | Endpoints |
|---------|----------|-----------|
| openclaw-orchestrator | localhost:8000 | /api/orchestrate, /health |
| scenespeak-agent | localhost:8001 | /health |
| translation-agent | localhost:8002 | /translate, /health |
| sentiment-agent | localhost:8004 | /api/analyze, /health |
| safety-filter | localhost:8006 | /v1/check, /health/live |
| operator-console | localhost:8007 | /api/show/control, /health |
| hardware-bridge | localhost:8008 | /health |
| redis | localhost:6379 | Direct connection |

## Current Test Status

✅ **All 11 tests passing** (as of 2026-04-19)

## CI/CD Integration

These tests run in GitHub Actions via:
- `.github/workflows/e2e-tests.yml` - E2E test workflow
- `.github/workflows/mvp-tests.yml` - MVP test suite

**Note**: Hourly scheduled runs have been disabled to prevent email notifications on failures. Tests still run on every push and PR.

## Notes

- Tests use localhost URLs for host machine execution
- Tests are designed to be resilient to service timeouts
- Some tests may show timeout/connection errors which are handled gracefully
- These tests complement (not replace) unit and integration tests

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker compose -f docker-compose.mvp.yml ps

# View logs
docker compose -f docker-compose.mvp.yml logs [service-name]

# Verify health
./scripts/verify-stack-health.sh
```

### Test Timeouts

```bash
# Increase timeout
pytest tests/e2e/test_mvp_user_journeys.py -v --timeout=120

# Run with verbose output
pytest tests/e2e/test_mvp_user_journeys.py -vv -s
```

### ML Model Loading Issues

```bash
# Check model status
docker exec chimera-sentiment-agent curl http://localhost:8004/health

# Restart service
docker compose -f docker-compose.mvp.yml restart sentiment-agent
```

---

**Last Updated**: 2026-04-19
**Python Version**: 3.12
**Docker Compose**: MVP (8 services)

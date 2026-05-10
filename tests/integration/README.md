# Integration Tests

This directory contains integration tests for Project Chimera, testing the complete flow across all services.

## Overview

Integration tests verify that all services work together correctly, from dialogue generation through safety filtering to sentiment analysis. These tests require the services to be running, either via Docker Compose or locally.

## Prerequisites

### Running Services

Integration tests require all services to be running. Use Docker Compose for the easiest setup:

```bash
# Start all services
docker-compose up -d

# Verify services are healthy
docker-compose ps
```

Or run services locally (see each service's documentation).

### Python Dependencies

Install test dependencies:

```bash
pip install pytest pytest-asyncio httpx websockets
```

## Test Structure

### Test Files

- `conftest.py` - Pytest fixtures and configuration
- `test_orchestrator_flow.py` - Orchestrator end-to-end tests
- `test_agent_communication.py` - Agent-to-agent communication tests
- `test_websocket_console.py` - Operator Console WebSocket tests
- `test_safety_filter.py` - Safety filter integration tests
- `test_full_pipeline.py` - Complete pipeline end-to-end tests

### Fixtures

Available fixtures in `conftest.py`:

- `all_services_running` - Ensures all services are up before tests
- `orchestrator_client` - HTTP client for orchestrator service
- `scenespeak_client` - HTTP client for SceneSpeak agent
- `captioning_client` - HTTP client for captioning agent
- `bsl_client` - HTTP client for BSL agent
- `sentiment_client` - HTTP client for sentiment agent
- `safety_client` - HTTP client for safety filter
- `console_client` - HTTP client for operator console
- `console_websocket` - WebSocket connection to console
- `test_text` - Sample text for analysis
- `test_dialogue_prompt` - Sample dialogue generation prompt
- `test_audio_file` - Temporary audio file for captioning
- `test_text_for_translation` - Sample text for BSL translation
- `safe_content` - Content that passes safety filters
- `unsafe_content` - Content that triggers safety filters
- `test_show_context` - Sample show metadata

## Running Tests

### Run All Integration Tests

```bash
# From project root
pytest tests/integration/

# With verbose output
pytest tests/integration/ -v

# With detailed output
pytest tests/integration/ -vv
```

### Run Specific Test Files

```bash
# Test orchestrator flow
pytest tests/integration/test_orchestrator_flow.py

# Test agent communication
pytest tests/integration/test_agent_communication.py

# Test safety filter
pytest tests/integration/test_safety_filter.py

# Test full pipeline
pytest tests/integration/test_full_pipeline.py
```

### Run by Test Markers

```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run only WebSocket tests
pytest -m websocket

# Run only tests requiring Docker
pytest -m requires_docker
```

### Run with Docker Services

```bash
# Set environment variable
export USE_DOCKER=true

# Run tests
pytest tests/integration/
```

## Test Scenarios

### 1. Orchestrator Flow (`test_orchestrator_flow.py`)

Tests the orchestrator service's ability to:

- Start up and respond to health checks
- List available tests
- Handle concurrent requests
- Validate input
- Expose metrics

### 2. Agent Communication (`test_agent_communication.py`)

Tests communication between services:

- **SceneSpeak → Captioning**: Generate dialogue and process for captions
- **Captioning → Sentiment**: Analyze sentiment of captions
- **BSL Translation**: English text to BSL gloss notation
- **Health Endpoints**: Verify all agents are healthy
- **Batch Processing**: Handle multiple requests efficiently

### 3. WebSocket Console (`test_websocket_console.py`)

Tests the operator console's real-time features:

- **WebSocket Connection**: Establish and maintain connections
- **Metrics Broadcast**: Receive real-time service metrics
- **Service Listing**: List all monitored services
- **Alert Generation**: Receive and handle alerts
- **Channel Subscription**: Subscribe to specific update channels

### 4. Safety Filter (`test_safety_filter.py`)

Tests content moderation across policies:

- **Family Policy**: Strict filtering for all ages
- **Teen Policy**: Moderate filtering (13+)
- **Adult Policy**: Minimal filtering (18+)
- **Unrestricted Policy**: No filtering
- **Context-aware Moderation**: Consider show context
- **Audit Logging**: Track all moderation decisions

### 5. Full Pipeline (`test_full_pipeline.py`)

Tests complete end-to-end flows:

1. **Generate Dialogue** (SceneSpeak Agent)
2. **Translate to BSL** (BSL Agent)
3. **Check Safety** (Safety Filter)
4. **Analyze Sentiment** (Sentiment Agent)

Additional scenarios:

- **Concurrent Processing**: Multiple pipelines simultaneously
- **Batch Processing**: Process multiple dialogues at once
- **Error Handling**: Graceful degradation on failures
- **Performance**: Pipeline timing and throughput
- **Metadata Tracking**: Context preservation through pipeline

## Configuration

### Environment Variables

- `USE_DOCKER` - Set to `true` when using docker-compose (default: `true`)
- `ORCHESTRATOR_URL` - Override orchestrator URL
- `SCENESPEAK_URL` - Override SceneSpeak agent URL
- `CAPTIONING_URL` - Override captioning agent URL
- `BSL_URL` - Override BSL agent URL
- `SENTIMENT_URL` - Override sentiment agent URL
- `SAFETY_URL` - Override safety filter URL
- `CONSOLE_URL` - Override console URL

### Service Ports (Local Development)

| Service | Port |
|---------|------|
| Orchestrator | 8000 |
| SceneSpeak Agent | 8001 |
| Captioning Agent | 8002 |
| BSL Agent | 8003 |
| Sentiment Agent | 8004 |
| Lighting/Sound/Music | 8005 |
| Safety Filter | 8006 |
| Operator Console | 8007 |

## Test Coverage

Current coverage targets:

- **Critical Paths**: >80% coverage
- **Service Health**: 100% (all services must be checked)
- **API Endpoints**: >90% coverage
- **Error Cases**: All error responses tested
- **WebSocket Communication**: Connection, messaging, disconnection

## Troubleshooting

### Services Not Starting

If services fail to start:

```bash
# Check service logs
docker-compose logs [service-name]

# Restart services
docker-compose restart

# Rebuild services
docker-compose up -d --build
```

### Tests Timing Out

Increase timeout in `conftest.py`:

```python
async with AsyncClient(base_url=base_url, timeout=60.0) as client:
```

### WebSocket Connection Failures

Verify console service is running:

```bash
curl http://localhost:8007/health/live
```

### Import Errors

Ensure project root is in Python path:

```bash
export PYTHONPATH=<repo>:$PYTHONPATH
```

## Continuous Integration

Integration tests run in CI/CD pipeline:

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

## Adding New Tests

When adding new integration tests:

1. Use appropriate markers (`@pytest.mark.integration`, `@pytest.mark.slow`)
2. Use existing fixtures when possible
3. Add new fixtures to `conftest.py` if needed
4. Test both success and failure cases
5. Include cleanup in fixtures if needed
6. Document the test scenario in this README

Example:

```python
@pytest.mark.asyncio
@pytest.mark.requires_docker
async def test_new_scenario(
    scenespeak_client: AsyncClient,
    test_text: str
):
    """Test description."""
    response = await scenespeak_client.post(
        "/v1/generate",
        json={"prompt": test_text}
    )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
```

## Related Documentation

- [Service Documentation](../../services/README.md)
- [API Documentation](../../docs/api/README.md)
- [Development Guide](../../DEVELOPMENT.md)
- [Deployment Guide](../../DEPLOYMENT.md)

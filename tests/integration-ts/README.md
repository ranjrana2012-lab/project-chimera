# Integration Tests

Comprehensive integration tests for Project Chimera services, testing service-to-service interactions and complete workflows.

## Overview

These integration tests verify that all services work together correctly, covering:
- Complete show workflows (audience input → AI response → BSL generation → display)
- Safety filter integration across all services
- BSL avatar rendering pipeline (text → gloss → animation → display)
- WebSocket streaming for real-time updates
- Show state transitions and lifecycle management

## Prerequisites

### Running Services

Integration tests require all services to be running. Use Docker Compose:

```bash
# Start all services
docker compose up -d

# Verify services are healthy
docker compose ps
```

### Node.js Dependencies

Install test dependencies:

```bash
cd tests/integration-ts
npm install
```

## Test Structure

### Test Files

- `conftest.ts` - Test fixtures and configuration
- `complete-show.spec.ts` - Complete show workflow tests
- `safety-integration.spec.ts` - Safety filter integration tests
- `bsl-pipeline.spec.ts` - BSL avatar pipeline tests
- `websocket-flows.spec.ts` - WebSocket streaming tests
- `show-state.spec.ts` - Show state transition tests

### Fixtures and Helpers

Available fixtures in `conftest.ts`:

- `testData` - Test data factory for creating test inputs
- `services` - HTTP clients for all services
- `websockets` - WebSocket clients for real-time communication
- `helper` - Common test utility methods
- `waitForService` - Wait for service to be healthy
- `cleanup` - Cleanup after tests

## Running Tests

### Run All Integration Tests

```bash
cd tests/integration-ts
npm test
```

### Run Specific Test Files

```bash
# Complete show workflow
npm run test:complete-show

# Safety filter tests
npm run test:safety

# BSL pipeline tests
npm run test:bsl

# WebSocket streaming tests
npm run test:websocket

# Show state transition tests
npm run test:show-state
```

### Run with Different Options

```bash
# Run tests in headed mode (see browser)
npm run test:headed

# Run tests with UI mode
npm run test:ui

# Run tests in debug mode
npm run test:debug

# Generate test report
npm run test:report
```

## Test Scenarios

### 1. Complete Show Workflow (`complete-show.spec.ts`)

Tests the full end-to-end show experience:

- Audience input → Sentiment analysis → Dialogue generation → BSL translation → Display
- Positive sentiment flow
- Negative sentiment flow
- Multiple audience inputs
- Character context in dialogue
- BSL avatar updates
- Show state transitions
- Rapid input handling
- Multi-scene shows

### 2. Safety Filter Integration (`safety-integration.spec.ts`)

Tests content moderation across all services:

- Family policy filtering
- Teen policy moderation
- Adult policy minimal filtering
- Unrestricted policy
- Context-aware moderation
- Audit logging
- Batch moderation
- Dialogue content filtering
- Audience input moderation
- Cross-service filtering
- Custom policy configuration
- Concurrent moderation requests

### 3. BSL Avatar Pipeline (`bsl-pipeline.spec.ts`)

Tests the complete BSL translation and rendering pipeline:

- Text to BSL gloss translation
- Gloss to NMM animation data
- Avatar generation with expressions
- Avatar generation with handshapes
- Real-time avatar streaming
- Playback controls (start, pause, resume, stop)
- Batch translation
- Context-aware translation
- Expression variations
- Complex sentence translation
- Timeline synchronization
- Connection management
- Performance metrics
- Renderer information
- Complete pipeline: text to display

### 4. WebSocket Streaming (`websocket-flows.spec.ts`)

Tests real-time WebSocket communication:

- Sentiment streaming
- Captioning/audio transcription
- BSL avatar updates
- Console dashboard updates
- Real-time sentiment analysis
- Captioning with timing
- Message filtering
- Connection reconnection
- Concurrent connections
- Message history tracking
- Broadcast messages
- Error handling
- Heartbeat and keep-alive
- Large message handling
- Batch analysis
- Animation streaming with timing

### 5. Show State Transitions (`show-state.spec.ts`)

Tests show lifecycle and state management:

- Initialization (idle → starting → active)
- State transitions (active → paused → resumed → ended)
- Scene progression
- Invalid transition handling
- Concurrent state changes
- State persistence
- Event broadcasting
- Audience metrics
- Show recovery after pause
- Timeout and auto-end
- Multiple independent shows

## Configuration

### Environment Variables

- `USE_DOCKER` - Set to `true` when using docker-compose (default: `true`)
- `BASE_URL` - Base URL for services (default: `http://localhost:8007`)
- `TIMEOUT` - Default timeout for tests (default: 60000ms)

### Service Ports

| Service | Port | WebSocket Path |
|---------|------|----------------|
| Orchestrator | 8000 | `/ws` |
| SceneSpeak | 8001 | `/ws` |
| Captioning | 8002 | `/v1/stream` |
| BSL | 8003 | `/ws/avatar` |
| Sentiment | 8004 | `/ws` |
| Lighting | 8005 | `/ws` |
| Safety | 8006 | `/ws` |
| Console | 8007 | `/ws` |
| Music | 8011 | `/ws` |

## Test Coverage

Current coverage targets:

- **Critical Workflows**: >90% coverage
- **Service Integration**: >85% coverage
- **State Management**: >90% coverage
- **WebSocket Communication**: >80% coverage
- **Error Cases**: All error scenarios tested

## Troubleshooting

### Services Not Starting

If services fail to start:

```bash
# Check service logs
docker compose logs [service-name]

# Restart services
docker compose restart

# Rebuild services
docker compose up -d --build
```

### Tests Timing Out

Increase timeout in `playwright.config.ts`:

```typescript
timeout: 120000, // 120 seconds per test
```

### WebSocket Connection Failures

Verify service WebSocket endpoints:

```bash
# Test WebSocket connection
wscat -c ws://localhost:8003/ws/avatar
```

### Import Errors

Ensure dependencies are installed:

```bash
npm install
```

## Adding New Tests

When adding new integration tests:

1. Use appropriate test markers (`@integration`, `@workflow`, etc.)
2. Use existing fixtures when possible
3. Add new fixtures to `conftest.ts` if needed
4. Test both success and failure cases
5. Include cleanup in tests if needed
6. Document the test scenario in this README

Example:

```typescript
test('@integration @smoke new test scenario', async ({ services, testData }) => {
  // Arrange
  const testInput = testData.createTestInput();

  // Act
  const response = await services.testService.post('http://localhost:8000/api/test', {
    data: testInput
  });

  // Assert
  expect(response.ok()).toBeTruthy();
  const result = await response.json();
  expect(result).toHaveProperty('success', true);
});
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
        run: docker compose up -d
      - name: Install dependencies
        run: cd tests/integration-ts && npm install
      - name: Run integration tests
        run: cd tests/integration-ts && npm test
```

## Related Documentation

- [Service Documentation](../../docs/services/)
- [API Documentation](../../docs/reference/api.md)
- [E2E Testing Guide](../e2e/docs/e2e-testing-guide.md)
- [Development Guide](../../docs/DEVELOPMENT.md)

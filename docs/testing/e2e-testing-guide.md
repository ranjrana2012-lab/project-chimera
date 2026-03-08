# E2E Testing Guide

## Overview

Project Chimera uses [Playwright](https://playwright.dev/) for comprehensive end-to-end testing of all services, workflows, and user interfaces. The E2E test suite validates the entire system from API contracts through cross-service workflows to the Operator Console UI.

### Testing Architecture

- **Monolithic test suite**: All tests run against real services and real models
- **Hybrid organization**: Service-specific tests + centralized cross-service workflow tests
- **Balanced test mix**: 70% critical journeys, 30% failure scenarios
- **Real-time testing**: WebSocket API integration for live show workflows
- **Fast feedback**: Smoke tests complete in <30 seconds

### Tech Stack

- **Test Framework**: Playwright (TypeScript)
- **Runtime**: Node.js 20
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Real-time**: WebSocket API

---

## Running Tests Locally

### Prerequisites

1. **Install Node.js dependencies**:
   ```bash
   cd tests/e2e
   npm install
   ```

2. **Install Playwright browsers** (first time only):
   ```bash
   npx playwright install chromium
   ```

3. **Ensure services are running**:
   ```bash
   # Either start services manually
   docker-compose up -d

   # Or let tests auto-start services (via global-setup)
   ```

### Test Commands

#### Run All Tests
```bash
cd tests/e2e
npm test
```

#### Run Smoke Tests (Fast)
```bash
npm run test:smoke
```
**Completes in <30 seconds** - Ideal for rapid iteration during development.

#### Run Specific Test Files
```bash
# API tests
npx playwright test api/orchestrator.spec.ts

# Workflow tests
npx playwright test cross-service/show-workflow.spec.ts

# UI tests
npx playwright test ui/operator-console.spec.ts
```

#### Run Tests by Tag
```bash
# Only smoke tests
npx playwright test --grep @smoke

# Only API tests
npx playwright test --grep @api

# Only workflow tests
npx playwright test --grep @workflow
```

#### Run Tests with UI (Debugging)
```bash
# Run with headed browser (shows browser window)
npm run test:headed

# Run with Playwright Inspector (step-through debugging)
npm run test:debug
```

#### View Test Reports
```bash
# Open HTML report
npm run report
```

---

## Test Organization

The test suite is organized into the following directories:

```
tests/e2e/
├── api/              # Service API contract tests
│   ├── orchestrator.spec.ts
│   ├── sentiment.spec.ts
│   ├── scenespeak.spec.ts
│   └── bsl.spec.ts
├── websocket/        # Real-time communication tests
│   └── sentiment-updates.spec.ts
├── ui/              # Frontend component tests
│   └── operator-console.spec.ts
├── cross-service/   # End-to-end workflow tests
│   └── show-workflow.spec.ts
├── failures/        # Failure scenario tests
│   └── service-failures.spec.ts
├── helpers/         # Test utilities
│   ├── test-utils.ts
│   ├── service-health.ts
│   ├── websocket-client.ts
│   └── ralph-mode.ts
└── fixtures/        # Test data
    ├── audio/
    └── data/
```

### Test Categories

1. **API Contract Tests** (`api/`)
   - Validate service health endpoints
   - Test API request/response formats
   - Verify business logic correctness
   - **Example**: Sentiment analysis returns valid score (0-1)

2. **WebSocket Tests** (`websocket/`)
   - Test real-time message flows
   - Validate multi-client synchronization
   - Verify connection stability
   - **Example**: Sentiment updates flow through WebSocket to all clients

3. **UI Tests** (`ui/`)
   - Test Operator Console interactions
   - Validate dashboard displays
   - Check button interactivity
   - **Example**: Start Show button changes show status to "active"

4. **Cross-Service Workflow Tests** (`cross-service/`)
   - Test complete show workflows
   - Validate service-to-service communication
   - Verify end-to-end data flows
   - **Example**: Audience input → Sentiment analysis → SceneSpeak dialogue → BSL avatar

5. **Failure Scenario Tests** (`failures/`)
   - Test service resilience
   - Validate fallback behavior
   - Verify graceful degradation
   - **Example**: Show continues when sentiment agent is unavailable

---

## Ralph Mode Integration

**Ralph Mode** is designed for autonomous agent workflows that need structured test output.

### What is Ralph Mode?

Ralph Mode provides machine-readable test results with:
- Structured JSON output
- Promise protocol for completion detection
- Detailed failure information
- Coverage metrics
- Execution timing

### Running Ralph Mode

```bash
cd tests/e2e
npm run ralph
```

### Ralph Mode Output

Ralph Mode outputs structured JSON:

```json
{
  "passed": true,
  "failures": [],
  "coverage": 85,
  "duration_ms": 12345
}
```

Or on failure:

```json
{
  "passed": false,
  "failures": [
    {
      "file": "tests/e2e/api/sentiment.spec.ts",
      "title": "sentiment analysis with ML model",
      "error": "Expected status 200 but got 500"
    }
  ],
  "coverage": 75,
  "duration_ms": 8432
}
```

### Promise Protocol

Ralph Mode outputs special promise markers for completion detection:

- **Success**: `<promise>TESTS_COMPLETE</promise>`
- **Failure**: `<promise>TESTS_FAILED</promise>`

### Quick Smoke Test (Ralph Mode)

For rapid iteration during autonomous workflows:

```bash
npm run test:smoke
```

Returns: `true` (exit code 0) or `false` (exit code 1)

### Use Cases

- **Pre-deployment validation**: Run tests before deploying to production
- **Continuous monitoring**: Hourly smoke tests in CI/CD
- **Autonomous agents**: Structured output for decision-making
- **Quality gates**: Block merges if tests fail

---

## CI/CD Integration

### GitHub Actions Workflow

E2E tests run automatically in CI/CD via `.github/workflows/e2e-tests.yml`:

#### Triggers

- **Push to main/master/develop**: Full test suite
- **Pull Requests**: Full test suite + PR comments with results
- **Hourly schedule**: Smoke tests for production monitoring
- **Manual dispatch**: On-demand with test suite selection

#### Workflow Steps

1. **Setup Node.js**: Install Node.js 20 and cache dependencies
2. **Install Playwright**: Install Playwright and Chromium browser
3. **Start Services**: Start all services via Docker Compose
4. **Wait for Services**: Poll health endpoints until all services are healthy
5. **Run Tests**: Execute test suite with sharding for parallel execution
6. **Upload Artifacts**: Save test results, HTML reports, and screenshots
7. **Report Results**: Comment PRs with test summary

#### Artifacts

- `playwright-report-shard-{N}`: HTML test reports
- `test-results-shard-{N}`: JSON test results
- `screenshots-shard-{N}`: Failure screenshots

### Viewing CI/CD Results

#### In GitHub Actions

1. Go to **Actions** tab
2. Select the **E2E Tests** workflow run
3. View logs and download artifacts

#### PR Comments

Tests automatically comment on PRs with:
- Test summary (passed/failed/skipped)
- Duration
- Failed test details
- Links to full reports

---

## Troubleshooting

### Services Not Starting

**Symptom**: `Error: connect ECONNREFUSED localhost:8000`

**Solutions**:
1. Ensure Docker is running: `docker ps`
2. Check port availability: `lsof -i :8000`
3. View service logs: `docker-compose logs orchestrator`
4. Restart services: `docker-compose restart`

**Quick Fix**:
```bash
docker-compose down
docker-compose up -d
./scripts/wait-for-services.sh
```

### Flaky Tests

**Symptom**: Tests pass locally but fail in CI/CD

**Solutions**:
1. **Increase timeout**: Tests may need more time in CI environment
   ```typescript
   await page.waitForSelector('[data-testid="show-status"]', {
     timeout: 30000  // Increase from default 5000ms
   });
   ```
2. **Add explicit waits**: Ensure services are ready
   ```typescript
   await page.waitForLoadState('networkidle');
   ```
3. **Check service health**: Add health check before test
   ```typescript
   await expect(page.request.get('http://localhost:8000/health')).toBeOK();
   ```

### Browser Issues

**Symptom**: `Error: Executable doesn't exist at /path/to/chromium`

**Solutions**:
1. Reinstall Playwright browsers:
   ```bash
   cd tests/e2e
   npx playwright install chromium
   ```
2. Clear browser cache:
   ```bash
   rm -rf ~/.cache/ms-playwright
   npx playwright install chromium
   ```

### Permission Denied on wait-for-services.sh

**Symptom**: `bash: ./scripts/wait-for-services.sh: Permission denied`

**Solution**:
```bash
chmod +x scripts/wait-for-services.sh
```

### Tests Timeout After 120s

**Symptom**: Tests fail with timeout error during service startup

**Solutions**:
1. Check service logs: `docker-compose logs {service-name}`
2. Increase timeout in `scripts/wait-for-services.sh`:
   ```bash
   TIMEOUT=180  # Increase from 120
   ```
3. Verify service health endpoints are accessible:
   ```bash
   curl http://localhost:8000/health
   ```

### WebSocket Connection Failures

**Symptom**: `WebSocket connection to 'ws://localhost:8003/ws/avatar' failed`

**Solutions**:
1. Verify WebSocket endpoint is available:
   ```bash
   curl -i -N \
     -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     http://localhost:8003/ws/avatar
   ```
2. Check if service is running:
   ```bash
   docker-compose ps bsl-agent
   ```
3. Add retry logic in tests:
   ```typescript
   const ws = await createWebSocketClient('ws://localhost:8003/ws/avatar');
   ```

### Test Data Not Found

**Symptom**: `Error: ENOENT: no such file or directory, open 'tests/e2e/fixtures/data/test.json'`

**Solution**:
```bash
# Create test fixtures directory
mkdir -p tests/e2e/fixtures/{audio,data}

# Add test data files
echo '{"test": "data"}' > tests/e2e/fixtures/data/test.json
```

---

## Test Writing Guidelines

### Test Naming

- Use descriptive test names: `test('should return 200 OK', ...)`
- Add tags: `test('@smoke @api health endpoint', ...)`
- Group related tests: `test.describe('Sentiment Agent API', () => { ... })`

### Test Structure

```typescript
test('@api sentiment analysis with ML model', async ({ request }) => {
  // 1. Arrange: Setup test data
  const input = { text: 'This is amazing!' };

  // 2. Act: Execute the action
  const response = await request.post('http://localhost:8004/api/analyze', {
    data: input
  });

  // 3. Assert: Verify results
  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(body).toMatchObject({
    sentiment: expect.any(String),
    score: expect.any(Number)
  });
});
```

### Using Test IDs

Always use `data-testid` attributes for element selection:

```typescript
// Good
await page.click('[data-testid="start-show-button"]');

// Avoid
await page.click('button');  // Fragile
await page.click('.btn-primary');  // Styling dependent
```

### Error Handling

```typescript
test('handles invalid input gracefully', async ({ page }) => {
  // Expect error but don't fail test
  await page.fill('[data-testid="audience-input"]', 'a'.repeat(100000));

  // Should show validation error
  await expect(page.locator('[data-testid="validation-error"]')).toBeVisible({
    timeout: 5000
  });
});
```

---

## Additional Resources

- **Playwright Documentation**: https://playwright.dev/
- **Test Report**: `tests/e2e/playwright-report/index.html`
- **Test Results**: `tests/e2e/test-results/results.json`
- **GitHub Actions**: `.github/workflows/e2e-tests.yml`
- **Service Health**: `http://localhost:8000/health`

---

## Getting Help

1. **Check logs**: `docker-compose logs {service-name}`
2. **Run locally**: `cd tests/e2e && npm run test:debug`
3. **View screenshots**: `tests/e2e/test-results/screenshots/`
4. **Read test output**: `tests/e2e/test-results/results.json`
5. **Check CI/CD**: GitHub Actions tab

---

**Happy Testing! 🎭**

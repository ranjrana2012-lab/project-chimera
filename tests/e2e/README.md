# Project Chimera E2E Tests

End-to-end testing infrastructure for Project Chimera AI-powered live theatre platform.

## Overview

This test suite uses Playwright with TypeScript to validate:
- **9 Microservices** (ports 8000-8007, 8011)
- **API Contracts** - REST and GraphQL endpoints
- **Real-time Communication** - WebSocket message flows
- **User Interfaces** - Operator Console dashboard
- **Cross-service Workflows** - Complete show orchestration
- **Failure Scenarios** - Graceful degradation

## Quick Start

```bash
cd tests/e2e
npm install
npx playwright install chromium
npm test
```

## Test Scripts

- `npm test` - Run all tests
- `npm run test:headed` - Run tests with visible browser
- `npm run test:debug` - Run tests in debug mode (with inspector)
- `npm run test:smoke` - Run only smoke tests (tagged with @smoke)
- `npm run report` - Open HTML test report
- `npm run ralph` - Run Ralph Mode for autonomous agent verification

## Directory Structure

```
tests/e2e/
├── helpers/              # Test utilities and helpers
│   ├── test-utils.ts     # Common test operations
│   ├── service-health.ts # Service health checks
│   ├── websocket-client.ts # WebSocket testing utilities
│   └── ralph-mode.ts     # Ralph Mode integration
├── api/                  # API contract tests
│   ├── orchestrator.spec.ts
│   ├── scenespeak.spec.ts
│   ├── sentiment.spec.ts
│   ├── bsl.spec.ts
│   └── ...
├── websocket/            # Real-time communication tests
│   └── sentiment-updates.spec.ts
├── ui/                   # User interface tests
│   └── operator-console.spec.ts
├── cross-service/        # End-to-end workflow tests
│   └── show-workflow.spec.ts
├── failures/             # Failure scenario tests
│   └── service-failures.spec.ts
└── fixtures/             # Test fixtures
    ├── audio/            # Audio test data
    └── data/             # JSON and other test data
```

## Configuration

### Base URL

Configure the base URL via environment variable:
```bash
BASE_URL=http://localhost:8000 npm test
```

### Docker Compose

Tests can auto-start services using Docker Compose if not already running.

## Test Tags

- `@smoke` - Fast health checks (runs in CI first)
- `@api` - API contract tests
- `@websocket` - WebSocket tests
- `@ui` - UI interaction tests
- `@workflow` - Cross-service workflow tests
- `@failure` - Failure scenario tests

## Ralph Mode

For autonomous agent workflows:

```bash
npm run ralph
```

Returns structured JSON output:
```json
{
  "passed": true,
  "failures": [],
  "coverage": 85,
  "duration_ms": 15000
}
```

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Hourly schedule (production monitoring)

See `.github/workflows/e2e-tests.yml`

## Troubleshooting

### Services Not Starting
Ensure Docker is running and ports 8000-8011 are available.

### Flaky Tests
Increase timeout in test or check service dependencies.

### Browser Issues
Reinstall: `npx playwright install chromium`

### Debugging Tests
```bash
npm run test:debug
# Opens Playwright Inspector for step-by-step debugging
```

## Test Organization Philosophy

**Monolithic test suite** - Tests run against real services and models
**Hybrid organization** - Service-specific + centralized cross-service
**Balanced mix** - 70% critical journeys, 30% failure scenarios

## Contributing

When adding new tests:
1. Place in appropriate directory (api/, websocket/, ui/, cross-service/, failures/)
2. Add relevant tags (@smoke, @api, @websocket, etc.)
3. Follow existing test patterns
4. Update this README if adding new test categories

## See Also

- [Playwright Documentation](https://playwright.dev/)
- [Project Chimera Development Guide](../../DEVELOPMENT.md)
- [E2E Testing Implementation Plan](../../docs/plans/2026-03-08-playwright-e2e-testing-implementation.md)

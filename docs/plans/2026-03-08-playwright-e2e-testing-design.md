# Playwright E2E Testing Strategy - Design Document

**Date:** 2026-03-08
**Status:** Approved
**Priority:** HIGH

## Overview

Comprehensive end-to-end testing strategy for Project Chimera using Playwright, serving three purposes: validation & regression, autonomous agent support (Ralph Mode), and production monitoring.

## Architecture

### Test Organization (Hybrid Structure)

```
tests/e2e/
├── cross-service/          # Critical show workflow tests
├── api/                    # API endpoint tests
├── websocket/              # Real-time communication tests
├── ui/                     # Frontend component tests
└── failures/               # Failure scenario tests

services/<service>/tests/e2e/  # Service-specific E2E tests
```

### Test Characteristics

- **Monolithic Suite:** Single comprehensive test suite
- **Full Integration:** Real services, real models, real infrastructure
- **All Report Formats:** Console + HTML + JSON
- **Always Full Suite:** No smart selection, no tiers
- **Test Mix:** 70% critical journeys, 30% failure scenarios

## Components

### 1. Testing Infrastructure

**Playwright Configuration:**
- TypeScript with strict mode
- Chromium browser
- HTML reporter with screenshots/video on failure
- JSON reporter for CI/CD integration
- Parallel execution with configurable workers
- Service startup/teardown via global hooks

**Test Utilities:**
- `ChimeraTestHelper` class for common operations
- Service health checks
- WebSocket client creation
- Show state management
- Audience input simulation
- Prometheus metrics querying

### 2. Critical User Journeys (70%)

**Complete Show Workflow:**
1. Navigate to Operator Console
2. Start new show
3. Simulate audience sentiment input
4. Verify sentiment processing (DistilBERT ML)
5. Verify dialogue generation (SceneSpeak local LLM)
6. Verify BSL avatar receives dialogue
7. Verify scene progress
8. End show and verify cleanup

**Additional Journeys:**
- Captioning agent speech-to-text pipeline
- Safety filter content moderation
- Lighting/sound DMX commands
- Music generation and delivery

**Frontend Tests:**
- Operator Console dashboard (all agent statuses)
- BSL Avatar viewer (API contract only, no visual regression)
- Responsive design validation

### 3. Failure Scenarios (30%)

**Service Failures (40% of failures):**
- Individual service crashes and restarts
- Orchestrator unavailable
- Sentiment agent fallback behavior
- GPU unavailability and graceful degradation

**Resource Exhaustion (30% of failures):**
- GPU exhaustion and queuing
- Out of memory handling
- Disk space exhaustion
- Network timeouts

**Data Issues (30% of failures):**
- Invalid input validation
- Malformed API requests
- Empty model responses
- Extremely long inputs

### 4. WebSocket Testing (Hybrid Approach)

**Playwright UI Tests:**
- Verify WebSocket state updates in UI
- Test real-time sentiment display
- Validate dialogue generation notifications

**Real WebSocket Client Tests:**
- Multiple client synchronization
- Message delivery guarantees
- BSL avatar animation data flow
- Connection resilience and reconnection

### 5. API Contract Tests

All 9 services tested:
- OpenClaw Orchestrator (8000)
- SceneSpeak Agent (8001)
- Captioning Agent (8002)
- BSL Agent (8003)
- Sentiment Agent (8004)
- Lighting Control (8005)
- Safety Filter (8006)
- Operator Console (8007)
- Music Generation (8011)

Each test validates:
- Endpoint availability
- Request/response contracts
- Error handling
- Performance metrics

### 6. Ralph Mode Integration

**Structured Output:**
- JSON results for programmatic consumption
- Promise protocol: `<promise>TESTS_COMPLETE</promise>`
- Failure details with actionable messages
- Coverage metrics integration

**Quick Iteration Support:**
- Smoke tests with `@smoke` tag (30s target)
- Service health checks (10s target)
- TDD loop script for continuous testing

### 7. CI/CD Integration

**GitHub Actions Workflow:**
- Triggers: push, PR, schedule (hourly), manual
- Service startup via Docker Compose
- Parallel test execution
- Artifact uploads (HTML report, screenshots, videos)
- PR comments with test results
- Production alerting on scheduled failures

**Production Monitoring:**
- Hourly smoke tests via cron
- Alert integration for failures
- Prometheus metrics export
- Automatic issue creation on failure

## Data Flow

```
User Action → Operator Console → OpenClaw Orchestrator
    ↓
Sentiment API → DistilBERT Model → Sentiment Result
    ↓
SceneSpeak API → Local LLM → Generated Dialogue
    ↓
BSL API → NMM Animation → Avatar Update (WebSocket)
    ↓
Lighting/Sound APIs → DMX/OSC Commands
    ↓
Show State Update → All Clients (WebSocket)
```

## Error Handling

**Test Failures:**
- Screenshots captured automatically
- Video recordings retained
- Trace files for debugging
- Structured error messages

**Service Unavailability:**
- Health check retries (30 attempts, 2s intervals)
- Clear error messages when services don't start
- Test marked as skipped (not failed) if environment is down

**Flaky Tests:**
- Automatic retry on failure (CI: 2 retries, local: 0)
- Flakiness detection and reporting
- Quarantine mechanism for consistently flaky tests

## Testing Strategy

### Test Types

1. **Smoke Tests (@smoke):** Critical path validation, < 30s
2. **Integration Tests:** Cross-service workflows
3. **API Tests:** Contract validation for all endpoints
4. **WebSocket Tests:** Real-time communication
5. **UI Tests:** Frontend component validation
6. **Failure Tests:** Resilience and error handling

### Test Execution

**Development:**
```bash
npm test              # Full suite
npm run test:smoke    # Quick smoke tests
npm run test:debug    # Interactive debugging
npm run report        # View HTML report
npm run ralph         # Ralph Mode structured output
```

**CI/CD:**
- Full suite on all PRs
- Hourly smoke tests for production monitoring
- Parallel execution for speed
- Automatic PR commenting with results

### Success Criteria

- All 9 services have API contract tests
- All WebSocket endpoints have real-time tests
- Complete show workflow tested end-to-end
- Failure scenarios cover all categories
- < 1% flaky test rate
- Full suite < 15 minutes
- Smoke tests < 30 seconds
- 95%+ CI/CD pass rate

## Ralph Mode Support

### Promise Protocol

```typescript
// Test completion signals
<promise>TESTS_COMPLETE</promise>  // All tests passed
<promise>TESTS_FAILED</promise>    // Tests failed
<promise>NEEDS_FIX</promise>       // Awaiting fixes
```

### Structured Output

```json
{
  "passed": true,
  "failures": [],
  "coverage": 85,
  "duration_ms": 12345
}
```

### Quick Feedback Loop

1. Ralph Mode agent makes changes
2. Run smoke tests (30s)
3. If pass → run full suite (15min)
4. If fail → fix → retry
5. Continue until `<promise>TESTS_COMPLETE</promise>`

## Implementation Order

1. Setup Playwright infrastructure (config, helpers)
2. Service health checks and startup automation
3. API contract tests (one service at a time)
4. WebSocket integration tests
5. Cross-service workflow tests
6. UI component tests
7. Failure scenario tests
8. CI/CD integration
9. Production monitoring setup

## Open Questions

None - design approved and ready for implementation.

---

**Design Status:** ✅ Approved
**Next Step:** Implementation Plan (writing-plans skill)
**Target Completion:** 2026-03-08

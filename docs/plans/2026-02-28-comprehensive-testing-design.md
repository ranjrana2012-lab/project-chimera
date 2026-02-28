# Comprehensive Testing Strategy - Design Document

**Date:** 2026-02-28
**Type:** Testing Strategy Design
**Status:** ✅ Design Approved

---

## Overview

This document outlines the comprehensive testing strategy for Project Chimera, including full end-to-end testing of all 8 services using Test-Driven Development (TDD), Playwright for UI testing, and mock models for fast iteration.

---

## Requirements

| Requirement | Choice |
|-------------|--------|
| Testing Scope | Full End-to-End (every service, every endpoint) |
| Fix Strategy | Test-Driven Development (fix as we find issues) |
| AI Models | Mock/Stub (fast tests, no real models) |
| Environment | Full Docker/k3s Stack (realistic testing) |
| UI Testing | Full User Journey (every button, flow, responsive) |

---

## Architecture

### Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Runner (pytest)                     │
│                  + Playwright for E2E                       │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    k3s Cluster                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              8 Services Deployed                       │  │
│  │  OpenClaw → SceneSpeak → Captioning → BSL →          │  │
│  │  Sentiment → Lighting → Safety → Console              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Infrastructure (Redis, Kafka, Milvus)          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mock Layer                               │
│         Fake Model Responses + Test Data                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Service Tests (8 test files)
```
tests/integration/test_service_openclaw.py
tests/integration/test_service_scenespeak.py
tests/integration/test_service_captioning.py
tests/integration/test_service_bsl.py
tests/integration/test_service_sentiment.py
tests/integration/test_service_lighting.py
tests/integration/test_service_safety.py
tests/integration/test_service_console.py
```

For each service:
- Health endpoint validation
- All API endpoints (GET, POST, WebSocket)
- Request/response model validation
- Error handling
- WebSocket connections (where applicable)

### 2. Model Validation Tests
```
tests/unit/test_models_validation.py
```

Pydantic model testing:
- Required field validation
- Type checking
- Boundary values
- Invalid input rejection

### 3. Console UI Tests (Playwright)
```
tests/e2e/test_console_ui_complete.py
```

Full user journey:
- Page load and layout
- All buttons and forms
- Approval workflows
- Emergency stop
- WebSocket event streaming
- Responsive design (mobile, tablet, desktop)
- Dark mode toggle

### 4. Integration Flow Tests
```
tests/integration/test_full_pipeline_e2e.py
```

Cross-service workflows:
- Sentiment → SceneSpeak → Safety → Console
- Captioning → BSL translation
- Orchestration pipelines

### 5. Test Fixtures & Mocks
```
tests/fixtures/
  ├── mock_models.py      # Fake AI model responses
  ├── test_data.py        # Sample requests
  └── deployments.py      # k3s helpers
```

---

## Data Flow

### TDD Cycle

```
For Each Service (1-8):

1. WRITE FAILING TEST
   ├─► Import service model
   ├─► Create test request (with test data)
   ├─► Call service endpoint
   ├─► Assert expected response
   └─► Test fails (Red)

2. VERIFY FAILURE IS EXPECTED
   ├─► Is it a known issue (from deep dive)?
   ├─► Is it a new bug?
   └─► Document the issue

3. WRITE FIX
   ├─► Add missing model field
   ├─► Fix endpoint logic
   ├─► Update validation
   └─► Rebuild Docker image

4. REDEPLOY & RETEST
   ├─► kubectl rollout restart deployment
   ├─► Wait for pod ready
   └─► Run test again

5. TEST PASSES (Green)
   ├─► Commit fix
   ├─► Move to next test
   └─► Repeat

Service Complete → Move to Next Service
```

### Mock Data Flow

```
Test → Service Request
     ↓
Service → Model Layer → Mock Returns Fake Response
     ↓
Service → Response → Test Assertion
```

---

## Error Handling

### Test Execution Errors

```python
class K3sNotReadyError(Exception):
    """k3s cluster not available"""
    pass

class ServiceNotRunningError(Exception):
    """Service pod not running"""
    pass
```

### Test Isolation

```python
@pytest.fixture(autouse=True)
def isolate_test_data():
    """Clean up test data between tests"""
    yield
    # Clear Redis
    # Reset Kafka offsets
    # Clean up any created resources
```

### Known Issues Tracking

```python
@pytest.mark.xfail(reason="HONEST_DEEP_DIVE_REPORT: Captioning missing processing_time_ms")
def test_captioning_response_has_all_fields():
    """Will be fixed during TDD cycle"""
```

---

## Testing Strategy

### Phase 1: Model Validation Tests (Foundation)

Test all Pydantic models across 8 services.

**Known issues to fix via TDD:**
- Captioning: Add `processing_time_ms`, `model_version`
- BSL: Add `translation_time_ms`, `model_version`
- Sentiment: Fix `sentiment` type to `SentimentScore`, add fields
- Safety: Add `score`, `flagged` to `CategoryScore`

### Phase 2: Service API Tests (8 services)

Service-by-service testing in order:
1. OpenClaw Orchestrator
2. SceneSpeak Agent
3. Captioning Agent
4. BSL Agent
5. Sentiment Agent
6. Lighting Control
7. Safety Filter
8. Operator Console

### Phase 3: Operator Console UI Tests (Playwright)

Full user journey tests:
1. Page Load
2. Service Status Panel
3. Event Stream
4. Approval Workflow
5. Override Controls
6. Responsive Design
7. Dark Mode

### Phase 4: Integration Flow Tests

End-to-end workflows:
1. Sentiment → SceneSpeak → Safety → Console
2. Captioning → BSL translation
3. OpenClaw orchestration through multiple skills

### Phase 5: Fix & Verify Cycle

For each failing test:
1. Document the issue
2. Write the fix
3. Rebuild & redeploy
4. Verify test passes
5. Commit with fix message

---

## Test Execution Order

```
1. Model validation tests (fix known issues first)
2. Service API tests (service-by-service, 1-8)
3. Integration flow tests
4. Console UI tests (Playwright)
5. Full regression suite
```

---

## Success Criteria

- ✅ All model validation tests pass
- ✅ All service API tests pass
- ✅ All integration tests pass
- ✅ All Console UI tests pass
- ✅ Zero known issues remaining
- ✅ Complete test report generated

---

## Tools & Dependencies

```python
# requirements-test.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-playwright>=0.4.0
pytest-xdist>=3.3.0  # parallel execution
pytest-cov>=4.1.0    # coverage
pytest-html>=3.2.0   # HTML reports
requests>=2.31.0
websockets>=12.0
```

---

## Next Steps

1. Execute implementation plan using `superpowers:writing-plans`
2. Run TDD cycle service-by-service
3. Generate comprehensive test report
4. Create issue fixes for all failures
5. Verify all tests passing
6. Document final results

---

*Design approved: 2026-02-28*
*Project Chimera - Comprehensive Testing Strategy*

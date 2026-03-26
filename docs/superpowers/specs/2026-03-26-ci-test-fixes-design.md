# CI Test Fixes Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all remaining CI test failures to eliminate GitHub notifications

**Architecture:** Independent fixes across 4 areas - sentiment tests, platform unit tests, operator console UI routing, and CI verification

**Tech Stack:** Python, Playwright/TypeScript, Docker Compose, GitHub Actions

---

## Overview

This design addresses 4 independent issues preventing CI tests from passing:

1. **Sentiment API test timeouts** - Tests timeout (15s) waiting for lazy-loaded ML model (30-60s)
2. **Platform unit test failures** - Services lack `pyproject.toml` for pytest discovery
3. **Operator console UI test failures** - Tests look for UI on wrong service/port
4. **CI verification** - Need to confirm fixes work consistently

## 1. Sentiment Test Timeouts

**Problem:** `tests/e2e/api/sentiment.spec.ts` has 15s timeout, but sentiment service lazy-loads the ML model on first request (30-60s in CI).

**Solution:** Increase timeout to 60s for ML-dependent tests.

**Files to modify:**
- `tests/e2e/api/sentiment.spec.ts`

**Changes:**
- Tests that POST to `/api/analyze`: increase timeout to 60000ms
- Keep 15000ms for fast tests (health checks, validation)
- Tests to update: lines 30, 50, 63, 76, 88, 107, 151, 164, 193, 218

**Example:**
```typescript
// Before
test('@api sentiment analysis with ML model', async ({ request }) => {
  const response = await request.post(`${baseURL}/api/analyze`, {
    data: { text: 'This is absolutely amazing!' },
    timeout: 15000
  });
  // ...
});

// After
test('@api sentiment analysis with ML model', async ({ request }) => {
  const response = await request.post(`${baseURL}/api/analyze`, {
    data: { text: 'This is absolutely amazing!' },
    timeout: 60000  // 60s for ML model lazy load
  });
  // ...
});
```

## 2. Platform Unit Tests

**Problem:** Platform services in `platform/` directory have `tests/` folders and `requirements.txt` but no `pyproject.toml`, so pytest can't discover/run tests.

**Solution:** Add `pyproject.toml` to each platform service.

**Services to update:**
- `platform/orchestrator/`
- `platform/dashboard/`
- `platform/quality-gate/`
- `platform/cicd-gateway/`
- `platform/perf-optimizer/`

**Template for pyproject.toml:**
```toml
[project]
name = "<service-name>"
version = "0.1.0"
description = "<service description>"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "pydantic>=2.0.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

**Process:**
1. Read each service's `requirements.txt` to extract dependencies
2. Create `pyproject.toml` with project metadata and dependencies
3. Commit each service individually or as a batch

## 3. Operator Console UI Tests

**Problem:** E2E tests navigate to operator-console service (port 8007) expecting show control UI, but the dashboard is served by orchestrator service (port 8000) at `platform/orchestrator/static/dashboard.html`.

**Solution:** Update test configuration to point to orchestrator dashboard.

**Files to modify:**
- `tests/e2e/helpers/test-utils.ts` - Update `ChimeraTestHelper.navigateToConsole()`
- `tests/e2e/cross-service/show-workflow.spec.ts` - Update base URL if hardcoded

**Current behavior:**
- Tests go to `http://localhost:8007` (operator-console)

**New behavior:**
- Tests go to `http://localhost:8000` (orchestrator) for dashboard

**Implementation:**
1. Update `navigateToConsole()` method to use orchestrator URL
2. Verify orchestrator serves dashboard at `/` or `/dashboard`
3. Update any hardcoded port references from 8007 → 8000

**Note:** If orchestrator doesn't serve the dashboard at root, we may need to add a route like `@app.get("/")` that serves the static file.

## 4. CI Verification

**Problem:** Need to confirm all fixes work consistently across multiple CI runs.

**Solution:** Monitor + manual verification smoke test.

**Actions:**
1. Watch next 2-3 scheduled E2E runs (hourly at XX:14, XX:49)
2. Verify all 4 test shards pass consistently
3. Add a quick local smoke test command:
   ```bash
   # Quick health check of all services
   ./scripts/wait-for-services.sh
   ```

**Success criteria:**
- All E2E test shards pass for 3 consecutive scheduled runs
- Platform unit tests pass in CI
- No "sentiment failed to start" errors
- No "operator console UI not found" errors

## Implementation Order

1. **Platform unit tests** (quickest win, isolated)
2. **Sentiment test timeouts** (simple file edit, isolated)
3. **Operator console UI tests** (needs verification of orchestrator routes)
4. **CI verification** (depends on above)

## Testing Strategy

- **Unit tests:** Run `pytest` in each platform service directory
- **E2E tests:** Run full test suite locally with `docker compose`
- **Smoke test:** Use wait-for-services.sh to verify startup

## Rollback Plan

If any fix causes issues:
- Revert the commit
- Investigate failure logs
- Adjust approach and retry

---

**Next Steps:** After spec approval, use `superpowers:writing-plans` to create detailed implementation plan.

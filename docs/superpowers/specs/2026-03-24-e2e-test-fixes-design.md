# E2E Test Fixes Design Specification

**Date:** 2026-03-24
**Status:** Draft
**Author:** Claude Code
**Related Issue:** GitHub Actions E2E Tests - 10 consecutive failures

---

## Overview

This specification defines a comprehensive fix for Project Chimera's failing E2E tests. The current state shows:
- **87% pass rate** (82/94 tests passing)
- **10 consecutive CI failures** on GitHub Actions
- **Root causes:** Outdated Docker images in CI, slow service startup, test timing issues

This design addresses all three root causes with durable, production-ready solutions.

---

## Problem Statement

### Current State

| Metric | Value |
|--------|-------|
| CI Success Rate | 0% (10 consecutive failures) |
| Local Test Pass Rate | 87% (82/94 tests) |
| Target Pass Rate | 93%+ |
| CI Timeout Frequency | 50%+ (services not ready in time) |

### Root Causes Identified

1. **Docker Build Mismatch**
   - CI builds images from source without local improvements
   - Missing `curl` for healthchecks
   - Missing shared modules (`services/shared/models/`)
   - No version tagging or caching strategy

2. **Service Startup Delays**
   - ML models load at startup (60-90s delay)
   - CI waits only 120s for ALL services
   - No differentiation between "container running" and "models loaded"
   - Sequential dependencies slow parallel startup

3. **Test Reliability Issues**
   - Hard-coded timeouts instead of condition-based waits
   - WebSocket race conditions
   - Orchestrator calls wrong endpoint paths
   - Inadequate failure diagnostics

---

## Solution Design

### 1. CI Environment Fixes

#### 1.1 CI Build Strategy Clarification

**Current CI Behavior:** The GitHub Actions workflow does NOT build Docker images. It runs `docker-compose up` which:
- Pulls existing images from Docker Hub/registry (if available)
- Builds images locally if not found (using local Dockerfile)
- Does NOT use version tags or consistent image naming

**Problem:** Local development has rebuilt images (with curl, shared modules), but CI builds from source each run, getting different results.

**Solution A: Pre-build and Push Images (Recommended)**
- Build all service images locally with consistent tags
- Push to Docker Hub or GitHub Container Registry
- Update CI to pull pre-built images instead of building
- Update docker-compose.yml to use specific image tags

**Solution B: CI Builds with Caching**
- Use GitHub Actions cache for Docker layers
- Add explicit build step to CI workflow before docker-compose up
- Implement BuildKit with cache mounts for faster builds

**Recommendation:** Use Solution A for consistency and speed.

#### 1.2 GPU/CPU Mismatch

**Problem:** ML services (scenespeak, captioning, bsl, sentiment, music) require CUDA/GPU, but GitHub Actions `ubuntu-latest` runners have no GPU.

**Solution: CPU-Only CI Mode**

Add environment variable to enable CPU mode in CI:
```yaml
env:
  CI_GPU_AVAILABLE: "false"
  DEVICE: "cpu"
```

Update services to detect this and:
- Skip CUDA initialization
- Use CPU versions of models (quantized where available)
- Disable GPU-dependent features gracefully
- Add mock/fast endpoints for CI testing

#### 1.3 Dockerfile Standards

All Dockerfiles MUST:
- Install `curl` in apt-get RUN command
- Copy shared modules from `../../shared/` (if applicable)
- Use consistent base images (python:3.12-slim where applicable)
- Follow layer caching best practices (dependencies before code)

#### 1.4 Build Context Configuration

Update docker-compose.yml build contexts:
```yaml
bsl-agent:
  build:
    context: ./services
    dockerfile: bsl-agent/Dockerfile
    args:
      - SERVICE_VERSION=${SERVICE_VERSION:-1.0.0}
```

This allows access to `./services/shared/` during build.

#### 1.5 Dockerfile Validation Script

**File:** `scripts/validate-dockerfiles.sh`

Checks:
- All Dockerfiles install `curl`
- All services importing from shared have proper COPY commands
- Consistent EXPOSE ports across Dockerfile and docker-compose.yml
- No deprecated patterns

**Integration:** Add to `e2e-tests.yml` as first step.

### 2. Service Startup Optimization

**Problem:** Services don't become healthy within CI's 120-second timeout. Model downloads and initialization take too long. Additionally, CI has no GPU which changes model loading behavior.

**Solution:**

**A. Implement Deferred Model Loading**
- Change services to load ML models **on first request** rather than at startup
- Add `model_loaded` status to `/health` endpoint
- Services return 200 immediately (container running), models load lazily
- First request to each service may be slow (model loading), subsequent requests fast
- Update wait-for-services.sh to only check container startup, not model loading
- In CI (no GPU), use smaller/quantized models or mock model responses

**B. CI Model Caching Strategy**

**Challenge:** GitHub Actions runners don't persist Docker volumes between runs.

**Solution A: GitHub Actions Cache (Recommended)**
```yaml
- name: Cache HuggingFace Models
  uses: actions/cache@v4
  with:
    path: ~/.cache/huggingface
    key: ${{ runner.os }}-models-${{ hashFiles('**/models.txt') }}
```

Add `models.txt` files listing required models for each service.

**Solution B: Pre-built CI Images with Models**
- Create separate Docker images with models baked in
- Tag as `chimera/{service}:ci-with-models`
- Use these images only in CI workflows
- Larger image size but instant startup

**Recommendation:** Use Solution A (GitHub Actions cache) for flexibility.

**C. CPU-Optimized Model Loading**
- In CI (no GPU), use smaller quantized models
- Set `MODEL_VARIANT=ci` env var in CI workflows
- Load 8-bit models instead of 16-bit where available
- Skip optional features (avatar rendering, music generation) in CI
- Add mock endpoints for CI where appropriate

**D. Parallelize Service Dependencies**
- Remove unnecessary `depends_on` conditions
- Use `restart: on-failure` with appropriate retry counts
- Let services start in parallel, fail independently if they have issues

**E. Optimize Healthcheck Intervals**
- Reduce `start_period` in healthchecks from 60-90s to 30s where appropriate
- Reduce `interval` from 30s to 10s for faster feedback
- Adjust `retries` to balance speed vs reliability

### 3. Test Reliability Fixes

#### 3.1 Orchestrator Endpoint Mapping Fix

**Problem:** `call_agent()` function (line 524) constructs `/v1/{skill}` but agents actually use `/api/{action}` endpoints.

**Current code (line 524):**
```python
endpoint = f"/v1/{skill}"  # Wrong! Constructs /v1/sentiment_analysis
```

**Agent endpoints actually implemented:**
- scenespeak: `/api/generate`
- captioning: `/api/transcribe`
- bsl: `/api/translate`
- sentiment: `/api/analyze`
- autonomous: `/execute` (already correct)

**Fix:** Update `call_agent()` function to use correct endpoint paths:
```python
# Map skill names to actual endpoint paths
skill_endpoints = {
    "dialogue_generator": "/api/generate",
    "captioning": "/api/transcribe",
    "bsl_translation": "/api/translate",
    "sentiment_analysis": "/api/analyze",
    "autonomous_execution": "/execute",
}

endpoint = skill_endpoints.get(skill, f"/v1/{skill}")
```

#### 3.2 Test Timing Improvements

**Replace:**
```typescript
await page.waitForTimeout(5000);
```

**With:**
```typescript
await page.waitForSelector('[data-testid="dialogue-result"]');
await page.waitForResponse(resp => resp.url().includes('/api/generate'));
```

#### 3.3 WebSocket Test Fixes

Add connection handshake:
```typescript
// Wait for WebSocket ready message
const wsMessage = await page.waitForEvent('websocket', ws => {
  return ws.frame().payloadData().includes('{"type":"connected"}');
});
```

#### 3.4 Test Data Factories

**File:** `tests/e2e/helpers/factories.ts`

```typescript
export function createShowRequest(overrides?: Partial<ShowRequest>): ShowRequest {
  return {
    show_id: `test-show-${Date.now()}`,
    duration: 300,
    ...overrides
  };
}
```

### 4. Implementation Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CI Pipeline Flow                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. VALIDATE STAGE                                                      │
│     └─ scripts/validate-dockerfiles.sh                                │
│     └─ Checks: curl, shared modules, consistent patterns                │
│                                                                         │
│  2. BUILD STAGE                                                         │
│     ├─ Generate VERSION from git SHA                                   │
│     ├─ docker-compose build with BuildKit                              │
│     ├─ Tag: chimera/{service}:v1.0.0-{sha}                            │
│     └─ Load model cache volume (optional)                              │
│                                                                         │
│  3. STARTUP STAGE                                                      │
│     ├─ docker-compose up -d (parallel startup)                        │
│     ├─ Wait for /health/ready (30s timeout)                           │
│     └─ Wait for /health/live (180s timeout, ML services)             │
│                                                                         │
│  4. TEST STAGE                                                          │
│     ├─ npx playwright test --shard=4/4                                │
│     ├─ Enhanced waits & assertions                                    │
│     └─ Screenshots + logs on failure                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `docker/VERSION` | Generated version file from git SHA |
| `scripts/validate-dockerfiles.sh` | Dockerfile validation |
| `scripts/pre-cache-models.sh` | Model cache warm-up |
| `tests/e2e/helpers/factories.ts` | Test data factories |

### Modified Files

| Category | Files | Changes |
|----------|-------|---------|
| Dockerfiles | 13 service Dockerfiles | Add curl, consistent patterns |
| CI/CD | `.github/workflows/e2e-tests.yml` | Add validation step, version tagging |
| Docker Compose | `docker-compose.yml` | Build contexts, shared volume mount |
| Services | `*/config.py` | Add endpoint configuration |
| Services | `*/main.py` | Add /health/ready endpoints |
| Scripts | `scripts/wait-for-services.sh` | Two-stage health check |
| Tests | ~30 test files | Timing, assertion, and wait fixes |

---

## Implementation Phases

### Phase 1: Pre-build and Push Docker Images (Week 1)

**Priority:** HIGH - Establishes consistent baseline for CI

1. Build all service images locally with consistent tagging
2. Tag images: `chimera/{service}:v1.0.0-latest` and `chimera/{service}:ci`
3. Push images to Docker Hub or GitHub Container Registry
4. Update docker-compose.yml to use pre-built images in CI
5. Test locally: verify images work correctly
6. Create `scripts/validate-dockerfiles.sh` for future validation

**Success Criteria:** CI pulls consistent images that match local environment

### Phase 1B: Add CI CPU Mode Support (Week 1)

**Priority:** HIGH - Required for CI functionality

1. Add `CI_GPU_AVAILABLE=false` environment variable to ML services
2. Update services to detect CPU mode and use appropriate models
3. Add `models.txt` files listing required models for GitHub Actions cache
4. Configure GitHub Actions cache in `.github/workflows/e2e-tests.yml`

**Success Criteria:** Services start in CI (without GPU) using CPU models

### Phase 2: Orchestrator Endpoint Fix (Week 1)

**Priority:** HIGH - Quick win, unblocks tests

1. Fix `call_agent()` function in `services/openclaw-orchestrator/main.py`
2. Update endpoint mapping to use `/api/{action}` paths
3. Test orchestrator locally with mocked agent responses
4. Deploy to CI and verify fix

**Success Criteria:** Orchestration calls reach correct agent endpoints

### Phase 3: Test Reliability Fixes (Week 1-2)

**Priority:** HIGH - Can validate locally

1. Update test files with proper waits (no hardcoded timeouts)
2. Fix WebSocket test race conditions
3. Add test data factories
4. Run tests locally to achieve 93%+ pass rate
5. Address specific failing tests identified from test runs

**Success Criteria:** 93%+ tests passing locally

### Phase 4: Service Startup Optimization (Week 2-3)

**Priority:** MEDIUM - Reduces CI flakiness

1. Implement deferred model loading (load on first request)
2. Add GitHub Actions cache for HuggingFace models
3. Create CI-specific configuration files
4. Rewrite wait-for-services.sh with simpler logic (just check container is up)
5. Add CPU-optimized model loading paths

**Success Criteria:** CI consistently completes within timeout

### Phase 5: Validation & Monitoring (Week 3)

**Priority:** LOW - Quality assurance

1. Run full CI pipeline 10+ times to verify stability
2. Add test metrics tracking (pass rate by test suite)
3. Create dashboard for CI health monitoring
4. Document known issues and future work

**Success Criteria:** 95%+ CI success rate over 20 runs
3. Fix WebSocket test race conditions
4. Add test data factories
5. Run tests locally to achieve 93%+ pass rate

**Success Criteria:** 93%+ tests passing locally

### Phase 3: Service Startup Optimization (Week 2)

**Priority:** MEDIUM - Reduces CI flakiness

1. Add `/health/ready` endpoints to all services
2. Implement model cache volume
3. Create pre-cache-models.sh script
4. Rewrite wait-for-services.sh with two-stage logic
5. Update CI workflow timeout values
6. Test in CI environment

**Success Criteria:** CI consistently completes startup phase within timeout

### Phase 4: Validation & Monitoring (Week 2-3)

**Priority:** LOW - Quality assurance

1. Run full CI pipeline 10+ times to verify stability
2. Add test metrics tracking (pass rate by test suite)
3. Create dashboard for CI health monitoring
4. Document known flaky tests for future investigation

**Success Criteria:** 95%+ CI success rate over 20 runs

---

## Testing Strategy

### Local Validation

Before pushing to CI, validate changes locally:
```bash
# 1. Validate Dockerfiles
./scripts/validate-dockerfiles.sh

# 2. Rebuild all services
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Run full test suite
cd tests/e2e
npx playwright test
```

### CI Validation

After merging, monitor CI for:
- Build success rate
- Test pass rate
- Startup time consistency
- Specific test failure patterns

### Rollback Plan

If any phase introduces regressions:
1. Identify which commit caused regression
2. Revert that specific change
3. Investigate alternative approach
4. Re-test before re-merging

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docker build breaks in CI | Medium | High | Validate locally first; add rollback step |
| Model cache increases CI storage | Low | Medium | Use cache only for main branch; clean old caches |
| Test fixes introduce new flakiness | Medium | Medium | Run tests 10+ times locally; add retry logic |
| CI timeout still insufficient | Low | Medium | Make timeout configurable; monitor and adjust |

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| CI Success Rate | 0% | 95%+ | 20 consecutive CI runs |
| Test Pass Rate | 87% | 93%+ | E2E test results |
| Startup Time (all services) | >120s (failing) | <60s | CI logs |
| Test Duration | ~15 min | <20 min | CI logs |
| False Negative Rate | Unknown | <5% | Flaky test tracking |

---

## Open Questions

1. **Model Cache Strategy:** Should we pre-build model cache images and push to registry, or build fresh in CI each run?
2. **Timeout Values:** 180s for model loading - is this sufficient for all services on CI hardware?
3. **Backward Compatibility:** Do we need to maintain support for `/health` returning immediately (breaking change)?

---

## References

- E2E Testing Progress: `docs/E2E-TESTING-PROGRESS.md`
- Docker Compose Config: `docker-compose.yml`
- CI Workflow: `.github/workflows/e2e-tests.yml`
- Test Documentation: `tests/e2e/README.md`

---

**Next Steps:**
1. User review of this spec
2. Create detailed implementation plan
3. Execute Phase 1 (Docker build fixes)
4. Execute Phase 2 (Test fixes)
5. Execute Phase 3 (Startup optimization)
6. Execute Phase 4 (Validation)

---

*Last Updated:* 2026-03-24
*Status:* Draft - Pending User Review

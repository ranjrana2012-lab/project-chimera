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

### 1. CI Docker Build Fixes

#### 1.1 Standardized Image Versioning

**Implementation:**
```bash
# Generate VERSION file from git SHA
VERSION="v1.0.0-$(git rev-parse --short HEAD)"
echo $VERSION > docker/VERSION
```

**Image tag format:** `chimera/{service-name}:v1.0.0-{git-sha}`

#### 1.2 Dockerfile Standards

All Dockerfiles MUST:
- Install `curl` in apt-get RUN command
- Copy shared modules from `../../shared/` (if applicable)
- Use consistent base images (python:3.12-slim where applicable)
- Follow layer caching best practices (dependencies before code)

#### 1.3 Build Context Configuration

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

#### 1.4 Dockerfile Validation Script

**File:** `scripts/validate-dockerfiles.sh`

Checks:
- All Dockerfiles install `curl`
- All services importing from shared have proper COPY commands
- Consistent EXPOSE ports across Dockerfile and docker-compose.yml
- No deprecated patterns (deprecated FROM images, etc.)

**Integration:** Add to `e2e-tests.yml` as first step before docker-compose build.

### 2. Service Startup Optimization

#### 2.1 Two-Stage Health Pattern

**Pattern:**
```
/health/ready → Returns 200 immediately (container running)
/health/live → Returns 200 only when models loaded
```

**Implementation per service:**

| Service | /health/ready | /health/live |
|---------|---------------|--------------|
| orchestrator | Immediate | Immediate (no ML) |
| scenespeak | Immediate | After LLM loads |
| captioning | Immediate | After Whisper loads |
| bsl | Immediate | After avatar loads |
| sentiment | Immediate | After DistilBERT loads |
| music-generation | Immediate | After MusicGen loads |
| safety-filter | Immediate | Immediate |
| operator-console | Immediate | Immediate |

#### 2.2 Model Cache Volume

**New volume:** `chimera-model-cache`

**Pre-population script:** `docker/pre-cache-models.sh`

Downloads models to cache volume once before starting services. Services then load from cache (5-10s vs 60-90s).

#### 2.3 Wait Script Rewrite

**File:** `scripts/wait-for-services.sh`

**New logic:**
1. Wait for `/health/ready` on all services (30s timeout)
2. Once all ready, wait for `/health/live` on ML services (180s timeout)
3. Report which services are ready and which are still loading

**Exit codes:**
- 0: All services fully ready
- 1: Service failed to start (container not running)
- 2: Service timeout during model load

#### 2.4 Parallel Startup

Remove `depends_on` conditions where services don't actually depend on each other. Use `restart: on-failure` instead.

### 3. Test Reliability Fixes

#### 3.1 Orchestrator Endpoint Mapping

**File:** `services/openclaw-orchestrator/main.py`

Update `get_agent_for_skill()` mapping:
```python
skill_to_agent = {
    "dialogue_generator": f"{AGENTS['scenespeak-agent']}/api/generate",
    "captioning": f"{AGENTS['captioning-agent']}/api/transcribe",
    "bsl_translation": f"{AGENTS['bsl-agent']}/api/translate",
    "sentiment_analysis": f"{AGENTS['sentiment-agent']}/api/analyze",
    "autonomous_execution": f"{AGENTS['autonomous-agent']}/execute",
}
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

### Phase 1: Docker Build Fixes (Week 1)

**Priority:** HIGH - Blocks all other improvements

1. Create `scripts/validate-dockerfiles.sh`
2. Update all 13 Dockerfiles to install curl
3. Add shared module COPY commands where needed
4. Update docker-compose.yml build contexts
5. Add VERSION generation to CI workflow
6. Test locally: rebuild all services, verify they work

**Success Criteria:** All services rebuild successfully with curl and shared modules

### Phase 2: Test Fixes (Week 1-2)

**Priority:** HIGH - Can validate locally

1. Fix orchestrator endpoint mappings
2. Update test files with proper waits (no hardcoded timeouts)
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

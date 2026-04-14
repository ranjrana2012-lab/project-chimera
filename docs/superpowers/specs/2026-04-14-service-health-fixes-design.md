# Service Health Fixes and Docker Optimization Design

> **Date:** 2026-04-14
> **Status:** Approved
> **Priority:** High

## Problem Statement

**Issue 1: Hardware-Bridge Health Check Failure**
- Docker health check fails with ImportError
- Root cause: `requests` library not in requirements.txt
- Impact: Service marked unhealthy despite API working correctly

**Issue 2: Sentiment-Agent ML Model Permission Denied**
- ML model fails to load: `[Errno 13] Permission denied: '/app/models/models--distilbert-base-uncased-finetuned-sst-2-english'`
- Service falls back to mock sentiment mode
- Root cause: `/app/models/` owned by root, appuser cannot write
- HuggingFace Hub ignores `cache_dir` parameter, uses default cache location

**Issue 3: Remaining Large Docker Images**
- sentiment-agent: 3.1GB
- safety-filter: 2.48GB
- operator-console: 2.48GB
- Should be <500MB like other services after .dockerignore optimization

## Proposed Approach: Comprehensive Fix

Fix both health issues, optimize remaining images, add tests to prevent regressions.

## Architecture Decisions

### Decision 1: Use HF_HUB_CACHE Environment Variable

**Chosen:** Set `HF_HUB_CACHE=/app/models_cache` in Dockerfile

**Rationale:**
- Documented HuggingFace approach
- /app/models_cache already owned by appuser
- No permission changes needed
- Cleaner than chown workaround

**Trade-off:** Requires rebuild to take effect

### Decision 2: Minimal Dockerfile Changes for Health Check

**Chosen:** Add single line to requirements.txt

**Rationale:**
- Smallest possible fix
- No logic changes needed
- Consistent with existing pattern

**Trade-off:** None

### Decision 3: Sequential Image Rebuilds

**Chosen:** Rebuild one at a time, verify health

**Rationale:**
- Minimizes downtime
- Can test each service independently
- Faster rollback if issues

**Trade-off:** Slower overall than parallel rebuild

## Implementation Design

### Phase 1: Fix Hardware-Bridge Health Check

**File:** `services/echo-agent/requirements.txt`
- Add: `requests>=2.31.0`
- Rebuild chimera-hardware-bridge image
- Verify health check passes

### Phase 2: Fix Sentiment-Agent ML Model Permissions

**File:** `services/sentiment-agent/Dockerfile`
- Add: `ENV HF_HUB_CACHE=/app/models_cache`
- Add: `ENV TRANSFORMERS_CACHE=/app/models_cache`
- Rebuild chimera-sentiment-agent image
- Verify model loads without permission errors
- Test real sentiment analysis endpoint

### Phase 3: Optimize Remaining Images

**Services to rebuild:**
1. chimera-sentiment-agent
2. chimera-safety-filter
3. chimera-operator-console

**Process per service:**
1. Stop container
2. Remove old image
3. Build with .dockerignore (verify build context <100MB)
4. Verify new image size <500MB
5. Start container
6. Verify health check passes

### Phase 4: Add Health Check Tests

**File:** `tests/integration/mvp/test_service_health.py` (new)

```python
import pytest
from scripts.test_helpers import get_service_health

@pytest.mark.integration
def test_all_services_healthy():
    """Verify all 8 services pass Docker health check."""
    services = {
        "orchestrator": 8000,
        "scenespeak": 8001,
        "sentiment": 8004,
        "safety": 8005,
        "translation": 8006,
        "hardware": 8008,
        "console": 8007,
    }
    for service, port in services.items():
        status = get_service_health(service)
        assert status == "healthy", f"{service} not healthy: {status}"
```

## Success Criteria

- [ ] hardware-bridge shows "(healthy)" in docker ps
- [ ] sentiment-agent loads ML model without errors
- [ ] sentiment-agent real sentiment analysis working
- [ ] All 8 services show "(healthy)"
- [ ] All rebuilt images <500MB
- [ ] Health check tests pass
- [ ] All integration tests pass

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HF_HUB_CACHE doesn't work | Low | High | Test in Dockerfile build, fallback to chown |
| Image rebuild breaks service | Low | Medium | Keep old image until new verified |
| Health check still fails | Low | Low | Add debug logging to healthcheck |

## Estimated Time

- Phase 1 (hardware-bridge): 5 minutes
- Phase 2 (sentiment-agent): 10 minutes
- Phase 3 (image optimization): 15 minutes
- Phase 4 (tests): 10 minutes
- **Total: ~40 minutes**

## Files to Modify

**Create:**
- `tests/integration/mvp/test_service_health.py`

**Modify:**
- `services/echo-agent/requirements.txt` (add requests)
- `services/sentiment-agent/Dockerfile` (add HF_HUB_CACHE)

**Rebuild:**
- chimera-hardware-bridge
- chimera-sentiment-agent
- chimera-safety-filter
- chimera-operator-console

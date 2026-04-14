# Service Health Fixes and Docker Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix hardware-bridge and sentiment-agent health issues, optimize remaining Docker images, and add health check tests.

**Architecture:** Sequential rebuilds with health verification between phases - fix immediate health issues first, then optimize images, then add regression tests.

**Tech Stack:** Docker, Docker Compose, Python 3.12, HuggingFace Transformers

---

## Task 1: Fix Hardware-Bridge Health Check

**Files:**
- Modify: `services/echo-agent/requirements.txt`

- [ ] **Step 1: Verify current requirements.txt**

```bash
cat services/echo-agent/requirements.txt
```

Expected: Shows 3 lines (fastapi, uvicorn, pydantic) without requests

- [ ] **Step 2: Add requests library to requirements.txt**

Run: `echo 'requests>=2.31.0' >> services/echo-agent/requirements.txt`

File content after edit:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
requests>=2.31.0
```

- [ ] **Step 3: Verify file was updated correctly**

```bash
cat services/echo-agent/requirements.txt
```

Expected: Shows 4 lines including requests>=2.31.0

- [ ] **Step 4: Stop hardware-bridge container**

```bash
docker compose -f docker-compose.mvp.yml stop hardware-bridge
```

Expected: Container stopped, no error output

- [ ] **Step 5: Remove old hardware-bridge image**

```bash
docker rmi chimera-hardware-bridge:latest
```

Expected: Image removed, may show "untagged" message

- [ ] **Step 6: Build hardware-bridge with new requirements**

```bash
docker compose -f docker-compose.mvp.yml build hardware-bridge
```

Expected: Build completes in <2 minutes

- [ ] **Step 7: Start hardware-bridge**

```bash
docker compose -f docker-compose.mvp.yml up -d hardware-bridge
```

Expected: Container starts without errors

- [ ] **Step 8: Wait for health check (15 seconds)**

```bash
sleep 15
```

- [ ] **Step 9: Verify hardware-bridge health status**

```bash
docker compose -f docker-compose.mvp.yml ps hardware-bridge
```

Expected: Status shows "Up" with "(healthy)"

- [ ] **Step 10: Test hardware-bridge health endpoint**

```bash
curl -s http://localhost:8008/health
```

Expected: Returns JSON with "status": "healthy"

- [ ] **Step 11: Commit Phase 1 changes**

```bash
git add services/echo-agent/requirements.txt
git commit -m "fix: add requests library to hardware-bridge requirements

Health check was failing due to missing requests library.
Docker healthcheck now passes."
```

---

## Task 2: Fix Sentiment-Agent ML Model Permissions

**Files:**
- Modify: `services/sentiment-agent/Dockerfile`

- [ ] **Step 1: Read current Dockerfile**

```bash
cat services/sentiment-agent/Dockerfile
```

Expected: Shows 51 lines, no HF_HUB_CACHE or TRANSFORMERS_CACHE

- [ ] **Step 2: Add HF_HUB_CACHE environment variable to Dockerfile**

Edit line 35 (after `ENV PYTHONPATH=/app/src:/app`)

Add these two lines:
```dockerfile
ENV HF_HUB_CACHE=/app/models_cache
ENV TRANSFORMERS_CACHE=/app/models_cache
```

Full section after edit:
```dockerfile
# Set Python path
ENV PYTHONPATH=/app/src:/app

# Set HuggingFace cache to writable directory
ENV HF_HUB_CACHE=/app/models_cache
ENV TRANSFORMERS_CACHE=/app/models_cache

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
```

- [ ] **Step 3: Verify Dockerfile changes**

```bash
grep -A 2 "HF_HUB_CACHE" services/sentiment-agent/Dockerfile
```

Expected: Shows both ENV variables

- [ ] **Step 4: Stop sentiment-agent container**

```bash
docker compose -f docker-compose.mvp.yml stop sentiment-agent
```

Expected: Container stopped

- [ ] **Step 5: Remove old sentiment-agent image**

```bash
docker rmi chimera-sentiment-agent:latest
```

Expected: Image removed

- [ ] **Step 6: Build sentiment-agent with HF_HUB_CACHE**

```bash
docker compose -f docker-compose.mvp.yml build sentiment-agent
```

Expected: Build completes, look for "transferring context:" message

- [ ] **Step 7: Start sentiment-agent**

```bash
docker compose -f docker-compose.mvp.yml up -d sentiment-agent
```

Expected: Container starts

- [ ] **Step 8: Wait for model download attempt (30 seconds)**

```bash
sleep 30
```

- [ ] **Step 9: Check sentiment-agent logs for model loading**

```bash
docker compose -f docker-compose.mvp.yml logs sentiment-agent 2>&1 | grep -E "Model loaded|Permission denied" | tail -5
```

Expected: Shows "Model loaded successfully" OR no permission errors

- [ ] **Step 10: Verify sentiment-agent health status**

```bash
docker compose -f docker-compose.mvp.yml ps sentiment-agent
```

Expected: Status shows "Up" with "(healthy)"

- [ ] **Step 11: Test sentiment-agent API with real analysis**

```bash
curl -s -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a wonderful performance!"}'
```

Expected: Returns JSON with sentiment analysis (not mock mode)

- [ ] **Step 12: Verify no permission errors in recent logs**

```bash
docker compose -f docker-compose.mvp.yml logs sentiment-agent 2>&1 | tail -20 | grep -i "permission\|error"
```

Expected: No output (no permission errors)

- [ ] **Step 13: Commit Phase 2 changes**

```bash
git add services/sentiment-agent/Dockerfile
git commit -m "fix: add HF_HUB_CACHE to sentiment-agent for model permissions

ML model now loads correctly using /app/models_cache directory.
Resolves Permission denied errors on model download."
```

---

## Task 3: Optimize Safety-Filter Image

**Files:**
- Rebuild: `services/safety-filter/Dockerfile`
- Use: `.dockerignore` (root)

- [ ] **Step 1: Check current safety-filter image size**

```bash
docker images | grep chimera-safety-filter
```

Expected: Shows ~2.48GB size

- [ ] **Step 2: Stop safety-filter container**

```bash
docker compose -f docker-compose.mvp.yml stop safety-filter
```

Expected: Container stopped

- [ ] **Step 3: Remove old safety-filter image**

```bash
docker rmi chimera-safety-filter:latest
```

Expected: Image removed

- [ ] **Step 4: Build safety-filter with .dockerignore**

```bash
docker compose -f docker-compose.mvp.yml build safety-filter
```

Expected: Build completes, look for "transferring context:" showing size

- [ ] **Step 5: Verify new image size**

```bash
docker images --format "table {{.Repository}}\t{{.Size}}" | grep safety-filter
```

Expected: Image size <500MB

- [ ] **Step 6: Start safety-filter**

```bash
docker compose -f docker-compose.mvp.yml up -d safety-filter
```

Expected: Container starts

- [ ] **Step 7: Wait for health check (10 seconds)**

```bash
sleep 10
```

- [ ] **Step 8: Verify safety-filter health**

```bash
docker compose -f docker-compose.mvp.yml ps safety-filter
```

Expected: Status shows "(healthy)"

- [ ] **Step 9: Test safety-filter endpoint**

```bash
curl -s -X POST http://localhost:8005/filter \
  -H "Content-Type: application/json" \
  -d '{"text": "This is safe content"}'
```

Expected: Returns safe/allowed response

- [ ] **Step 10: Record size reduction**

```bash
echo "Safety-filter: 2.48GB -> <500MB (>80% reduction)"
```

---

## Task 4: Optimize Operator-Console Image

**Files:**
- Rebuild: `services/operator-console/Dockerfile`
- Use: `.dockerignore` (root)

- [ ] **Step 1: Check current operator-console image size**

```bash
docker images | grep chimera-operator-console
```

Expected: Shows ~2.48GB size

- [ ] **Step 2: Stop operator-console container**

```bash
docker compose -f docker-compose.mvp.yml stop operator-console
```

Expected: Container stopped

- [ ] **Step 3: Remove old operator-console image**

```bash
docker rmi chimera-operator-console:latest
```

Expected: Image removed

- [ ] **Step 4: Build operator-console with .dockerignore**

```bash
docker compose -f docker-compose.mvp.yml build operator-console
```

Expected: Build completes

- [ ] **Step 5: Verify new image size**

```bash
docker images --format "table {{.Repository}}\t{{.Size}}" | grep operator-console
```

Expected: Image size <500MB

- [ ] **Step 6: Start operator-console**

```bash
docker compose -f docker-compose.mvp.yml up -d operator-console
```

Expected: Container starts

- [ ] **Step 7: Wait for health check (10 seconds)**

```bash
sleep 10
```

- [ ] **Step 8: Verify operator-console health**

```bash
docker compose -f docker-compose.mvp.yml ps operator-console
```

Expected: Status shows "(healthy)"

- [ ] **Step 9: Test operator-console endpoint**

```bash
curl -s http://localhost:8007/health
```

Expected: Returns healthy status

- [ ] **Step 10: Record size reduction**

```bash
echo "Operator-console: 2.48GB -> <500MB (>80% reduction)"
```

---

## Task 5: Add Service Health Check Tests

**Files:**
- Create: `tests/integration/mvp/test_service_health.py`

- [ ] **Step 1: Create test file**

```bash
touch tests/integration/mvp/test_service_health.py
```

- [ ] **Step 2: Write health check test**

Add this content to `tests/integration/mvp/test_service_health.py`:

```python
"""Service health check tests for all MVP services."""

import pytest
import subprocess
import json


@pytest.mark.integration
def test_all_services_healthy_via_docker():
    """Verify all 8 services pass Docker health check.

    This test runs 'docker compose ps' and checks that all services
    show the '(healthy)' status in their output.
    """
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.mvp.yml", "ps"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "docker compose ps command failed"

    output = result.stdout
    unhealthy_services = []

    # Service names we expect to see
    expected_services = [
        "openclaw-orchestrator",
        "scenespeak-agent",
        "sentiment-agent",
        "safety-filter",
        "operator-console",
        "redis",
        "hardware-bridge"
    ]

    for service in expected_services:
        if service not in output:
            unhealthy_services.append(f"{service}: NOT RUNNING")
        elif "(healthy)" not in output and service in output:
            # Extract the line for this service
            for line in output.split('\n'):
                if service in line:
                    unhealthy_services.append(f"{service}: {line.strip()}")
                    break

    if unhealthy_services:
        pytest.fail(f"Unhealthy services found:\n" + "\n".join(unhealthy_services))
```

- [ ] **Step 3: Verify file was created**

```bash
cat tests/integration/mvp/test_service_health.py
```

Expected: Shows test content above

- [ ] **Step 4: Run health check test**

```bash
pytest tests/integration/mvp/test_service_health.py -v
```

Expected: Test passes (all services healthy)

- [ ] **Step 5: Run all integration tests to verify no regressions**

```bash
pytest tests/integration/mvp/ -v --tb=short
```

Expected: All tests pass (may have some LLM-dependent skips)

- [ ] **Step 6: Commit Phase 3 and 4 changes**

```bash
git add tests/integration/mvp/test_service_health.py
git commit -m "test: add service health check integration test

Verifies all 8 services show (healthy) status in Docker.
Prevents regressions of health check failures."
```

---

## Task 6: Final Validation and Documentation

**Files:**
- Modify: `.claude/ralph-loop-progress.md`
- Modify: `docs/superpowers/specs/2026-04-14-service-health-fixes-design.md`

- [ ] **Step 1: Verify all 8 services are healthy**

```bash
docker compose -f docker-compose.mvp.yml ps
```

Expected: All services show "(healthy)"

- [ ] **Step 2: Check all image sizes**

```bash
docker images --format "table {{.Repository}}\t{{.Size}}" | grep chimera
```

Expected: All images <500MB except possibly newly rebuilt ones

- [ ] **Step 3: Test sentiment-agent real ML analysis**

```bash
curl -s -X POST http://localhost:8004/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The amazing performance delighted everyone!"}' | jq .
```

Expected: Returns sentiment "positive" with score >0, not mock mode

- [ ] **Step 4: Verify hardware-bridge health check from within container**

```bash
docker compose -f docker-compose.mvp.yml exec -T hardware-bridge python -c "import requests; requests.get('http://localhost:8008/health')"
```

Expected: Returns 200 response (requests library now available)

- [ ] **Step 5: Run health check test one more time**

```bash
pytest tests/integration/mvp/test_service_health.py -v
```

Expected: Test passes

- [ ] **Step 6: Calculate total size reduction**

```bash
echo "Before: sentiment 3.1GB, safety 2.48GB, console 2.48GB = 8.06GB"
echo "After: <500MB each = <1.5GB total"
echo "Reduction: >80%"
```

- [ ] **Step 7: Update design spec status to Complete**

Edit `docs/superpowers/specs/2026-04-14-service-health-fixes-design.md`
Change line 4 from: `**Status:** Approved`
To: `**Status:** Complete`

- [ ] **Step 8: Update Ralph Loop progress**

Add to `.claude/ralph-loop-progress.md`:

```markdown
## Iteration 34: Service Health Fixes and Docker Optimization (2026-04-14)

**Status:** ✅ COMPLETE
**Objective:** Fix unhealthy services and optimize remaining Docker images

### Issues Resolved
1. **hardware-bridge health check** - Added requests library to requirements.txt
2. **sentiment-agent ML model permissions** - Added HF_HUB_CACHE environment variable
3. **Image sizes optimized** - safety-filter and operator-console rebuilt with .dockerignore

### Results
- All 8 services healthy (no more unhealthy status)
- sentiment-agent: Mock mode → Real ML sentiment analysis
- Image size reduction: >80% (2.48GB → <500MB each)
- Health check regression tests added

### Files Changed
- services/echo-agent/requirements.txt (added requests)
- services/sentiment-agent/Dockerfile (added HF_HUB_CACHE)
- tests/integration/mvp/test_service_health.py (new)
- Docker images rebuilt with .dockerignore
```

- [ ] **Step 9: Verify git status**

```bash
git status
```

Expected: Shows modified design spec and progress file

- [ ] **Step 10: Commit final documentation**

```bash
git add docs/superpowers/specs/2026-04-14-service-health-fixes-design.md .claude/ralph-loop-progress.md
git commit -m "docs: update service health fixes to complete status

All 8 services now healthy.
Image optimization: >80% size reduction.
Health check tests added to prevent regressions."
```

- [ ] **Step 11: Push all changes to remote**

```bash
git push origin main
```

Expected: Push successful

---

## Success Criteria Verification

After completing all tasks, verify:

- [ ] All 8 services show "(healthy)" in `docker compose ps`
- [ ] hardware-bridge responds to health check (requests library available)
- [ ] sentiment-agent loads ML model without permission errors
- [ ] sentiment-agent returns real sentiment analysis (not mock mode)
- [ ] All rebuilt images <500MB
- [ ] Health check test passes
- [ ] All integration tests pass
- [ ] Design spec marked complete
- [ ] Ralph Loop progress updated

**Estimated completion time:** 40-45 minutes

**Risk level:** Low (minimal code changes, rebuilds only, health verification between phases)

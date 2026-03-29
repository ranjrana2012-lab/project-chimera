# E2E Test Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all failing GitHub Actions E2E tests by addressing Docker build inconsistencies, service startup timeouts, and test reliability issues

**Architecture:** Multi-phase approach: (1) establish consistent Docker images, (2) fix orchestrator endpoint bug, (3) add CPU-only CI mode, (4) improve test timing, (5) optimize service startup

**Tech Stack:** Docker, GitHub Actions, Python FastAPI, TypeScript Playwright, HuggingFace models

---

## Pre-Flight Check (Before Any Modifications)

### Task 0: Verify Project Structure

**Files:**
- No file modifications

- [ ] **Step 1: Verify services/shared directory exists**

Run: `ls -la services/shared/`
Expected: Directory exists with models/ subdirectory

- [ ] **Step 2: Verify key services exist**

Run: `ls -d services/scenespeak-agent services/sentiment-agent services/bsl-agent services/captioning-agent services/openclaw-orchestrator`
Expected: All directories exist

- [ ] **Step 3: Check current CI timeout value**

Run: `grep "timeout-minutes" .github/workflows/e2e-tests.yml`
Expected: Note current value for later comparison

---

## Phase 1: Dockerfile Validation and Quick Fixes

### Task 1: Create Dockerfile Validation Script

**Files:**
- Create: `scripts/validate-dockerfiles.sh`

- [ ] **Step 1: Write the validation script**

```bash
#!/bin/bash
# Validate all service Dockerfiles for CI consistency
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ERRORS=0

echo "Validating Dockerfiles..."

for dockerfile in services/*/Dockerfile; do
  service=$(basename $(dirname "$dockerfile"))
  echo -n "Checking $service... "

  # Check for curl installation (simple check: curl must appear somewhere)
  if ! grep -q "curl" "$dockerfile"; then
    echo -e "${RED}FAIL${NC} (missing curl)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Check for consistent base image (python:3.11-slim or 3.12-slim)
  if ! grep -q "FROM python:3.1[12]-slim" "$dockerfile"; then
    # Non-Python services are OK (e.g., Node.js)
    if ! grep -q "FROM python:" "$dockerfile"; then
      echo -e "${GREEN}OK${NC} (non-Python service)"
      continue
    fi
    echo -e "${RED}FAIL${NC} (inconsistent base image)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  echo -e "${GREEN}OK${NC}"
done

if [ $ERRORS -gt 0 ]; then
  echo -e "${RED}$ERRORS validation errors found${NC}"
  exit 1
fi

echo -e "${GREEN}All Dockerfiles validated!${NC}"
exit 0
```

- [ ] **Step 2: Make script executable**

Run: `chmod +x scripts/validate-dockerfiles.sh`
Expected: No error, script is executable

- [ ] **Step 3: Test the validation script**

Run: `./scripts/validate-dockerfiles.sh`
Expected: May show failures for services missing curl - note these for fixing

- [ ] **Step 4: Commit**

```bash
git add scripts/validate-dockerfiles.sh
git commit -m "feat: add Dockerfile validation script for CI consistency"
```

---

### Task 2: Fix Missing curl in Remaining Dockerfiles

**Files:**
- Modify: `services/autonomous-agent/Dockerfile`
- Modify: `services/nemoclaw-orchestrator/Dockerfile`
- Modify: `services/simulation-engine/Dockerfile`
- Modify: `services/director-agent/Dockerfile`
- Modify: `services/educational-platform/Dockerfile`

- [ ] **Step 1: Check which Dockerfiles are missing curl**

Run: `grep -L "curl" services/*/Dockerfile`
Expected: autonomous-agent, nemoclaw-orchestrator, simulation-engine, director-agent, educational-platform

- [ ] **Step 2: Fix autonomous-agent Dockerfile (line 6)**

Current: `RUN apt-get update && apt-get install -y gcc git && rm -rf /var/lib/apt/lists/*`

Change to:
```dockerfile
RUN apt-get update && apt-get install -y gcc git curl && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 3: Fix simulation-engine Dockerfile**

First find the apt-get line:
Run: `grep -n "apt-get install" services/simulation-engine/Dockerfile`

Add `curl \` to the apt-get install list

- [ ] **Step 4: Fix director-agent and educational-platform Dockerfiles**

Follow same pattern as Step 3

- [ ] **Step 5: Fix nemoclaw-orchestrator Dockerfile**

Follow same pattern as Step 3

- [ ] **Step 6: Re-run validation to verify all fixes**

Run: `./scripts/validate-dockerfiles.sh`
Expected: All Dockerfiles pass validation

- [ ] **Step 7: Commit**

```bash
git add services/autonomous-agent/Dockerfile services/nemoclaw-orchestrator/Dockerfile services/simulation-engine/Dockerfile services/director-agent/Dockerfile services/educational-platform/Dockerfile
git commit -m "fix: add curl to service Dockerfiles for healthcheck compatibility"
```

---

### Task 3: Verify Shared Module Access in Services

**Files:**
- Verify: `services/sentiment-agent/Dockerfile`
- Verify: `services/bsl-agent/Dockerfile`
- Verify: `services/scenespeak-agent/Dockerfile`

- [ ] **Step 1: Check which services import from shared module**

Run: `find services/ -name "*.py" -type f -exec grep -l "from shared" {} \; 2>/dev/null | cut -d/ -f2 | sort -u`
Expected: List of service directories using shared module

- [ ] **Step 2: Verify sentiment-agent Dockerfile has shared module copy**

Run: `grep -n "shared" services/sentiment-agent/Dockerfile`
Expected: Line 28 shows `COPY services/shared/ /app/shared/`

- [ ] **Step 3: Verify bsl-agent has shared module access**

Run: `grep -n "shared" services/bsl-agent/Dockerfile`
Expected: Comment about shared module or volume mount

- [ ] **Step 4: Check if scenespeak-agent imports from shared**

Run: `grep -r "from shared" services/scenespeak-agent/ 2>/dev/null`
Expected: If output is empty, scenespeak-agent doesn't use shared module

- [ ] **Step 5: Check if scenespeak-agent needs shared module**

If Step 4 returned nothing, verify: `grep -r "shared" services/scenespeak-agent/Dockerfile`
Expected: If empty, no shared module needed

- [ ] **Step 6: Only add shared module copy to services that actually import from it**

For services from Step 1 that are missing COPY in Dockerfile:
```dockerfile
# After copying requirements, before copying app code
COPY services/shared/ /app/shared/
```

- [ ] **Step 7: Only update PYTHONPATH for services that need it**

For services using shared module, check if PYTHONPATH already exists:
Run: `grep "PYTHONPATH" services/SERVICE/Dockerfile`

If missing, add:
```dockerfile
ENV PYTHONPATH=/app/src:/app:/app/shared
```

- [ ] **Step 8: Commit**

```bash
git add services/*/Dockerfile
git commit -m "fix: ensure shared module access in service Dockerfiles that need it"
```

---

## Phase 2: Orchestrator Endpoint Fix (Critical Bug)

### Task 4: Fix Orchestrator Agent Endpoint Mapping

**Files:**
- Modify: `services/openclaw-orchestrator/main.py`

- [ ] **Step 1: Find the call_agent function**

Run: `grep -n "async def call_agent" services/openclaw-orchestrator/main.py`
Expected: Found at line ~515

- [ ] **Step 2: Read the call_agent function**

Run: `sed -n '515,540p' services/openclaw-orchestrator/main.py`
Expected: See the buggy endpoint construction at line ~524

- [ ] **Step 3: Create endpoint mapping dictionary**

Add at module level (after imports, before functions):
```python
# Map skill names to actual agent endpoint paths
SKILL_ENDPOINTS = {
    "dialogue_generator": "/api/generate",
    "captioning": "/api/transcribe",
    "bsl_translation": "/api/translate",
    "sentiment_analysis": "/api/analyze",
    "autonomous_execution": "/execute",
}
```

- [ ] **Step 4: Update endpoint construction in call_agent**

Find the line: `endpoint = f"/v1/{skill}"` and replace with:
```python
endpoint = SKILL_ENDPOINTS.get(skill, f"/v1/{skill}")
```

- [ ] **Step 5: Check for duplicate code after call_agent function**

Run: `grep -n "async with httpx.AsyncClient" services/openclaw-orchestrator/main.py`
Expected: Should only appear once in call_agent function

- [ ] **Step 6: Remove any duplicate code if found**

If there's duplicate httpx.AsyncClient code, remove it

- [ ] **Step 7: Commit**

```bash
git add services/openclaw-orchestrator/main.py
git commit -m "fix: correct orchestrator agent endpoint paths to use /api/{action}"
```

---

## Phase 3: CPU-Only CI Mode Support

### Task 5: Add GitHub Actions Cache for HuggingFace Models

**Files:**
- Modify: `.github/workflows/e2e-tests.yml`

- [ ] **Step 1: Read the CI workflow to find the Checkout step**

Run: `grep -n "name:" .github/workflows/e2e-tests.yml | head -10`
Expected: See step names including "Checkout Repository"

- [ ] **Step 2: Add cache step after "Checkout Repository" step**

Insert after the "Checkout Repository" step:
```yaml
      - name: Cache HuggingFace Models
        uses: actions/cache@v4
        with:
          path: ~/.cache/huggingface
          key: ${{ runner.os }}-hf-models-${{ hashFiles('services/**/models.txt') }}
          restore-keys: |
            ${{ runner.os }}-hf-models-
```

- [ ] **Step 3: Create models.txt files for ML services**

Create: `services/scenespeak-agent/models.txt`:
```
distilbert-base-uncased-finetuned-sst-2-english
```

Create: `services/sentiment-agent/models.txt`:
```
distilbert-base-uncased-finetuned-sst-2-english
```

Create: `services/bsl-agent/models.txt`:
```
cognitivecomputations/wav2vec2-bart-asr-bn-transcribe
```

- [ ] **Step 4: Add CI environment variable for CPU mode**

Find the `env:` section at top of workflow and add:
```yaml
  CI_GPU_AVAILABLE: "false"
  DEVICE: "cpu"
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/e2e-tests.yml services/scenespeak-agent/models.txt services/sentiment-agent/models.txt services/bsl-agent/models.txt
git commit -m "feat: add GitHub Actions cache for HuggingFace models and CPU-only CI mode"
```

---

### Task 6: Update Services to Detect CPU Mode

**Files:**
- Create: `services/shared/ci_mode.py`
- Modify: `services/scenespeak-agent/main.py`
- Modify: `services/sentiment-agent/src/sentiment_agent/main.py`
- Modify: `services/bsl-agent/main.py`
- Modify: `services/captioning-agent/main.py`

- [ ] **Step 1: Add CPU mode detection helper**

Create: `services/shared/ci_mode.py`:
```python
"""CI mode detection for CPU-only environments."""
import os

def is_cpu_mode():
    """Check if running in CPU-only CI mode."""
    return os.getenv("CI_GPU_AVAILABLE", "true").lower() == "false"

def get_device():
    """Get appropriate device for current environment."""
    return "cpu" if is_cpu_mode() else "cuda"

def get_model_variant():
    """Get model variant for current environment."""
    return "ci" if is_cpu_mode() else "full"
```

- [ ] **Step 2: Read scenespeak-agent main.py to understand model loading**

Run: `head -50 services/scenespeak-agent/main.py`
Expected: See model initialization pattern

- [ ] **Step 3: Add model_is_loaded flag to scenespeak-agent**

At module level (after imports):
```python
# Module-level flag for model loading state
model_is_loaded = False
```

- [ ] **Step 4: Add CPU mode imports and device setup**

After imports, add:
```python
import sys
sys.path.insert(0, '/app/shared')  # Ensure shared module is accessible
from ci_mode import get_device, is_cpu_mode

# Get device for model loading
device = get_device()
```

- [ ] **Step 5: Update model loading to set flag**

After model loads successfully, add:
```python
global model_is_loaded
# ... existing model loading code ...
model_is_loaded = True
```

- [ ] **Step 6: Add /health/ready and /health/live endpoints**

```python
@app.get("/health/ready")
async def readiness():
    """Return 200 if service is running (models may not be loaded yet)."""
    return {"status": "ready", "service": "scenespeak-agent", "models_loaded": model_is_loaded}

@app.get("/health/live")
async def liveness():
    """Return 200 if service is running AND models are loaded."""
    if not model_is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return {"status": "live", "service": "scenespeak-agent", "models_loaded": True}
```

- [ ] **Step 7: Read sentiment-agent main.py to understand its structure**

Run: `head -100 services/sentiment-agent/src/sentiment_agent/main.py`
Expected: Note how this service differs from scenespeak-agent

- [ ] **Step 8: For sentiment-agent, the model is downloaded in Dockerfile**

Since sentiment-agent downloads models during build (see Dockerfile line 22), it loads models at startup differently.

Add these steps to sentiment-agent:
a. Add `model_is_loaded = False` at module level
b. Add import: `from shared.ci_mode import get_device, is_cpu_mode`
c. After model loads in startup code, add: `model_is_loaded = True`
d. Add `/health/ready` and `/health/live` endpoints (same as scenespeak-agent)

- [ ] **Step 9: Repeat steps 3-6 for bsl-agent**

File: `services/bsl-agent/main.py`
Follow the same pattern as scenespeak-agent

- [ ] **Step 10: Repeat steps 3-6 for captioning-agent**

File: `services/captioning-agent/main.py`
Follow the same pattern as scenespeak-agent

- [ ] **Step 11: Verify ci_mode.py was created correctly**

Run: `ls -la services/shared/ci_mode.py`
Expected: File exists with is_cpu_mode(), get_device(), get_model_variant() functions

- [ ] **Step 8: Repeat steps 3-6 for bsl-agent**

File: `services/bsl-agent/main.py`

- [ ] **Step 9: Repeat steps 3-6 for captioning-agent**

File: `services/captioning-agent/main.py`

- [ ] **Step 10: Update Dockerfile healthcheck to use /health/ready**

For each ML service Dockerfile, change HEALTHCHECK:
```dockerfile
# Before
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:PORT/health/live')"

# After
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:PORT/health/ready')"
```

- [ ] **Step 11: Commit**

```bash
git add services/shared/ci_mode.py services/scenespeak-agent/main.py services/sentiment-agent/src/sentiment_agent/main.py services/bsl-agent/main.py services/captioning-agent/main.py
git commit -m "feat: add CPU-only CI mode support with deferred model loading"
```

---

## Phase 4: Test Reliability Fixes

### Task 7: Replace Hard-coded Timeouts with Condition Waits

**Files:**
- Modify: `tests/e2e/cross-service/show-workflow.spec.ts`
- Modify: All test files using `page.waitForTimeout()`

- [ ] **Step 1: Find all uses of waitForTimeout**

Run: `grep -rn "waitForTimeout" tests/e2e/`
Expected: List of files with hard-coded timeouts

- [ ] **Step 2: Replace timeout with selector waits in show-workflow.spec.ts**

Line 164: Replace `await page.waitForTimeout(1000)` with:
```typescript
await page.waitForResponse(resp => resp.url().includes('/api/analyze'), { timeout: 5000 });
```

Line 275: Replace `await page.waitForTimeout(200)` with:
```typescript
// Wait for sentiment analysis response instead of hard-coded delay
await page.waitForResponse(resp => resp.url().includes('/api/analyze'), { timeout: 5000 });
```

Line 299: Replace `await page.waitForTimeout(2000)` with:
```typescript
await expect(page.locator('[data-testid="generated-dialogue"]')).toBeVisible({ timeout: 5000 });
```

Line 346: Replace `await page.waitForTimeout(3000)` with:
```typescript
await page.waitForResponse(resp => resp.url().includes('/api/generate'), { timeout: 10000 });
```

Line 372: Replace `await page.waitForTimeout(2000)` with:
```typescript
await expect(page.locator('[data-testid="scene-progress"]')).toBeVisible({ timeout: 10000 });
```

- [ ] **Step 3: Run tests locally to verify fixes**

Run: `cd tests/e2e && npx playwright test cross-service/show-workflow.spec.ts`
Expected: Tests pass or fail for unrelated reasons

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/cross-service/show-workflow.spec.ts
git commit -m "test: replace hard-coded timeouts with condition-based waits"
```

---

### Task 8: Fix WebSocket Race Conditions

**Files:**
- Modify: `tests/e2e/websocket/sentiment-updates.spec.ts`
- Modify: `tests/e2e/helpers/websocket-client.ts`

- [ ] **Step 1: Add connection handshake to WebSocket client**

Read: `tests/e2e/helpers/websocket-client.ts`
Expected: See current WebSocket implementation

- [ ] **Step 2: Add ready state check**

```typescript
async waitForReady(timeout = 5000): Promise<void> {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    if (this.ws.readyState === WebSocket.OPEN) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('WebSocket not ready within timeout');
}
```

- [ ] **Step 3: Update tests to wait for ready before sending**

```typescript
const wsClient = await createWebSocketClient('ws://localhost:8003/ws/avatar');
await wsClient.waitForReady();
```

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/helpers/websocket-client.ts tests/e2e/websocket/*.spec.ts
git commit -m "test: fix WebSocket race conditions with ready state checks"
```

---

## Phase 5: Service Startup Optimization

### Task 9: Update wait-for-services.sh for Two-Stage Health Check

**Files:**
- Modify: `scripts/wait-for-services.sh`

- [ ] **Step 1: Verify current service port mappings**

Run: `grep "SERVICES=" scripts/wait-for-services.sh`
Expected: Confirm ports: 8000=orchestrator, 8001=scenespeak, 8002=captioning, 8003=bsl, 8004=sentiment, 8005=lighting, 8006=safety, 8007=console, 8011=music

- [ ] **Step 2: Update health check to use /health/ready**

Find the check_service function (around line 35) and replace:
```bash
# Before
if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then

# After
if curl -sf "http://localhost:${port}/health/ready" > /dev/null 2>&1; then
```

- [ ] **Step 3: Reduce TIMEOUT from 120 to 60 seconds**

Find line: `TIMEOUT=120` and change to `TIMEOUT=60`

- [ ] **Step 4: Verify ML services list is current**

Run: `grep -E "scenespeak|captioning|bsl|sentiment|music" /home/ranj/Project_Chimera/docker-compose.yml | grep PORT`
Expected: Confirm these services exist and ports are correct

- [ ] **Step 5: Add model loading wait after containers are ready**

Add new function after the `wait_for_service` function:
```bash
# Function to wait for model loading (only for ML services)
wait_for_models() {
  local ml_services=("8001:scenespeak" "8002:captioning" "8003:bsl" "8004:sentiment" "8011:music")

  echo ""
  echo "Waiting for ML models to load..."

  for service in "${ml_services[@]}"; do
    IFS=':' read -r PORT NAME <<< "$service"
    echo -n "  $NAME models... "

    local elapsed=0
    while [ $elapsed -lt 180 ]; do
      if curl -sf "http://localhost:${PORT}/health/live" > /dev/null 2>&1; then
        echo -e "${GREEN}loaded${NC}"
        break
      fi
      sleep 5
      elapsed=$((elapsed + 5))
    done
  done
}
```

- [ ] **Step 6: Find the main function's service loop**

Run: `grep -n "for service in" scripts/wait-for-services.sh`
Expected: Find where services are checked

- [ ] **Step 7: Call model loading wait after containers are ready**

After the service checking loop completes (before final status display), add:
```bash
wait_for_models
```

- [ ] **Step 8: Commit**

```bash
git add scripts/wait-for-services.sh
git commit -m "feat: implement two-stage health check (ready + model loaded)"
```

---

### Task 10: Add Validation Step to CI Workflow

**Files:**
- Modify: `.github/workflows/e2e-tests.yml`

- [ ] **Step 1: Add Dockerfile validation as first step in job**

Insert as first step under `steps:` (before "Checkout Repository"):
```yaml
      - name: Validate Dockerfiles
        run: |
          chmod +x scripts/validate-dockerfiles.sh
          ./scripts/validate-dockerfiles.sh
```

- [ ] **Step 2: Check current job timeout value**

Run: `grep "timeout-minutes" .github/workflows/e2e-tests.yml`
Expected: Note current value (from pre-flight check)

- [ ] **Step 3: Increase job timeout to 90 minutes**

If current value is less than 90, change to: `timeout-minutes: 90`

- [ ] **Step 4: Find the "Wait for Services to be Healthy" step**

Run: `grep -n "Wait for Services" .github/workflows/e2e-tests.yml`
Expected: Find step location

- [ ] **Step 5: Add service logs on failure after "Wait for Services"**

Insert after the "Wait for Services to be Healthy" step:
```yaml
      - name: Upload Service Logs on Failure
        if: failure()
        run: |
          mkdir -p logs
          docker-compose logs > logs/docker-compose.log 2>&1 || true
          for service in orchestrator scenespeak captioning bsl sentiment lighting safety console music; do
            docker logs chimera-${service}-1 > logs/${service}.log 2>&1 || true
          done
          echo "Service logs saved"

      - name: Upload Logs Artifact
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: service-logs-shard-${{ matrix.shard }}
          path: logs/
          retention-days: 3
```

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/e2e-tests.yml
git commit -m "feat: add Dockerfile validation and service log upload to CI"
```

---

## Phase 6: Final Verification

### Task 11: Run Full Test Suite Locally

**Files:**
- No file modifications

- [ ] **Step 1: Rebuild all services**

Run: `docker-compose build`
Expected: All services build successfully

- [ ] **Step 2: Start services**

Run: `docker-compose up -d`
Expected: All containers start

- [ ] **Step 3: Run wait script**

Run: `./scripts/wait-for-services.sh`
Expected: All services pass readiness, models load within timeout

- [ ] **Step 4: Run full E2E test suite**

Run: `cd tests/e2e && npx playwright test`
Expected: 93%+ pass rate (88+ of 94 tests passing)

- [ ] **Step 5: Note any remaining failures**

Document any tests still failing in `docs/E2E-TESTING-PROGRESS.md`

- [ ] **Step 6: Commit**

```bash
git add docs/E2E-TESTING-PROGRESS.md
git commit -m "test: document final test results after E2E fixes"
```

---

### Task 12: Push and Monitor CI

**Files:**
- No file modifications

- [ ] **Step 1: Push all changes to remote**

Run: `git push origin main`
Expected: Changes push successfully

- [ ] **Step 2: Monitor CI workflow**

Run: `gh run list --limit 1` or watch GitHub Actions tab
Expected: Workflow starts

- [ ] **Step 3: Check first CI results**

Wait for workflow completion and check results
Expected: Improved pass rate, reduced timeout failures

- [ ] **Step 4: Iterate on any remaining failures**

If CI still has failures, analyze logs and create follow-up issues

---

## Success Criteria

After completing all tasks:

- [ ] `./scripts/validate-dockerfiles.sh` passes with no errors
- [ ] All Dockerfiles have `curl` installed
- [ ] Orchestrator calls correct agent endpoints
- [ ] Services have both `/health/ready` and `/health/live` endpoints
- [ ] CI caches HuggingFace models between runs
- [ ] CI has `CI_GPU_AVAILABLE=false` set for CPU-only mode
- [ ] No `waitForTimeout()` with >500ms in test files (except specific cases)
- [ ] WebSocket tests have connection handshake
- [ ] Local test pass rate: 93%+ (88+/94)
- [ ] CI success rate: 95%+ over 20 runs

---

## Rollback Plan

If any task introduces issues:

1. Identify the specific commit that caused regression
2. Revert that commit: `git revert <commit-sha>`
3. Investigate alternative approach
4. Re-test before re-merging

---

**Next Steps After Plan Approval:**
1. Choose execution approach: Subagent-Driven (recommended) or Inline Execution
2. Execute tasks sequentially
3. Monitor progress after each phase
4. Adjust plan if unexpected issues arise

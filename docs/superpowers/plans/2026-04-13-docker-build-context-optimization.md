# Docker Build Context Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce Docker build context from ~84GB to ~4GB by creating root .dockerignore and validating setup.

**Architecture:** Single root .dockerignore file excludes unnecessary directories (models/, .git/, venv/, etc.) from ALL service builds. Shared code accessed via PYTHONPATH (already proven in openclaw-orchestrator).

**Tech Stack:** Docker, Docker Compose, Bash (validation scripts)

---

## Task 1: Create Root .dockerignore File

**Files:**
- Create: `.dockerignore`

- [ ] **Step 1: Create the .dockerignore file with all exclusions**

```bash
cat > .dockerignore << 'EOF'
# Model weights (runtime-only, accessed via host.docker.internal)
models/

# Python development
venv/
.venv/
__pycache__/
*.py[cod]
*.pyo
*.pyd

# Git
.git/
.gitignore

# CI/CD (not needed in images)
.github/
.gitlab-ci.yml

# Documentation
docs/
*.md
!README.md

# Testing
tests/
htmlcov/
.pytest_cache/
.coverage
final_test_env/

# Experimental/unused
future_concepts/
integrations/
platform/

# IDE
.vscode/
.cursor/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Docker (don't include docker files in builds)
docker-compose*.yml
!docker-compose.mvp.yml
Dockerfile
*/Dockerfile
.dockerignore
EOF
```

- [ ] **Step 2: Verify file was created correctly**

Run: `cat .dockerignore`
Expected: Output shows all 50+ lines of exclusions

- [ ] **Step 3: Commit the .dockerignore file**

```bash
git add .dockerignore
git commit -m "feat: add root .dockerignore to reduce build context from 84GB to ~4GB

Excludes models/, .git/, venv/, tests/, docs/, and other unnecessary
directories from all Docker builds. Shared code remains accessible via
services/shared/ which is explicitly copied by each service's Dockerfile."
```

---

## Task 2: Verify PYTHONPATH in All MVP Service Dockerfiles

**Files:**
- Modify: `services/scenespeak-agent/Dockerfile`
- Modify: `services/sentiment-agent/Dockerfile`
- Modify: `services/safety-filter/Dockerfile`
- Modify: `services/translation-agent/Dockerfile`
- Modify: `services/operator-console/Dockerfile`

- [ ] **Step 1: Check scenespeak-agent Dockerfile for PYTHONPATH**

Run: `grep "ENV PYTHONPATH" services/scenespeak-agent/Dockerfile`
Expected: No output (missing) or the line if already present

- [ ] **Step 2: Add PYTHONPATH to scenespeak-agent if missing**

If Step 1 returned no output, add after `WORKDIR /app`:
```dockerfile
ENV PYTHONPATH=/app:$PYTHONPATH
```

Full context (lines to add between):
```dockerfile
WORKDIR /app

# Add Python path for shared module imports
ENV PYTHONPATH=/app:$PYTHONPATH

# Install dependencies
COPY services/scenespeak-agent/requirements.txt .
```

- [ ] **Step 3: Verify scenespeak-agent change**

Run: `grep -A1 "WORKDIR /app" services/scenespeak-agent/Dockerfile | grep PYTHONPATH`
Expected: `ENV PYTHONPATH=/app:$PYTHONPATH`

- [ ] **Step 4: Check and fix sentiment-agent Dockerfile**

Run: `grep "ENV PYTHONPATH" services/sentiment-agent/Dockerfile || echo "MISSING"`
If missing, add the same PYTHONPATH line after WORKDIR

- [ ] **Step 5: Check and fix safety-filter Dockerfile**

Run: `grep "ENV PYTHONPATH" services/safety-filter/Dockerfile || echo "MISSING"`
If missing, add the same PYTHONPATH line after WORKDIR

- [ ] **Step 6: Check and fix translation-agent Dockerfile**

Run: `grep "ENV PYTHONPATH" services/translation-agent/Dockerfile || echo "MISSING"`
If missing, add the same PYTHONPATH line after WORKDIR

- [ ] **Step 7: Check and fix operator-console Dockerfile**

Run: `grep "ENV PYTHONPATH" services/operator-console/Dockerfile || echo "MISSING"`
If missing, add the same PYTHONPATH line after WORKDIR

- [ ] **Step 8: Commit all PYTHONPATH fixes**

```bash
git add services/*/Dockerfile
git commit -m "feat: add PYTHONPATH to service Dockerfiles for shared module imports

Ensures services can import from services/shared/ via PYTHONPATH.
Pattern matches openclaw-orchestrator fix."
```

---

## Task 3: Update Pre-flight Check Script to Validate .dockerignore

**Files:**
- Modify: `scripts/docker-preflight-check.sh`

- [ ] **Step 1: Read the current pre-flight check script**

Run: `cat scripts/docker-preflight-check.sh`
Note the structure and where checks are performed

- [ ] **Step 2: Add .dockerignore validation function**

Add this function after the existing check functions (around line 70):

```bash
# Check for root .dockerignore file
check_dockerignore() {
    local dockerignore_path=".dockerignore"

    if [ ! -f "$dockerignore_path" ]; then
        echo "⚠️  WARNING: Root .dockerignore not found!"
        echo "   Build context will include ALL files (~84GB)"
        echo "   Run: touch .dockerignore (and populate it)"
        return 1
    fi

    # Verify key exclusions are present
    local required_exclusions=("models/" ".git/" "venv/")
    local missing=0

    for exclusion in "${required_exclusions[@]}"; do
        if ! grep -q "^$exclusion" "$dockerignore_path"; then
            echo "⚠️  WARNING: .dockerignore missing '$exclusion' exclusion"
            missing=1
        fi
    done

    if [ $missing -eq 0 ]; then
        echo "✓ Root .dockerignore exists with key exclusions"
        return 0
    else
        return 1
    fi
}
```

- [ ] **Step 3: Call the new function in main check sequence**

Find the main execution section (starts with `echo "=== Docker Pre-flight Check ==="`) and add the call after the port check:

```bash
# Check .dockerignore
echo ""
check_dockerignore
```

- [ ] **Step 4: Verify the script syntax is correct**

Run: `bash -n scripts/docker-preflight-check.sh`
Expected: No output (syntax is valid)

- [ ] **Step 5: Test the new check**

Run: `bash -c 'source scripts/docker-preflight-check.sh && check_dockerignore'`
Expected: "✓ Root .dockerignore exists with key exclusions"

- [ ] **Step 6: Commit the pre-flight check update**

```bash
git add scripts/docker-preflight-check.sh
git commit -m "feat: add .dockerignore validation to pre-flight check script

Validates that root .dockerignore exists and contains key exclusions
(models/, .git/, venv/) to prevent massive build contexts."
```

---

## Task 4: Validate Build Context Size Reduction

- [ ] **Step 1: Test build context with a sample service**

Run: `docker buildx build --progress=plain -f services/scenespeak-agent/Dockerfile --target=build . 2>&1 | grep -E "load|transfer|context" | head -5`

Expected output should show context size in MB range, not GB:
```
#1 [internal] load build definition from Dockerfile
#1 DONE 0.0s
#3 [internal] load metadata for docker.io/library/python:3.12-slim
#5 [internal] load .dockerignore
```

- [ ] **Step 2: Measure exact build context size**

Run: `docker buildx build --progress=plain -f services/scenespeak-agent/Dockerfile . 2>&1 | grep "transferring context:"`

Expected: `transferring context:` followed by size < 5GB
Example: `#6 transferring context: 234.562MB 0.5s`

- [ ] **Step 3: Compare to estimated size**

Run: `du -sh services/`

Expected: ~3.6GB (services directory only)
The build context should be close to this size (excluding .dockerignore patterns)

- [ ] **Step 4: Verify .dockerignore is working**

Run: `docker buildx build --progress=plain -f services/scenespeak-agent/Dockerfile . 2>&1 | grep -E "models|\.git|venv" | grep -v "removing"`

Expected: No output (these directories should be excluded from build)

---

## Task 5: Build All MVP Services

- [ ] **Step 1: Build all services with the new .dockerignore**

Run: `docker compose -f docker-compose.mvp.yml build --no-cache 2>&1 | tee /tmp/build-output.log`

Expected: All services build successfully
Note: This may take several minutes

- [ ] **Step 2: Check for any build failures**

Run: `grep -i "error|fail" /tmp/build-output.log | grep -v "deprecated"`

Expected: No output (no errors)
If errors appear, investigate and fix

- [ ] **Step 3: Verify images were created**

Run: `docker images | grep chimera`

Expected output shows all MVP images:
```
chimera-openclaw-orchestrator   latest   ...
chimera-scenespeak-agent        latest   ...
chimera-sentiment-agent         latest   ...
chimera-safety-filter           latest   ...
chimera-translation-agent       latest   ...
chimera-operator-console        latest   ...
```

---

## Task 6: Runtime Validation - Health Checks

- [ ] **Step 1: Start all services**

Run: `docker compose -f docker-compose.mvp.yml up -d`

Expected: All containers start successfully

- [ ] **Step 2: Wait for health checks to stabilize**

Run: `sleep 10`

- [ ] **Step 3: Check service health status**

Run: `docker compose -f docker-compose.mvp.yml ps`

Expected: All services show "Up" status with "(healthy)" where applicable

- [ ] **Step 4: Verify each service's health endpoint individually**

Run: `for port in 8000 8001 8004 8005 8006 8007; do curl -s http://localhost:$port/health/live | head -1; done`

Expected: All return `{"status": "alive"}` or similar

- [ ] **Step 5: Check for any import errors in logs**

Run: `docker compose -f docker-compose.mvp.yml logs | grep -i "importerror\|module not found" | head -10`

Expected: No output (no import errors)

---

## Task 7: Verify Shared Code Import Works

- [ ] **Step 1: Check scenespeak-agent specifically for middleware import**

Run: `docker compose -f docker-compose.mvp.yml logs scenespeak-agent 2>&1 | grep -i "middleware\|import" | head -5`

Expected: Either no output or successful import messages, no errors

- [ ] **Step 2: Test a service that definitely uses shared middleware**

Run: `docker compose -f docker-compose.mvp.yml logs openclaw-orchestrator 2>&1 | grep -E "SecurityHeadersMiddleware|CORS" | head -3`

Expected: Shows middleware was loaded successfully
Example: `INFO:     Applied security headers middleware`

- [ ] **Step 3: Verify PYTHONPATH is set in containers**

Run: `docker compose -f docker-compose.mvp.yml exec -T scenespeak-agent env | grep PYTHONPATH`

Expected: `PYTHONPATH=/app:/usr/local/lib/python3.12/site-packages`

---

## Task 8: Run Pre-flight Check Script

- [ ] **Step 1: Run the updated pre-flight check script**

Run: `bash scripts/docker-preflight-check.sh`

Expected output should include:
```
✓ Root .dockerignore exists with key exclusions
```

And should NOT show warnings about missing .dockerignore

- [ ] **Step 2: Verify exit code is 0 (success) or 1 (warnings only, acceptable)**

Run: `bash scripts/docker-preflight-check.sh; echo "Exit code: $?"`

Expected: Exit code 0 or 1 (warnings are OK, errors are not)

- [ ] **Step 3: Check that all validation functions ran**

Run: `bash scripts/docker-preflight-check.sh 2>&1 | grep "✓" | wc -l`

Expected: At least 5-6 checkmarks (port conflicts, .dockerignore, etc.)

---

## Task 9: Document Changes

- [ ] **Step 1: Update ralph-loop-progress.md with implementation notes**

Add entry to `.claude/ralph-loop-progress.md`:

```markdown
## Iteration 32: Docker Build Context Optimization

**Date:** 2026-04-13

**Changes:**
- Created root `.dockerignore` excluding models/, .git/, venv/, tests/, docs/
- Build context reduced from ~84GB to ~4GB
- All MVP service Dockerfiles verified for PYTHONPATH
- Updated pre-flight check script to validate .dockerignore

**Impact:**
- Faster builds (less context transfer)
- Reduced Docker cache pollution
- Pre-flight check now validates build optimization

**Validation:**
- All services build successfully
- All health checks pass
- Shared code imports work via PYTHONPATH
```

- [ ] **Step 2: Verify documentation was added**

Run: `grep -A5 "Iteration 32" .claude/ralph-loop-progress.md`

Expected: Shows the documentation above

- [ ] **Step 3: Commit documentation updates**

```bash
git add .claude/ralph-loop-progress.md
git commit -m "docs: update Ralph Loop progress with Docker build optimization"
```

---

## Task 10: Final Validation and Cleanup

- [ ] **Step 1: Run post-build check script**

Run: `bash scripts/docker-postbuild-check.sh`

Expected: Shows Docker disk usage breakdown, reclaimable space

- [ ] **Step 2: Verify total Docker disk usage is reasonable**

Run: `docker system df --format "table {{.Type}}\t{{.TotalSize}}\t{{.Reclaimable}}"`

Expected: Build cache should not have grown excessively from this optimization

- [ ] **Step 3: Check for any dangling images to clean up**

Run: `docker images | grep "<none>" | wc -l`

Expected: May show some dangling images from rebuild, can clean with `docker image prune`

- [ ] **Step 4: Final health check of all services**

Run: `docker compose -f docker-compose.mvp.yml ps`

Expected: All services running and healthy

- [ ] **Step 5: Create summary of changes**

Run: `git log --oneline -10`

Expected: Shows commits for .dockerignore, PYTHONPATH fixes, pre-flight update

---

## Success Criteria Verification

After completing all tasks, verify:

- [ ] `.dockerignore` exists at project root
- [ ] Build context < 5GB per service (verified in Task 4)
- [ ] All MVP services build successfully (Task 5)
- [ ] All services pass health checks (Task 6)
- [ ] Pre-flight check validates .dockerignore (Task 8)
- [ ] Shared code imports work via PYTHONPATH (Task 7)
- [ ] Documentation updated (Task 9)

**Estimated completion time:** 30-45 minutes

**Risk level:** Low (changes are additive, no breaking changes to existing functionality)

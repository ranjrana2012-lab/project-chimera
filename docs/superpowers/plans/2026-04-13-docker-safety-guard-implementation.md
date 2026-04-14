# Docker Safety Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and integrate Docker Safety Guard into Ralph Loop master prompt to prevent hard drive bloat from Docker operations.

**Architecture:** Three-layer protection (Hard Gate → Pre-flight Checklist → Post-Operation Cleanup) integrated into a master prompt document that the Ralph Loop loads at session start.

**Tech Stack:** Markdown documentation, Bash scripting (for helper scripts)

---

## File Structure

```
.claude/
├── RALPH_LOOP_MASTER_PROMPT.md    # NEW - Main master prompt with integrated safety guard
└── ralph-loop.local.md             # EXISTING - Update to reference master prompt

docs/superpowers/
├── DOCKER_SAFETY_REFERENCE.md      # NEW - Quick reference for Docker commands
└── specs/2026-04-13-docker-safety-guard-design.md  # EXISTING - Design doc
```

---

## Task 1: Create Docker Safety Reference Document

**Files:**
- Create: `docs/superpowers/DOCKER_SAFETY_REFERENCE.md`

- [ ] **Step 1: Create Docker safety reference document**

```bash
cat > /home/ranj/Project_Chimera/docs/superpowers/DOCKER_SAFETY_REFERENCE.md << 'EOF'
# Docker Safety Reference

> **Purpose:** Quick reference for safe Docker operations in Project Chimera

---

## Pre-Flight Checklist

Before ANY Docker operation:

```bash
# 1. Check .dockerignore exists
ls services/*/Dockerfile | xargs -I {} sh -c 'echo "=== {} ===" && cat $(dirname {})/.dockerignore 2>/dev/null || echo "NO .dockerignore!"'

# 2. Check current disk usage
docker system df

# 3. Check for port conflicts
netstat -tuln | grep -E ':(8000|8001|8002|8004|8006|8007|8008|6379)'

# 4. Verify only specific service targeted
# (manual check - confirm you're not building entire stack)
```

---

## Forbidden Commands

🚨 **NEVER run these without explicit user approval:**

```bash
docker build *
docker buildx build *
docker compose build *
docker compose up --build *
podman build *
```

---

## Cleanup Commands

```bash
# Check disk usage
docker system df

# Remove dangling images (safe)
docker image prune -f

# Remove stopped containers (safe)
docker container prune -f

# Remove unused volumes (careful!)
docker volume prune -f

# Remove build cache (common bloat source)
docker builder prune -a -f

# Nuclear: clean everything (use with caution)
docker system prune -a --volumes -f
```

---

## Understanding `docker system df`

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          10        5         2.5GB     1.2GB (48%)
Containers      8         3         450MB     200MB (44%)
Local Volumes   15        8         3.1GB     800MB (26%)
Build Cache     50        0         1.8GB     1.8GB (100%)  ← COMMON BLOAT SOURCE
```

**Key:**
- SIZE = total space used
- RECLAIMABLE = safe to free
- ACTIVE = currently in use (don't delete)

---

## Project Chimera Service Ports

```
services/
├── openclaw-orchestrator/  (port 8000)
├── scenespeak-agent/       (port 8001)
├── translation-agent/      (port 8002) - not running
├── sentiment-agent/        (port 8004)
├── safety-filter/          (port 8006)
├── operator-console/       (port 8007)
├── hardware-bridge/        (port 8008)
└── redis/                  (port 6379)
```

---

## What Causes Bloat

| Source | Typical Size | Prevention |
|--------|--------------|-------------|
| Build cache | 1-5GB | Prune regularly, use .dockerignore |
| Dangling images | 500MB-2GB | `docker image prune -f` after builds |
| Old layers | 100MB-1GB each | Tag images, prune old versions |
| Volume data | Variable | Don't mount build artifacts |

---

## Emergency: Disk Full

If disk fills up:

```bash
# 1. Stop all Docker
docker compose down

# 2. Check usage
docker system df

# 3. Clean build cache (usually the culprit)
docker builder prune -a -f

# 4. Clean dangling images
docker image prune -a -f

# 5. If still full, nuclear option
docker system prune -a --volumes -f

# 6. Verify
df -h
docker system df
```
EOF
```

- [ ] **Step 2: Verify file created**

Run: `ls -lh docs/superpowers/DOCKER_SAFETY_REFERENCE.md`
Expected: File exists, readable

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/DOCKER_SAFETY_REFERENCE.md
git commit -m "docs: add Docker safety reference guide"
```

---

## Task 2: Create Ralph Loop Master Prompt

**Files:**
- Create: `.claude/RALPH_LOOP_MASTER_PROMPT.md`

- [ ] **Step 1: Create master prompt with integrated Docker safety guard**

```bash
cat > /home/ranj/Project_Chimera/.claude/RALPH_LOOP_MASTER_PROMPT.md << 'EOF'
# Ralph Loop Master Prompt - Project Chimera

> **Last Updated:** 2026-04-13
> **Iteration:** 30+
> **Purpose:** Autonomous development workflow for Project Chimera

---

## Project Context

```
Project: Project Chimera - AI-Powered Adaptive Live Theatre Framework
Status: Phase 1 Complete, MVP Validation Complete (Iteration 30)
Repository: /home/ranj/Project_Chimera
Branch: main
Working Directory: /home/ranj/Project_Chimera
```

### What's Been Done

✅ **Phase 1** (8 weeks): Local-First AI Framework Proof-of-Concept
✅ **Phase 2 Enhancement**: Production-ready services (14,335 lines)
✅ **Iteration 30**: MVP validation with 77 integration tests across 8 services
✅ **Documentation**: OVERVIEW, GETTING_STARTED, TESTING all refreshed
✅ **Tests**: 58 passing, 22 skipped (LLM-dependent services)

### Current System Architecture

```
services/
├── openclaw-orchestrator/  (port 8000) - Main orchestration
├── scenespeak-agent/       (port 8001) - LLM dialogue generation
├── sentiment-agent/        (port 8004) - DistilBERT sentiment analysis
├── safety-filter/          (port 8006) - Content safety
├── operator-console/       (port 8007) - Web UI
├── hardware-bridge/        (port 8008) - DMX lighting
├── translation-agent/      (port 8002) - Translation (not running)
└── redis/                  (port 6379) - Message broker
```

---

## ⚠️ CRITICAL CONSTRAINTS - DO NOT VIOLATE

### Docker Build Safety (CRITICAL - Hard Drive Protection)

**THESE RULES EXIST BECAUSE DOCKER HAS FILLED THE HARD DRIVE TWICE.**

#### 🚨 HARD GATE: Forbidden Commands

NEVER run these commands without EXPLICIT user approval:

```
docker build *
docker buildx build *
docker compose build *
docker compose up --build *
podman build *
```

**If you think you need to build:**

1. STOP immediately
2. Explain exactly WHY you think a build is necessary
3. Ask user for permission to proceed
4. Only build the SPECIFIC service needed (not entire stack)

#### ✅ Pre-Flight Checklist (REQUIRED before any Docker operation)

Before running ANY Docker operation (even `docker compose up`):

- [ ] `.dockerignore` exists in each service being built
- [ ] Build context is minimal (no venv, __pycache__, node_modules, .git)
- [ ] Run `docker system df` to check current disk usage
- [ ] Verify no port conflicts with existing services
- [ ] Confirm only specific service(s) targeted, not entire stack

#### 🧹 Post-Operation Cleanup (REQUIRED after any Docker build)

After any Docker build operation:

- [ ] Run `docker system df` to check new disk usage
- [ ] Run `docker image prune -f` if dangling images > 500MB
- [ ] Run `docker builder prune -f` if build cache > 1GB
- [ ] Confirm no unexpected bloat occurred

**Quick reference:** See `docs/superpowers/DOCKER_SAFETY_REFERENCE.md`

---

## Work Style Guidelines

1. **Read before writing** - Check existing code patterns
2. **Small, focused changes** - One thing at a time
3. **Test after changes** - Run relevant integration tests
4. **Commit frequently** - Small, descriptive commits
5. **No massive rebuilds** - Incremental changes only

---

## What Needs To Be Done

### Immediate Tasks (Priority Order)

1. **Review test failures from last run**
   - Check: `pytest tests/integration/ --verbose`
   - Identify what's actually broken vs. needs LLM/translation running

2. **Fix any genuine code issues**
   - API endpoint mismatches
   - Service integration bugs
   - Configuration issues

3. **Consider next steps**
   - Should Translation Agent be integrated?
   - Any new features needed?
   - Performance optimizations?

---

## Success Criteria

- All non-skipped tests passing
- No Docker bloat (verify with `docker system df`)
- Documentation matches current state
- Git history is clean and descriptive

---

## Startup Protocol

When starting a new Ralph Loop session:

1. Read this master prompt
2. Check current git status: `git status`
3. Check Docker disk usage: `docker system df`
4. Ask: "What would you like me to work on first?"

---

## This Prompt Ensures The Ralph Loop:

1. ✅ Understands the project context
2. ✅ Knows what's already been done
3. ✅ Has clear safety boundaries around Docker
4. ✅ Knows the priority order for tasks
5. ✅ Can ask clarifying questions before diving in

---

*For Docker safety details, refer to: docs/superpowers/DOCKER_SAFETY_REFERENCE.md*
*For project architecture, refer to: docs/MVP_OVERVIEW.md*
*For testing, refer to: docs/TESTING.md*
EOF
```

- [ ] **Step 2: Verify file created and readable**

Run: `cat .claude/RALPH_LOOP_MASTER_PROMPT.md | head -20`
Expected: File shows first 20 lines of master prompt

- [ ] **Step 3: Commit**

```bash
git add .claude/RALPH_LOOP_MASTER_PROMPT.md
git commit -m "feat: add Ralph Loop master prompt with Docker safety guard"
```

---

## Task 3: Update Local Session Reference

**Files:**
- Modify: `.claude/ralph-loop.local.md`

- [ ] **Step 1: Add reference to master prompt**

```bash
cat >> /home/ranj/Project_Chimera/.claude/ralph-loop.local.md << 'EOF'

---

## Ralph Loop Master Prompt

**Location:** `.claude/RALPH_LOOP_MASTER_PROMPT.md`

**Usage:** At the start of each Ralph Loop session, load and read the master prompt to ensure:

1. Project context is understood
2. Docker safety constraints are active
3. Work style guidelines are followed
4. Success criteria are clear

**Load command:** The master prompt should be provided as initial context when starting the loop.
EOF
```

- [ ] **Step 2: Verify update**

Run: `tail -15 .claude/ralph-loop.local.md`
Expected: Shows the new reference section

- [ ] **Step 3: Commit**

```bash
git add .claude/ralph-loop.local.md
git commit -m "docs: reference master prompt in local session file"
```

---

## Task 4: Create Pre-Flight Helper Script

**Files:**
- Create: `scripts/docker-preflight-check.sh`

- [ ] **Step 1: Create pre-flight check script**

```bash
mkdir -p /home/ranj/Project_Chimera/scripts

cat > /home/ranj/Project_Chimera/scripts/docker-preflight-check.sh << 'EOF'
#!/bin/bash
# Docker Pre-Flight Check
# Run this before any Docker build operation

set -e

echo "🔍 Docker Pre-Flight Check"
echo "=========================="
echo ""

# Check 1: .dockerignore files
echo "📋 Check 1: .dockerignore files"
echo "-------------------------------"
MISSING=0
for service in services/*/; do
    if [ -f "$service/Dockerfile" ]; then
        if [ -f "$service/.dockerignore" ]; then
            echo "✅ $service: .dockerignore found"
        else
            echo "❌ $service: .dockerignore MISSING!"
            MISSING=1
        fi
    fi
done
if [ $MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  WARNING: Missing .dockerignore files can cause bloat!"
    echo "   Consider adding them before building."
fi
echo ""

# Check 2: Current disk usage
echo "💾 Check 2: Current Docker Disk Usage"
echo "-------------------------------------"
docker system df
echo ""

# Check 3: Port conflicts
echo "🔌 Check 3: Port Conflicts"
echo "--------------------------"
PORTS=(8000 8001 8002 8004 8006 8007 8008 6379)
CONFLICTS=0
for port in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  Port $port is IN USE"
        CONFLICTS=1
    else
        echo "✅ Port $port is free"
    fi
done
echo ""

# Summary
echo "=========================="
if [ $MISSING -eq 0 ] && [ $CONFLICTS -eq 0 ]; then
    echo "✅ Pre-flight check PASSED"
    echo ""
    echo "Ready to proceed with Docker operations."
    exit 0
else
    echo "⚠️  Pre-flight check had WARNINGS"
    echo ""
    echo "Please review above before proceeding."
    exit 1
fi
EOF

chmod +x /home/ranj/Project_Chimera/scripts/docker-preflight-check.sh
```

- [ ] **Step 2: Test the script**

Run: `./scripts/docker-preflight-check.sh`
Expected: Script runs, shows .dockerignore status, disk usage, port conflicts

- [ ] **Step 3: Commit**

```bash
git add scripts/docker-preflight-check.sh
git commit -m "feat: add Docker pre-flight check helper script"
```

---

## Task 5: Create Post-Build Helper Script

**Files:**
- Create: `scripts/docker-postbuild-check.sh`

- [ ] **Step 1: Create post-build check script**

```bash
cat > /home/ranj/Project_Chimera/scripts/docker-postbuild-check.sh << 'EOF'
#!/bin/bash
# Docker Post-Build Check
# Run this after any Docker build operation

set -e

echo "🧹 Docker Post-Build Check"
echo "=========================="
echo ""

# Check current disk usage
echo "💾 Current Docker Disk Usage:"
echo "----------------------------"
docker system df
echo ""

# Parse and warn about reclaimable space
RECLAIMABLE=$(docker system df --format "{{.Reclaimable}}" | grep -E "[0-9]+GB|[0-9]+MB" | head -1)

echo "=========================="
echo "✅ Post-build check complete"
echo ""
echo "💡 Tips:"
echo "   - Run 'docker image prune -f' to clean dangling images"
echo "   - Run 'docker builder prune -f' to clean build cache"
echo "   - Run 'docker system df' anytime to check usage"
EOF

chmod +x /home/ranj/Project_Chimera/scripts/docker-postbuild-check.sh
```

- [ ] **Step 2: Test the script**

Run: `./scripts/docker-postbuild-check.sh`
Expected: Script shows disk usage and cleanup tips

- [ ] **Step 3: Commit**

```bash
git add scripts/docker-postbuild-check.sh
git commit -m "feat: add Docker post-build check helper script"
```

---

## Task 6: Update Master Prompt with Helper Script References

**Files:**
- Modify: `.claude/RALPH_LOOP_MASTER_PROMPT.md`

- [ ] **Step 1: Add helper script references to master prompt**

Edit `.claude/RALPH_LOOP_MASTER_PROMPT.md` - add after "Pre-Flight Checklist" section:

```bash
# Backup original
cp .claude/RALPH_LOOP_MASTER_PROMPT.md .claude/RALPH_LOOP_MASTER_PROMPT.md.bak

# Add helper script references (insert after "Quick reference:" line)
cat > /tmp/patch.txt << 'PATCH'

**Helper Scripts:**
```bash
# Pre-flight check (run before Docker operations)
./scripts/docker-preflight-check.sh

# Post-build check (run after Docker builds)
./scripts/docker-postbuild-check.sh
```
PATCH

# Insert after "Quick reference:" line (using sed)
sed -i '/Quick reference:/a\
\
**Helper Scripts:**\
```bash\
# Pre-flight check (run before Docker operations)\
./scripts/docker-preflight-check.sh\
\
# Post-build check (run after Docker builds)\
./scripts/docker-postbuild-check.sh\
```' .claude/RALPH_LOOP_MASTER_PROMPT.md
```

- [ ] **Step 2: Verify the update**

Run: `grep -A 5 "Helper Scripts" .claude/RALPH_LOOP_MASTER_PROMPT.md`
Expected: Shows the helper script references

- [ ] **Step 3: Clean up and commit**

```bash
rm .claude/RALPH_LOOP_MASTER_PROMPT.md.bak
git add .claude/RALPH_LOOP_MASTER_PROMPT.md
git commit -m "docs: add helper script references to master prompt"
```

---

## Task 7: Update README with Quick Start

**Files:**
- Modify: `README.md` (add brief section about Ralph Loop)

- [ ] **Step 1: Add Ralph Loop section to README**

```bash
# Check if README has a Ralph Loop section first
if ! grep -q "Ralph Loop" README.md; then
    cat >> /home/ranj/Project_Chimera/README.md << 'EOF'

---

## Ralph Loop (Autonomous Development)

Project Chimera uses an autonomous AI agent ("Ralph Loop") for iterative development.

**Master Prompt:** `.claude/RALPH_LOOP_MASTER_PROMPT.md`

**Docker Safety:** The Ralph Loop has strict constraints on Docker operations to prevent disk bloat. See `docs/superpowers/DOCKER_SAFETY_REFERENCE.md` for details.

**Progress Tracking:** See `.claude/ralph-loop-progress.md` for iteration history.
EOF
fi
```

- [ ] **Step 2: Verify update**

Run: `tail -15 README.md`
Expected: Shows Ralph Loop section

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Ralph Loop section to README"
```

---

## Task 8: Verification Test Run

**Files:**
- None (verification task)

- [ ] **Step 1: Run pre-flight check**

Run: `./scripts/docker-preflight-check.sh`
Expected: All checks pass or warnings are shown

- [ ] **Step 2: Run post-build check**

Run: `./scripts/docker-postbuild-check.sh`
Expected: Shows disk usage and tips

- [ ] **Step 3: Verify master prompt is complete**

Run: `wc -l .claude/RALPH_LOOP_MASTER_PROMPT.md`
Expected: File has 100+ lines with all sections

- [ ] **Step 4: Check all files committed**

Run: `git status`
Expected: No uncommitted changes (except this plan file)

---

## Task 9: Create Integration Test (Optional)

**Files:**
- Create: `tests/test_docker_safety_helpers.py`

- [ ] **Step 1: Create test for helper scripts**

```bash
cat > /home/ranj/Project_Chimera/tests/test_docker_safety_helpers.py << 'EOF'
"""Test Docker safety helper scripts."""

import subprocess
import os
from pathlib import Path


def test_preflight_script_exists():
    """Test that pre-flight check script exists and is executable."""
    script = Path("scripts/docker-preflight-check.sh")
    assert script.exists()
    assert os.access(script, os.X_OK)


def test_postbuild_script_exists():
    """Test that post-build check script exists and is executable."""
    script = Path("scripts/docker-postbuild-check.sh")
    assert script.exists()
    assert os.access(script, os.X_OK)


def test_preflight_runs():
    """Test that pre-flight check runs without error."""
    result = subprocess.run(
        ["./scripts/docker-preflight-check.sh"],
        capture_output=True,
        text=True
    )
    assert result.returncode in [0, 1]  # 0 = pass, 1 = warnings
    assert "Docker Pre-Flight Check" in result.stdout


def test_postbuild_runs():
    """Test that post-build check runs without error."""
    result = subprocess.run(
        ["./scripts/docker-postbuild-check.sh"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Docker Post-Build Check" in result.stdout


def test_master_prompt_exists():
    """Test that master prompt file exists."""
    prompt = Path(".claude/RALPH_LOOP_MASTER_PROMPT.md")
    assert prompt.exists()
    content = prompt.read_text()
    assert "CRITICAL CONSTRAINTS" in content
    assert "Docker Build Safety" in content


def test_docker_safety_reference_exists():
    """Test that Docker safety reference exists."""
    reference = Path("docs/superpowers/DOCKER_SAFETY_REFERENCE.md")
    assert reference.exists()
    content = reference.read_text()
    assert "Pre-Flight Checklist" in content
    assert "docker system df" in content
EOF
```

- [ ] **Step 2: Run the tests**

Run: `pytest tests/test_docker_safety_helpers.py -v`
Expected: All tests pass

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_docker_safety_helpers.py
git commit -m "test: add Docker safety helpers integration tests"
```

---

## Final Verification

- [ ] **All files created and committed**
- [ ] **Helper scripts executable**
- [ ] **Tests passing**
- [ ] **No Docker bloat** (verify with `docker system df`)

---

**Total Estimated Time:** 30-45 minutes

**Success Criteria:**
- ✅ Master prompt created at `.claude/RALPH_LOOP_MASTER_PROMPT.md`
- ✅ Docker safety guard integrated with three-layer protection
- ✅ Helper scripts created and tested
- ✅ Documentation updated
- ✅ All changes committed to git

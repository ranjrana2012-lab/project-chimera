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
3. Ask user for permission to proceed with this format:
   ```
   🔔 DOCKER BUILD REQUEST
   Service: <service-name>
   Build Context: <path>
   Estimated Size: <check with du -sh>
   .dockerignore: <yes/no>
   Reason: <why build is needed>
   Permission to proceed? (yes/no)
   ```
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

- All non-skipped tests passing (22 LLM-dependent tests are expected to skip)
- No Docker bloat (verify with `docker system df` - RECLAIMABLE should be < 1GB)
- Documentation matches current state (check README.md and docs/GETTING_STARTED.md)
- Git history is clean and descriptive (no WIP commits, clear messages)

---

## Error Recovery

If things go wrong:

**Docker bloat detected after operation:**
1. Stop: `docker compose down`
2. Check: `docker system df`
3. Clean: `docker builder prune -a -f && docker image prune -f`
4. Verify: `docker system df` (confirm RECLAIMABLE decreased)

**Tests fail after changes:**
1. Review test output for specific failure
2. Check if failure is related to your changes
3. Fix the issue or revert if unsure
4. Run tests again before committing

**Git status shows conflicts:**
1. Don't commit with conflicts
2. Resolve conflicts systematically
3. Test after resolution
4. Commit with clear message about what was resolved

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

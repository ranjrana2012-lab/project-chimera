# Docker Cleanup and Service Fixes Design

> **Date:** 2026-04-14
> **Status:** Draft
> **Priority:** High

## Problem Statement

**Issue 1: Bloated Docker Images**
- `chimera-openclaw-orchestrator` image is 184GB (should be ~13MB)
- `.dockerignore` was created AFTER images were built
- Old images contain 84GB build context that should have been excluded

**Issue 2: scenespeak-agent Restart Loop**
- Container stuck restarting with exit code 1
- Root cause: Pydantic validation errors from unprefixed environment variables
- Fix: `env_prefix="SCENESPEAK_"` already added to config.py but service not rebuilt

**Issue 3: Docker Cache Bloat**
- 273.6GB build cache accumulated
- Only 38.66GB showing as reclaimable
- Need cleanup after successful rebuilds

## Proposed Approach: Selective Rebuild + Fix + Cleanup

### Phase 1: Fix scenespeak-agent (Quick Win)

**Why first:** Fastest path to get all services healthy

**Steps:**
1. Rebuild scenespeak-agent with new env_prefix configuration
2. Verify service starts healthy
3. Test API endpoint responds correctly

**Expected outcome:** scenespeak-agent stops restarting, all 7 services healthy

### Phase 2: Rebuild openclaw-orchestrator (Big Impact)

**Why second:** Addresses the 184GB bloat, biggest disk space win

**Steps:**
1. Stop openclaw-orchestrator container
2. Remove old image (184GB)
3. Build with new .dockerignore
4. Verify new image size (~13MB expected)
5. Start and verify health

**Expected outcome:** openclaw-orchestrator image reduced to <500MB (measured: 13MB in previous validation)

### Phase 3: Verify PYTHONPATH Works

**Critical validation:** Ensure shared code imports still work after rebuild

**Steps:**
1. Check logs for import errors
2. Test /health endpoint
3. Test shared middleware is loaded

**Expected outcome:** No import errors, service healthy

### Phase 4: Clean Up Docker Cache

**Why last:** Only clean after confirming everything works

**Steps:**
1. Verify all services healthy
2. Run `docker system prune -a` with user approval
3. Check reclaimed space
4. Confirm services still running

**Expected outcome:** ~39GB+ reclaimed, system sustainable

## Architecture Decisions

### Decision 1: Selective Rebuild vs Full Rebuild

**Chosen:** Selective rebuild

**Rationale:**
- Minimizes downtime for healthy services
- Faster iteration cycle
- Can test each phase independently

**Trade-off:** Slightly more complex orchestration

### Decision 2: Keep Services Running During Rebuild

**Chosen:** Keep 6 healthy services running

**Rationale:**
- User can continue working/developing
- Only affected service goes down temporarily
- Faster validation between phases

**Trade-off:** Port conflicts during rebuild (handled by stopping specific service first)

### Decision 3: Prune Strategy

**Chosen:** `docker system prune -a` (removes unused images)

**Rationale:**
- Clears both dangling and old unused images
- Maximizes space reclamation
- Safe because .dockerignore ensures future builds are lean

**Trade-off:** Requires rebuild if switching between service versions

## Success Criteria

- [ ] All 7 services healthy (no restarting)
- [ ] `chimera-openclaw-orchestrator` image < 500MB
- [ ] scenespeak-agent responding to API calls
- [ ] Docker cache < 100GB
- [ ] No import errors in logs
- [ ] Shared code (middleware) accessible via PYTHONPATH

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Rebuild fails | Low | High | Keep old image until new one verified |
| PYTHONPATH breaks | Low | High | Test immediately after rebuild |
| Cache prune removes needed image | Medium | Low | Verify images tagged `latest` before prune |
| Port conflict during rebuild | Low | Low | Stop container before rebuild |

## Estimated Time

- Phase 1 (scenespeak-agent): 5 minutes
- Phase 2 (openclaw-orchestrator): 5 minutes
- Phase 3 (validation): 2 minutes
- Phase 4 (cleanup): 3 minutes
- **Total: ~15 minutes**

## Files to Modify

- **Rebuild only (no code changes):**
  - `services/scenespeak-agent/Dockerfile` (use existing)
  - `services/openclaw-orchestrator/Dockerfile` (use existing)

- **Verification scripts:**
  - Use existing `scripts/docker-preflight-check.sh`
  - Use existing `scripts/docker-postbuild-check.sh`

## Next Steps

Upon approval, invoke `writing-plans` skill to create implementation plan with detailed steps.

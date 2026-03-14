# Documentation Sync Design

> **Status:** Approved
> **Date:** 2026-03-14
> **Context:** After completing autonomous-agent service implementation (20 tasks, 20/20 tests passing, 79% coverage)

## Problem Statement

The autonomous-agent service has been fully implemented with 26 commits, but:
- Local commits not pushed to GitHub
- Project documentation doesn't reflect the new service
- API catalog missing autonomous-agent endpoints
- Service status page incomplete

## Design Approach

### Phase 1: Git Push (Critical Path)
Push 26 commits to origin/main to establish remote history. This must happen before documentation updates to ensure the documentation accurately reflects what's in the repository.

**Commands:**
```bash
git push origin main
```

**Validation:** Verify all 26 commits appear in remote repository.

### Phase 2: Service Status Update
Update `docs/SERVICE_STATUS.md` to include autonomous-agent entry.

**Changes:**
- Add row: `| Autonomous Agent | ✅ Operational | Port 8008 | Ralph Engine, GSD Orchestrator |`
- Update service count references (8 → 9 services)

### Phase 3: API Documentation
Create `docs/api/autonomous-agent.md` with complete API reference.

**Sections:**
- Overview (Ralph Engine + GSD Orchestrator)
- Base URL: `http://autonomous-agent:8008`
- Endpoints:
  - `GET /health` - Health check
  - `GET /status` - Detailed status with state file contents
  - `GET /metrics` - Prometheus metrics
  - `POST /execute` - Submit async task
  - `GET /execute/{task_id}` - Get task status/result
- Request/Response schemas
- Error responses
- Integration notes (connects to other agents via OpenClaw)

### Phase 4: Service Documentation
Create `docs/services/autonomous-agent.md` with operational documentation.

**Sections:**
- Purpose: Autonomous task execution engine
- Architecture: Ralph Engine + GSD Orchestrator + Flow-Next Manager
- Configuration: Environment variables
- Deployment: K8s HPA (2-10 replicas), resource limits
- State management: External state files (STATE.md, PLAN.md, REQUIREMENTS.md)
- Monitoring: Prometheus alerts, metrics
- Troubleshooting: Common issues and solutions

### Phase 5: Index and Catalog Updates
Update navigation to link new documentation.

**Files:**
- `docs/index.md`: Add autonomous-agent to Project Status table
- `docs/api/endpoints.md`: Add autonomous-agent endpoints to catalog

## Success Criteria

1. All 26 commits visible in GitHub repository
2. SERVICE_STATUS.md shows autonomous-agent as operational
3. API documentation complete with all 5 endpoints documented
4. Service documentation complete with architecture and ops info
5. Index and catalog link to new docs
6. No broken links or missing references

## Risk Mitigation

- **Git push fails:** Check network, credentials, remote URL
- **Merge conflicts:** None expected (no divergent changes)
- **Broken links:** Validate all internal links after updates

## Timeline Estimate

- Git push: 2 minutes
- Documentation updates: 10-15 minutes
- Validation: 3 minutes
- **Total:** ~20 minutes

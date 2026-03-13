# Requirements: Autonomous Agent Service

## Purpose
Transform Project Chimera into a self-managing autonomous system through Ralph Mode, GSD framework, and Flow-Next architecture.

## Success Criteria
- [ ] Ralph Engine implements 5-retry backstop
- [ ] GSD Orchestrator enforces Discuss→Plan→Execute→Verify
- [ ] Flow-Next provides fresh context per iteration
- [ ] All tests passing (unit + integration)
- [ ] Deployed on K3s with monitoring

## Constraints
- Must maintain external state (no in-context memory)
- Must verify each task against spec before proceeding
- Must not proceed without plan approval

## Dependencies
- FastAPI 0.100+
- OpenTelemetry instrumentation
- K3s cluster access
- Git write access

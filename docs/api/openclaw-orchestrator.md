# OpenClaw Orchestrator API Documentation

> **⚠️ DEPRECATED:** This service has been replaced by **Nemo Claw Orchestrator**.
>
> Please see [Nemo Claw Orchestrator API Documentation](../api/nemoclaw-orchestrator.md) for the current implementation.

**Version:** v0.5.0 (Legacy)
**Status:** Replaced by Nemo Claw Orchestrator
**Replacement:** See [Nemo Claw Orchestrator](../api/nemoclaw-orchestrator.md)

---

## Migration Notice

The OpenClaw Orchestrator has been replaced by **Nemo Claw Orchestrator** with the following enhancements:

### What's New in Nemo Claw

| Feature | OpenClaw (Legacy) | Nemo Claw (Current) |
|---------|-------------------|---------------------|
| **Policy Enforcement** | None | OpenShell policy layer (ALLOW/DENY/SANITIZE/ESCALATE) |
| **LLM Routing** | Direct calls | Privacy Router (95% local Nemotron, 5% guarded cloud) |
| **State Management** | In-memory | Redis-backed persistence |
| **Resilience** | Basic retry | Circuit breaker + exponential backoff |
| **WebSocket** | Basic broadcast | Policy-filtered broadcasts with PII removal |
| **Error Handling** | Generic errors | Structured error codes with detailed context |

### API Changes

Most endpoints remain compatible, but responses now include policy metadata:

**Old Response (OpenClaw):**
```json
{
  "result": {...},
  "skill_used": "dialogue_generator",
  "execution_time": 0.15
}
```

**New Response (Nemo Claw):**
```json
{
  "result": {...},
  "skill_used": "dialogue_generator",
  "execution_time": 0.15,
  "policy": {
    "checked": true,
    "action": "allow",
    "rules_applied": []
  },
  "llm_backend": "nemotron_local"
}
```

### New Endpoints

Nemo Claw adds the following endpoints:

- `GET /policy/rules` - List active OpenShell policies
- `POST /policy/test` - Test input against policies
- `GET /llm/status` - Privacy Router and backend status
- `GET /llm/backends` - Available LLM backends

### Migration Guide

For complete migration instructions, see:
- [Migration Guide](../migration-guide.md)
- [Nemo Claw Orchestrator API](../api/nemoclaw-orchestrator.md)
- [Nemo Claw Design Specification](../superpowers/specs/2026-03-18-nemoclaw-orchestrator-design.md)

### Quick Migration

**Old OpenClaw endpoint:**
```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"skill": "dialogue_generator", "input": {...}}'
```

**New Nemo Claw endpoint (same URL, enhanced response):**
```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"skill": "dialogue_generator", "input": {...}}'
```

The endpoint URL remains the same - you'll receive enhanced policy and routing metadata in the response.

---

*This documentation is preserved for historical reference. For current development, refer to the Nemo Claw Orchestrator documentation.*

*Last Updated: March 2026*
*OpenClaw Orchestrator v0.5.0 (Legacy) → Nemo Claw Orchestrator v1.0.0*

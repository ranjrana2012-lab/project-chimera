# Service Ports Reference

Complete port assignment reference for Project Chimera MVP services.

## Port Assignments

| Service | External Port | Internal Port | Purpose | Dependencies |
|---------|---------------|---------------|---------|---------------|
| OpenClaw Orchestrator | 8000 | 8000 | Main orchestration | All agents |
| SceneSpeak Agent | 8001 | 8001 | LLM dialogue | External LLM API |
| Translation Agent | 8002 | 8002 | Translation (15 languages) | None (mock mode) |
| Sentiment Agent | 8004 | 8004 | Sentiment analysis | Redis |
| Safety Filter | 8006 | 8006 | Content moderation | Redis |
| Operator Console | 8007 | 8007 | Show control UI | Orchestrator |
| Hardware Bridge | 8008 | 8008 | DMX simulation | Orchestrator |
| Redis | 6379 | 6379 | State management | None |

## Communication Flow

```
Operator Console (8007) → Orchestrator (8000) → Agents:
  → SceneSpeak (8001)
  → Sentiment (8004)
  → Safety (8006)
  → Hardware Bridge (8008)
Translation Agent (8002) - Independent, not called by orchestrator
```

**Note:** Port 8002 was originally assigned to captioning-agent in the full architecture.
The orchestrator's config.py still contains a legacy `captioning_agent_url: str = "http://localhost:8002"`
reference, but captioning-agent is NOT included in the MVP. Translation Agent now uses port 8002.

## Internal vs External Ports

All services use the same port internally and externally (no port remapping).
This simplifies debugging and service discovery.

## Port Change History

### Iteration 34 (2026-04-15)
- **Safety Filter:** 8005 → 8006 (reverted unauthorized change from Task 3)
- **Translation Agent:** 8006 → 8002 (resolved port collision with Safety Filter)

### Initial MVP Setup (Pre-Iteration 34)
- Safety Filter assigned to 8006
- Translation Agent assigned to 8006 (collision created later)
- No port conflicts in original design

## Why These Ports?

- **8000-8008:** Consecutive range for core application services
- **8002:** Available after moving Translation Agent during Iteration 34 (originally captioning-agent in full architecture)
- **8003:** Reserved for captioning-agent (private/local future concept, not in MVP)
- **8005:** Reserved for BSL/BeagleScore-Listener (private/local future concept, not in MVP)
- **8006:** Originally assigned to Safety Filter, restored after collision resolution
- **6379:** Standard Redis port (no reason to change)

## Usage Guidelines

### When Adding New Services
1. Check this reference for port conflicts
2. Choose an available port in the 8000-8008 range
3. Update this reference when assigning new ports
4. Update docker-compose.yml to match
5. Update dependent services' URLs if they call your service

### When Troubleshooting
1. Verify service is listening on expected port: `docker compose ps`
2. Check service logs for port binding errors
3. Verify no other service is using the port
4. Test endpoint directly: `curl http://localhost:<port>/health`

## Related Documentation

- [README.md](../../README.md) - Service status overview
- [MVP_OVERVIEW.md](../MVP_OVERVIEW.md) - Architecture overview
- [API_ENDPOINT_VERIFICATION.md](../API_ENDPOINT_VERIFICATION.md) - API documentation

*Last Updated: April 15, 2026*

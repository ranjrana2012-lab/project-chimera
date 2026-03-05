# Project Chimera API Documentation

This directory contains API documentation for Project Chimera services.

**Version:** 3.0.0
**Last Updated:** March 2026

---

## Core Service APIs

### [OpenClaw Orchestrator](./openclaw-orchestrator.md)
**Port:** 8000
- Skill routing and agent coordination
- Pipeline execution
- Health and metrics endpoints

### [SceneSpeak Agent](./scenespeak-agent.md)
**Port:** 8001
- LLM-powered dialogue generation
- **NEW:** LoRA adapter support for genre-specific styling
- Context-aware generation with sentiment

### [Captioning Agent](./captioning-agent.md)
**Port:** 8002
- Speech-to-text transcription
- Real-time WebSocket streaming
- Language detection

### [BSL Agent](./bsl-agent.md)
**Port:** 8003
- Text to BSL gloss translation
- **NEW:** Real-time avatar rendering for sign language
- Gesture library with caching

### [Sentiment Agent](./sentiment-agent.md)
**Port:** 8004
- Audience sentiment and emotion analysis
- Batch processing
- Sentiment trends and aggregation

### [Lighting Service](./lighting-service.md)
**Port:** 8005
- DMX/sACN lighting control
- Scene management
- Fixture control

### [Safety Filter](./safety-filter.md)
**Port:** 8006
- **NEW:** Multi-layer ML-based content moderation
- Pattern matching + ML classification + context-aware analysis
- Audit logging and statistics

### [Operator Console](./operator-console.md)
**Port:** 8007
- **NEW:** Real-time WebSocket updates
- Human oversight dashboard
- Manual approval and override controls

---

## Platform Service APIs

### [Dashboard Service](./dashboard-service.md)
**Port:** 8010
- Quality platform dashboards
- Service metrics visualization
- Test results display

### [Test Orchestrator](./test-orchestrator.md)
**Port:** 8011
- Test discovery and execution
- Result reporting
- Suite management

### [CI/CD Gateway](./cicd-gateway.md)
**Port:** 8012
- GitHub/GitLab webhook integration
- Deployment triggers
- Workflow run management

### [Quality Gate](./quality-gate.md)
**Port:** 8013
- Quality threshold enforcement
- PR quality checks
- Coverage, test, and performance gates

---

## Quick Reference

| Service | Port | Key Endpoint |
|---------|------|--------------|
| OpenClaw | 8000 | `POST /v1/orchestrate` |
| SceneSpeak | 8001 | `POST /v1/generate` |
| Captioning | 8002 | `POST /api/v1/transcribe` |
| BSL | 8003 | `POST /api/v1/translate` |
| Sentiment | 8004 | `POST /api/v1/analyze` |
| Lighting | 8005 | `POST /v1/lighting/set` |
| Safety | 8006 | `POST /api/v1/check` |
| Console | 8007 | `WS /ws/realtime` |
| Dashboard | 8010 | `GET /api/v1/dashboard` |
| Test Orchestrator | 8011 | `POST /api/v1/tests/run` |
| CI/CD Gateway | 8012 | `POST /api/v1/deploy` |
| Quality Gate | 8013 | `GET /api/v1/gate/check` |

---

## New Features in v0.4.0

### SceneSpeak LoRA Adapters
```bash
# Load adapter
curl -X POST http://localhost:8001/v1/adapters/load \
  -d '{"name": "dramatic-theatre"}'

# Generate with adapter
curl -X POST http://localhost:8001/v1/generate \
  -d '{"context": "...", "adapter": "dramatic-theatre"}'
```

### Multi-Layer Safety Filtering
```bash
curl -X POST http://localhost:8006/api/v1/check \
  -d '{
    "content": "Test message",
    "conversation_history": [...]
  }'
```

### BSL Avatar Rendering
```bash
curl -X POST http://localhost:8003/api/v1/avatar/sign \
  -d '{"text": "Hello!", "session_id": "user123"}'
```

### Real-Time Console Updates
```javascript
const ws = new WebSocket('ws://localhost:8007/ws/realtime');
ws.send(JSON.stringify({
  action: 'subscribe',
  channels: ['metrics:*', 'alerts']
}));
```

---

## Authentication

Current (local development): No authentication required

Production: API key authentication will be required

---

## Error Responses

All services follow this error format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

---

## Common Headers

| Header | Description |
|--------|-------------|
| `Content-Type` | `application/json` for POST/PUT |
| `Accept` | `application/json` for API responses |
| `User-Agent` | Recommended for debugging |

---

*For the latest API updates, see [API_ENDPOINT_VERIFICATION.md](../API_ENDPOINT_VERIFICATION.md)*

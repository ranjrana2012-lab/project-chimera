# Nemo Claw Orchestrator API Documentation

**Version:** v1.0.0
**Base URL:** `http://localhost:8000`
**Service:** Privacy-aware orchestration with OpenShell policy enforcement

---

## Overview

Nemo Claw Orchestrator is the next-generation replacement for OpenClaw Orchestrator, providing enhanced security, privacy, and policy enforcement for Project Chimera. It routes requests to appropriate AI agents while enforcing OpenShell policies and implementing privacy-preserving LLM routing.

### Key Differences from OpenClaw

| Feature | OpenClaw | Nemo Claw |
|---------|----------|-----------|
| Policy Enforcement | Basic | OpenShell comprehensive |
| Privacy Routing | None | 95% local / 5% cloud |
| State Management | In-memory | Redis-backed persistence |
| LLM Routing | Direct only | Privacy-aware with fallback |
| Circuit Breakers | No | Yes, per-agent |
| WebSocket | Basic | Enhanced with policy filtering |
| API Version | v0.5.0 | v1.0.0 |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Nemo Claw Orchestrator                      │
│                      (Port 8000)                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Policy Engine │  │ Privacy Router│  │ State Machine   │  │
│  │ (OpenShell)   │  │ (95% local)   │  │ (Redis-backed)  │  │
│  └───────────────┘  └──────────────┘  └─────────────────┘  │
│           │                  │                  │            │
│           └──────────────────┴──────────────────┘            │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │   Agent     │                          │
│                    │Coordinator  │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│      ┌────────────────────┼────────────────────┐           │
│      │                    │                    │           │
│  ┌───▼───┐          ┌────▼────┐         ┌────▼────┐       │
│  │Scene  │          │Sentiment │         │   BSL   │       │
│  │Speak  │          │  Agent   │         │  Agent  │       │
│  └───────┘          └──────────┘         └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Endpoints

### 1. Orchestrate Request

Execute orchestration through privacy-aware LLM router with policy enforcement.

**Endpoint:** `POST /v1/orchestrate`

**Request Body:**

```json
{
  "prompt": "Generate dialogue for a romantic scene",
  "max_tokens": 512,
  "temperature": 0.7,
  "agent": "scenespeak",
  "skill": "generate"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | Input prompt for LLM processing |
| `max_tokens` | integer | No | Maximum tokens to generate (default: 512) |
| `temperature` | float | No | Sampling temperature (default: 0.7) |
| `agent` | string | No | Target agent (default: auto-detect) |
| `skill` | string | No | Skill/method to call (default: auto-detect) |

**Response:**

```json
{
  "status": "success",
  "response": {
    "text": "ROMEO: What light through yonder window breaks?",
    "metadata": {
      "model": "nemotron-8b",
      "tokens_used": 45
    }
  },
  "routing_metadata": {
    "backend": "nemotron_local",
    "policy_action": "allow",
    "policy_rule": "default_allow",
    "processing_time_ms": 234
  }
}
```

**Policy Metadata:**

The response includes policy enforcement metadata:

| Field | Description |
|-------|-------------|
| `backend` | Which LLM backend was used (`nemotron_local`, `cloud_guarded`, `fallback`) |
| `policy_action` | Policy action taken (`allow`, `deny`, `sanitize`, `escalate`) |
| `policy_rule` | Name of the policy rule that was applied |
| `processing_time_ms` | Total processing time in milliseconds |

---

### 2. Health Checks

**Endpoint:** `GET /health/live`

Liveness probe - checks if the service is running.

**Response:**

```json
{
  "status": "alive",
  "service": "nemoclaw-orchestrator"
}
```

---

**Endpoint:** `GET /health/ready`

Readiness probe with detailed component status.

**Response:**

```json
{
  "status": "ready",
  "service": "nemoclaw-orchestrator",
  "components": {
    "policy_engine": true,
    "privacy_router": true,
    "state_machine": true,
    "state_store": true,
    "agent_coordinator": true,
    "websocket_manager": true
  }
}
```

**Component Status:**

| Component | Description |
|-----------|-------------|
| `policy_engine` | OpenShell policy engine initialized |
| `privacy_router` | Privacy router ready (DGX + cloud) |
| `state_machine` | Show state machine operational |
| `state_store` | Redis connection established |
| `agent_coordinator` | Agent adapters initialized |
| `websocket_manager` | WebSocket manager ready |

---

### 3. Show Management

**Endpoint:** `POST /api/show/start`

Start a new show or resume an existing show.

**Request Body:**

```json
{
  "show_id": "romeo-and-juliet-2026-03-19",
  "metadata": {
    "title": "Romeo and Juliet",
    "date": "2026-03-19",
    "venue": "University Theatre"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `show_id` | string | No | Show identifier (default: "default") |
| `metadata` | object | No | Additional show metadata |

**Response:**

```json
{
  "status": "success",
  "state": {
    "show_id": "romeo-and-juliet-2026-03-19",
    "status": "running",
    "started_at": "2026-03-19T19:00:00Z",
    "metadata": {
      "title": "Romeo and Juliet",
      "date": "2026-03-19",
      "venue": "University Theatre"
    }
  }
}
```

---

**Endpoint:** `POST /api/show/end`

End the current show.

**Request Body:**

```json
{
  "show_id": "romeo-and-juliet-2026-03-19"
}
```

**Response:**

```json
{
  "status": "success",
  "state": {
    "show_id": "romeo-and-juliet-2026-03-19",
    "status": "ended",
    "ended_at": "2026-03-19T21:30:00Z",
    "duration_seconds": 9000
  }
}
```

---

**Endpoint:** `GET /api/show/state`

Get current show state.

**Response:**

```json
{
  "status": "success",
  "state": "running",
  "is_running": true,
  "is_paused": false,
  "is_ended": false,
  "show_id": "romeo-and-juliet-2026-03-19",
  "started_at": "2026-03-19T19:00:00Z",
  "elapsed_seconds": 1800
}
```

---

### 4. WebSocket Connection

**Endpoint:** `WebSocket /ws/show`

Real-time show updates via WebSocket connection.

**Connection URL:**

```
ws://localhost:8000/ws/show
```

**Message Format:**

```json
{
  "action": "start_show | end_show | agent_call | ping",
  "data": {
    // Action-specific data
  }
}
```

**Actions:**

| Action | Description | Data Format |
|--------|-------------|-------------|
| `start_show` | Start a new show | `{"show_id": "..."}` |
| `end_show` | End the current show | `{"show_id": "..."}` |
| `agent_call` | Call an agent | `{"agent": "...", "skill": "...", "input": {...}}` |
| `ping` | Ping server | `{}` |

**Server Response Format:**

```json
{
  "type": "connected | update | error | agent_response",
  "data": {
    // Response-specific data
  },
  "timestamp": "2026-03-19T19:00:00Z"
}
```

**Response Types:**

| Type | Description |
|------|-------------|
| `connected` | Connection established confirmation |
| `update` | Show state update |
| `error` | Error occurred |
| `agent_response` | Agent call response |

**Example WebSocket Session:**

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/show');

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);
};

// Send start_show action
ws.send(JSON.stringify({
  action: 'start_show',
  data: {
    show_id: 'my-show',
    metadata: { title: 'My Show' }
  }
}));

// Send agent_call action
ws.send(JSON.stringify({
  action: 'agent_call',
  data: {
    agent: 'scenespeak',
    skill: 'generate',
    input: {
      prompt: 'Generate dialogue',
      context: { scene: 'garden' }
    }
  }
}));

// Expected response:
// {
//   "type": "agent_response",
//   "data": {
//     "agent": "scenespeak",
//     "response": {...},
//     "policy": {...}
//   },
//   "timestamp": "2026-03-19T19:00:00Z"
// }
```

---

### 5. Policy Management

**Endpoint:** `GET /policy/rules`

Get all active policy rules.

**Response:**

```json
{
  "rules": [
    {
      "name": "deny_dangerous_commands",
      "agent": "lighting-sound-music",
      "action": "deny",
      "conditions": {
        "command_contains": ["shutdown", "reboot", "format"]
      },
      "output_filter": true
    },
    {
      "name": "sanitize_user_input",
      "agent": "scenespeak",
      "action": "sanitize",
      "conditions": {
        "max_length": 1000
      },
      "output_filter": true
    }
  ],
  "total": 10,
  "active": 10
}
```

---

**Endpoint:** `POST /policy/test`

Test a policy rule against input data.

**Request Body:**

```json
{
  "agent": "scenespeak",
  "skill": "generate",
  "input_data": {
    "prompt": "Generate dialogue",
    "context": {"scene": "garden"}
  }
}
```

**Response:**

```json
{
  "action": "allow",
  "reason": "No specific policy applies",
  "rule_name": null,
  "sanitization_rules": null
}
```

---

### 6. LLM Status

**Endpoint:** `GET /llm/status`

Get status of LLM backends.

**Response:**

```json
{
  "backends": {
    "nemotron_local": {
      "available": true,
      "endpoint": "http://dgx.local:8000",
      "model": "nemotron-8b",
      "last_check": "2026-03-19T19:00:00Z"
    },
    "cloud_guarded": {
      "available": true,
      "endpoint": "anthropic-api",
      "model": "claude-3-haiku-20240307",
      "last_check": "2026-03-19T19:00:00Z"
    }
  },
  "routing_config": {
    "local_ratio": 0.95,
    "cloud_fallback_enabled": true
  },
  "statistics": {
    "total_requests": 1000,
    "local_requests": 950,
    "cloud_requests": 50,
    "fallback_count": 5
  }
}
```

---

## Configuration

The Nemo Claw Orchestrator uses environment variables for configuration. Create a `.env` file in the service directory or set these variables in your deployment environment.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `nemoclaw-orchestrator` | Service identifier for logging and monitoring |
| `PORT` | integer | `8000` | HTTP server port |
| `DEBUG` | boolean | `false` | Enable debug mode (verbose logging) |
| `DGX_ENDPOINT` | string | `http://localhost:8000` | NVIDIA DGX endpoint for local LLM |
| `NEMOTRON_MODEL` | string | `nemotron-8b` | Nemotron model to use |
| `LOCAL_RATIO` | float | `0.95` | Ratio of local vs cloud LLM requests (0.0-1.0) |
| `CLOUD_FALLBACK_ENABLED` | boolean | `true` | Enable cloud fallback on local failure |
| `REDIS_URL` | string | `redis://localhost:6379` | Redis connection URL for state persistence |
| `REDIS_SHOW_STATE_TTL` | integer | `3600` | TTL for show state in Redis (seconds) |
| `SCENESPEAK_AGENT_URL` | string | `http://localhost:8001` | SceneSpeak agent service URL |
| `CAPTIONING_AGENT_URL` | string | `http://localhost:8002` | Captioning agent service URL |
| `BSL_AGENT_URL` | string | `http://localhost:8003` | BSL (sign language) agent service URL |
| `SENTIMENT_AGENT_URL` | string | `http://localhost:8004` | Sentiment analysis agent service URL |
| `LIGHTING_SOUND_MUSIC_URL` | string | `http://localhost:8005` | Lighting, sound, and music agent service URL |
| `SAFETY_FILTER_URL` | string | `http://localhost:8006` | Safety filter agent service URL |
| `MUSIC_GENERATION_URL` | string | `http://localhost:8011` | Music generation service URL |
| `AUTONOMOUS_AGENT_URL` | string | `http://localhost:8012` | Autonomous agent service URL |
| `OTLP_ENDPOINT` | string | `http://localhost:4317` | OpenTelemetry protocol endpoint for tracing |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Example .env File

```bash
# Service Configuration
SERVICE_NAME=nemoclaw-orchestrator
PORT=8000
DEBUG=false

# DGX Configuration
DGX_ENDPOINT=http://dgx.local:8000
NEMOTRON_MODEL=nemotron-8b

# Privacy Router Configuration
LOCAL_RATIO=0.95
CLOUD_FALLBACK_ENABLED=true

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_SHOW_STATE_TTL=3600

# Agent URLs (use localhost for development, service names for K8s)
SCENESPEAK_AGENT_URL=http://localhost:8001
CAPTIONING_AGENT_URL=http://localhost:8002
BSL_AGENT_URL=http://localhost:8003
SENTIMENT_AGENT_URL=http://localhost:8004
LIGHTING_SOUND_MUSIC_URL=http://localhost:8005
SAFETY_FILTER_URL=http://localhost:8006
MUSIC_GENERATION_URL=http://localhost:8011
AUTONOMOUS_AGENT_URL=http://localhost:8012

# OpenTelemetry Configuration
OTLP_ENDPOINT=http://localhost:4317

# Logging Configuration
LOG_LEVEL=INFO
```

### Configuration Notes

- **DGX Endpoint**: Set `DGX_ENDPOINT` to your NVIDIA DGX server address for local LLM inference
- **Privacy Ratio**: `LOCAL_RATIO` determines the percentage of LLM requests processed locally (0.95 = 95%)
- **Redis**: Required for show state persistence. Disable by omitting `REDIS_URL` (state will be in-memory only)
- **Agent URLs**: For local development, use `localhost` with the appropriate port. For Kubernetes deployments, use the service names
- **OpenTelemetry**: Set `OTLP_ENDPOINT` to your OTLP collector address. Disable tracing by omitting this variable
- **Debug Mode**: When `DEBUG=true`, additional logging is enabled and detailed error messages are returned

---

## Examples

### Orchestrate with Policy Enforcement

**Using curl:**

```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate romantic dialogue for Romeo and Juliet",
    "max_tokens": 512,
    "temperature": 0.7,
    "agent": "scenespeak",
    "skill": "generate"
  }'
```

**Response:**

```json
{
  "status": "success",
  "response": {
    "text": "ROMEO: What light through yonder window breaks?",
    "metadata": {
      "model": "nemotron-8b",
      "tokens_used": 45
    }
  },
  "routing_metadata": {
    "backend": "nemotron_local",
    "policy_action": "allow",
    "policy_rule": "default_allow",
    "processing_time_ms": 234
  }
}
```

---

### Start a Show

**Using Python:**

```python
import requests
import json

url = "http://localhost:8000/api/show/start"
headers = {"Content-Type": "application/json"}
payload = {
    "show_id": "romeo-and-juliet-2026-03-19",
    "metadata": {
        "title": "Romeo and Juliet",
        "date": "2026-03-19",
        "venue": "University Theatre"
    }
}

response = requests.post(url, json=payload, headers=headers)
response.raise_for_status()
result = response.json()

print(f"Show started: {result['state']['show_id']}")
print(f"Status: {result['state']['status']}")
```

---

### Test Policy Rules

**Using Python:**

```python
import requests

url = "http://localhost:8000/policy/test"
payload = {
    "agent": "scenespeak",
    "skill": "generate",
    "input_data": {
        "prompt": "Generate dialogue",
        "context": {"scene": "garden"}
    }
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Policy Action: {result['action']}")
print(f"Reason: {result['reason']}")
```

---

### WebSocket Connection

**Using JavaScript:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/show');

ws.onopen = () => {
  console.log('Connected to Nemo Claw Orchestrator');

  // Start a show
  ws.send(JSON.stringify({
    action: 'start_show',
    data: {
      show_id: 'my-show',
      metadata: { title: 'My Show' }
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);

  if (message.type === 'connected') {
    console.log('Connection ID:', message.data.connection_id);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from Nemo Claw Orchestrator');
};
```

---

### Check LLM Status

**Using curl:**

```bash
curl http://localhost:8000/llm/status
```

**Response:**

```json
{
  "backends": {
    "nemotron_local": {
      "available": true,
      "endpoint": "http://dgx.local:8000",
      "model": "nemotron-8b"
    },
    "cloud_guarded": {
      "available": true,
      "endpoint": "anthropic-api",
      "model": "claude-3-haiku-20240307"
    }
  },
  "routing_config": {
    "local_ratio": 0.95,
    "cloud_fallback_enabled": true
  },
  "statistics": {
    "total_requests": 1000,
    "local_requests": 950,
    "cloud_requests": 50
  }
}
```

---

### Health Check with Component Status

**Using Python:**

```python
import requests

response = requests.get("http://localhost:8000/health/ready")
status = response.json()

print(f"Service: {status['service']}")
print(f"Status: {status['status']}")
print("\nComponents:")
for component, ready in status['components'].items():
    print(f"  {component}: {'✓' if ready else '✗'}")
```

---

## Error Codes

| HTTP Code | Error Type | Description |
|-----------|------------|-------------|
| 400 | `ValidationError` | Invalid request parameters |
| 401 | `AuthenticationError` | Authentication required |
| 403 | `PolicyViolationError` | Request denied by policy |
| 404 | `NotFoundError` | Resource not found |
| 429 | `RateLimitError` | Too many requests |
| 500 | `InternalError` | Internal server error |
| 503 | `ServiceUnavailableError` | Service temporarily unavailable |
| 503 | `CircuitBreakerOpenError` | Agent circuit breaker is open |

**Error Response Format:**

```json
{
  "error": {
    "type": "PolicyViolationError",
    "message": "Request denied by policy: dangerous command detected",
    "code": "POLICY_DENY",
    "details": {
      "agent": "lighting-sound-music",
      "skill": "execute",
      "rule": "deny_dangerous_commands"
    }
  }
}
```

---

## Policy Actions

The Nemo Claw Orchestrator supports the following policy actions:

| Action | Description | Example |
|--------|-------------|---------|
| `ALLOW` | Request is allowed as-is | Default behavior for benign requests |
| `DENY` | Request is blocked | Dangerous commands, malicious input |
| `SANITIZE` | Input is sanitized before processing | Profanity filtering, PII removal |
| `ESCALATE` | Request requires human approval | Unusual patterns, edge cases |

**Policy Enforcement Flow:**

1. **Input Check**: Policy engine evaluates input against rules
2. **Action Determination**: Returns ALLOW, DENY, SANITIZE, or ESCALATE
3. **Processing**:
   - ALLOW: Proceed normally
   - DENY: Return 403 error
   - SANITIZE: Clean input and proceed
   - ESCALATE: Queue for human approval
4. **Output Filter**: Response filtered through output policies

---

## Migration from OpenClaw

### API Changes

| OpenClaw | Nemo Claw | Notes |
|----------|-----------|-------|
| `POST /v1/orchestrate` | `POST /v1/orchestrate` | Compatible, adds policy metadata |
| `GET /skills` | `GET /policy/rules` | Different endpoint, new structure |
| `GET /skills/{name}` | `GET /policy/test` | Use test endpoint to check policies |
| `POST /api/show/start` | `POST /api/show/start` | Compatible, adds metadata |
| `POST /api/show/end` | `POST /api/show/end` | Compatible |

### Migration Steps

1. **Update Base URL**: Change from `openclaw-orchestrator` to `nemoclaw-orchestrator`
2. **Handle Policy Metadata**: Update clients to process `routing_metadata` in responses
3. **Update Health Checks**: Use new `/health/ready` endpoint for component status
4. **Configure Privacy**: Set `LOCAL_RATIO` and `DGX_ENDPOINT` environment variables
5. **Test Policies**: Use `/policy/test` endpoint to verify policy behavior

---

## Performance Considerations

### Latency

| Operation | Typical Latency | Notes |
|-----------|----------------|-------|
| Local LLM (Nemotron) | 200-500ms | 95% of requests |
| Cloud LLM (Guarded) | 500-1000ms | 5% of requests + PII stripping |
| Policy Check | <10ms | In-memory evaluation |
| Agent Call | 100-300ms | Depends on agent |
| WebSocket | <50ms | Real-time updates |

### Throughput

- **Max Requests/Second**: 100+ (depends on DGX capacity)
- **Concurrent Connections**: 1000+ WebSocket connections
- **State Persistence**: <5ms for Redis operations

### Optimization Tips

1. **Increase Local Ratio**: Set `LOCAL_RATIO=0.99` for maximum privacy
2. **Enable Redis Cache**: Reduce state retrieval latency
3. **Use Connection Pooling**: Reuse HTTP connections to agents
4. **Monitor Circuit Breakers**: Track agent availability and adjust timeouts

---

## Security

### Authentication

Currently, Nemo Claw Orchestrator does not implement authentication. For production deployments:

1. Enable TLS/HTTPS
2. Implement API key authentication
3. Use network policies to restrict access
4. Enable audit logging

### Authorization

Policy enforcement is handled by the OpenShell policy engine. Configure policies in `policy/rules.py`.

### PII Protection

- Local LLM requests: No data leaves your infrastructure
- Cloud LLM requests: PII is stripped before sending to cloud
- State persistence: Sensitive data is encrypted in Redis

---

## Monitoring

### Metrics

Nemo Claw Orchestrator exposes Prometheus metrics at `/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `orchestrate_requests_total` | Counter | Total orchestration requests |
| `orchestrate_duration_seconds` | Histogram | Request duration |
| `policy_checks_total` | Counter | Total policy checks |
| `policy_violations_total` | Counter | Total policy violations |
| `llm_requests_total` | Counter | Total LLM requests (by backend) |
| `agent_requests_total` | Counter | Total agent requests (by agent) |
| `websocket_connections_active` | Gauge | Active WebSocket connections |

### Logging

Logs are structured JSON with the following fields:

- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `service`: Service name
- `message`: Log message
- `context`: Additional context (agent, policy, etc.)

**Example Log Entry:**

```json
{
  "timestamp": "2026-03-19T19:00:00Z",
  "level": "INFO",
  "service": "nemoclaw-orchestrator",
  "message": "Agent call completed",
  "context": {
    "agent": "scenespeak",
    "skill": "generate",
    "policy_action": "allow",
    "backend": "nemotron_local",
    "duration_ms": 234
  }
}
```

---

## Troubleshooting

### Common Issues

**Issue**: "Privacy router not initialized"

**Solution**: Check DGX endpoint configuration and connectivity

```bash
curl http://dgx.local:8000/health
```

---

**Issue**: "Redis connection failed"

**Solution**: Verify Redis is running and accessible

```bash
redis-cli ping
```

---

**Issue**: "Policy violation denied"

**Solution**: Review policy rules and adjust if needed

```bash
curl http://localhost:8000/policy/rules
```

---

**Issue**: "Circuit breaker is open"

**Solution**: Wait for circuit breaker to reset or check agent health

```bash
curl http://localhost:8001/health/ready
```

---

## Support

For issues, questions, or contributions:

- **GitHub**: https://github.com/ranjrana2012-lab/project-chimera
- **Issues**: https://github.com/ranjrana2012-lab/project-chimera/issues
- **Discussions**: https://github.com/ranjrana2012-lab/project-chimera/discussions

---

*Last Updated: March 2026*
*Nemo Claw Orchestrator v1.0.0*

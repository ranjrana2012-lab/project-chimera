# OpenClaw Orchestrator API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8000`
**Service:** Skill routing and agent coordination

---

## Overview

OpenClaw Orchestrator routes requests to appropriate skills and coordinates between AI agents.

---

## Endpoints

### 1. Orchestrate Request

Execute orchestration through available skills.

**Endpoint:** `POST /v1/orchestrate`

**Request Body:**

```json
{
  "skill": "dialogue_generator",
  "input": {
    "scene_context": "A garden at sunset",
    "sentiment": 0.7
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill` | string | Yes | Name of the skill to invoke |
| `input` | object | Yes | Skill-specific input data |
| `context` | object | No | Additional orchestration context |

**Response:**

```json
{
  "result": {
    "dialogue": "ROMEO: What light through yonder window breaks?"
  },
  "skill_used": "dialogue_generator",
  "execution_time": 0.15,
  "metadata": {}
}
```

---

### 2. List Available Skills

Get list of all available skills.

**Endpoint:** `GET /skills`

**Response:**

```json
{
  "skills": [
    {
      "name": "dialogue_generator",
      "description": "Generate contextual dialogue",
      "version": "1.0.0",
      "enabled": true
    },
    {
      "name": "sentiment_analyzer",
      "description": "Analyze audience sentiment",
      "version": "1.0.0",
      "enabled": true
    }
  ],
  "total": 10,
  "enabled": 10
}
```

---

### 3. Get Skill Metadata

Get metadata for a specific skill.

**Endpoint:** `GET /skills/{skill_name}`

**Response:**

```json
{
  "name": "dialogue_generator",
  "description": "Generate contextual dialogue",
  "version": "1.0.0",
  "enabled": true,
  "parameters": {
    "scene_context": {"type": "string", "required": true},
    "sentiment": {"type": "float", "required": false, "default": 0.0}
  }
}
```

---

### 4. Health Checks

**Endpoint:** `GET /health/live`

**Response:** `OK`

**Endpoint:** `GET /health/ready`

**Response:** `OK`

---

### 5. Metrics

**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format.

---

## Configuration

The OpenClaw Orchestrator uses environment variables for configuration. Create a `.env` file in the service directory or set these variables in your deployment environment.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `openclaw-orchestrator` | Service identifier for logging and monitoring |
| `PORT` | integer | `8000` | HTTP server port |
| `DEBUG` | boolean | `false` | Enable debug mode (verbose logging) |
| `SCENESPEAK_AGENT_URL` | string | `http://localhost:8001` | SceneSpeak agent service URL |
| `CAPTIONING_AGENT_URL` | string | `http://localhost:8002` | Captioning agent service URL |
| `BSL_AGENT_URL` | string | `http://localhost:8003` | BSL (sign language) agent service URL |
| `SENTIMENT_AGENT_URL` | string | `http://localhost:8004` | Sentiment analysis agent service URL |
| `LIGHTING_SOUND_MUSIC_URL` | string | `http://localhost:8005` | Lighting, sound, and music agent service URL |
| `SAFETY_FILTER_URL` | string | `http://localhost:8006` | Safety filter agent service URL |
| `OTLP_ENDPOINT` | string | `http://localhost:4317` | OpenTelemetry protocol endpoint for tracing |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Example .env File

```bash
# Service Configuration
SERVICE_NAME=openclaw-orchestrator
PORT=8000
DEBUG=false

# Agent URLs (use localhost for development, service names for K8s)
SCENESPEAK_AGENT_URL=http://localhost:8001
CAPTIONING_AGENT_URL=http://localhost:8002
BSL_AGENT_URL=http://localhost:8003
SENTIMENT_AGENT_URL=http://localhost:8004
LIGHTING_SOUND_MUSIC_URL=http://localhost:8005
SAFETY_FILTER_URL=http://localhost:8006

# OpenTelemetry Configuration
OTLP_ENDPOINT=http://localhost:4317

# Logging Configuration
LOG_LEVEL=INFO
```

### Configuration Notes

- **Agent URLs**: For local development, use `localhost` with the appropriate port. For Kubernetes deployments, use the service names (e.g., `http://scenespeak-agent:8001`)
- **OpenTelemetry**: Set `OTLP_ENDPOINT` to your OTLP collector address. Disable tracing by omitting this variable or setting it to an empty string
- **Debug Mode**: When `DEBUG=true`, additional logging is enabled and detailed error messages are returned
- **Environment Priority**: Environment variables take precedence over defaults defined in `config.py`

---

## Examples

### Orchestrate Dialogue Generation

**Using curl:**

```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "dialogue_generator",
    "input": {
      "scene_context": "A garden at sunset",
      "sentiment": 0.7
    }
  }'
```

**Using Python:**

```python
import requests
import json

url = "http://localhost:8000/v1/orchestrate"
headers = {"Content-Type": "application/json"}
payload = {
    "skill": "dialogue_generator",
    "input": {
        "scene_context": "A garden at sunset",
        "sentiment": 0.7
    }
}

response = requests.post(url, json=payload, headers=headers)
response.raise_for_status()
result = response.json()

print(f"Result: {result['result']}")
print(f"Execution time: {result['execution_time']}s")
```

**Using JavaScript/fetch:**

```javascript
const response = await fetch('http://localhost:8000/v1/orchestrate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    skill: 'dialogue_generator',
    input: {
      scene_context: 'A garden at sunset',
      sentiment: 0.7
    }
  })
});

const result = await response.json();
console.log('Result:', result.result);
```

### List Skills

**Using curl:**

```bash
curl http://localhost:8000/skills
```

**Using Python:**

```python
import requests

response = requests.get("http://localhost:8000/skills")
skills = response.json()['skills']

for skill in skills:
    print(f"{skill['name']}: {skill['description']}")
```

### Get Skill Metadata

**Using curl:**

```bash
curl http://localhost:8000/skills/dialogue_generator
```

**Using Python:**

```python
import requests

response = requests.get("http://localhost:8000/skills/dialogue_generator")
metadata = response.json()

print(f"Skill: {metadata['name']}")
print(f"Parameters: {metadata['parameters']}")
```

### Health Check

**Using curl:**

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

**Using Python:**

```python
import requests

live = requests.get("http://localhost:8000/health/live")
ready = requests.get("http://localhost:8000/health/ready")

print(f"Live: {live.status_code == 200}")
print(f"Ready: {ready.status_code == 200}")
```

### Error Handling

**Python example with error handling:**

```python
import requests
from requests.exceptions import HTTPError, RequestException

try:
    response = requests.post(
        "http://localhost:8000/v1/orchestrate",
        json={
            "skill": "dialogue_generator",
            "input": {"scene_context": "A garden"}
        },
        timeout=5.0
    )
    response.raise_for_status()

    result = response.json()

except HTTPError as e:
    print(f"HTTP error: {e.response.status_code}")
    print(f"Error detail: {e.response.text}")

except RequestException as e:
    print(f"Request failed: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

---

*Last Updated: March 2026*
*OpenClaw Orchestrator v0.4.0*

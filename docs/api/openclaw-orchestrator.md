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

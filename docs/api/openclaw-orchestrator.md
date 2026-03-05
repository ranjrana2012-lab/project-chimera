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

### List Skills

```bash
curl http://localhost:8000/skills
```

---

*Last Updated: March 2026*
*OpenClaw Orchestrator v0.4.0*

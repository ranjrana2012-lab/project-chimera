# OpenClaw Orchestrator API

Base URL: `http://openclaw-orchestrator.live.svc.cluster.local:8000`

## Health Endpoints

### GET /health/live
Liveness probe - checks if service is running.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /health/ready
Readiness probe - checks if service can accept traffic.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "cache_connected": true
}
```

## Orchestration Endpoints

### POST /api/v1/orchestration/invoke
Invoke a single skill.

**Request:**
```json
{
  "skill_name": "scenespeak",
  "input": {
    "current_scene": {"title": "Scene 1"},
    "dialogue_context": []
  },
  "timeout_ms": 3000
}
```

**Response:**
```json
{
  "skill_name": "scenespeak",
  "success": true,
  "output": {
    "proposed_lines": "CHARACTER: [Looking around] Hello world.",
    "stage_cues": ["[LIGHTING: Warm blue wash]"]
  },
  "metadata": {...},
  "latency_ms": 450
}
```

## Skills Endpoints

### GET /api/v1/skills
List all available skills.

**Response:**
```json
{
  "skills": [
    {
      "name": "scenespeak",
      "version": "1.0.0",
      "description": "Generates real-time dialogue",
      "enabled": true
    }
  ],
  "total": 7
}
```

### GET /api/v1/skills/{name}
Get metadata for a specific skill.

## Pipelines Endpoints

### POST /api/v1/pipelines/execute
Execute a pipeline of skills.

**Request:**
```json
{
  "steps": [
    {"skill_name": "sentiment", "input_mapping": {}},
    {"skill_name": "scenespeak", "input_mapping": {"sentiment": "sentiment_output"}}
  ],
  "input": {"social_posts": ["Amazing!", "Great!"]},
  "parallel": false
}
```

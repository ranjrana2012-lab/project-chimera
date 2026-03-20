# Z.AI Endpoints API Documentation

## Overview

The Nemo Claw Orchestrator provides administrative endpoints for monitoring and managing the Z.AI integration.

## Endpoints

### GET /llm/zai/status

Get current Z.AI availability and configuration.

**Response:**
```json
{
  "available": true,
  "models": {
    "primary": "glm-5-turbo",
    "programming": "glm-4.7",
    "fast": "glm-4.7-flashx"
  },
  "cache_ttl": 3600,
  "thinking_enabled": true
}
```

### POST /llm/zai/reset

Manually reset the Z.AI credit exhaustion flag. Use this after replenishing credits.

**Response:**
```json
{
  "status": "reset",
  "message": "Z.AI status reset successfully"
}
```

### GET /llm/backends

List all available LLM backends with their status.

**Response:**
```json
{
  "backends": [
    {
      "name": "zai_primary",
      "model": "glm-5-turbo",
      "available": true,
      "description": "GLM-5-Turbo - OpenClaw optimized"
    },
    {
      "name": "zai_programming",
      "model": "glm-4.7",
      "available": true,
      "description": "GLM-4.7 - Programming and reasoning"
    },
    {
      "name": "zai_fast",
      "model": "glm-4.7-flashx",
      "available": true,
      "description": "GLM-4.7-FlashX - Fast simple tasks"
    },
    {
      "name": "nemotron_local",
      "model": "nemotron-8b",
      "available": true,
      "description": "Local DGX Nemotron"
    }
  ]
}
```

## Usage Examples

### Check Z.AI Status

```bash
curl http://localhost:8000/llm/zai/status
```

### Reset Credit Exhaustion Flag

```bash
curl -X POST http://localhost:8000/llm/zai/reset
```

### List All Backends

```bash
curl http://localhost:8000/llm/backends
```

## Credit Exhaustion Flow

1. **Normal Operation**: Z.AI backends report `available: true`
2. **Credit Exhaustion Detected**: System automatically marks Z.AI as unavailable
3. **Automatic Fallback**: Requests route to local Nemotron backend
4. **TTL Expiration**: After 1 hour (default), Z.AI availability is automatically rechecked
5. **Manual Reset**: Use `/llm/zai/reset` to immediately clear the exhaustion flag after replenishing credits

## Configuration

Configure Z.AI settings via environment variables:

- `ZAI_API_KEY`: Your Z.AI API key (required)
- `ZAI_PRIMARY_MODEL`: Primary model (default: `glm-5-turbo`)
- `ZAI_PROGRAMMING_MODEL`: Programming model (default: `glm-4.7`)
- `ZAI_FAST_MODEL`: Fast model (default: `glm-4.7-flashx`)
- `ZAI_CACHE_TTL`: Credit status cache TTL in seconds (default: `3600`)
- `ZAI_THINKING_ENABLED`: Enable thinking parameter (default: `true`)

## Monitoring

Use the `/llm/zai/status` endpoint to monitor:
- Current availability of Z.AI backends
- Configured model names
- Cache TTL settings
- Whether thinking mode is enabled

This is useful for:
- Health checks
- Dashboard displays
- Automated monitoring systems
- Debugging routing issues

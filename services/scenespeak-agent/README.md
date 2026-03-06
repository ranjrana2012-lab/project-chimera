# SceneSpeak Agent

Real-time dialogue generation service using GLM 4.7 API and local LLM fallback for Project Chimera.

## Overview

The SceneSpeak Agent generates theatrical dialogue in real-time based on:
- Scene context and narrative parameters
- Audience sentiment feedback
- Performance state transitions
- Character and plot constraints

Supports both cloud-based GLM API and local model inference.

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - GLM API key (from https://open.bigmodel.cn/)
# - Optional: Local LLM model files

# Local development setup
cd services/scenespeak-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your GLM_API_KEY

# Run service
uvicorn main:app --reload --port 8001
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `scenespeak-agent` | Service identifier |
| `PORT` | `8001` | HTTP server port |
| `GLM_API_KEY` | *required* | GLM 4.7 API key |
| `GLM_API_BASE` | `https://open.bigmodel.cn/api/paas/v4/` | GLM API endpoint |
| `LOCAL_MODEL_PATH` | *optional* | Path to local LLM model |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks GLM API)
- `GET /metrics` - Prometheus metrics

### Dialogue Generation
- `POST /api/v1/generate` - Generate dialogue for scene
- `POST /api/v1/continue` - Continue existing dialogue
- `GET /api/v1/models` - List available models

**Example: Generate dialogue**
```bash
curl -X POST http://localhost:8001/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "scene_context": "A mystical forest clearing at dusk",
    "characters": ["Hero", "Spirit"],
    "sentiment": "hopeful",
    "max_tokens": 500
  }'
```

## Development

### Code Structure
```
scenespeak-agent/
├── main.py              # FastAPI application
├── glm_client.py        # GLM API client
├── local_model.py       # Local LLM fallback
├── dialogue_manager.py  # Dialogue state management
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new dialogue templates in `dialogue_manager.py`
2. Implement model switching logic in `local_model.py`
3. Add API endpoints in `main.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_dialogue.py -v
```

## Troubleshooting

### GLM API Connection Failed
**Symptom:** 401 Unauthorized errors
**Solution:** Verify `GLM_API_KEY` is valid, check account quota

### Model Not Loading
**Symptom:** Local model fails to load
**Solution:** Check `LOCAL_MODEL_PATH`, verify model files exist

### Generation Timeout
**Symptom:** Requests take too long
**Solution:** Reduce `max_tokens`, check network connectivity to GLM API

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

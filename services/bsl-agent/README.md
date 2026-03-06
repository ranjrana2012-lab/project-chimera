# BSL Agent

British Sign Language gloss translation and avatar rendering service for Project Chimera.

## Overview

The BSL Agent provides accessibility for Deaf and hard-of-hearing audiences by:
- Converting English text to BSL gloss notation
- Rendering BSL-signing avatars in real-time
- Supporting facial expressions and body language
- Caching translations for performance

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Avatar model files (optional for development)

# Local development setup
cd services/bsl-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your avatar model path

# Run service
uvicorn main:app --reload --port 8003
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `bsl-agent` | Service identifier |
| `PORT` | `8003` | HTTP server port |
| `AVATAR_MODEL_PATH` | `/models/bsl_avatar` | Avatar model directory |
| `AVATAR_RESOLUTION` | `1920x1080` | Output video resolution |
| `AVATAR_FPS` | `30` | Frames per second |
| `CACHE_TTL` | `86400` | Translation cache TTL (seconds) |
| `ENABLE_FACIAL_EXPRESSIONS` | `true` | Enable facial expressions |
| `ENABLE_BODY_LANGUAGE` | `true` | Enable body language gestures |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks avatar model)
- `GET /metrics` - Prometheus metrics

### Translation
- `POST /api/v1/text-to-gloss` - Convert text to BSL gloss
- `POST /api/v1/gloss-to-pose` - Convert gloss to avatar pose sequence
- `POST /api/v1/render` - Render avatar video from pose sequence
- `GET /api/v1/avatar/frames` - Stream avatar frames via WebSocket

**Example: Text to gloss**
```bash
curl -X POST http://localhost:8003/api/v1/text-to-gloss \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, welcome to the show"}'
```

## Development

### Code Structure
```
bsl-agent/
├── main.py              # FastAPI application
├── gloss_translator.py  # English to BSL gloss conversion
├── avatar_renderer.py   # Avatar rendering engine
├── pose_generator.py    # Gloss to pose sequence
├── cache.py            # Translation cache
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new gloss mappings in `gloss_translator.py`
2. Implement new poses in `pose_generator.py`
3. Enhance rendering in `avatar_renderer.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_gloss.py -v
```

## Troubleshooting

### Avatar Model Not Found
**Symptom:** Ready check fails, model errors
**Solution:** Set correct `AVATAR_MODEL_PATH`, ensure model files exist

### Poor Translation Quality
**Symptom:** Gloss output incorrect
**Solution:** Update gloss dictionary in `gloss_translator.py`, check NMM markers

### Rendering Slow
**Symptom:** High latency on render endpoint
**Solution:** Reduce `AVATAR_RESOLUTION`, lower `AVATAR_FPS`

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

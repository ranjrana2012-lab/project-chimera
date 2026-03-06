# OpenClaw Orchestrator

Central control plane for Project Chimera - coordinates all AI agents and manages the performance state machine.

## Overview

The OpenClaw Orchestrator is the heart of Project Chimera, responsible for:
- Coordinating all 8 AI agents (SceneSpeak, Captioning, BSL, Sentiment, Lighting, Safety, Console)
- Managing the scene state machine (idle → prelude → active → postlude → cleanup)
- Routing events between agents via Kafka
- Providing a unified API for performance control

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Docker (for containerized deployment)
# - Access to Kafka message broker

# Local development setup
cd services/openclaw-orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your agent URLs

# Run service
uvicorn main:app --reload --port 8000
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `openclaw-orchestrator` | Service identifier |
| `PORT` | `8000` | HTTP server port |
| `SCENESPEAK_AGENT_URL` | `http://localhost:8001` | SceneSpeak Agent URL |
| `CAPTIONING_AGENT_URL` | `http://localhost:8002` | Captioning Agent URL |
| `BSL_AGENT_URL` | `http://localhost:8003` | BSL Agent URL |
| `SENTIMENT_AGENT_URL` | `http://localhost:8004` | Sentiment Agent URL |
| `LIGHTING_SOUND_MUSIC_URL` | `http://localhost:8005` | Lighting/Sound/Music URL |
| `SAFETY_FILTER_URL` | `http://localhost:8006` | Safety Filter URL |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry traces endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks all agents)
- `GET /metrics` - Prometheus metrics

### Scene Control
- `POST /api/scene/start` - Start a new scene
- `POST /api/scene/stop` - Stop current scene
- `POST /api/scene/transition` - Trigger state transition
- `GET /api/scene/state` - Get current scene state

### Agent Communication
- `POST /api/agent/send` - Send message to specific agent
- `GET /api/agent/status` - Get status of all agents

**Example: Start a scene**
```bash
curl -X POST http://localhost:8000/api/scene/start \
  -H "Content-Type: application/json" \
  -d '{"scene_id": "scene_001", "duration": 300}'
```

## Development

### Code Structure
```
openclaw-orchestrator/
├── main.py              # FastAPI application
├── orchestrator.py      # Core orchestration logic
├── state_machine.py     # Scene state machine
├── kafka_consumer.py    # Kafka message consumption
├── kafka_producer.py    # Kafka message publishing
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Implement new state in `state_machine.py`
2. Add corresponding API endpoint in `main.py`
3. Update Pydantic models in `models.py`
4. Add tests in `tests/`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_orchestrator.py -v
```

## Troubleshooting

### Agent Not Responding
**Symptom:** Readiness probe fails
**Solution:** Check agent URL in `.env`, ensure agent is running

### Kafka Connection Error
**Symptom:** Unable to publish/subscribe messages
**Solution:** Verify Kafka is running, check `KAFKA_BROKER` in config

### State Machine Stuck
**Symptom:** Scene won't transition to next state
**Solution:** Check logs for validation errors, use `POST /api/scene/transition` to force transition

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

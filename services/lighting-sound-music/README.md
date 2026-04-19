# Lighting-Sound-Music Service

Stage automation service controlling DMX lighting, audio playback, and music generation for Project Chimera.

## Overview

The Lighting-Sound-Music Service manages all stage automation:
- DMX lighting control (scenes, fades, effects)
- Audio playback and mixing
- Music generation integration
- Synchronized playback with <50ms tolerance

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - DMX interface (optional - can run in mock mode)
# - Audio output device

# Local development setup
cd services/lighting-sound-music
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your DMX/audio configuration

# Run service
uvicorn main:app --reload --port 8005
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `lighting-sound-music` | Service identifier |
| `PORT` | `8005` | HTTP server port |
| `DMX_ENABLED` | `true` | Enable DMX control |
| `DMX_UNIVERSE` | `1` | DMX universe number |
| `DMX_INTERFACE` | `placeholder` | DMX interface device |
| `AUDIO_ENABLED` | `true` | Enable audio playback |
| `AUDIO_SAMPLE_RATE` | `44100` | Audio sample rate (Hz) |
| `AUDIO_CHANNELS` | `2` | Audio channels (stereo) |
| `AUDIO_BUFFER_SIZE` | `1024` | Audio buffer size |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `SYNC_TOLERANCE_MS` | `50` | Synchronization tolerance |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks DMX/audio)
- `GET /metrics` - Prometheus metrics

### Lighting Control
- `POST /api/v1/lighting/scene` - Set lighting scene
- `POST /api/v1/lighting/fade` - Fade to scene
- `GET /api/v1/lighting/status` - Get current lighting state

### Audio Control
- `POST /api/v1/audio/play` - Play audio file
- `POST /api/v1/audio/stop` - Stop audio playback
- `POST /api/v1/audio/volume` - Set volume level
- `GET /api/v1/audio/status` - Get audio status

### Synchronization
- `POST /api/v1/sync/start` - Start synchronized playback
- `POST /api/v1/sync/stop` - Stop synchronized playback

**Example: Set lighting scene**
```bash
curl -X POST http://localhost:8005/api/v1/lighting/scene \
  -H "Content-Type: application/json" \
  -d '{
    "scene": "forest_clearing",
    "intensity": 0.8,
    "color_temperature": 4500
  }'
```

## Development

### Code Structure
```
lighting-sound-music/
├── main.py              # FastAPI application
├── dmx_controller.py    # DMX lighting control
├── audio_engine.py      # Audio playback engine
├── sync_manager.py      # Synchronization manager
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Define new lighting scenes in `dmx_controller.py`
2. Implement audio effects in `audio_engine.py`
3. Add sync events in `sync_manager.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_dmx.py -v
```

## Troubleshooting

### DMX Not Connected
**Symptom:** DMX commands fail
**Solution:** Check `DMX_INTERFACE` in `.env`, verify DMX USB adapter connected

### Audio Playback Stutters
**Symptom:** Audio glitching during playback
**Solution:** Increase `AUDIO_BUFFER_SIZE`, check system CPU load

### Sync Drift Detected
**Symptom:** Lighting/audio out of sync
**Solution:** Adjust `SYNC_TOLERANCE_MS`, check network latency to other services

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

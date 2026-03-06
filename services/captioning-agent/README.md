# Captioning Agent

Speech-to-text transcription service using OpenAI's Whisper model for Project Chimera.

## Overview

The Captioning Agent provides real-time and batch audio transcription capabilities using the Whisper model. It supports:

- File-based transcription via REST API
- Real-time streaming via WebSocket
- Multi-language support
- Configurable model sizes (tiny, base, small, medium, large)

## API Endpoints

### Health Checks

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks Whisper model)
- `GET /metrics` - Prometheus metrics

### Transcription

- `POST /v1/transcribe` - Transcribe audio file
  - Accepts: multipart/form-data with audio file
  - Supports: WAV, MP3, OGG, FLAC, M4A
  - Returns: Transcription with segments and timing

### Streaming

- `WebSocket /v1/stream` - Real-time transcription streaming
  - Send: Audio chunks as binary messages
  - Receive: Transcription results as JSON

## Configuration

Environment variables (see `.env.example`):

- `WHISPER_MODEL_SIZE` - Model size (default: base)
- `WHISPER_DEVICE` - cpu or cuda
- `MAX_FILE_SIZE` - Max upload size (default: 25MB)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn main:app --reload --port 8002
```

## Docker

```bash
# Build image
docker build -t captioning-agent:latest .

# Run container
docker run -p 8002:8002 captioning-agent:latest
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Architecture

```
captioning-agent/
├── main.py              # FastAPI application
├── whisper_service.py   # Whisper model wrapper
├── websocket_handler.py # WebSocket streaming
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

## Mock Mode

When Whisper is not installed, the service falls back to mock mode for development and testing.

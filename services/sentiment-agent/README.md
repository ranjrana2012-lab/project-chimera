# Sentiment Agent

Audience sentiment analysis service enhanced with WorldMonitor global intelligence for Project Chimera.

## Overview

The Sentiment Agent analyzes audience feedback to guide performance adaptations:
- Real-time sentiment scoring from text input
- WorldMonitor integration for global context
- WebSocket streaming for live sentiment updates
- Category-based event filtering
- Trend analysis and aggregation

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - DistilBERT model (~250MB, auto-downloaded)

# Local development setup
cd services/sentiment-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env if needed (default: auto-detect cuda/cpu)

# Run service
uvicorn main:app --reload --port 8004
```

### Model Information

The service uses **DistilBERT fine-tuned on SST-2** for sentiment analysis:
- **Model:** `distilbert-base-uncased-finetuned-sst-2-english`
- **Size:** ~250MB
- **Labels:** Negative (0), Positive (1)
- **Auto-downloaded:** On first run or during Docker build
- **Device:** Auto-detects GPU (CUDA) or CPU

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `sentiment-agent` | Service identifier |
| `PORT` | `8004` | HTTP server port |
| `HOST` | `0.0.0.0` | Bind address |
| `USE_ML_MODEL` | `false` | Enable DistilBERT model |
| `MODEL_PATH` | `./models/distilbert` | ML model directory |
| `MODEL_CACHE_DIR` | `./models_cache` | Model cache directory |
| `MAX_TEXT_LENGTH` | `10000` | Max input text length |
| `BATCH_SIZE` | `32` | Batch processing size |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks model if enabled)
- `GET /metrics` - Prometheus metrics

### Sentiment Analysis
- `POST /api/v1/analyze` - Analyze sentiment of text
- `POST /api/v1/batch` - Batch analyze multiple texts
- `GET /api/v1/trends` - Get sentiment trend data
- `WebSocket /v1/stream` - Real-time sentiment streaming

**Example: Analyze sentiment**
```bash
curl -X POST http://localhost:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The audience is loving this performance!"}'
```

**Response:**
```json
{
  "sentiment": "positive",
  "score": 0.87,
  "confidence": 0.92,
  "categories": ["entertainment", "emotion"],
  "worldmonitor_context": {
    "global_events": [],
    "cultural_context": "western"
  }
}
```

## Development

### Code Structure
```
sentiment-agent/
├── main.py              # FastAPI application
├── sentiment_analyzer.py # Sentiment analysis engine
├── ml_model.py          # DistilBERT model wrapper
├── worldmonitor.py      # WorldMonitor integration
├── websocket_handler.py # WebSocket streaming
├── cache.py            # Result caching
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new sentiment categories in `sentiment_analyzer.py`
2. Implement new WorldMonitor filters in `worldmonitor.py`
3. Enhance ML model in `ml_model.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_sentiment.py -v
```

## Troubleshooting

### Model Download Failed
**Symptom:** Service fails to start with model import error
**Solution:** Ensure internet connectivity for first run, or build Docker image with network access

### CUDA Out of Memory
**Symptom:** Service crashes with CUDA OOM error
**Solution:** Set `DEVICE=cpu` in .env to use CPU instead

### Slow Inference
**Symptom:** Analysis takes >1 second per request
**Solution:** Ensure GPU is being used (check logs for device detection)

### WorldMonitor Connection Failed
**Symptom:** No global context in response
**Solution:** Check WorldMonitor API credentials, verify network connectivity

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

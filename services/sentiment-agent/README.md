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

The service uses **BETTAfish and MIROFISH models** for comprehensive sentiment and emotion analysis:

#### BETTAfish - Sentiment Classification
- **Model:** `bettafish/sentiment-classifier`
- **Purpose:** Primary sentiment classification (positive/negative/neutral)
- **Labels:** Negative (0), Neutral (1), Positive (2)
- **Size:** ~250MB
- **Auto-downloaded:** On first run or during Docker build
- **Device:** Auto-detects GPU (CUDA) or CPU

#### MIROFISH - Emotion Detection
- **Model:** `mirofish/emotion-detector`
- **Purpose:** Fine-grained emotion detection (joy, sadness, anger, surprise, fear, disgust)
- **Labels:** 6 basic emotions + confidence scores
- **Size:** ~300MB
- **Auto-downloaded:** On first run or during Docker build
- **Device:** Auto-detects GPU (CUDA) or CPU
- **Features:** Returns emotion probabilities for all 6 emotions

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `sentiment-agent` | Service identifier |
| `PORT` | `8004` | HTTP server port |
| `HOST` | `0.0.0.0` | Bind address |
| `USE_ML_MODEL` | `true` | Enable BETTAfish/MIROFISH models |
| `SENTIMENT_MODEL_TYPE` | `bettafish` | Sentiment model (bettafish/mirofish) |
| `SENTIMENT_MODEL_PATH` | `./models/bettafish` | Sentiment model directory |
| `EMOTION_MODEL_TYPE` | `mirofish` | Emotion model (mirofish) |
| `EMOTION_MODEL_PATH` | `./models/mirofish` | Emotion model directory |
| `MODEL_CACHE_DIR` | `./models_cache` | Model cache directory |
| `MAX_TEXT_LENGTH` | `10000` | Max input text length |
| `BATCH_SIZE` | `32` | Batch processing size |
| `DEVICE` | `auto` | Computing device (auto/cuda/cpu) |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

### BETTAfish/MIROFISH Configuration

**BETTAfish Sentiment Model:**
- Optimized for real-time sentiment analysis
- Response time target: <200ms
- Confidence threshold: 0.7

**MIROFISH Emotion Model:**
- Returns 6 emotion probabilities: joy, sadness, anger, surprise, fear, disgust
- Enables nuanced sentiment understanding
- Response time target: <300ms

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
├── bettafish_model.py  # BETTAfish sentiment classifier wrapper
├── mirofish_model.py   # MIROFISH emotion detector wrapper
├── ml_model.py          # Legacy ML model wrapper (DistilBERT)
├── worldmonitor.py      # WorldMonitor integration
├── websocket_handler.py # WebSocket streaming
├── cache.py            # Result caching
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Model Files
```
models/
├── bettafish/          # BETTAfish sentiment model
│   └── sentiment-classifier/
├── mirofish/           # MIROFISH emotion model
│   └── emotion-detector/
└── distilbert/         # Legacy DistilBERT model (deprecated)
```

### Adding Features
1. Add new sentiment categories in `sentiment_analyzer.py`
2. Implement new WorldMonitor filters in `worldmonitor.py`
3. Enhance ML models in `bettafish_model.py` or `mirofish_model.py`

### BETTAfish vs MIROFISH

**BETTAfish (Sentiment Classification):**
- Use for: Quick positive/negative/neutral classification
- Response time: <200ms
- Best for: Real-time sentiment monitoring, high-volume processing
- Output: Single sentiment label with confidence score

**MIROFISH (Emotion Detection):**
- Use for: Detailed emotion analysis
- Response time: <300ms
- Best for: Understanding audience emotional state, nuanced feedback
- Output: 6 emotion probabilities (joy, sadness, anger, surprise, fear, disgust)

**Combined Usage:**
```python
# Quick sentiment check
sentiment = bettafish_model.classify(text)

# Detailed emotion analysis
emotions = mirofish_model.analyze_emotions(text)

# Combined response
{
    "sentiment": "positive",
    "confidence": 0.89,
    "emotions": {
        "joy": 0.72,
        "surprise": 0.15,
        "neutral": 0.13
    }
}
```

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

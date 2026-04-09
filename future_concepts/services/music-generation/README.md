# Music Generation Service

AI-powered music generation service for Project Chimera using MusicGen and ACE-Step models.

## Overview

The Music Generation Service creates original music content from text prompts:
- Text-to-music generation using MusicGen model
- Multi-model support (MusicGen, ACE-Step)
- Audio processing with normalization and silence trimming
- Model pool management for efficient GPU resource usage
- Async inference engine for non-blocking generation

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - CUDA-capable GPU (recommended: Nvidia GB10 with 8GB+ VRAM)
# - ~20GB disk space for models

# Local development setup
cd services/music-generation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env to configure model paths and settings

# Run service (without GPU for testing)
export DEVICE=cpu
uvicorn main:app --reload --port 8011

# Run service (with GPU)
uvicorn main:app --reload --port 8011
```

## Configuration

Environment variables (see `.env.example`):

### Service Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `music-generation` | Service identifier |
| `PORT` | `8011` | HTTP server port |
| `HOST` | `0.0.0.0` | Bind address |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | `development` | Environment name |

### Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MUSICGEN_MODEL_PATH` | `/models/musicgen` | MusicGen model directory |
| `ACESTEP_MODEL_PATH` | `/models/acestep` | ACE-Step model directory |
| `HUGGINGFACE_CACHE_DIR` | `/models/cache` | HuggingFace cache location |
| `DEFAULT_MODEL` | `musicgen` | Default model to use |
| `MAX_VRAM_MB` | `8192` | Maximum VRAM to use (MB) |
| `MODEL_OFFLOAD` | `true` | Offload models to CPU when idle |

### Generation Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_DURATION` | `5.0` | Default generation duration (seconds) |
| `MAX_DURATION` | `30.0` | Maximum generation duration (seconds) |
| `SAMPLE_RATE` | `44100` | Audio sample rate (Hz) |
| `NORMALIZE_DB` | `-1.0` | Normalization target level (dB) |
| `TRIM_SILENCE` | `true` | Trim silence from generated audio |

### GPU Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE` | `cuda` | Device to use (cuda/cpu) |
| `TORCH_THREADS` | `4` | Number of PyTorch threads |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

### Model Management
- `GET /api/v1/models` - List available models
- `GET /api/v1/models/{model}` - Get model info
- `POST /api/v1/models/load` - Load a model
- `POST /api/v1/models/unload` - Unload a model

### Music Generation
- `POST /api/v1/generate` - Generate music from prompt

**Example: Generate music**
```bash
curl -X POST http://localhost:8011/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Upbeat electronic dance music with synths",
    "model": "musicgen",
    "duration": 10.0,
    "sample_rate": 44100
  }'
```

**Response:**
```json
{
  "success": true,
  "audio_url": "/audio/generated_123456.wav",
  "duration": 10.0,
  "sample_rate": 44100,
  "format": "wav",
  "model": "musicgen",
  "generation_time": 4.2,
  "file_size": 882000
}
```

## Development

### Code Structure
```
music-generation/
├── main.py              # FastAPI application
├── config.py            # Configuration with pydantic-settings
├── models.py            # Pydantic models
├── audio.py             # Audio processing utilities
├── model_pool.py        # Model pool manager
├── inference.py         # Inference engine
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── Dockerfile           # ARM64 Docker image
├── manifests/
│   └── k8s.yaml         # Kubernetes deployment
└── tests/               # Test suite
    └── test_music_generation.py
```

### Architecture

#### Audio Processor
Handles audio post-processing:
- **Normalization**: Adjusts audio to target dB level
- **Silence trimming**: Removes silence from start/end
- **WAV conversion**: Converts numpy arrays to WAV format

#### Model Pool
Manages model lifecycle:
- Lazy loading of models
- VRAM estimation
- Model unloading to free memory
- Thread-safe access with locks

#### Inference Engine
Async music generation:
- Non-blocking generation
- Progress callbacks
- Cancellation support
- Timeout handling

### Adding Features

#### Add a New Model

1. Update `models.py`:
```python
class ModelName(str, Enum):
    MUSICGEN = "musicgen"
    ACESTEP = "acestep"
    YOUR_MODEL = "your-model"
```

2. Update `model_pool.py` to handle the new model

3. Update `inference.py` for model-specific generation logic

#### Add Audio Effects

Add new processing methods to `audio.py`:
```python
def apply_reverb(self, audio: np.ndarray) -> np.ndarray:
    # Implement reverb effect
    pass
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_music_generation.py::TestAudioProcessor -v

# Run tests without GPU
export DEVICE=cpu
pytest tests/
```

### Test Coverage

The test suite covers:
- AudioProcessor: normalization, trimming, WAV conversion
- ModelPool: initialization, VRAM estimation, model loading
- GenerationRequest: validation, defaults, edge cases
- InferenceEngine: VRAM estimation, generation flow
- Integration tests: end-to-end workflows

## Troubleshooting

### Model Not Loading

**Symptom:** Ready check fails, 503 errors

**Solutions:**
- Check model paths in configuration
- Verify model files exist
- Ensure sufficient VRAM (check `MAX_VRAM_MB`)
- Check CUDA availability with `torch.cuda.is_available()`

### Generation Timeout

**Symptom:** Requests take too long or time out

**Solutions:**
- Reduce `MAX_DURATION`
- Decrease generation complexity in prompt
- Use CPU for testing (`DEVICE=cpu`)
- Check GPU memory usage

### Out of Memory

**Symptom:** CUDA out of memory errors

**Solutions:**
- Enable `MODEL_OFFLOAD=true`
- Reduce `MAX_VRAM_MB`
- Generate shorter durations
- Unload unused models

### Poor Audio Quality

**Symptom:** Generated audio sounds distorted or quiet

**Solutions:**
- Adjust `NORMALIZE_DB` target
- Enable `TRIM_SILENCE=true`
- Try different prompts
- Switch between models

## Model Details

### MusicGen (facebook/musicgen-small)
- **Size**: ~3GB
- **VRAM**: ~4GB
- **Quality**: Good for most use cases
- **Speed**: Fast generation

### ACE-Step
- **Size**: ~2GB
- **VRAM**: ~2GB
- **Quality**: Specialized for step-based composition
- **Speed**: Variable

## Performance

### Typical Generation Times

| Duration | MusicGen | ACE-Step |
|----------|----------|----------|
| 5s | ~2s | ~1.5s |
| 10s | ~4s | ~3s |
| 30s | ~12s | ~10s |

### Resource Usage

- **Idle**: ~500MB VRAM (with offloading)
- **Generating**: 4-8GB VRAM depending on model
- **CPU**: 2-8 cores during generation

## Deployment

### Docker

```bash
# Build image
docker build -t music-generation:latest .

# Run with GPU
docker run --gpus all -p 8011:8011 \
  -v /path/to/models:/models \
  -e DEVICE=cuda \
  music-generation:latest

# Run without GPU
docker run -p 8011:8011 \
  -e DEVICE=cpu \
  music-generation:latest
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f manifests/k8s.yaml

# Check status
kubectl get pods -l app=music-generation -n project-chimera

# View logs
kubectl logs -f deployment/music-generation -n project-chimera
```

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

# SceneSpeak Agent

Real-time dialogue generation service using GLM 4.7 API and local LLM (Ollama) fallback for Project Chimera.

## Overview

The SceneSpeak Agent generates theatrical dialogue in real-time based on:
- Scene context and narrative parameters
- Audience sentiment feedback
- Performance state transitions
- Character and plot constraints

Supports both cloud-based GLM API and local model inference via Ollama with automatic fallback.

## Quick Start

### Option 1: Using GLM API (Cloud)

```bash
# Prerequisites
# - Python 3.10+
# - GLM API key (from https://open.bigmodel.cn/)

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

### Option 2: Using Local LLM (Ollama)

```bash
# Prerequisites
# - Python 3.10+
# - Ollama installed (see below)
# - Local LLM model downloaded

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull ARM64-compatible model (for GB10 GPU)
ollama pull llama3.2
# Or use Mistral 7B (quantized for 8GB VRAM)
ollama pull mistral:7b-q4_K_M

# Start Ollama service
ollama serve

# In another terminal, start SceneSpeak agent
cd services/scenespeak-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure local LLM in .env
echo "LOCAL_LLM_ENABLED=true" >> .env
echo "LOCAL_LLM_URL=http://localhost:11434" >> .env
echo "LOCAL_LLM_MODEL=llama3.2" >> .env

# Run service
uvicorn main:app --reload --port 8001
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `scenespeak-agent` | Service identifier |
| `PORT` | `8001` | HTTP server port |
| `GLM_API_KEY` | *optional* | GLM 4.7 API key |
| `GLM_API_BASE` | `https://open.bigmodel.cn/api/paas/v4/` | GLM API endpoint |
| `LOCAL_LLM_ENABLED` | `true` | Enable local LLM via Ollama |
| `LOCAL_LLM_URL` | `http://localhost:11434` | Ollama API endpoint |
| `LOCAL_LLM_MODEL` | `llama3.2` | Model to use for local inference |
| `GLM_API_FALLBACK` | `true` | Use GLM API if local LLM fails |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

### Priority Order

1. If `LOCAL_LLM_ENABLED=true` and Ollama is available, use local LLM
2. If local LLM fails and `GLM_API_FALLBACK=true`, try GLM API
3. If GLM API key is configured, use GLM API
4. Raise error if no option is available

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks local LLM and GLM API)
- `GET /health/local-llm` - Detailed local LLM health status
- `GET /metrics` - Prometheus metrics

### Dialogue Generation
- `POST /v1/generate` - Generate dialogue for scene (primary endpoint)
- `POST /v1/generate/legacy` - Legacy endpoint for backward compatibility

**Example: Generate dialogue**
```bash
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A mystical forest clearing at dusk. The Hero encounters a Spirit.",
    "max_tokens": 500,
    "temperature": 0.7,
    "context": {
      "show_id": "demo_show",
      "scene_number": 1,
      "adapter": "default"
    }
  }'
```

**Example: Check local LLM health**
```bash
curl http://localhost:8001/health/local-llm
```

Response:
```json
{
  "connected": true,
  "status": "healthy",
  "base_url": "http://localhost:11434",
  "model": "llama3.2",
  "available_models": ["llama3.2", "mistral:7b"]
}
```

## Development

### Code Structure
```
scenespeak-agent/
├── main.py              # FastAPI application
├── glm_client.py        # GLM API client with fallback
├── local_llm.py         # Local LLM (Ollama) integration
├── config.py           # Configuration management
├── models.py           # Pydantic request/response models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
├── lora_adapter.py     # LoRA adapter for fine-tuned models
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image
└── tests/              # Test suite
    ├── test_local_llm.py    # Local LLM tests
    ├── test_glm_client.py   # GLM client tests
    ├── test_main.py         # Main app tests
    └── ...
```

### ARM64 GB10 GPU Optimization

For optimal performance on ARM64 systems with GB10 GPU (8GB VRAM):

**Recommended Models:**
- `llama3.2` - Lightweight, fast inference
- `mistral:7b-q4_K_M` - Balanced quality/speed with quantization
- `gemma:2b` - Smallest option, fastest inference

**Installation:**
```bash
# Install Ollama with ARM64 support
curl -fsSL https://ollama.com/install.sh | sh

# Pull quantized model for 8GB VRAM
ollama pull mistral:7b-q4_K_M

# Verify GPU acceleration
ollama run mistral:7b-q4_K_M "Hello, test prompt"
```

**Performance Tips:**
- Use Q4_K_M quantization for best quality/size ratio
- Set `max_tokens` to 500 or less for real-time performance
- Enable CUDA 13.0 in Ollama for GPU acceleration

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

### Local LLM Issues

**Ollama Connection Failed**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama if not running
ollama serve

# Verify Ollama is listening
curl http://localhost:11434/api/tags
```

**Model Not Available**
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.2

# Test model directly
ollama run llama3.2 "Test prompt"
```

**GPU Not Being Used**
```bash
# Check Ollama GPU support
ollama --version

# Verify CUDA is available
nvidia-smi

# Force GPU usage
export CUDA_VISIBLE_DEVICES=0
ollama serve
```

### GLM API Issues

**GLM API Connection Failed**
**Symptom:** 401 Unauthorized errors
**Solution:** Verify `GLM_API_KEY` is valid, check account quota

**Fallback Not Working**
**Symptom:** GLM API fails but doesn't fall back to local
**Solution:**
- Ensure `GLM_API_FALLBACK=true` in .env
- Verify `LOCAL_LLM_ENABLED=true`
- Check local LLM health at `/health/local-llm`

### Performance Issues

**Generation Timeout**
**Symptom:** Requests take too long
**Solutions:**
- Reduce `max_tokens` to 500 or less
- Use quantized model (e.g., `mistral:7b-q4_K_M`)
- Check GPU utilization with `nvidia-smi`
- Verify Ollama is using GPU acceleration

**Slow Inference**
**Symptom:** Generation takes >10 seconds
**Solutions:**
- Switch to smaller model (`gemma:2b`)
- Enable GPU acceleration
- Check system resources with `htop`

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

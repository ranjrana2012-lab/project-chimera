# Music Generation API Documentation

**Version:** v0.5.0
**Base URL:** `http://localhost:8011`
**Service:** AI-powered music generation using MusicGen and ACE-Step models

---

## Endpoints

### 1. List Available Models

Get list of available music generation models.

**Endpoint:** `GET /api/v1/models`

**Response:**

```json
{
  "models": [
    {
      "name": "musicgen",
      "loaded": true,
      "vram_mb": 4096,
      "sample_rate": 32000,
      "description": "Facebook MusicGen small model for text-to-music generation"
    },
    {
      "name": "acestep",
      "loaded": false,
      "vram_mb": 2048,
      "sample_rate": 44100,
      "description": "ACE-Step model for step-based music composition"
    }
  ]
}
```

---

### 2. Get Model Information

Get detailed information about a specific model.

**Endpoint:** `GET /api/v1/models/{model}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name: `musicgen` or `acestep` |

**Example:**

```bash
curl http://localhost:8011/api/v1/models/musicgen
```

**Response:**

```json
{
  "name": "musicgen",
  "loaded": true,
  "vram_mb": 4096,
  "sample_rate": 32000,
  "description": "Facebook MusicGen small model for text-to-music generation"
}
```

---

### 3. Load Model

Load a model into memory for faster generation.

**Endpoint:** `POST /api/v1/models/load`

**Request Body:**

```json
{
  "model": "musicgen"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Model musicgen loaded successfully",
  "vram_mb": 4096
}
```

---

### 4. Unload Model

Unload a model from memory to free VRAM.

**Endpoint:** `POST /api/v1/models/unload`

**Request Body:**

```json
{
  "model": "musicgen"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Model musicgen unloaded successfully",
  "freed_mb": 4096
}
```

---

### 5. Generate Music

Generate music from a text prompt.

**Endpoint:** `POST /api/v1/generate`

**Request Body:**

```json
{
  "prompt": "Upbeat electronic dance music with synths and drum beat",
  "model": "musicgen",
  "duration": 10.0,
  "sample_rate": 44100
}
```

**Request Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | Text description of music to generate (1-500 chars) |
| `model` | string | No | `musicgen` | Model to use: `musicgen` or `acestep` |
| `duration` | float | No | `5.0` | Duration in seconds (1.0-30.0) |
| `sample_rate` | int | No | `44100` | Sample rate in Hz (16000-48000) |

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

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether generation succeeded |
| `audio_url` | string | URL to download generated audio |
| `duration` | float | Actual duration in seconds |
| `sample_rate` | int | Audio sample rate |
| `format` | string | Audio format (always `wav`) |
| `model` | string | Model used for generation |
| `generation_time` | float | Time taken to generate (seconds) |
| `file_size` | int | File size in bytes |
| `error` | string | Error message (if `success=false`) |

**Example:**

```bash
curl -X POST http://localhost:8011/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cinematic orchestral music with dramatic strings",
    "duration": 15.0
  }'
```

---

### 6. Download Generated Audio

Download a previously generated audio file.

**Endpoint:** `GET /audio/{filename}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | string | Generated audio filename |

**Example:**

```bash
curl -O http://localhost:8011/audio/generated_123456.wav
```

---

### 7. Health Check - Liveness

Check if the service is running.

**Endpoint:** `GET /health/live`

**Response:**

```json
{
  "status": "alive"
}
```

---

### 8. Health Check - Readiness

Check if the service is ready to handle requests.

**Endpoint:** `GET /health/ready`

**Response:**

```json
{
  "status": "ready"
}
```

---

### 9. Metrics

Get Prometheus metrics for monitoring.

**Endpoint:** `GET /metrics`

**Response Type:** `text/plain`

**Example Metrics:**

```
# HELP music_generation_requests_total Total number of generation requests
# TYPE music_generation_requests_total counter
music_generation_requests_total{model="musicgen",status="success"} 123
music_generation_requests_total{model="acestep",status="success"} 45
music_generation_requests_total{model="musicgen",status="error"} 2

# HELP music_generation_model_load_seconds Time taken to load models
# TYPE music_generation_model_load_seconds gauge
music_generation_model_load_seconds{model="musicgen"} 3.45
music_generation_model_load_seconds{model="acestep"} 2.10

# HELP music_generation_active Number of active generation tasks
# TYPE music_generation_active gauge
music_generation_active 2
```

---

## Configuration

The Music Generation Service uses environment-based configuration with pydantic-settings.

### Service Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `music-generation` | Service identifier |
| `PORT` | integer | `8011` | HTTP server port |
| `HOST` | string | `0.0.0.0` | Server bind address |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Model Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MUSICGEN_MODEL_PATH` | string | `/models/musicgen` | MusicGen model directory |
| `ACESTEP_MODEL_PATH` | string | `/models/acestep` | ACE-Step model directory |
| `HUGGINGFACE_CACHE_DIR` | string | `/models/cache` | HuggingFace cache |
| `DEFAULT_MODEL` | string | `musicgen` | Default model |
| `MAX_VRAM_MB` | integer | `8192` | Maximum VRAM to use |
| `MODEL_OFFLOAD` | boolean | `true` | Offload to CPU when idle |

### Generation Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEFAULT_DURATION` | float | `5.0` | Default duration (seconds) |
| `MAX_DURATION` | float | `30.0` | Maximum duration (seconds) |
| `SAMPLE_RATE` | integer | `44100` | Audio sample rate (Hz) |
| `NORMALIZE_DB` | float | `-1.0` | Normalization target (dB) |
| `TRIM_SILENCE` | boolean | `true` | Trim silence from audio |

### GPU Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEVICE` | string | `cuda` | Device (cuda/cpu) |
| `TORCH_THREADS` | integer | `4` | PyTorch threads |

## Metrics

The Music Generation Service exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `music_generation_requests_total` | Counter | model, status | Total generation requests |
| `music_generation_model_load_seconds` | Gauge | model | Model load time |
| `music_generation_active` | Gauge | - | Active generation tasks |
| `music_generation_duration_seconds` | Histogram | model | Generation duration |
| `music_generation_audio_size_bytes` | Histogram | model | Generated audio size |

### System Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `music_generation_vram_used_mb` | Gauge | model | VRAM usage |
| `music_generation_model_loaded` | Gauge | model | Model loaded status |

## Model Comparison

### MusicGen (facebook/musicgen-small)

| Attribute | Value |
|-----------|-------|
| Size | ~3GB |
| VRAM | ~4GB |
| Sample Rate | 32000 Hz |
| Quality | Good for most use cases |
| Speed | Fast |
| Best For | General music generation |

### ACE-Step

| Attribute | Value |
|-----------|-------|
| Size | ~2GB |
| VRAM | ~2GB |
| Sample Rate | 44100 Hz |
| Quality | Specialized |
| Speed | Variable |
| Best For | Step-based composition |

## Error Handling

The service returns standard HTTP status codes:

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Not found (model or audio file) |
| 500 | Internal server error |
| 503 | Service unavailable (model not loaded) |

**Error Response Format:**

```json
{
  "error": {
    "message": "Prompt cannot be empty",
    "code": "INVALID_PROMPT"
  }
}
```

## Rate Limiting

Current limits:
- Max duration: 30 seconds
- Max prompt length: 500 characters
- Concurrent generations: Limited by available VRAM

## Examples

### Generate Short Music Clip

```bash
curl -X POST http://localhost:8011/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Lo-fi hip hop beat",
    "duration": 5.0
  }'
```

### Generate with ACE-Step Model

```bash
curl -X POST http://localhost:8011/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Ambient electronic pads",
    "model": "acestep",
    "duration": 20.0
  }'
```

### Check Service Health

```bash
curl http://localhost:8011/health/ready
```

### List Models

```bash
curl http://localhost:8011/api/v1/models
```

## Tracing

The Music Generation Service uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)

---

*Last Updated: March 2026*
*Music Generation Service v0.5.0*

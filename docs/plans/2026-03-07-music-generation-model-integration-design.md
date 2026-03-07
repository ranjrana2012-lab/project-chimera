# Music Generation Model Integration Design

**Date:** March 7, 2026
**Status:** Design Approved
**Goal:** Build music generation service with MusicGen and ACE-Step model integration on ARM64 GB10 GPU

---

## Overview

Build a focused music generation service that integrates both MusicGen and ACE-Step models on the Nvidia GB10 ARM64 GPU. This phase prioritizes getting both AI models working correctly before adding orchestration, caching, and approval workflow features.

**Priority Order:** C (Music Generation) → D (Sentiment ML) → B (SceneSpeak Local LLM) → A (BSL Avatar - later)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Music Generation Service                   │
│                   Port: 8011                                │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │   Model    │  │  Inference  │  │   Audio          │     │
│  │   Pool     │──│  Engine     │──│   Processor     │     │
│  │            │  │  (ARM64)    │  │                  │     │
│  └────────────┘  └─────────────┘  └──────────────────┘     │
│       ↓                 ↓                                      │
│  MusicGen          PyTorch         Normalization             │
│  ACE-Step          CUDA 13         Silence Trim             │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- Single service first - orchestration service comes later
- Model pool with both MusicGen (large, high quality) and ACE-Step (smaller, faster)
- ARM64-optimized PyTorch builds for GB10 GPU
- CUDA 13.0 support
- Async generation with cancellation
- Mixed deployment: local development + K3s Kubernetes

---

## Components

### 1. Model Pool Manager (`model_pool.py`)
- Loads/unloads models based on VRAM availability
- Switches between MusicGen and ACE-Step
- Lazy loading (only load when first request comes)
- VRAM estimation and tracking
- ARM64-specific model paths

### 2. Inference Engine (`inference.py`)
- Async generation with cancellation support
- Batch processing for efficiency
- Progress callbacks for streaming
- CUDA 13.0 optimized for GB10
- Model-specific parameter handling

### 3. Audio Processor (`audio.py`)
- Normalize audio output (-1dB target)
- Trim silence from start/end
- Format conversion (raw → WAV)
- Sample rate adjustment (44.1kHz standard)
- Audio quality validation

### 4. FastAPI Service (`main.py`)
- `POST /generate` - Generate music from text prompt
- `GET /health/live` - Health check
- `GET /health/ready` - Readiness check (models loaded)
- `GET /models` - List available models
- `GET /metrics` - Prometheus metrics
- WebSocket support for progress streaming (optional)

### 5. Configuration (`config.py`, `.env.example`)
- Model paths (MusicGen, ACE-Step)
- Generation parameters (duration, sample rate, etc.)
- GPU settings (memory limits, device selection)
- Server settings (port, workers, timeouts)

### 6. Supporting Components
- `models.py` - Pydantic models for API validation
- `metrics.py` - Prometheus metrics integration
- `tracing.py` - OpenTelemetry tracing

---

## Data Flow

```
┌──────────────┐
│ Client Request│
│ (Prompt,     │
│  Duration,   │
│  Model)      │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  POST /generate                                              │
│  • Validate prompt                                          │
│  • Select model (MusicGen or ACE-Step)                      │
│  • Check VRAM availability                                   │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Model Pool Manager                                          │
│  • Load model if not in memory                               │
│  • Switch models if VRAM insufficient                        │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Inference Engine (PyTorch + CUDA 13)                        │
│  • Generate audio from prompt                                │
│  • Stream progress via callback                               │
│  • Support cancellation                                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Audio Processor                                             │
│  • Normalize to -1dB                                          │
│  • Trim silence                                              │
│  • Convert to WAV                                            │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Response     │
│ (WAV file,   │
│  metadata)   │
└──────────────┘
```

---

## Error Handling

### Model Loading Failures
- **Model file not found** → Return 404 with download instructions
- **Insufficient VRAM** → Fall back to smaller model (ACE-Step) or return error
- **CUDA errors** → Log GPU state, return 503 with retry-after

### Generation Failures
- **Invalid prompt** → Return 400 with validation error
- **Timeout** → Cancel generation, return 408 with partial result if available
- **Out of memory during generation** → Unload model, return 503, retry with smaller model

### Audio Processing Failures
- **Truncation errors** → Log and return raw audio
- **Format conversion failure** → Return 500 with error details

### GPU/Driver Issues
- **GPU not accessible** → Return 503 with "GPU unavailable" message
- **CUDA version mismatch** → Return 500 with driver version info

### Error Response Format
```json
{
  "error": {
    "code": "INSUFFICIENT_VRAM",
    "message": "Not enough GPU memory. Try ACE-Step model or reduce duration.",
    "details": {
      "required_mb": 8192,
      "available_mb": 4096,
      "suggested_model": "ace-step"
    }
  }
}
```

---

## Testing Strategy

### Unit Tests (`tests/test_music_generation.py`)
- Model pool loading/unloading
- Audio processing (normalize, trim)
- Configuration parsing
- Error handling
- VRAM estimation (mocked)

### Integration Tests (`tests/test_integration.py`)
- End-to-end generation with mock models
- Model switching behavior
- Progress callbacks
- API endpoint validation

### Model Tests (`tests/test_models.py`)
- Verify MusicGen loads and generates (marked as slow, optional)
- Verify ACE-Step loads and generates (marked as slow, optional)
- Model fallback behavior
- ARM64 compatibility verification

### Test Requirements
- Mock audio output for fast CI tests
- Mock VRAM to avoid GPU requirements for CI
- Real model tests marked as "slow" and optional
- Coverage target: 80%

---

## Implementation Approach

### Phase 1: Foundation (Model Integration Focus)
- Set up project structure and dependencies
- Implement model pool manager (ARM64 PyTorch)
- Basic FastAPI service with health endpoint
- Configuration and environment setup

### Phase 2: Model Integration
- Integrate MusicGen model (test with small prompt)
- Integrate ACE-Step model
- Implement inference engine with async support
- Test both models generate audio on GB10 GPU

### Phase 3: Audio & API
- Audio processing (normalize, trim, format conversion)
- Complete `/generate` endpoint with all parameters
- Progress streaming callbacks
- Error handling and validation

### Phase 4: Docker & Deployment
- Multi-stage Dockerfile (ARM64)
- K3s deployment manifests
- Service registration with other Chimera services
- Documentation updates

---

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Language** | Python 3.12+ | ARM64 compatible |
| **Framework** | FastAPI | Async support |
| **ML Framework** | PyTorch 2.5+ | CUDA 13.0, ARM64 build |
| **Models** | MusicGen, ACE-Step | From HuggingFace |
| **Audio** | librosa, soundfile | Processing |
| **Container** | Docker | Multi-stage ARM64 |
| **Orchestration** | K3s | GPU node scheduling |

---

## System Specifications

**Target Platform:**
- **Architecture:** ARM64 (aarch64)
- **GPU:** NVIDIA GB10
- **CUDA:** Version 13.0
- **Driver:** 580.126.09

**Development Environment:**
- Local development with GPU access
- K3s Kubernetes pods with GPU support
- Mixed deployment approach

---

## Files to Create

### Core Service (10 files)
1. `services/music-generation/main.py` - FastAPI application
2. `services/music-generation/model_pool.py` - Model loading/unloading
3. `services/music-generation/inference.py` - Generation engine
4. `services/music-generation/audio.py` - Audio processing
5. `services/music-generation/config.py` - Configuration
6. `services/music-generation/models.py` - Pydantic models
7. `services/music-generation/metrics.py` - Prometheus metrics
8. `services/music-generation/tracing.py` - OpenTelemetry setup
9. `services/music-generation/requirements.txt` - Dependencies
10. `services/music-generation/Dockerfile` - ARM64 build

### Configuration & Testing (4 files)
11. `services/music-generation/.env.example` - Configuration template
12. `services/music-generation/tests/test_music_generation.py` - Unit tests
13. `services/music-generation/tests/test_integration.py` - Integration tests
14. `services/music-generation/tests/__init__.py` - Test package

### Documentation (3 files)
15. `services/music-generation/README.md` - Service documentation
16. `docs/api/music-generation.md` - API reference
17. `docs/plans/2026-03-07-music-generation-implementation.md` - Implementation plan

---

## Success Criteria

- [ ] Design document written (THIS)
- [ ] Design approved by user ✅
- [ ] Implementation plan created
- [ ] MusicGen model loads and generates audio
- [ ] ACE-Step model loads and generates audio
- [ ] Model pool switching works correctly
- [ ] `/generate` endpoint functional
- [ ] Audio processing works (normalize, trim, convert)
- [ ] Docker build succeeds for ARM64
- [ ] Service runs on K3s with GPU access
- [ ] Tests passing (80% coverage)
- [ ] Documentation complete
- [ ] Integration with other Chimera services

---

## Future Phases (Out of Scope)

After model integration is complete:
- **Music Orchestration Service** - Caching, approval workflow, JWT auth
- **MinIO Storage** - Persistent audio storage
- **PostgreSQL** - Request tracking and history
- **WebSocket Progress** - Real-time generation updates
- **Service Integration** - Called by OpenClaw Orchestrator

---

*Design Document - Project Chimera v0.5.0 - March 7, 2026*

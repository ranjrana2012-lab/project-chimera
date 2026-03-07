# Music Generation Platform

**Note:** The Music Generation Platform has been integrated into the unified **Lighting, Sound & Music (LSM)** service on port 8005.

See: [Lighting, Sound & Music Documentation](lighting-sound-music.md)

## Overview

The Music Generation functionality enables on-demand music generation using local AI models:

- **ACE-Step-1.5** - Advanced AI music generation model (<4GB VRAM)
  - base: Full model for highest quality
  - sft: Fine-tuned variant
  - turbo: Fast generation
  - mlx: MLX-optimized for Apple Silicon

## Current Architecture

The music generation functionality is now part of the **Lighting, Sound & Music** service:

```bash
# Access via the LSM service
curl http://localhost:8005/music/models
curl http://localhost:8005/music/generate
```

## Features

### Music Generation (Port 8005)

**Endpoints:**
- `GET /music/models` - List available ACE-Step-1.5 models
- `POST /music/generate` - Generate music with AI
- `GET /music/generate/{request_id}` - Check generation status
- `POST /music/play` - Play a track
- `POST /music/stop` - Stop playback
- `GET /music/tracks` - List all tracks
- `GET /music/tracks/{id}` - Get track info
- `DELETE /music/tracks/{id}` - Delete a track
- `WebSocket /music/ws/generate/{request_id}` - Real-time progress

### Orchestration Features

- **Redis caching** with 7-day TTL for repeated requests
- **Staged approval** (marketing=auto, show=manual)
- **WebSocket progress streaming** for real-time updates
- **MinIO storage** for audio files

## Use Cases

### Marketing (Auto-Approved)
- Social media content
- Promotional materials
- Preview generation

### Show (Manual Approval)
- Live underscore music
- Scene transitions
- Performance audio

## Quick Start

```bash
# List available models
curl http://localhost:8005/music/models

# Generate music (marketing - auto-approved)
curl -X POST http://localhost:8005/music/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "upbeat electronic",
    "model": "ace-step-turbo",
    "duration_seconds": 30,
    "use_case": "marketing"
  }'

# Check status
curl http://localhost:8005/music/generate/{request_id}

# Play a track
curl -X POST http://localhost:8005/music/play \
  -H "Content-Type: application/json" \
  -d '{"track_id": "uuid"}'
```

## Migration Notes

### Previous Architecture (Deprecated)

The following services have been consolidated:

- **Music Generation Service** (port 8011) - Merged into LSM
- **Music Orchestration Service** (port 8012) - Merged into LSM

### New Endpoint Mapping

| Old Endpoint | New Endpoint |
|-------------|--------------|
| `POST /api/v1/music/generate` (8011) | `POST /music/generate` (8005) |
| `GET /api/v1/music/{id}` (8012) | `GET /music/generate/{request_id}` (8005) |
| `WebSocket /ws/music/{id}` (8012) | `WebSocket /music/ws/generate/{request_id}` (8005) |

## Architecture

```
┌─────────────────┐      ┌──────────────────┐
│   LSM Service   │──────│   OpenClaw       │
│   Music Module  │      │   Orchestrator   │
│   (Port 8005)   │      │   (Port 8000)    │
└────────┬────────┘      └──────────────────┘
         │
         ▼
    ┌─────────┐
    │ Models  │
    │ACE-Step │
    │1.5      │
    │base/sft │
    │turbo/mlx│
    └─────────┘
         │
         ▼
    ┌──────────┐
    │  Cache   │
    │  Redis   │
    └──────────┘
         │
         ▼
    ┌──────────┐
    │  MinIO   │
    │ Storage  │
    └──────────┘
```

## Related Documentation

- [Lighting, Sound & Music Service](lighting-sound-music.md) - Complete LSM documentation
- [API Reference](../reference/api.md#lighting-sound--music-lsm-service) - API endpoints
- [Architecture](../reference/architecture.md) - System architecture
- Migration Summary - Complete migration details

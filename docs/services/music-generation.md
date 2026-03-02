# Music Generation Platform

AI-powered local music generation for social media and live shows.

## Overview

The Music Generation Platform enables on-demand music generation using local AI models:
- **Meta MusicGen-Small** - Lightweight model (~2GB VRAM)
- **ACE-Step** - Advanced model (<4GB VRAM)

## Services

### Music Generation Service (Port 8011)

**Purpose:** Direct AI music generation

**Endpoints:**
- `POST /api/v1/music/generate` - Generate music
- `GET /api/v1/music/{id}` - Check status

**Features:**
- Multi-model pool management
- Async generation with cancellation
- VRAM-aware model loading

### Music Orchestration Service (Port 8012)

**Purpose:** Caching, approval, and progress streaming

**Endpoints:**
- `POST /api/v1/music/generate` - Generate with caching
- `GET /api/v1/music/{id}` - Get music status
- `WebSocket /ws/music/{id}` - Real-time progress

**Features:**
- Redis caching with 7-day TTL
- Staged approval (marketing=auto, show=manual)
- WebSocket progress streaming
- MinIO storage integration

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
# Generate music (marketing)
curl -X POST http://localhost:8012/api/v1/music/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "upbeat electronic", "use_case": "marketing", "duration_seconds": 30}'

# Check status
curl http://localhost:8012/api/v1/music/{music_id}
```

## Architecture

```
┌─────────────────┐      ┌──────────────────┐
│   Music Gen     │──────│   Music Orch     │
│   Service       │      │   Service        │
│   (Port 8011)   │      │   (Port 8012)   │
└────────┬────────┘      └────────┬─────────┘
         │                       │
         ▼                       ▼
    ┌─────────┐            ┌──────────┐
    │ Models  │            │  Cache   │
    │MusicGen │            │  Redis   │
    │ACE-Step │            └──────────┘
    └─────────┘                 │
                                ▼
                          ┌──────────┐
                          │  MinIO   │
                          │ Storage  │
                          └──────────┘
```

## Related Documentation

- [Architecture Design](../plans/2026-03-01-music-generation-platform-design.md)
- [Implementation Plan](../plans/2026-03-01-music-generation-platform-implementation.md)
- [API Reference](../reference/api.md#music-generation)

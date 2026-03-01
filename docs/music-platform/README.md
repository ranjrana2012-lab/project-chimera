# Chimera Music Platform

AI-powered music generation for Project Chimera.

## Overview
Generates original music locally via AI for social media content and live theatrical performances.

## Services
- **Music Generation Service** (8011): Model inference
- **Music Orchestration Service** (8012): Caching, approval, show integration

## Quick Start

```bash
# Generate music for social media
curl -X POST http://localhost:8012/api/v1/music/generate \
  -H "Authorization: Bearer <token>" \
  -d '{
    "prompt": "upbeat electronic background",
    "use_case": "marketing",
    "duration_seconds": 30
  }'
```

## Documentation
- [API Documentation](../../services/music-orchestration/reference/api.md)
- [Deployment Guide](../../services/music-orchestration/reference/runbooks/deployment.md)
- [Design Document](../../plans/2026-03-01-music-generation-platform-design.md)

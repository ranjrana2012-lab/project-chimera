# DEPRECATED - Music Generation Service

⚠️ **This service has been merged into the Lighting, Sound & Music service.**

## Migration Information

**New Service:** `services/lighting-sound-music/`
**New Port:** 8005
**Migration Date:** 2026-03-02

All music generation functionality has been preserved and enhanced in the new unified service with ACE-Step-1.5 integration.

### API Migration

| Old Endpoint (music-generation) | New Endpoint (lighting-sound-music) |
|---------------------------------|--------------------------------------|
| POST /generate | POST /music/generate |
| GET /models | GET /music/models |
| GET /tracks | GET /music/tracks |
| POST /play | POST /music/play |
| POST /stop | POST /music/stop |

### What Changed

- Service name: Music Generation → Lighting, Sound & Music
- API prefix: `/generate` → `/music/generate`
- Model integration: ACE-Step-1.5 models (base, sft, turbo, mlx)
- Enhanced features: Now includes lighting and sound effects
- Coordinated cues: New module for synchronized scenes

### Migration Steps

1. Update API calls to use new endpoint prefix
2. Update model references to use ACE-Step-1.5
3. Review new coordinated cues functionality
4. Update any hardcoded paths

### Documentation

See docs/services/lighting-sound-music.md for complete details.

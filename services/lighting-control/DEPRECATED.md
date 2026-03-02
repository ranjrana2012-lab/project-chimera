# DEPRECATED - Lighting Control Service

⚠️ **This service has been merged into the Lighting, Sound & Music service.**

## Migration Information

**New Service:** `services/lighting-sound-music/`
**New Port:** 8005
**Migration Date:** 2026-03-02

All lighting functionality has been preserved and enhanced in the new unified service.

### API Migration

| Old Endpoint (lighting-control) | New Endpoint (lighting-sound-music) |
|----------------------------------|--------------------------------------|
| POST /v1/lighting/set | POST /lighting/set |
| POST /v1/lighting/fixture/{id} | POST /lighting/fixture/{id} |
| GET /v1/lighting/state | GET /lighting/state |
| POST /v1/lighting/blackout | POST /lighting/blackout |
| POST /v1/osc/send | POST /lighting/osc/send |
| GET /v1/cues/* | GET /cues/* |
| GET /v1/presets/* | GET /cues/preset/* |

### What Changed

- Service name: Lighting Control → Lighting, Sound & Music
- API prefix: /v1/lighting/* → /lighting/*
- Enhanced features: Now includes sound effects and music generation
- Coordinated cues: New module for synchronized lighting + sound + music

### Migration Steps

1. Update API calls to use new endpoint prefix
2. Update port references (still 8005)
3. Review new coordinated cues functionality
4. Update any hardcoded paths

### Documentation

See docs/services/lighting-sound-music.md for complete details.

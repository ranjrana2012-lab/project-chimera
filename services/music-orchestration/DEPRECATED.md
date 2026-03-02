# DEPRECATED - Music Orchestration Service

⚠️ **This service has been merged into the Lighting, Sound & Music service.**

## Migration Information

**New Service:** `services/lighting-sound-music/`
**New Port:** 8005
**Migration Date:** 2026-03-02

All music orchestration functionality has been consolidated into the Cues module of the new unified service.

### API Migration

| Old Endpoint (music-orchestration) | New Endpoint (lighting-sound-music) |
|-------------------------------------|--------------------------------------|
| GET /ready | GET /health/ready |
| POST /generate | POST /music/generate |
| GET /cues | GET /cues/library |
| POST /cues | POST /cues/execute |
| WebSocket /ws | WebSocket /cues/ws/execute |

### What Changed

- Service name: Music Orchestration → Lighting, Sound & Music
- Orchestration → Cues module with enhanced features
- Model integration: ACE-Step-1.5 models now included
- Enhanced features: Now includes lighting and sound effects
- Timeline execution: Improved synchronization primitives

### Migration Steps

1. Update API calls to use new endpoint structure
2. Review coordinated cues functionality
3. Update WebSocket connections
4. Update any hardcoded paths

### Documentation

See docs/services/lighting-sound-music.md for complete details.

# Lighting, Sound & Music Service

## Overview

The **Lighting, Sound & Music (LSM)** service provides unified control over theatrical lighting, sound effects, and AI-generated music. It runs on port 8005 as part of the 8 core pillars of Project Chimera, consolidating the previous Lighting Control, Music Generation, and Music Orchestration services into a single cohesive component.

### Key Features

- **Unified Control**: Single API endpoint for all audio-visual elements
- **AI Music Generation**: Built-in ACE-Step-1.5 models for on-demand music
- **Coordinated Scenes**: Execute complex lighting + sound + music cues simultaneously
- **Real-time Updates**: WebSocket support for live generation and execution updates
- **Theatrical Focus**: Designed specifically for live performance and theatrical productions

---

## Architecture

### Module Structure

```
lighting-sound-music/
├── main.py              # FastAPI application entry point
├── lighting.py          # Lighting control module (DMX/sACN)
├── sound.py             # Sound effects and playback module
├── music.py             # AI music generation and playback
├── cues.py              # Coordinated multi-media scenes
├── schemas.py           # Shared data models
├── config.yaml          # Service configuration
├── config_loader.py     # Configuration manager
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build
└── manifests/           # Kubernetes deployment files
```

### Modules

| Module | Purpose | Endpoints |
|--------|---------|------------|
| **Lighting** | DMX/sACN stage automation | 9 |
| **Sound** | Sound effects, playback, mixing | 9 |
| **Music** | AI generation + playback (ACE-Step-1.5) | 12 + WS |
| **Cues** | Coordinated multi-media scenes | 12 + WS |

**Total:** 42 module endpoints + 8 health/root = **50 routes**

---

## API Endpoints

### Health Checks

```
GET /health/live     # Liveness probe
GET /health/ready    # Readiness probe (checks dependencies)
GET /health          # Detailed health with subsystem status
```

### Lighting (`/lighting/*`)

```
GET  /lighting/status           # System status
POST /lighting/set              # Set DMX values
POST /lighting/fixture/{id}     # Set specific fixture
GET  /lighting/state            # Get current state
POST /lighting/blackout         # Blackout all lights
POST /lighting/channel/{ch}     # Set single DMX channel
POST /lighting/osc/send         # Send OSC message
GET  /lighting/fixtures         # List all fixtures
DELETE /lighting/fixtures/{id}  # Delete fixture
```

### Sound (`/sound/*`)

```
GET  /sound/status              # System status
GET  /sound/sounds              # List available sounds
POST /sound/play                # Play sound effect
POST /sound/stop                # Stop all sounds
POST /sound/volume              # Set master volume
GET  /sound/volume              # Get current volume
GET  /sound/catalog/reload      # Reload sound catalog
POST /sound/catalog             # Add sound to catalog
DELETE /sound/catalog/{name}    # Remove sound from catalog
```

### Music (`/music/*`)

```
GET  /music/models              # List available ACE-Step-1.5 models
POST /music/generate            # Generate music with AI
GET  /music/generate/{id}       # Get generation status
GET  /music/tracks              # List generated/imported tracks
GET  /music/tracks/{id}         # Get specific track info
POST /music/play                # Play music track
POST /music/stop                # Stop music playback
POST /music/pause               # Pause playback
POST /music/volume              # Set music volume
GET  /music/status              # Get music status
DELETE /music/tracks/{id}       # Delete track
WS   /music/ws/generate/{id}    # Real-time generation updates
```

### Cues (`/cues/*`)

```
GET    /cues/library            # List all saved cues
POST   /cues/library            # Save a cue to library
GET    /cues/library/{name}     # Get specific cue
PUT    /cues/library/{name}     # Update existing cue
DELETE /cues/library/{name}     # Delete cue
POST   /cues/execute            # Execute a coordinated cue
POST   /cues/stop/{id}          # Stop running execution
GET    /cues/status             # Get all active executions
GET    /cues/status/{id}        # Get specific execution status
GET    /cues/history            # Get execution history
POST   /cues/preset/{name}      # Load preset scene
WS     /cues/ws/execute         # Real-time execution updates
```

---

## Getting Started

### Local Development

```bash
# Navigate to service directory
cd services/lighting-sound-music

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

The service will start on `http://localhost:8005`

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_lighting.py -v
pytest tests/test_sound.py -v
pytest tests/test_music.py -v
pytest tests/test_cues.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Building Docker Image

```bash
cd services/lighting-sound-music
docker build -t lighting-sound-music:v0.1.0 .
```

---

## Configuration

Configuration is managed through `config.yaml` or environment variables:

### Environment Variables

Prefix with `LSM_` and use double underscore `__` for nesting:

```bash
export LSM_SERVICE__PORT=8005
export LSM_LOGGING__LEVEL=DEBUG
export LSM_LIGHTING__DMX_UNIVERSE=2
export LSM_SOUND__MAX_CONCURRENT_SOUNDS=16
```

### Key Configuration Options

| Section | Option | Default | Description |
|---------|--------|---------|-------------|
| `service` | `port` | 8005 | Service port |
| `service` | `debug` | false | Debug mode |
| `lighting` | `dmx_universe` | 1 | DMX universe number |
| `lighting` | `sacn_enabled` | true | Enable sACN protocol |
| `sound` | `max_concurrent_sounds` | 8 | Max simultaneous sounds |
| `music` | `default_model` | turbo | ACE-Step-1.5 model |
| `cues` | `max_concurrent_cues` | 4 | Max simultaneous cues |

---

## ACE-Step-1.5 Integration

The music module uses **ACE-Step-1.5** models for AI music generation.

### Available Models

| Model | Path | Description |
|-------|------|-------------|
| `base` | `./models/base/` | Base foundation model |
| `sft` | `./models/sft/` | Supervised fine-tuned |
| `turbo` | `./models/turbo/` | Optimized for speed |
| `mlx` | `./models/mlx/` | Apple Silicon optimized |

### Music Generation

```python
# Generate music
POST /music/generate
{
  "prompt": "dramatic tension building slowly",
  "duration": 30,
  "model": "turbo",
  "use_case": "show",
  "format": "wav",
  "mood": "tense",
  "tempo": 120
}

# Response
{
  "request_id": "req_1",
  "status": "queued",
  "estimated_time": 15
}
```

---

## Coordinated Cues

Execute complex scenes combining lighting, sound, and music:

### Example Cue

```python
{
  "name": "thunder_scene",
  "description": "Dramatic thunder with lightning flash",
  "duration": 5.0,
  "lighting": [
    {
      "fixture_id": "stage_main",
      "intensity": 1.0,
      "color": "#FFFFFF",
      "fade_time": 0.1
    }
  ],
  "sound": [
    {
      "sound_name": "thunder_crack",
      "volume": 0.9,
      "start_time": 0.0
    }
  ],
  "music": {
    "action": "fade",
    "volume": 0.3,
    "fade_time": 2.0
  }
}
```

### Preset Scenes

Available presets:
- `blackout` - Complete blackout (emergency/reset)
- `opening` - Warm lights with ambient music

```bash
POST /cues/preset/opening
```

---

## Kubernetes Deployment

### Deploy to Cluster

```bash
# Create namespace and resources
kubectl apply -f services/lighting-sound-music/manifests/

# Wait for deployment
kubectl wait --for=condition=available --timeout=120s \
  deployment/lighting-sound-music -n chimera

# Port forward for local testing
kubectl port-forward -n chimera svc/lighting-sound-music 8005:8005
```

### Resources

| Resource | Value |
|----------|-------|
| Memory Request | 512Mi |
| Memory Limit | 4Gi |
| CPU Request | 250m |
| CPU Limit | 2000m |

### Persistent Volumes

| PVC | Size | Access Mode | Purpose |
|-----|------|-------------|---------|
| `ace-models-pvc` | 10Gi | ReadOnlyMany | ACE-Step-1.5 models |
| `sound-effects-pvc` | 5Gi | ReadWriteMany | Sound library |
| `music-library-pvc` | 20Gi | ReadWriteMany | Generated music |

---

## Contributing

This service is part of the 8 core pillars of Project Chimera. See Sprint 0 issues for onboarding tasks.

### Module Responsibilities

When contributing, focus on the relevant module:
- **Lighting:** DMX/sACN protocols, fixture management
- **Sound:** Audio playback, mixing, effects
- **Music:** ACE-Step-1.5 integration, generation pipeline
- **Cues:** Timeline execution, synchronization

### Testing

All contributions must include:
- Unit tests for new functionality
- Integration tests for API endpoints
- Documentation updates

---

## Troubleshooting

### Common Issues

**Service fails to start:**
- Check if port 8005 is available: `lsof -i :8005`
- Verify config.yaml exists or use defaults
- Check Python version (requires 3.12+)

**ACE-Step-1.5 models not loading:**
- Verify models directory: `ls models/`
- Check model permissions
- Review logs for specific error messages

**Sound playback not working:**
- Check sound files exist in `assets/sounds/`
- Verify audio backend is available
- Test with simple WAV file first

---

## Migration from Previous Services

### From Lighting Control

Old endpoint: `http://localhost:8005/*` (lighting-control)
New endpoint: `http://localhost:8005/lighting/*` (lighting-sound-music)

The API remains the same, just prefixed with `/lighting/`.

### From Music Generation/Orchestration

All functionality has been consolidated:
- Music generation → `/music/generate`
- Track management → `/music/tracks`
- Playback controls → `/music/play`, `/music/stop`

---

## Version History

- **v0.1.0** (2026-03-02) - Initial release consolidating 3 services
  - Lighting Control migration
  - Sound effects module (new)
  - Music generation with ACE-Step-1.5
  - Coordinated cues module (new)
  - Kubernetes deployment manifests

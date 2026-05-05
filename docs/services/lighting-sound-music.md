# Lighting, Sound & Music Service Documentation

**Version:** 0.4.0
**Last Updated:** March 2026

---

## Overview

The Lighting, Sound & Music (LSM) services provide unified audio-visual control for Project Chimera performances, integrating stage lighting, sound management, and AI-powered music generation.

---

## Components

| Service | Port | Description |
|---------|------|-------------|
| Lighting Service | 8005 | DMX/sACN stage lighting control |
| Sound Service | - | Audio playback and mixing |
| Music Generation | - | AI music generation via MusicGen |
| Music Orchestration | - | Caching, approval, WebSocket progress |

---

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Operator Console │────▶│  LSM Orchestrator │────▶│  Lighting Service │
│   (Port 8007)    │     │                   │     │   (Port 8005)    │
└──────────────────┘     └────────┬───────────┘     └────────┬─────────┘
                                  │                          │
                                  │         ┌──────────────────┴──────────┐
                                  │         │                          │
                                  ▼         ▼                          ▼
                           ┌──────────────┐              ┌──────────────┐
                           │ Sound Service│              │  DMX/sACN    │
                           └──────┬───────┘              │   Network    │
                                  │                      └───────────────┘
                                  ▼
                    ┌──────────────────────────────┐
                    │     Music Generation        │
                    │  ┌───────────────────────┐  │
                    │  │ MusicGen (ACE-Step)   │  │
                    │  └───────────┬───────────┘  │
                    │              │              │
                    │  ┌───────────▼───────────┐  │
                    │  │   Orchestration       │  │
                    │  │ (Caching, Approval)   │  │
                    │  └───────────────────────┘  │
                    └──────────────────────────────┘
```

---

## Lighting Service (Port 8005)

### Purpose

Provides DMX and sACN protocol support for controlling professional stage lighting equipment.

### Features

- **DMX512 Support:** Control up to 512 channels per universe
- **sACN (Streaming ACN):** Modern IP-based lighting control
- **Multi-Universe:** Support for multiple DMX universes
- **Fade Curves:** Smooth transitions with customizable curves
- **Cue System:** Store and recall lighting cues
- **Master Controls:** Grand master, blackout, strobe

### API Endpoints

#### Set Channel Value
```http
POST /api/v1/lighting/dmx/{universe}/channel
Content-Type: application/json

{
  "channel": 1,
  "value": 255
}
```

#### Set Multiple Channels
```http
POST /api/v1/lighting/dmx/{universe}/channels
Content-Type: application/json

{
  "channels": {
    "1": 255,
    "2": 128,
    "3": 64
  }
}
```

#### Create Cue
```http
POST /api/v1/lighting/cues
Content-Type: application/json

{
  "name": "opening_scene",
  "universe": 1,
  "channels": {
    "1": 255,
    "2": 200,
    "3": 150
  },
  "fade_time": 3.0
}
```

#### Recall Cue
```http
POST /api/v1/lighting/cues/{cue_name}/recall
Content-Type: application/json

{
  "fade_time": 2.0
}
```

#### Blackout
```http
POST /api/v1/lighting/control/blackout
```

#### Set Grand Master
```http
POST /api/v1/lighting/control/grandmaster
Content-Type: application/json

{
  "value": 0.8
}
```

### Configuration

Environment variables:
- `DMX_INTERFACE`: DMX interface type (enttec-usb-pro, art-net, sacn)
- `DMX_UNIVERSES`: Number of DMX universes (default: 2)
- `DMX_REFRESH_RATE`: Refresh rate in Hz (default: 44)
- `SACN_INTERFACE`: Network interface for sACN (default: eth0)

### DMX Channel Mapping

Typical lighting fixture channel mapping:

| Channel | Function | Range |
|---------|----------|-------|
| 1 | Intensity | 0-255 |
| 2 | Red | 0-255 |
| 3 | Green | 0-255 |
| 4 | Blue | 0-255 |
| 5 | Pan | 0-255 |
| 6 | Tilt | 0-255 |
| 7 | Zoom | 0-255 |
| 8 | Focus | 0-255 |

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lighting_dmx_frames_total` | Counter | DMX frames sent |
| `lighting_sacn_packets_total` | Counter | sACN packets sent |
| `lighting_cues_recalled_total` | Counter | Cues recalled |
| `lighting_fade_duration_seconds` | Histogram | Fade transition times |
| `lighting_universe_errors_total` | Counter | DMX universe errors |

---

## Sound Service

### Purpose

Handles audio playback, mixing, and synchronization for performances.

### Features

- **Multi-Track Playback:** Play multiple audio tracks simultaneously
- **Real-Time Mixing:** Adjust volume, pan, EQ per track
- **Synchronization:** Sync audio with show events
- **Effects:** Reverb, delay, compression
- **Cue Points:** Mark and jump to cue points
- **Looping:** Loop sections of audio

### API Endpoints

#### Load Audio Track
```http
POST /api/v1/sound/tracks
Content-Type: multipart/form-data

{
  "file": <audio_file>,
  "name": "background_music",
  "track": 1
}
```

#### Play Track
```http
POST /api/v1/sound/tracks/{track_id}/play
```

#### Stop Track
```http
POST /api/v1/sound/tracks/{track_id}/stop
```

#### Set Volume
```http
POST /api/v1/sound/tracks/{track_id}/volume
Content-Type: application/json

{
  "volume": 0.75
}
```

#### Add Cue Point
```http
POST /api/v1/sound/tracks/{track_id}/cues
Content-Type: application/json

{
  "name": "chorus_start",
  "position": 45.2
}
```

#### Set Effect
```http
POST /api/v1/sound/tracks/{track_id}/effects
Content-Type: application/json

{
  "effect": "reverb",
  "parameters": {
    "room_size": 0.7,
    "damping": 0.5
  }
}
```

### Configuration

Environment variables:
- `AUDIO_DEVICE`: Audio output device (default: default)
- `SAMPLE_RATE`: Audio sample rate (default: 48000)
- `BUFFER_SIZE`: Audio buffer size in frames (default: 1024)
- `MAX_TRACKS`: Maximum simultaneous tracks (default: 16)

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `sound_tracks_playing` | Gauge | Currently playing tracks |
| `sound_buffer_underruns` | Counter | Audio buffer underruns |
| `sound_latency_seconds` | Gauge | Audio latency |

---

## Music Generation Service

### Purpose

AI-powered music generation using Meta's MusicGen and ACE-Step models.

### Features

- **Text-to-Music:** Generate music from text descriptions
- **Style Transfer:** Apply musical styles to melodies
- **Duration Control:** Generate music of specified duration
- **Instrument Control:** Specify instruments in generation
- **Caching:** Cache generated music for reuse
- **Approval Workflow:** Require approval before deployment

### Models Used

| Model | Purpose | Provider |
|-------|---------|----------|
| MusicGen | Text-to-music generation | Meta |
| ACE-Step | Continuation and style transfer | Meta |

### API Endpoints

#### Generate Music
```http
POST /api/v1/music/generate
Content-Type: application/json

{
  "prompt": "upbeat theatrical music with orchestral instruments",
  "duration": 30,
  "instruments": ["piano", "strings", "brass"],
  "tempo": 120
}
```

**Response:**
```json
{
  "generation_id": "gen-abc123",
  "status": "processing",
  "estimated_time": 45
}
```

#### Get Generation Status
```http
GET /api/v1/music/generations/{generation_id}
```

**Response:**
```json
{
  "generation_id": "gen-abc123",
  "status": "completed",
  "audio_url": "/music/generated/gen-abc123.wav",
  "duration": 30,
  "prompt": "upbeat theatrical music...",
  "created_at": "2026-03-05T12:00:00Z"
}
```

#### List Cached Music
```http
GET /api/v1/music/cache
```

#### Approve Generation
```http
POST /api/v1/music/generations/{generation_id}/approve
```

#### Regenerate
```http
POST /api/v1/music/generations/{generation_id}/regenerate
```

### Configuration

Environment variables:
- `MUSICGEN_MODEL_PATH`: Path to MusicGen model
- `ACE_STEP_MODEL_PATH`: Path to ACE-Step model
- `GENERATION_CACHE_DIR`: Directory for caching (default: `/tmp/music-cache`)
- `MAX_GENERATION_DURATION`: Max duration in seconds (default: 120)
- `DEFAULT_TEMPO`: Default tempo (default: 120)

### Prompt Guidelines

Effective music generation prompts:

**Good Examples:**
- "Upbeat orchestral music with brass and percussion, 120 BPM"
- "Ambient electronic texture with soft synthesizer pads"
- "Dramatic theatrical underscore with strings and timpani"

**Include:**
- Genre/style
- Instruments
- Tempo/BPM
- Mood/emotion
- Duration

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `music_generations_total` | Counter | Total music generations |
| `music_generations_completed` | Counter | Completed generations |
| `music_cache_hits` | Counter | Cache hits |
| `music_cache_misses` | Counter | Cache misses |
| `music_generation_duration_seconds` | Histogram | Generation time |
| `music_approval_rate` | Gauge | Approval rate (approved/total) |

---

## Music Orchestration Service

### Purpose

Manages music generation caching, approval workflow, and real-time progress streaming.

### Features

- **Smart Caching:** Cache generations by prompt hash
- **Approval Queue:** Queue for human review before deployment
- **WebSocket Progress:** Real-time generation progress
- **Batch Generation:** Generate multiple variations
- **Version Control:** Track different versions of same prompt

### API Endpoints

#### Request Generation
```http
POST /api/v1/orchestration/request
Content-Type: application/json

{
  "prompt": "dramatic underscore",
  "priority": "high",
  "webhook_url": "http://callback-url/webhook"
}
```

#### Get Queue Status
```http
GET /api/v1/orchestration/queue
```

**Response:**
```json
{
  "queue_length": 5,
  "processing": 1,
  "pending": 4,
  "estimated_wait": 120
}
```

#### WebSocket Progress

Connect to: `ws://localhost:8099/progress/{generation_id}`

**Message Format:**
```json
{
  "type": "progress",
  "generation_id": "gen-abc123",
  "progress": 0.45,
  "status": "generating",
  "eta": 30
}
```

### Configuration

Environment variables:
- `ORCHESTRATION_QUEUE_SIZE`: Max queue size (default: 100)
- `CACHE_TTL_SECONDS`: Cache time-to-live (default: 86400)
- `WEBSOCKET_PORT`: WebSocket server port (default: 8099)

---

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r services/lighting/requirements.txt

# Run Lighting Service
cd services/lighting-service && python -m main

# Run Music Generation
cd services/music-generation && python -m main
```

### Docker

```bash
# Build lighting service image
docker build -t chimera-lighting services/lighting-service/

# Run lighting service
docker run -p 8005:8005 --device=/dev/dmx chimera-lighting
```

### Kubernetes

```bash
# Deploy all LSM services
kubectl apply -f platform/deployment/lsm/

# Verify deployment
kubectl get pods -n lsm
```

---

## Hardware Setup

### DMX Interface

Recommended USB-DMX interfaces:
- ENTTEC Open DMX USB
- DMXking ultraDMX Pro
- FTDI USB-to-DMX adapters

### Audio Interface

Recommended audio interfaces:
- Focusrite Scarlett series
- Native Instruments Komplete Audio
- PreSonus AudioBox

### Connection Diagram

```
┌──────────────┐         ┌──────────────┐
│   Lighting   │  USB    │  DMX Interface│
│   Service    │────────▶│   (ENTTEC)    │
│              │         └───────┬───────┘
└──────────────┘                 │
                                 │ DMX
                                 ▼
                        ┌─────────────────┐
                        │  Lighting Fixtures│
                        │   (Stage Wash)  │
                        └─────────────────┘
```

---

## Monitoring

All LSM services expose Prometheus metrics and use OpenTelemetry for distributed tracing.

See [Observability Guide](../observability.md) for complete monitoring setup.

---

## Troubleshooting

### Common Issues

**DMX not outputting:**
- Check USB permissions: `sudo chmod 666 /dev/ttyUSB0`
- Verify DMX interface connection
- Check DMX universe configuration

**Audio not playing:**
- Verify audio device is connected
- Check system audio settings
- Verify audio file format compatibility

**Music generation slow:**
- Check GPU availability
- Verify model files are downloaded
- Check system resources

---

## Related Documentation

- [Lighting Service API](../api/lighting-service.md) - Complete API reference
- [Music Generation Guide](music-generation.md) - Music generation guide
- [Observability Guide](../observability.md) - Monitoring and metrics
- [Performance Analysis Runbook](../runbooks/performance-analysis.md) - Performance optimization

---

**Need help?** Start with the [Student / Laptop setup guide](../guides/STUDENT_LAPTOP_SETUP.md)
and the repository `CONTRIBUTING.md`.

# BSL Agent

British Sign Language gloss translation and 3D avatar rendering service for Project Chimera.

## Overview

The BSL Agent provides accessibility for Deaf and hard-of-hearing audiences by:
- Converting English text to BSL gloss notation
- Rendering BSL-signing 3D avatars in real-time using WebGL/Three.js
- Supporting facial expressions and body language with NMM format
- Real-time avatar animation via WebSocket
- Caching translations for performance

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Avatar model files (optional for development)

# Local development setup
cd services/bsl-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your avatar model path

# Run service
uvicorn main:app --reload --port 8003
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `bsl-agent` | Service identifier |
| `PORT` | `8003` | HTTP server port |
| `AVATAR_MODEL_PATH` | `/models/bsl_avatar` | Avatar model directory |
| `AVATAR_RESOLUTION` | `1920x1080` | Output video resolution |
| `AVATAR_FPS` | `30` | Frames per second |
| `CACHE_TTL` | `86400` | Translation cache TTL (seconds) |
| `ENABLE_FACIAL_EXPRESSIONS` | `true` | Enable facial expressions |
| `ENABLE_BODY_LANGUAGE` | `true` | Enable body language gestures |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks avatar model)
- `GET /metrics` - Prometheus metrics

### Translation
- `POST /v1/translate` - Convert English text to BSL gloss notation
- `POST /v1/render` - Generate avatar animation data for BSL gloss

### Avatar Rendering (WebGL/Three.js)
- `GET /avatar` - 3D avatar viewer HTML page
- `GET /static/{file_path:path}` - Serve static assets for avatar viewer
- `POST /api/avatar/generate` - Generate NMM animation for BSL gloss
- `GET /api/avatar/info` - Get avatar renderer information
- `POST /api/avatar/expression` - Set facial expression
- `POST /api/avatar/handshape` - Set hand shape for signing
- `WS /ws/avatar` - WebSocket for real-time avatar animation updates

**Example: Text to gloss**
```bash
curl -X POST http://localhost:8003/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, welcome to the show"}'
```

**Example: Generate NMM animation**
```bash
curl -X POST http://localhost:8003/api/avatar/generate \
  -H "Content-Type: application/json" \
  -d '{"gloss": "HELLO HOW YOU", "include_nmm": true}'
```

**Example: Set facial expression**
```bash
curl -X POST http://localhost:8003/api/avatar/expression \
  -H "Content-Type: application/json" \
  -d '{"expression": "happy", "intensity": 0.8}'
```

## 3D Avatar Viewer

The BSL Agent includes a web-based 3D avatar viewer powered by Three.js:

- **Access**: Navigate to `http://localhost:8003/avatar` in a web browser
- **Features**:
  - Real-time 3D avatar rendering with WebGL
  - Interactive controls for animation playback
  - Facial expression selection
  - Hand shape configuration
  - Timeline scrubbing and playback speed control
  - Real-time FPS and debug information

### NMM Animation Format

The avatar uses the NMM (Neural Model Format) for animations:

```json
{
  "name": "wave_animation",
  "duration": 2.0,
  "fps": 30,
  "loop": false,
  "easing": "easeInOut",
  "keyframes": [
    {
      "time": 0.0,
      "morph_targets": {"brows": 0.0, "smile": 0.0},
      "bone_positions": {"right_hand": [0.2, 1.0, 0.0]},
      "facial_expression": "neutral"
    },
    {
      "time": 1.0,
      "morph_targets": {"brows": 0.3, "smile": 0.5},
      "bone_positions": {"right_hand": [0.4, 1.3, 0.3]},
      "facial_expression": "happy"
    }
  ]
}
```

### Supported Facial Expressions
- `neutral`, `happy`, `sad`, `surprised`, `angry`, `questioning`
- `brows-up`, `brows-down`

### Supported Hand Shapes
- `fist`, `open`, `point`, `peace`, `thumbs_up`, `wave`

## Development

### Code Structure
```
bsl-agent/
├── main.py              # FastAPI application
├── translator.py        # English to BSL gloss conversion
├── avatar_renderer.py   # Legacy avatar rendering (placeholder)
├── avatar_webgl.py      # WebGL/Three.js avatar renderer
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
├── static/             # Frontend assets for avatar viewer
│   ├── avatar.html     # 3D avatar viewer page
│   ├── css/
│   │   └── avatar.css  # Avatar viewer styling
│   └── js/
│       ├── avatar.js              # Three.js scene setup
│       ├── nmm-loader.js          # NMM animation loader
│       └── animation-controller.js # Animation playback controller
├── models/             # Avatar 3D models (GLTF/GLB)
├── animations/         # NMM animation files
└── tests/              # Test suite
```

### Adding Features
1. Add new gloss mappings in `translator.py`
2. Create new NMM animations in `animations/` directory
3. Enhance avatar rendering in `avatar_webgl.py`
4. Extend viewer UI in `static/avatar.html` and `static/js/`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_gloss.py -v
```

## Troubleshooting

### Avatar Model Not Found
**Symptom:** Ready check fails, model errors
**Solution:** Set correct `AVATAR_MODEL_PATH`, ensure model files exist

### Poor Translation Quality
**Symptom:** Gloss output incorrect
**Solution:** Update gloss dictionary in `gloss_translator.py`, check NMM markers

### Rendering Slow
**Symptom:** High latency on render endpoint
**Solution:** Reduce `AVATAR_RESOLUTION`, lower `AVATAR_FPS`

### Avatar Viewer Not Loading
**Symptom:** 3D viewer shows blank page or errors
**Solution:** Check browser console for WebGL support, verify static files are being served correctly

### WebSocket Connection Failed
**Symptom:** Real-time updates not working
**Solution:** Ensure WebSocket endpoint is accessible, check firewall settings

## Architecture

### WebGL Avatar Rendering

The BSL Agent uses a modern WebGL-based rendering pipeline:

1. **Server-Side (Python)**:
   - `AvatarWebGLRenderer` generates NMM animation data
   - Processes BSL gloss into keyframe animations
   - Manages facial expressions and hand shapes
   - Provides REST API and WebSocket endpoints

2. **Client-Side (JavaScript/Three.js)**:
   - `BSLAvatarViewer` sets up Three.js scene
   - `NMMLoader` parses and interpolates NMM animations
   - `AnimationController` manages playback state
   - Real-time rendering in user's browser

### Technology Stack

- **Backend**: FastAPI, Python 3.10+
- **3D Rendering**: Three.js (WebGL)
- **Animation Format**: NMM (Neural Model Format) - JSON-based
- **Real-time Communication**: WebSocket
- **Observability**: OpenTelemetry, Prometheus

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera

# Documentation Comprehensive Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete documentation synchronization for v0.5.0 release - create 7 missing service READMEs, add dashboard documentation, resolve 32 TODO/FIXME markers, standardize version to v0.5.0, and validate all internal links.

**Architecture:** 5-phase pipeline: (1) Create 7 service READMEs based on captioning-agent template, (2) Create dashboard user guide and update API docs, (3) Resolve all TODO/FIXME markers, (4) Standardize all version references to v0.5.0, (5) Validate and fix broken internal links.

**Tech Stack:** Markdown documentation, grep for scanning, bash scripts for validation, git for commits.

---

## Phase 1: Service README Files (7 comprehensive documents)

### Task 1: Create openclaw-orchestrator/README.md

**Files:**
- Create: `services/openclaw-orchestrator/README.md`

**Step 1: Write the README content**

```markdown
# OpenClaw Orchestrator

Central control plane for Project Chimera - coordinates all AI agents and manages the performance state machine.

## Overview

The OpenClaw Orchestrator is the heart of Project Chimera, responsible for:
- Coordinating all 8 AI agents (SceneSpeak, Captioning, BSL, Sentiment, Lighting, Safety, Console)
- Managing the scene state machine (idle → prelude → active → postlude → cleanup)
- Routing events between agents via Kafka
- Providing a unified API for performance control

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Docker (for containerized deployment)
# - Access to Kafka message broker

# Local development setup
cd services/openclaw-orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your agent URLs

# Run service
uvicorn main:app --reload --port 8000
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `openclaw-orchestrator` | Service identifier |
| `PORT` | `8000` | HTTP server port |
| `SCENESPEAK_AGENT_URL` | `http://localhost:8001` | SceneSpeak Agent URL |
| `CAPTIONING_AGENT_URL` | `http://localhost:8002` | Captioning Agent URL |
| `BSL_AGENT_URL` | `http://localhost:8003` | BSL Agent URL |
| `SENTIMENT_AGENT_URL` | `http://localhost:8004` | Sentiment Agent URL |
| `LIGHTING_SOUND_MUSIC_URL` | `http://localhost:8005` | Lighting/Sound/Music URL |
| `SAFETY_FILTER_URL` | `http://localhost:8006` | Safety Filter URL |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry traces endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks all agents)
- `GET /metrics` - Prometheus metrics

### Scene Control
- `POST /api/scene/start` - Start a new scene
- `POST /api/scene/stop` - Stop current scene
- `POST /api/scene/transition` - Trigger state transition
- `GET /api/scene/state` - Get current scene state

### Agent Communication
- `POST /api/agent/send` - Send message to specific agent
- `GET /api/agent/status` - Get status of all agents

**Example: Start a scene**
```bash
curl -X POST http://localhost:8000/api/scene/start \
  -H "Content-Type: application/json" \
  -d '{"scene_id": "scene_001", "duration": 300}'
```

## Development

### Code Structure
```
openclaw-orchestrator/
├── main.py              # FastAPI application
├── orchestrator.py      # Core orchestration logic
├── state_machine.py     # Scene state machine
├── kafka_consumer.py    # Kafka message consumption
├── kafka_producer.py    # Kafka message publishing
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Implement new state in `state_machine.py`
2. Add corresponding API endpoint in `main.py`
3. Update Pydantic models in `models.py`
4. Add tests in `tests/`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_orchestrator.py -v
```

## Troubleshooting

### Agent Not Responding
**Symptom:** Readiness probe fails
**Solution:** Check agent URL in `.env`, ensure agent is running

### Kafka Connection Error
**Symptom:** Unable to publish/subscribe messages
**Solution:** Verify Kafka is running, check `KAFKA_BROKER` in config

### State Machine Stuck
**Symptom:** Scene won't transition to next state
**Solution:** Check logs for validation errors, use `POST /api/scene/transition` to force transition

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/openclaw-orchestrator/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/openclaw-orchestrator/README.md
git commit -m "docs: add openclaw-orchestrator README"
```

---

### Task 2: Create scenespeak-agent/README.md

**Files:**
- Create: `services/scenespeak-agent/README.md`

**Step 1: Write the README content**

```markdown
# SceneSpeak Agent

Real-time dialogue generation service using GLM 4.7 API and local LLM fallback for Project Chimera.

## Overview

The SceneSpeak Agent generates theatrical dialogue in real-time based on:
- Scene context and narrative parameters
- Audience sentiment feedback
- Performance state transitions
- Character and plot constraints

Supports both cloud-based GLM API and local model inference.

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - GLM API key (from https://open.bigmodel.cn/)
# - Optional: Local LLM model files

# Local development setup
cd services/scenespeak-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your GLM_API_KEY

# Run service
uvicorn main:app --reload --port 8001
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `scenespeak-agent` | Service identifier |
| `PORT` | `8001` | HTTP server port |
| `GLM_API_KEY` | *required* | GLM 4.7 API key |
| `GLM_API_BASE` | `https://open.bigmodel.cn/api/paas/v4/` | GLM API endpoint |
| `LOCAL_MODEL_PATH` | *optional* | Path to local LLM model |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks GLM API)
- `GET /metrics` - Prometheus metrics

### Dialogue Generation
- `POST /api/v1/generate` - Generate dialogue for scene
- `POST /api/v1/continue` - Continue existing dialogue
- `GET /api/v1/models` - List available models

**Example: Generate dialogue**
```bash
curl -X POST http://localhost:8001/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "scene_context": "A mystical forest clearing at dusk",
    "characters": ["Hero", "Spirit"],
    "sentiment": "hopeful",
    "max_tokens": 500
  }'
```

## Development

### Code Structure
```
scenespeak-agent/
├── main.py              # FastAPI application
├── glm_client.py        # GLM API client
├── local_model.py       # Local LLM fallback
├── dialogue_manager.py  # Dialogue state management
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new dialogue templates in `dialogue_manager.py`
2. Implement model switching logic in `local_model.py`
3. Add API endpoints in `main.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_dialogue.py -v
```

## Troubleshooting

### GLM API Connection Failed
**Symptom:** 401 Unauthorized errors
**Solution:** Verify `GLM_API_KEY` is valid, check account quota

### Model Not Loading
**Symptom:** Local model fails to load
**Solution:** Check `LOCAL_MODEL_PATH`, verify model files exist

### Generation Timeout
**Symptom:** Requests take too long
**Solution:** Reduce `max_tokens`, check network connectivity to GLM API

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/scenespeak-agent/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/scenespeak-agent/README.md
git commit -m "docs: add scenespeak-agent README"
```

---

### Task 3: Create bsl-agent/README.md

**Files:**
- Create: `services/bsl-agent/README.md`

**Step 1: Write the README content**

```markdown
# BSL Agent

British Sign Language gloss translation and avatar rendering service for Project Chimera.

## Overview

The BSL Agent provides accessibility for Deaf and hard-of-hearing audiences by:
- Converting English text to BSL gloss notation
- Rendering BSL-signing avatars in real-time
- Supporting facial expressions and body language
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
- `POST /api/v1/text-to-gloss` - Convert text to BSL gloss
- `POST /api/v1/gloss-to-pose` - Convert gloss to avatar pose sequence
- `POST /api/v1/render` - Render avatar video from pose sequence
- `GET /api/v1/avatar/frames` - Stream avatar frames via WebSocket

**Example: Text to gloss**
```bash
curl -X POST http://localhost:8003/api/v1/text-to-gloss \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, welcome to the show"}'
```

## Development

### Code Structure
```
bsl-agent/
├── main.py              # FastAPI application
├── gloss_translator.py  # English to BSL gloss conversion
├── avatar_renderer.py   # Avatar rendering engine
├── pose_generator.py    # Gloss to pose sequence
├── cache.py            # Translation cache
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new gloss mappings in `gloss_translator.py`
2. Implement new poses in `pose_generator.py`
3. Enhance rendering in `avatar_renderer.py`

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

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/bsl-agent/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/bsl-agent/README.md
git commit -m "docs: add bsl-agent README"
```

---

### Task 4: Create sentiment-agent/README.md

**Files:**
- Create: `services/sentiment-agent/README.md`

**Step 1: Write the README content**

```markdown
# Sentiment Agent

Audience sentiment analysis service enhanced with WorldMonitor global intelligence for Project Chimera.

## Overview

The Sentiment Agent analyzes audience feedback to guide performance adaptations:
- Real-time sentiment scoring from text input
- WorldMonitor integration for global context
- WebSocket streaming for live sentiment updates
- Category-based event filtering
- Trend analysis and aggregation

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Optional: DistilBERT model files for ML-based analysis

# Local development setup
cd services/sentiment-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env to enable ML model if available

# Run service
uvicorn main:app --reload --port 8004
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `sentiment-agent` | Service identifier |
| `PORT` | `8004` | HTTP server port |
| `HOST` | `0.0.0.0` | Bind address |
| `USE_ML_MODEL` | `false` | Enable DistilBERT model |
| `MODEL_PATH` | `./models/distilbert` | ML model directory |
| `MODEL_CACHE_DIR` | `./models_cache` | Model cache directory |
| `MAX_TEXT_LENGTH` | `10000` | Max input text length |
| `BATCH_SIZE` | `32` | Batch processing size |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks model if enabled)
- `GET /metrics` - Prometheus metrics

### Sentiment Analysis
- `POST /api/v1/analyze` - Analyze sentiment of text
- `POST /api/v1/batch` - Batch analyze multiple texts
- `GET /api/v1/trends` - Get sentiment trend data
- `WebSocket /v1/stream` - Real-time sentiment streaming

**Example: Analyze sentiment**
```bash
curl -X POST http://localhost:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The audience is loving this performance!"}'
```

**Response:**
```json
{
  "sentiment": "positive",
  "score": 0.87,
  "confidence": 0.92,
  "categories": ["entertainment", "emotion"],
  "worldmonitor_context": {
    "global_events": [],
    "cultural_context": "western"
  }
}
```

## Development

### Code Structure
```
sentiment-agent/
├── main.py              # FastAPI application
├── sentiment_analyzer.py # Sentiment analysis engine
├── ml_model.py          # DistilBERT model wrapper
├── worldmonitor.py      # WorldMonitor integration
├── websocket_handler.py # WebSocket streaming
├── cache.py            # Result caching
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new sentiment categories in `sentiment_analyzer.py`
2. Implement new WorldMonitor filters in `worldmonitor.py`
3. Enhance ML model in `ml_model.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_sentiment.py -v
```

## Troubleshooting

### Model Not Loading
**Symptom:** Ready check fails when `USE_ML_MODEL=true`
**Solution:** Verify `MODEL_PATH`, check model files, ensure sufficient memory

### Analysis Timeout
**Symptom:** Requests take too long
**Solution:** Reduce `MAX_TEXT_LENGTH`, decrease `BATCH_SIZE`, disable ML model

### WorldMonitor Connection Failed
**Symptom:** No global context in response
**Solution:** Check WorldMonitor API credentials, verify network connectivity

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/sentiment-agent/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/sentiment-agent/README.md
git commit -m "docs: add sentiment-agent README"
```

---

### Task 5: Create lighting-sound-music/README.md

**Files:**
- Create: `services/lighting-sound-music/README.md`

**Step 1: Write the README content**

```markdown
# Lighting-Sound-Music Service

Stage automation service controlling DMX lighting, audio playback, and music generation for Project Chimera.

## Overview

The Lighting-Sound-Music Service manages all stage automation:
- DMX lighting control (scenes, fades, effects)
- Audio playback and mixing
- Music generation integration
- Synchronized playback with <50ms tolerance

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - DMX interface (optional - can run in mock mode)
# - Audio output device

# Local development setup
cd services/lighting-sound-music
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your DMX/audio configuration

# Run service
uvicorn main:app --reload --port 8005
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `lighting-sound-music` | Service identifier |
| `PORT` | `8005` | HTTP server port |
| `DMX_ENABLED` | `true` | Enable DMX control |
| `DMX_UNIVERSE` | `1` | DMX universe number |
| `DMX_INTERFACE` | `placeholder` | DMX interface device |
| `AUDIO_ENABLED` | `true` | Enable audio playback |
| `AUDIO_SAMPLE_RATE` | `44100` | Audio sample rate (Hz) |
| `AUDIO_CHANNELS` | `2` | Audio channels (stereo) |
| `AUDIO_BUFFER_SIZE` | `1024` | Audio buffer size |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `SYNC_TOLERANCE_MS` | `50` | Synchronization tolerance |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks DMX/audio)
- `GET /metrics` - Prometheus metrics

### Lighting Control
- `POST /api/v1/lighting/scene` - Set lighting scene
- `POST /api/v1/lighting/fade` - Fade to scene
- `GET /api/v1/lighting/status` - Get current lighting state

### Audio Control
- `POST /api/v1/audio/play` - Play audio file
- `POST /api/v1/audio/stop` - Stop audio playback
- `POST /api/v1/audio/volume` - Set volume level
- `GET /api/v1/audio/status` - Get audio status

### Synchronization
- `POST /api/v1/sync/start` - Start synchronized playback
- `POST /api/v1/sync/stop` - Stop synchronized playback

**Example: Set lighting scene**
```bash
curl -X POST http://localhost:8005/api/v1/lighting/scene \
  -H "Content-Type: application/json" \
  -d '{
    "scene": "forest_clearing",
    "intensity": 0.8,
    "color_temperature": 4500
  }'
```

## Development

### Code Structure
```
lighting-sound-music/
├── main.py              # FastAPI application
├── dmx_controller.py    # DMX lighting control
├── audio_engine.py      # Audio playback engine
�├── sync_manager.py      # Synchronization manager
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Define new lighting scenes in `dmx_controller.py`
2. Implement audio effects in `audio_engine.py`
3. Add sync events in `sync_manager.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_dmx.py -v
```

## Troubleshooting

### DMX Not Connected
**Symptom:** DMX commands fail
**Solution:** Check `DMX_INTERFACE` in `.env`, verify DMX USB adapter connected

### Audio Playback Stutters
**Symptom:** Audio glitching during playback
**Solution:** Increase `AUDIO_BUFFER_SIZE`, check system CPU load

### Sync Drift Detected
**Symptom:** Lighting/audio out of sync
**Solution:** Adjust `SYNC_TOLERANCE_MS`, check network latency to other services

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/lighting-sound-music/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/lighting-sound-music/README.md
git commit -m "docs: add lighting-sound-music README"
```

---

### Task 6: Create safety-filter/README.md

**Files:**
- Create: `services/safety-filter/README.md`

**Step 1: Write the README content**

```markdown
# Safety Filter

Multi-layer content moderation service ensuring family-friendly output for Project Chimera.

## Overview

The Safety Filter provides comprehensive content moderation:
- Word-based profanity filtering
- ML-based offensive content detection (optional)
- Context-aware policy enforcement
- Audit logging for all filtered content
- Multiple policy levels (family, teen, adult)

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Optional: ML model for enhanced filtering

# Local development setup
cd services/safety-filter
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your policy preferences

# Run service
uvicorn main:app --reload --port 8006
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `safety-filter` | Service identifier |
| `PORT` | `8006` | HTTP server port |
| `DEFAULT_POLICY` | `family` | Default moderation policy |
| `ENABLE_ML_FILTER` | `false` | Enable ML-based filtering |
| `ENABLE_CONTEXT_FILTER` | `true` | Enable context-aware filtering |
| `CACHE_TTL` | `3600` | Filter cache TTL (seconds) |
| `AUDIT_LOG_MAX_SIZE` | `10000` | Max audit log entries |
| `AUDIT_LOG_RETENTION_HOURS` | `24` | Audit log retention |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks word lists)
- `GET /metrics` - Prometheus metrics

### Content Filtering
- `POST /api/v1/filter` - Filter content for policy violations
- `POST /api/v1/check` - Check content without filtering
- `GET /api/v1/policies` - List available policies
- `GET /api/v1/audit` - Get audit log

**Example: Filter content**
```bash
curl -X POST http://localhost:8006/api/v1/filter \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your text here",
    "policy": "family"
  }'
```

**Response (safe):**
```json
{
  "safe": true,
  "content": "Your text here",
  "filtered": false,
  "reason": null
}
```

**Response (unsafe):**
```json
{
  "safe": false,
  "content": "*** text here",
  "filtered": true,
  "reason": "profanity_detected",
  "violations": ["word_list"]
}
```

## Development

### Code Structure
```
safety-filter/
├── main.py              # FastAPI application
├── word_filter.py       # Word-based filtering
├── ml_filter.py         # ML-based filtering (optional)
├── context_filter.py    # Context-aware filtering
├── audit_logger.py      # Audit log management
├── cache.py            # Filter result cache
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new policy levels in `word_filter.py`
2. Implement new ML models in `ml_filter.py`
3. Add context rules in `context_filter.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_filter.py -v
```

## Troubleshooting

### Over-Filtering Content
**Symptom:** Safe content being blocked
**Solution:** Adjust `DEFAULT_POLICY`, review word lists, check context rules

### Under-Filtering Content
**Symptom:** Unsafe content not caught
**Solution:** Enable `ENABLE_ML_FILTER`, update word lists, add context rules

### Audit Log Growing Too Large
**Symptom:** High disk usage
**Solution:** Reduce `AUDIT_LOG_RETENTION_HOURS`, decrease `AUDIT_LOG_MAX_SIZE`

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/safety-filter/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/safety-filter/README.md
git commit -m "docs: add safety-filter README"
```

---

### Task 7: Create operator-console/README.md

**Files:**
- Create: `services/operator-console/README.md`

**Step 1: Write the README content**

```markdown
# Operator Console

Central monitoring and control dashboard for all Project Chimera services with real-time WebSocket updates.

## Overview

The Operator Console provides human oversight and control:
- Real-time service status monitoring (all 8 services)
- WebSocket-based live metrics streaming
- Alert management with thresholds
- Service control (start/stop/restart)
- Integrated web dashboard at `/static/dashboard.html`
- Prometheus metrics aggregation

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Access to all Chimera services (ports 8000-8006)

# Local development setup
cd services/operator-console
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your service URLs

# Run service
uvicorn main:app --reload --port 8007

# Access dashboard
# Open http://localhost:8007 in browser
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `operator-console` | Service identifier |
| `PORT` | `8007` | HTTP server port |
| `OPENCLAW_ORCHESTRATOR_URL` | `http://localhost:8000` | Orchestrator URL |
| `SCENESPEAK_AGENT_URL` | `http://localhost:8001` | SceneSpeak URL |
| `CAPTIONING_AGENT_URL` | `http://localhost:8002` | Captioning URL |
| `BSL_AGENT_URL` | `http://localhost:8003` | BSL URL |
| `SENTIMENT_AGENT_URL` | `http://localhost:8004` | Sentiment URL |
| `LIGHTING_SOUND_MUSIC_URL` | `http://localhost:8005` | Lighting URL |
| `SAFETY_FILTER_URL` | `http://localhost:8006` | Safety URL |
| `METRICS_POLL_INTERVAL` | `5.0` | Metrics poll interval (seconds) |
| `ALERT_CPU_THRESHOLD` | `80.0` | CPU warning threshold (%) |
| `ALERT_MEMORY_THRESHOLD` | `2000.0` | Memory warning threshold (MB) |
| `ALERT_ERROR_RATE_THRESHOLD` | `0.05` | Error rate warning threshold |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks all services)
- `GET /metrics` - Prometheus metrics

### Dashboard
- `GET /` - Redirect to web dashboard
- `GET /static/dashboard.html` - Web dashboard UI

### Service Status
- `GET /api/services` - List all services with status
- `GET /api/metrics` - Get current metrics from all services

### Alerts
- `GET /api/alerts` - Get all active alerts
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert

### Service Control
- `POST /api/control/{service_name}` - Control service (start/stop/restart)

### WebSocket
- `WS /ws` - Real-time updates WebSocket

**Example: Get service status**
```bash
curl http://localhost:8007/api/services
```

**Example: Control service**
```bash
curl -X POST http://localhost:8007/api/control/scenespeak-agent \
  -H "Content-Type: application/json" \
  -d '{"action": "restart", "reason": "Performance degradation"}'
```

## Dashboard Features

The web dashboard at `http://localhost:8007` provides:

1. **Service Status Panel** - 8 service cards with health indicators
2. **Alerts Console** - Real-time alert feed with acknowledge action
3. **Control Panel** - Start/stop/restart controls for all services
4. **Metrics Charts** - CPU, Memory, Request Rate, Error Rate sparklines
5. **Event Feed** - Scrolling log of system events
6. **WebSocket Connection** - Auto-reconnecting real-time updates

## Development

### Code Structure
```
operator-console/
├── main.py              # FastAPI application
├── metrics_collector.py # Metrics polling from services
├── alert_manager.py     # Alert threshold management
├── websocket_manager.py # WebSocket broadcast handler
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
├── static/             # Web dashboard files
│   ├── dashboard.html  # Dashboard UI
│   └── dashboard.js    # Dashboard JavaScript
└── tests/              # Test suite
```

### Adding Features
1. Add new metrics in `metrics_collector.py`
2. Implement new alert types in `alert_manager.py`
3. Update dashboard UI in `static/dashboard.html`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_websocket.py -v
```

## Troubleshooting

### Services Showing as Down
**Symptom:** Service cards show red/offline status
**Solution:** Check service URLs in `.env`, verify services are running

### WebSocket Not Connecting
**Symptom:** Dashboard shows "Disconnected"
**Solution:** Check browser console, verify `/ws` endpoint accessible

### Alerts Not Firing
**Symptom:** Thresholds exceeded but no alerts
**Solution:** Adjust `ALERT_*_THRESHOLD` values in `.env`, check metrics collection

### Dashboard Not Loading
**Symptom:** 404 on dashboard URL
**Solution:** Verify `static/` directory exists, check Dockerfile COPY command

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
```

**Step 2: Verify file was created**

Run: `ls -la services/operator-console/README.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add services/operator-console/README.md
git commit -m "docs: add operator-console README"
```

---

## Phase 2: Dashboard Documentation

### Task 8: Create docs/guides/operator-console-dashboard.md

**Files:**
- Create: `docs/guides/operator-console-dashboard.md`

**Step 1: Write the guide content**

```markdown
# Operator Console Dashboard Guide

**Version:** v0.5.0
**Last Updated:** March 6, 2026

---

## Dashboard Overview

The Operator Console Dashboard is a single-page web application that provides real-time monitoring and control of all Project Chimera services. Accessible at `http://localhost:8007`, the dashboard offers:

- Live service status monitoring
- Real-time metrics visualization
- Alert management and acknowledgment
- Service control capabilities
- WebSocket-based auto-updating UI

---

## Accessing the Dashboard

### Local Development

1. Start the operator-console service:
   ```bash
   cd services/operator-console
   uvicorn main:app --reload --port 8007
   ```

2. Open your browser to: `http://localhost:8007`

### Docker Deployment

1. Ensure operator-console container is running:
   ```bash
   docker ps | grep operator-console
   ```

2. Access dashboard at: `http://localhost:8007`

### Authentication

Currently, no authentication is required (development mode). Production deployments should implement authentication via reverse proxy.

---

## Dashboard Sections

### 1. Header Section

The top header displays:
- **Project Chimera** branding
- **Operator Console** title
- **Connection Status** indicator:
  - 🟢 Green: Connected (receiving real-time updates)
  - 🔴 Red: Disconnected (will auto-reconnect)
- **Current Time** (updates every second)

### 2. Service Status Panel

Displays 8 service cards (one per Chimera service):

**Services Monitored:**
- OpenClaw Orchestrator (port 8000)
- SceneSpeak Agent (port 8001)
- Captioning Agent (port 8002)
- BSL Agent (port 8003)
- Sentiment Agent (port 8004)
- Lighting-Sound-Music (port 8005)
- Safety Filter (port 8006)
- Operator Console (port 8007)

**Each Card Shows:**
- Service name with icon
- Health status indicator:
  - 🟢 **Online**: Service responding and healthy
  - 🟡 **Degraded**: Service up but performance issues detected
  - 🔴 **Offline**: Service not responding
- Current metrics (CPU %, Memory MB)
- Last update timestamp
- Quick action buttons (Logs, Restart)

### 3. Alerts Console

Displays active alerts requiring attention:

**Alert Severity Levels:**
- 🔴 **Critical**: Service down or critical failure - Immediate action required
- 🟡 **Warning**: Degraded performance or concerning metric - Monitor closely
- 🔵 **Info**: Informational event - No action required

**Alert Card Shows:**
- Severity color-coding (left border)
- Alert title and message
- Source service
- Timestamp
- Acknowledge button (click to dismiss)

**Alert Actions:**
- Click **Acknowledge** to dismiss alert
- Filter by severity using the filter controls
- Auto-refreshes via WebSocket

### 4. Control Panel

Provides bulk service control actions:

**Control Buttons:**
- **Start All Services** - Start all stopped services
- **Stop All Services** - Stop all running services
- **Restart Degraded** - Restart only degraded services
- **Refresh Status** - Force immediate status refresh

**Confirmation Dialog:**
- Control actions require confirmation
- Dialog shows action and affected services
- Click **Confirm** to execute, **Cancel** to abort

### 5. Metrics Charts

Four real-time sparkline charts display system metrics:

**Chart Types:**
1. **CPU Usage (%)** - CPU percentage across all services
2. **Memory Usage (MB)** - Memory consumption in megabytes
3. **Request Rate (req/s)** - Requests per second per service
4. **Error Rate (%)** - Error rate percentage

**Chart Features:**
- Live updates via WebSocket (every 5 seconds)
- Scroll back shows last 5 minutes of data
- Hover for exact values at data points
- Color-coded lines per service

### 6. Event Feed

Scrolling log of system events at the bottom of the dashboard:

**Event Types:**
- Service status changes (up/down/degraded)
- Alerts triggered/acknowledged
- Control actions executed
- Threshold violations

**Event Display:**
- Timestamp (HH:MM:SS format)
- Event message
- Color-coded by type (green=info, yellow=warning, red=error)

**Feed Controls:**
- Auto-scroll toggle (default: on)
- Export to clipboard button
- Max 100 events displayed (older events auto-removed)

---

## WebSocket Connection

### Connection Behavior

The dashboard uses WebSocket (`/ws` endpoint) for real-time updates:

**Connection Flow:**
1. Dashboard opens WebSocket connection on load
2. Sends subscription message for all channels
3. Receives continuous updates for:
   - Service status changes
   - Metrics updates
   - New alerts
   - Control action results

**Auto-Reconnect:**
- If connection drops, dashboard automatically reconnects
- Exponential backoff: 1s, 2s, 4s, 8s, 15s (max)
- Connection status indicator shows current state

**WebSocket Message Types:**
```javascript
// Metric update
{
  "type": "metric",
  "service": "scenespeak-agent",
  "metric": "cpu_percent",
  "value": 45.2
}

// Alert update
{
  "type": "alert",
  "id": "alert_abc123",
  "severity": "warning",
  "title": "High CPU Usage",
  "message": "CPU exceeded 80%"
}

// Status update
{
  "type": "status",
  "service": "sentiment-agent",
  "status": "degraded"
}
```

---

## Troubleshooting

### Dashboard Won't Load

**Problem:** Browser shows "Unable to connect" or 404 error

**Solutions:**
1. Verify operator-console service is running:
   ```bash
   curl http://localhost:8007/health/live
   ```
2. Check static files exist:
   ```bash
   ls -la services/operator-console/static/
   ```
3. Verify port 8007 is not in use by another service
4. Check browser console for JavaScript errors

### Services Showing as Offline

**Problem:** All service cards show red/offline status

**Solutions:**
1. Verify services are running:
   ```bash
   docker ps | grep -E "8000|8001|8002|8003|8004|8005|8006"
   ```
2. Check `.env` file has correct service URLs
3. Test individual service health:
   ```bash
   curl http://localhost:8000/health/live
   curl http://localhost:8001/health/live
   # ... etc
   ```

### WebSocket Not Connecting

**Problem:** Connection status shows "Disconnected"

**Solutions:**
1. Check browser console for WebSocket errors
2. Verify WebSocket endpoint is accessible:
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8007/ws
   ```
3. Check firewall/proxy settings (may block WebSocket)
4. Try accessing dashboard from different browser

### Metrics Not Updating

**Problem:** Charts show stale data, no new values

**Solutions:**
1. Check metrics poll interval in `.env` (`METRICS_POLL_INTERVAL`)
2. Verify services are exposing `/metrics` endpoints
3. Check browser console for WebSocket messages
4. Force refresh using **Refresh Status** button

### Alerts Not Firing

**Problem:** Metrics exceed thresholds but no alerts appear

**Solutions:**
1. Verify alert thresholds in `.env`:
   - `ALERT_CPU_THRESHOLD`
   - `ALERT_MEMORY_THRESHOLD`
   - `ALERT_ERROR_RATE_THRESHOLD`
2. Check alert manager is initialized (see logs)
3. Test alert manually by triggering threshold condition

---

## Advanced Usage

### Custom Alert Thresholds

Edit `.env` file to adjust alert thresholds:

```bash
# CPU threshold (percentage)
ALERT_CPU_THRESHOLD=80.0

# Memory threshold (megabytes)
ALERT_MEMORY_THRESHOLD=2000.0

# Error rate threshold (0.0-1.0)
ALERT_ERROR_RATE_THRESHOLD=0.05
```

### Polling Interval Adjustment

Adjust how often metrics are collected:

```bash
# Collect metrics every 5 seconds (default)
METRICS_POLL_INTERVAL=5.0

# Collect metrics every 10 seconds (lower CPU usage)
METRICS_POLL_INTERVAL=10.0
```

### Exporting Dashboard State

Use browser DevTools to export current dashboard state:

```javascript
// In browser console
copy(JSON.stringify(window.dashboardState, null, 2))
```

---

## Related Documentation

- [Operator Console API Reference](../api/operator-console.md)
- [Monitoring Runbook](../runbooks/monitoring.md)
- [Incident Response Guide](../runbooks/incident-response.md)

---

*Dashboard Guide - Project Chimera v0.5.0 - March 6, 2026*
```

**Step 2: Verify file was created**

Run: `ls -la docs/guides/operator-console-dashboard.md`
Expected: File exists with content

**Step 3: Commit**

```bash
git add docs/guides/operator-console-dashboard.md
git commit -m "docs: add operator console dashboard guide"
```

---

### Task 9: Update docs/api/operator-console.md

**Files:**
- Modify: `docs/api/operator-console.md:1-100` (Update header and add dashboard endpoint)

**Step 1: Update version and add dashboard endpoint**

Find line 3: `**Version:** 3.0.0`
Replace with: `**Version:** 3.1.0`

Find line 21-27 (Endpoints section after "## Endpoints")
Add after "### 1. Web Dashboard":

```markdown
**Endpoint:** `GET /` or `GET /static/dashboard.html`

**Response:** HTML dashboard interface

**Description:** Single-page web dashboard with real-time service monitoring, alerts console, metrics charts, and service control panel.

**Features:**
- 8 service status cards with health indicators
- Real-time alerts console with acknowledge action
- Metrics charts (CPU, Memory, Request Rate, Error Rate)
- Control panel for start/stop/restart operations
- Event feed with system activity log
- WebSocket auto-reconnecting updates

**Access:** Open `http://localhost:8007` in browser

---
```

**Step 2: Update WebSocket endpoint documentation**

Find line 33: `**Endpoint:** `WS /ws/realtime``
Replace with: `**Endpoint:** `WS /ws``

Find line 38: `const ws = new WebSocket('ws://localhost:8007/ws/realtime');`
Replace with: `const ws = new WebSocket('ws://localhost:8007/ws');`

**Step 3: Add new API endpoints section**

After "### 5. Get Service Status" section, add:

```markdown
---

### 5.1. Get Services List

Get list of all monitored services with their status.

**Endpoint:** `GET /api/services`

**Response:**

```json
{
  "services": [
    {
      "name": "openclaw-orchestrator",
      "url": "http://localhost:8000",
      "status": "up",
      "health_check_url": "http://localhost:8000/health/live",
      "metrics_url": "http://localhost:8000/metrics"
    }
  ],
  "total": 8,
  "up": 7,
  "down": 0,
  "degraded": 1
}
```

---

### 5.2. Get All Metrics

Get current metrics from all services.

**Endpoint:** `GET /api/metrics`

**Response:**

```json
{
  "metrics": {
    "openclaw-orchestrator": {
      "service_name": "openclaw-orchestrator",
      "cpu_percent": 25.3,
      "memory_mb": 512,
      "request_rate": 45.2,
      "error_rate": 0.01
    }
  }
}
```

---

### 5.3. Control Service

Manually control a service (start, stop, restart).

**Endpoint:** `POST /api/control/{service_name}`

**Request Body:**

```json
{
  "action": "restart",
  "reason": "Performance degradation"
}
```

**Response:**

```json
{
  "service": "scenespeak-agent",
  "action": "restart",
  "status": "success",
  "message": "Service scenespeak-agent restart successful"
}
```

---
```

**Step 4: Verify changes**

Run: `head -100 docs/api/operator-console.md | grep -E "Version|/static/dashboard.html|WS /ws"`
Expected: Version 3.1.0, dashboard.html endpoint, WS /ws endpoint

**Step 5: Commit**

```bash
git add docs/api/operator-console.md
git commit -m "docs: update operator-console API docs for dashboard"
```

---

## Phase 3: TODO/FIXME Resolution

### Task 10: Resolve all TODO/FIXME markers

**Files:**
- Modify: Multiple files across `docs/`

**Step 1: Scan for all markers**

```bash
grep -rn "TODO\|FIXME\|XXX\|PLACEHOLDER" docs/ --include="*.md" > /tmp/todo-scan.txt
cat /tmp/todo-scan.txt
```

Expected: List of all 32 markers with file paths and line numbers

**Step 2: Create resolution tracking file**

```bash
cat > docs/TODO-RESOLUTION-LOG.md << 'EOF'
# TODO/FIXME Resolution Log

**Date:** March 6, 2026
**Total Markers Resolved:** 32

## Resolution Actions

### FIXME Markers (8)
1. **docs/DOCUMENTATION_AUDIT_REPORT.md:261** - Removed outdated FIXME (v0.4.0 changes already applied)
2. **docs/DOCUMENTATION_AUDIT_REPORT.md:265** - Added Prometheus metrics reference (see [Monitoring Runbook](../runbooks/monitoring.md))
3. **docs/DOCUMENTATION_AUDIT_REPORT.md:269** - Authentication flow documented in API docs
4. [Add remaining FIXME resolutions]

### TODO Markers (24)
1. **docs/architecture/README.md:160** - ADR template documented with example
2. **docs/getting-started/monday-demo/demo-script.md:116** - Component lifecycle documented in GitHub Workflow guide
3. [Add remaining TODO resolutions]

## Conversion to GitHub Issues

The following TODOs were converted to GitHub issues for future work:
- [List any items that became GitHub issues]

## Removals

The following markers were removed as obsolete or resolved:
- [List removed markers]
EOF
```

**Step 3: Process each marker**

For each marker in scan results:
- **If content exists:** Replace marker with actual content
- **If outdated:** Remove marker and stale reference
- **If future work:** Create GitHub issue, replace with link

**Priority: FIXME markers first (High), then TODO markers (Medium)**

**Step 4: Verify no markers remain**

```bash
grep -r "TODO\|FIXME\|XXX\|PLACEHOLDER" docs/ --include="*.md" | wc -l
```

Expected: 0 (all markers resolved)

**Step 5: Commit**

```bash
git add docs/
git commit -m "docs: resolve all TODO/FIXME markers (32 total)"
```

---

## Phase 4: Version Standardization

### Task 11: Update all version references to v0.5.0

**Files:**
- Modify: `README.md`, `docs/api/*.md`, `docs/services/*.md`, `docs/architecture/*.md`

**Step 1: Update main README.md version badge**

Find line 5: `![Version](https://img.shields.io/badge/version-0.4.0-blue)`
Replace with: `![Version](https://img.shields.io/badge/version-0.5.0-blue)`

Find line 285: `### v0.4.0 (Current - March 2026)`
Replace with: `### v0.5.0 (Current - March 2026)`

Find line 292: `### v0.5.0 (Planned)`
Replace with: `### v0.6.0 (Planned)`

**Step 2: Update API documentation version headers**

```bash
# Update all version: x.y.z lines in API docs
find docs/api -name "*.md" -exec sed -i 's/\*\*Version:\*\* [0-9.]+/\*\*Version:\*\* v0.5.0/g' {} \;
```

**Step 3: Update service documentation versions**

```bash
# Update version references in service docs
find docs/services -name "*.md" -exec sed -i 's/v0\.[0-9]\+\.[0-9]\+/v0.5.0/g' {} \;
```

**Step 4: Update architecture documentation**

```bash
# Update version references in architecture docs
find docs/architecture -name "*.md" -exec sed -i 's/v0\.[0-9]\+\.[0-9]\+/v0.5.0/g' {} \;
```

**Step 5: Update release notes**

Find `docs/release-notes/v0.5.0.md`
Find line with status like "Status: In Development" or similar
Replace with: `**Status:** Current Release`

**Step 6: Verify all version changes**

```bash
# Check for any remaining old version references
grep -r "v0\.4\." docs/ README.md | grep -v "v0.5.0" | wc -l
```

Expected: 0 (or only in historical context)

**Step 7: Commit**

```bash
git add README.md docs/
git commit -m "docs: standardize all version references to v0.5.0"
```

---

## Phase 5: Cross-Reference Validation

### Task 12: Verify and fix all internal links

**Files:**
- Modify: Files with broken internal links

**Step 1: Extract all internal markdown links**

```bash
# Find all []() links in docs
grep -roh '\[[^]]*\](\[[^]]*\]\|([^)]*)\)' docs/ --include="*.md" | \
  grep -E '\(.*\.md' | \
  sort -u > /tmp/internal-links.txt
cat /tmp/internal-links.txt
```

Expected: List of all internal markdown references

**Step 2: Check each target exists**

```bash
# Create link validation script
cat > /tmp/validate-links.sh << 'EOF'
#!/bin/bash
cd /home/ranj/Project_Chimera
while read -r link; do
  # Extract target from link
  target=$(echo "$link" | grep -oP '\(\K[^)]+(?=\.md)')
  if [ -n "$target" ]; then
    # Try to find the file
    if [ ! -f "docs/$target" ] && [ ! -f "$target" ]; then
      echo "BROKEN: $target"
    fi
  fi
done < /tmp/internal-links.txt
EOF

chmod +x /tmp/validate-links.sh
/tmp/validate-links.sh
```

Expected: List of broken internal links (or empty if all valid)

**Step 3: Fix broken links**

For each broken link found:
1. Determine correct target path
2. Update link in source file
3. Verify fix

**Common fixes:**
- Update relative paths (e.g., `../api/service.md` → `../../api/service.md`)
- Update renamed files (e.g., `old-name.md` → `new-name.md`)
- Remove links to deleted files

**Step 4: Verify all links fixed**

```bash
# Re-run link validation
/tmp/validate-links.sh
```

Expected: No broken links reported

**Step 5: Commit**

```bash
git add docs/
git commit -m "docs: fix all broken internal links"
```

---

## Final Steps

### Task 13: Run automated validation

**Step 1: Check for remaining TODO/FIXME**

```bash
grep -r "TODO\|FIXME\|XXX\|PLACEHOLDER" docs/ --include="*.md"
```

Expected: No output (all markers resolved)

**Step 2: Count documentation files**

```bash
find docs -name "*.md" | wc -l
```

Expected: 152+ (145 original + 7 new service READMEs + dashboard guide)

**Step 3: Verify service READMEs**

```bash
for svc in openclaw-orchestrator scenespeak-agent bsl-agent sentiment-agent lighting-sound-music safety-filter operator-console; do
  [ -f "services/$svc/README.md" ] && echo "✓ $svc" || echo "✗ $svc"
done
```

Expected: All 7 services show ✓

**Step 4: Validate markdown syntax**

```bash
# Install markdownlint if not available
# npm install -g markdownlint-cli

# Run markdownlint
markdownlint docs/ --ignore node_modules
```

Expected: No errors (or only non-critical warnings)

**Step 5: Generate final sync report**

```bash
cat > docs/sync-report-$(date +%Y-%m-%d).md << 'EOF'
# Documentation Sync Report

**Date:** March 6, 2026
**Version:** v0.5.0

## Summary

- Service READMEs created: 7/7 ✓
- Dashboard documentation: Complete ✓
- API documentation updated: Complete ✓
- TODO/FIXME markers resolved: 32/32 ✓
- Version references standardized: v0.5.0 ✓
- Internal links validated: Complete ✓

## Files Created

1. services/openclaw-orchestrator/README.md
2. services/scenespeak-agent/README.md
3. services/bsl-agent/README.md
4. services/sentiment-agent/README.md
5. services/lighting-sound-music/README.md
6. services/safety-filter/README.md
7. services/operator-console/README.md
8. docs/guides/operator-console-dashboard.md

## Files Modified

1. docs/api/operator-console.md
2. README.md (version updates)
3. Multiple files with TODO/FIXME markers
4. Multiple files with version references

## Validation Results

- Markdown syntax: Valid ✓
- Internal links: All valid ✓
- Service documentation coverage: 100% ✓

## Next Steps

- Set up automated link checking in CI
- Schedule quarterly documentation audits
- Establish documentation contribution guidelines

EOF
```

**Step 6: Final commit and push**

```bash
# Add all remaining changes
git add docs/ services/*/README.md

# Commit final validation report
git commit -m "docs: complete v0.5.0 documentation sync

- Created 7 comprehensive service READMEs
- Added Operator Console dashboard guide
- Updated API documentation with dashboard endpoints
- Resolved all 32 TODO/FIXME markers
- Standardized version references to v0.5.0
- Validated and fixed all internal links
- Generated sync report"

# Push to GitHub
git push origin main
```

---

## Success Criteria Verification

Run this final checklist:

```bash
echo "=== Documentation Update Checklist ==="
echo ""

# 1. Service READMEs
echo "1. Service READMEs:"
for svc in openclaw-orchestrator scenespeak-agent bsl-agent sentiment-agent lighting-sound-music safety-filter operator-console; do
  [ -f "services/$svc/README.md" ] && echo "  ✓ $svc/README.md" || echo "  ✗ $svc/README.md MISSING"
done
echo ""

# 2. Dashboard guide
echo "2. Dashboard documentation:"
[ -f "docs/guides/operator-console-dashboard.md" ] && echo "  ✓ Dashboard guide exists" || echo "  ✗ Dashboard guide MISSING"
echo ""

# 3. TODO/FIXME count
echo "3. TODO/FIXME markers:"
todo_count=$(grep -r "TODO\|FIXME\|XXX\|PLACEHOLDER" docs/ --include="*.md" | wc -l)
echo "  Remaining markers: $todo_count (should be 0)"
echo ""

# 4. Version consistency
echo "4. Version consistency:"
v050_count=$(grep -r "v0\.5\.0" docs/ services/*/README.md 2>/dev/null | wc -l)
echo "  v0.5.0 references: $v050_count"
echo ""

# 5. Documentation file count
echo "5. Documentation files:"
doc_count=$(find docs -name "*.md" | wc -l)
echo "  Total .md files: $doc_count"
echo ""

echo "=== Validation Complete ==="
```

Expected output: All checks pass, 0 TODO/FIXME markers, v0.5.0 references present

---

*Implementation Plan - Project Chimera v0.5.0 Documentation Sync - March 6, 2026*

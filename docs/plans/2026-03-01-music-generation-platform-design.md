# Music Generation Platform - Design Document

**Date:** 2026-03-01
**Status:** Approved
**Author:** Claude + User Collaboration

## Overview

A dual-service AI music generation platform integrated into Project Chimera, supporting both social media content creation and live show underscore with adaptive real-time modulation based on audience sentiment.

## Goal

Enable Project Chimera to generate original music locally via AI for social media content and live theatrical performances, running entirely on the NVIDIA DGX Spark cluster without external API costs.

## Architecture

### Multi-Tier Orchestration Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CHIMERA MUSIC PLATFORM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────────────────────────────┐ │
│  │ CALLING SERVICES│    │        MUSIC ORCHESTRATION SERVICE       │ │
│  ├─────────────────┤    │ (Port 8012)                              │ │
│  │ • SceneSpeak    │───▶│ • Request Router & Validator             │ │
│  │ • Operator Con. │    │ • Cache Manager (Redis exact-match)      │ │
│  │ • Social Media  │    │ • Approval Pipeline (Staged)             │ │
│  │ • CI/CD Gateway │    │ • Sentiment Adapter (live modulation)    │ │
│  └─────────────────┘    │ • Metadata Store (PostgreSQL)            │ │
│                         └──────────────┬──────────────────────────┘ │
│                                        │                             │
│                         ┌──────────────▼──────────────────────────┐ │
│                         │        MUSIC GENERATION SERVICE          │ │
│                         │ (Port 8011)                              │ │
│                         │ • Model Pool Manager                     │ │
│                         │   - Meta MusicGen-Small (marketing)      │ │
│                         │   - ACE-Step (show underscore)           │ │
│                         │ • Inference Engine                       │ │
│                         │ • Audio Processor (format conversion)     │ │
│                         └──────────────┬──────────────────────────┘ │
│                                        │                             │
│                         ┌──────────────▼──────────────────────────┐ │
│                         │              STORAGE LAYER                │ │
│                         │ • MinIO/S3 (audio files)                 │ │
│                         │ • PostgreSQL (metadata: prompts, tags)    │ │
│                         │ • Redis (cache, session state)           │ │
│                         └──────────────────────────────────────────┘ │
│
└─────────────────────────────────────────────────────────────────────┘
```

### Service Split

| Service | Port | Responsibility | State |
|---------|------|-----------------|-------|
| **Music Generation** | 8011 | Model inference, raw audio output | Stateless, GPU-bound |
| **Music Orchestration** | 8012 | Caching, approval workflow, adaptive show integration | Stateful, CPU-bound |

## Technology Stack

- **Models**: Meta MusicGen-Small (~2GB VRAM), ACE-Step (<4GB VRAM)
- **Storage**: MinIO (audio files), PostgreSQL (metadata), Redis (cache/pub/sub)
- **Communication**: REST API + WebSocket (real-time progress)
- **Deployment**: k3s on NVIDIA DGX Spark GB10-Arm64
- **Monitoring**: Prometheus metrics, Grafana dashboards

## Components

### Music Generation Service (Port 8011)

**ModelPoolManager**: Manages multiple AI music models with lazy loading
- `load_model(model_name: str) -> Model`
- `unload_model(model_name: str)`
- `estimate_vram_usage() -> dict[str, int]`

**InferenceEngine**: Runs generation on loaded models, thread-safe
- `generate(prompt: str, params: GenerationParams) -> AudioResult`
- `generate_batch(requests: list) -> list[AudioResult]`
- `cancel_generation(request_id: str)`

**AudioProcessor**: Post-processing (format, normalization, trimming)
- `normalize(audio: bytes) -> bytes`
- `convert_format(audio: bytes, format: str) -> bytes`
- `trim_silence(audio: bytes, threshold_db: float) -> bytes`

### Music Orchestration Service (Port 8012)

**RequestRouter**: Validates requests, checks auth, routes to cache or generation
- `route(request: MusicRequest) -> MusicResponse`
- `authenticate(token: str) -> UserContext`
- `select_model(use_case: UseCase) -> str`

**CacheManager**: Redis-based exact-match caching with TTL
- Key: `SHA256(prompt + params_hash)`
- TTL: 7 days
- `get(cache_key: str) -> CachedAudio | None`
- `set(cache_key: str, audio: CachedAudio, ttl: int)`

**ApprovalPipeline**: Staged approval workflow
- Marketing: Auto-approve
- Show: Manual approval via Operator Console
- `submit_for_approval(audio_id: str, context: ApprovalContext)`
- `approve(audio_id: str, user: str)`

**SentimentAdapter**: Live show integration for adaptive music
- `on_sentiment_update(sentiment: SentimentScore)`
- `modulate_track(audio_id: str, modulation: ModulationParams) -> AudioStream`

**MusicWebSocket**: Real-time progress streaming (Quality Platform pattern)
- `subscribe(run_id: str)`
- `publish_progress(run_id: str, progress: GenerationProgress)`

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| `SOCIAL_MEDIA_USER` | Generate, auto-approve marketing content |
| `SHOW_OPERATOR` | Generate, approve show content |
| `DEVELOPER` | Full access, model management |
| `ADMIN` | All permissions |

## Data Flow

### Flow 1: Social Media Clip (Cache Hit - Fast Path)
```
SceneSpeak → Orchestration → Cache Hit → Return MinIO URL (~50ms)
```

### Flow 2: New Show Music (Cache Miss - Approval Path)
```
Operator Console → Orchestration → Generation Service
  → MinIO Upload → Approval Queue → Operator Approval → Show Ready
  (~30-45s generation + human review)
```

### Flow 3: Live Show Modulation (Adaptive)
```
Sentiment Analysis → Orchestration → Modulate cached track
  → Show Output (<100ms real-time)
```

## Data Models

### PostgreSQL Schema

```sql
CREATE TABLE music_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    use_case VARCHAR(20) NOT NULL CHECK (use_case IN ('marketing', 'show')),
    model_name VARCHAR(50) NOT NULL,
    minio_key TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approval_status VARCHAR(20),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cache_hit_count INTEGER DEFAULT 0
);

CREATE TABLE music_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    music_id UUID NOT NULL REFERENCES music_generations(id),
    action VARCHAR(20) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Redis Structure

```
music:cache:{hash} → Cached audio metadata (TTL: 7 days)
music:progress:{request_id} → Generation progress (TTL: 1 hour)
music:modulation:{scene_id} → Active modulation state (TTL: 2 hours)
```

### MinIO Structure

```
chimeramusic/
├── marketing/
│   ├── social/          # Short clips for social media
│   └── promotional/     # Longer promo content
├── show/
│   ├── underscore/      # Background/scene music
│   ├── transitions/     # Scene transition stings
│   └── approved/        # Final approved show music
└── previews/            # Low-quality previews for approval
```

## API Interface

### Generate Music
```http
POST /api/v1/music/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "upbeat electronic for celebration",
  "use_case": "marketing",
  "duration_seconds": 30,
  "genre": "electronic",      // optional
  "mood": "upbeat",           // optional
  "tempo": 120                // optional
}
```

### Response
```json
{
  "request_id": "uuid",
  "music_id": "uuid",
  "status": "cached",
  "audio_url": "https://minio...",
  "duration_seconds": 30,
  "was_cache_hit": true
}
```

### WebSocket Progress
```json
{
  "type": "progress",
  "request_id": "uuid",
  "progress": 45,
  "stage": "inference",
  "eta_seconds": 15
}
```

## Error Handling

| Status Code | Type | Description |
|-------------|------|-------------|
| 400 | `invalid_request` | Bad prompt, invalid parameters |
| 401 | `unauthorized` | Missing/invalid token |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not_found` | Music ID not found |
| 409 | `approval_required` | Show music not approved |
| 429 | `rate_limited` | Quota exceeded |
| 500 | `generation_failed` | Model inference error |
| 503 | `service_unavailable` | Model loading, no capacity |
| 504 | `timeout` | Generation exceeded limit |

### Circuit Breaker
- Opens after 5 consecutive failures per model
- Routes to alternative model when open
- Auto-recovers after 60 seconds

### Graceful Degradation
1. Return cached version if available
2. Route to alternative model
3. Return error with helpful message

## Security

- **Authentication**: JWT-based service tokens
- **Authorization**: Role-based permissions
- **Input Validation**: Prompt length limits, blocked patterns, SQL injection prevention
- **Model Security**: Signature verification before loading
- **Rate Limiting**: Per-role limits via Redis
- **Audit Logging**: All actions logged to `music_audit_log` table
- **Network Policies**: Kubernetes NetworkPolicy for service-to-service traffic

## Testing

### Coverage Target: >95%

- **Unit Tests**: Component isolation, mock external dependencies
- **Integration Tests**: Service interactions, database operations
- **Property-Based Tests**: Hypothesis for invariant validation
- **Load Tests**: Locust for concurrency testing
- **Model Tests**: Output quality, duration accuracy, modulation quality

### Quality Gates
- Minimum 95% code coverage
- Maximum 2% mutation survival
- All test suites required before merge

## Deployment

### Resource Allocation

**Current (Single Node - 128GB RAM, 1x GPU):**
- Music Generation: 1 replica, 1 GPU, 16GB RAM
- Music Orchestration: 3 replicas, 512MB RAM each
- Total: ~17.5GB

**With Second Node (256GB RAM, 2x GPU):**
- Music Generation: 2 replicas, 1 GPU each, 16GB RAM
- Music Orchestration: 3 replicas, 512MB RAM each
- Total: ~33.5GB (222GB remaining for other services)

### Health Checks
- Liveness: `/health` - Service alive
- Readiness: `/ready` - Database, Redis, MinIO, models loaded
- Startup: 30 second initial delay for model loading

### Monitoring
- Request rate, latency, error rate
- Cache hit rate
- VRAM usage per model
- Approval queue depth
- Active generations

## Integration Points

- **SceneSpeak**: Request scene-specific background music
- **Operator Console**: Approval workflow, preview playback
- **Sentiment Analysis**: Real-time modulation triggers
- **CI/CD Gateway**: Webhook-based test generation
- **Quality Platform**: Test orchestration and reporting

## Success Criteria

1. Social media clips generated in < 100ms (cache) or < 60s (generation)
2. Show underscore generated in < 45s, approved via console
3. Live modulation latency < 100ms
4. 95%+ test coverage maintained
5. Zero external API dependencies
6. Fits within single-node resource allocation

## Timeline

- **Week 1**: Core generation service (MusicGen integration)
- **Week 2**: Orchestration service (caching, RBAC)
- **Week 3**: Approval pipeline, Operator Console integration
- **Week 4**: ACE-Step integration, show modulation
- **Week 5**: Testing, documentation, deployment

## Definition of Done

- [ ] Both services deployed and operational
- [ ] All tests passing with >95% coverage
- [ ] Quality Platform gates passing
- [ ] Documentation complete (API, deployment, operations)
- [ ] Integration with SceneSpeak, Operator Console, Sentiment Analysis
- [ ] Load tested to target metrics
- [ ] Security audit passed
- [ ] Committed to git, tagged release

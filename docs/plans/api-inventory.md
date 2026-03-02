# API Inventory: Lighting, Sound and Music Integration Services

**Date:** 2026-03-02
**Project:** Project Chimera - Lighting, Sound and Music Integration
**Purpose:** Document existing API endpoints from three services before merging into unified service

---

## Summary

This document catalogs all existing API endpoints across the three services that will be integrated into the unified Lighting, Sound and Music (LSM) service:

1. **Lighting Control Service** (Port 8005) - 29 endpoints
2. **Music Generation Service** (Port 8011) - 2 endpoints
3. **Music Orchestration Service** (Port 8012) - 4 endpoints

**Total: 35 endpoints**

---

## 1. Lighting Control Service (Port 8005)

Base URL: `http://localhost:8005`

### Health Check Endpoints (6 endpoints)

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/health` | Liveness probe | `{"status": "healthy"}` |
| GET | `/health/live` | Alternative liveness endpoint | `{"status": "healthy"}` |
| GET | `/health/ready` | Readiness probe with connection status | Connection status for sACN and OSC |
| GET | `/health/health` | Detailed health check | Full health status with subsystem info |
| GET | `/health/health/detailed` | Comprehensive health information | All subsystems status (sACN, OSC, fixtures, presets, cues) |
| GET | `/` | Root endpoint with service info | Service name, version, endpoint list |

### Lighting Control Endpoints (6 endpoints)

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| POST | `/v1/lighting/set` | Set lighting values via sACN | `LightingRequest` (universe, channels, fade_time) |
| POST | `/v1/lighting/fixture/{fixture_id}` | Set values for specific fixture | `fixture_id`, `channel_values`, `intensity` |
| GET | `/v1/lighting/state` | Get current lighting system state | Returns all fixtures, active preset/cue, connection status |
| POST | `/v1/lighting/blackout` | Blackout all lighting | Immediate blackout of all channels |
| POST | `/v1/lighting/channel/{channel}` | Set single DMX channel | `channel` (1-512), `value` (0-255) |
| POST | `/v1/osc/send` | Send OSC message | `OSCMessageRequest` (address, arguments, host, port) |

### Cue Management Endpoints (8 endpoints)

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| POST | `/v1/cues/execute` | Execute a lighting cue | `CueRequest` (cue_number, preset_name, fade_time, etc.) |
| POST | `/v1/cues/{cue_list}/go` | Execute next/specified cue in list | `cue_list` (default: "main"), `cue_number` (default: "next") |
| POST | `/v1/cues/{cue_list}/stop` | Stop cue executions in list | `cue_list` (or "all" for all lists) |
| GET | `/v1/cues/{cue_list}` | Get all cues in a cue list | `cue_list` (default: "main") |
| GET | `/v1/cues/{cue_list}/{cue_number}` | Get specific cue definition | `cue_list`, `cue_number` |
| GET | `/v1/cues/statistics` | Get cue execution statistics | Execution stats, cue list info |
| POST | `/v1/cues/lists` | Create a new cue list | `name` |
| GET | `/v1/cues/lists` | List all cue lists | Returns list of cue list names |

### Preset Management Endpoints (9 endpoints)

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/v1/presets` | List all available presets | Returns preset metadata and active preset |
| GET | `/v1/presets/{name}` | Get specific preset details | `name` |
| POST | `/v1/presets` | Create new lighting preset | `PresetRequest` (name, values, fixtures, fade_time, description) |
| PUT | `/v1/presets/{name}` | Update existing preset | `name`, `PresetRequest` |
| DELETE | `/v1/presets/{name}` | Delete a preset | `name` |
| POST | `/v1/presets/{name}/recall` | Recall (apply) a preset | `name`, optional `fade_time` override |
| POST | `/v1/presets/save` | Save current state as preset | `name`, `fade_time`, `description` |
| POST | `/v1/presets/import` | Import presets from dictionary | Preset data dictionary |
| GET | `/v1/presets/export` | Export all presets | All preset data |

### Additional Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Prometheus metrics endpoint |
| GET | `/info` | Detailed service configuration information |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |

---

## 2. Music Generation Service (Port 8011)

Base URL: `http://localhost:8011`

### Core Endpoints (2 endpoints)

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/health` | Health check endpoint | Returns status, service name, models loaded |
| POST | `/api/v1/generate` | Generate music with specified model | `GenerateRequest` (model_name, prompt, duration_seconds, format, sample_rate) |

### Request/Response Models

**GenerateRequest:**
- `model_name`: str - Name of the model to use
- `prompt`: str - Text prompt for generation
- `duration_seconds`: int - Duration in seconds (default: 30)
- `format`: str - Audio format (default: "wav")
- `sample_rate`: int - Sample rate (default: 44100)

**GenerateResponse:**
- `request_id`: str - Unique request identifier
- `status`: str - Generation status
- `audio_url`: str | None - URL to generated audio
- `duration_seconds`: int - Actual duration

---

## 3. Music Orchestration Service (Port 8012)

Base URL: `http://localhost:8012`

### Core Endpoints (4 endpoints)

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/health` | Health check endpoint | Returns status and service name |
| GET | `/ready` | Readiness check | Cache, router, and auth status |
| POST | `/api/v1/music/generate` | Generate music with caching and approval | `MusicRequest`, requires Bearer token |
| WS | `/ws/music/{request_id}` | WebSocket for real-time progress updates | `request_id` path parameter |

### Authentication

All non-health endpoints require Bearer token authentication:
```
Authorization: Bearer <token>
```

### Request/Response Models

**MusicRequest:**
- `duration_seconds`: int
- `format`: str
- Additional orchestration parameters

**MusicResponse:**
- `request_id`: str
- `music_id`: str | None
- `status`: str
- `audio_url`: str | None
- `duration_seconds`: int
- `format`: str
- `was_cache_hit`: bool

**UserContext:**
- `service_name`: str
- `role`: Role enum (ADMIN, etc.)
- `permissions`: List[str]

---

## Integration Considerations

### Endpoint Conflicts
- No direct path conflicts between services
- Health endpoints follow similar patterns but are on different ports
- Both music services have generate endpoints but different paths

### Common Patterns

**Health Checks:**
- All services have `/health` endpoint
- Lighting Control has most comprehensive health checking
- Music Orchestration includes readiness checks

**Versioning:**
- Lighting Control uses `/v1/` prefix for all operational endpoints
- Music services use `/api/v1/` prefix
- Standardized to `/api/v1/` recommended for unified service

**Response Models:**
- All services use Pydantic models
- Consistent response patterns (status, timing, affected resources)
- Async/await pattern used throughout

### Authentication
- Lighting Control: No authentication
- Music Generation: No authentication
- Music Orchestration: Bearer token authentication required
- **Decision needed**: Authentication strategy for unified service

### WebSocket Support
- Only Music Orchestration has WebSocket support for real-time updates
- **Consideration**: May be useful for lighting status updates in unified service

---

## Data Models Reference

### Lighting Control Models

**LightingRequest:**
- `universe`: int
- `values`: Dict[int, int]
- `fade_time`: float

**LightingResponse:**
- `status`: str
- `affected_fixtures`: List[str]
- `timing`: Dict[str, float]
- `universe`: int
- `channels_updated`: int

**CueRequest:**
- `cue_number`: str
- `cue_list`: str
- `preset_name`: str | None
- `values`: Dict[str, Any] | None
- `fade_time`: float
- `delay_secs`: float
- `follow_on`: bool
- `description`: str

**PresetRequest:**
- `name`: str
- `values`: Dict[str, Any]
- `fixtures`: List[str]
- `fade_time`: float
- `description`: str

### Music Generation Models

**GenerateRequest:** (see above)
**GenerateResponse:** (see above)

### Music Orchestration Models

**MusicRequest:**
- Duration and format parameters
- Orchestration-specific fields

**MusicResponse:** (see above)
**UserContext:** (see above)

---

## Next Steps for Integration

1. **Standardize API versioning** to `/api/v1/`
2. **Define authentication strategy** for unified service
3. **Plan WebSocket support** for real-time lighting status
4. **Create unified response models** maintaining backward compatibility
5. **Design unified health check** combining all subsystems
6. **Plan endpoint deprecation** strategy for old endpoints

---

## Appendix: Service Configuration

### Lighting Control
- **Port:** 8005
- **Protocol:** HTTP/REST
- **Protocols:** sACN (streaming ACN), OSC (Open Sound Control)
- **Documentation:** Swagger UI at `/docs`, ReDoc at `/redoc`
- **Metrics:** Prometheus at `/metrics`

### Music Generation
- **Port:** 8011
- **Protocol:** HTTP/REST
- **Audio Processing:** WAV format, 44.1kHz default
- **Model Management:** Dynamic model loading via ModelPoolManager

### Music Orchestration
- **Port:** 8012
- **Protocol:** HTTP/REST + WebSocket
- **Authentication:** Bearer token
- **Features:** Caching, approval pipeline, permission checking
- **Real-time:** WebSocket for progress updates

---

*Document generated as part of Task 1: Document Current API Endpoints for Lighting, Sound and Music Integration project.*

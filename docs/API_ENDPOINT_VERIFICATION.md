# Project Chimera - API Endpoint Verification Report

**Date:** 2026-02-28
**Type:** Documentation Audit
**Status:** ⚠️ DOCUMENTATION NEEDS UPDATES

---

## Summary

This document verifies the actual API endpoints against the documented endpoints in `docs/API.md`. The actual code was inspected to determine the correct endpoints.

---

## Service-by-Service Analysis

### 1. OpenClaw Orchestrator (Port 8000)

**Actual Endpoints:**
- `POST /v1/orchestrate` - Execute orchestration through skills
- `GET /skills` - List available skills
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/orchestrate` ❌ MISMATCH
- `GET /api/v1/skills` ❌ MISMATCH

**Correction:** The routes are mounted with `prefix="/v1"` and the router is included without additional prefix, so the endpoints are `/v1/orchestrate`, not `/api/v1/orchestrate`.

**Files:**
- `services/openclaw-orchestrator/src/routes/orchestration.py` - Line 11: `router = APIRouter(prefix="/v1")`
- `services/openclaw-orchestrator/src/main.py` - Line 50: `app.include_router(orchestration.router)`

---

### 2. SceneSpeak Agent (Port 8001)

**Actual Endpoints:**
- `POST /v1/generate` - Generate dialogue
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/dialogue/generate` ❌ MISMATCH

**Correction:** The routes are mounted with `prefix="/v1"` and included without additional prefix, so the endpoint is `/v1/generate`, not `/api/v1/dialogue/generate`.

**Files:**
- `services/scenespeak-agent/src/routes/generation.py` - Line 11: `router = APIRouter(prefix="/v1")`
- `services/scenespeak-agent/src/main.py` - Line 47: `app.include_router(generation.router)`

---

### 3. Captioning Agent (Port 8002)

**Actual Endpoints:**
- `POST /api/v1/transcribe` - Transcribe audio
- `POST /api/v1/detect-language` - Detect language
- `WebSocket /api/v1/stream` - Real-time transcription
- `POST /api/v1/invoke` - Skill invocation
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/captioning/transcribe` ❌ MISMATCH (extra `/captioning`)
- `POST /api/v1/captioning/detect-language` ❌ MISMATCH
- `WebSocket /api/v1/captioning/stream` ❌ MISMATCH

**Correction:** The router is included with `prefix="/api/v1"`, and the routes are defined without the `/captioning` segment.

**Files:**
- `services/captioning-agent/src/routes/captioning.py` - Routes: `/transcribe`, `/detect-language`, `/stream`
- `services/captioning-agent/src/main.py` - Line 91: `app.include_router(captioning_router, prefix="/api/v1")`

---

### 4. BSL-Text2Gloss Agent (Port 8003)

**Actual Endpoints:**
- `POST /api/v1/translate` - Translate text to BSL gloss
- `POST /api/v1/translate/batch` - Batch translation
- `POST /api/v1/invoke` - Skill invocation
- `GET /api/v1/formats` - List available formats
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/gloss/translate` ❌ MISMATCH (extra `/gloss`)
- `POST /api/v1/batch` ❌ MISMATCH (should be `/translate/batch`)

**Correction:** The router is included with `prefix="/api/v1"`, and the routes are `/translate`, not `/gloss/translate`.

**Files:**
- `services/bsl-text2gloss-agent/src/routes/gloss.py` - Routes: `/translate`, `/translate/batch`
- `services/bsl-text2gloss-agent/src/main.py` - Line 42: `app.include_router(gloss_router, prefix="/api/v1")`

---

### 5. Sentiment Agent (Port 8004)

**Actual Endpoints:**
- `POST /api/v1/analyze` - Analyze sentiment of single text
- `POST /api/v1/analyze-batch` - Analyze multiple texts
- `GET /api/v1/trend` - Get sentiment trend
- `GET /api/v1/aggregate` - Get aggregated sentiment
- `GET /api/v1/emotions` - Get emotion aggregates
- `POST /api/v1/invoke` - Skill invocation
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/sentiment/analyze` ❌ MISMATCH (extra `/sentiment`)
- `POST /api/v1/sentiment/batch` ❌ MISMATCH
- `GET /api/v1/trends` ❌ MISMATCH (singular `trend`)

**Correction:** The router is included with `prefix="/api/v1"`, and routes are `/analyze`, not `/sentiment/analyze`.

**Files:**
- `services/sentiment-agent/src/routes/analysis.py` - Routes: `/analyze`, `/analyze-batch`, `/trend`
- `services/sentiment-agent/src/main.py` - Line 105: `app.include_router(analysis_router, prefix="/api/v1")`

---

### 6. Lighting Control (Port 8005)

**Actual Endpoints:**
- `POST /v1/lighting/set` - Set lighting values
- `POST /v1/lighting/fixture/{fixture_id}` - Set fixture values
- `GET /v1/lighting/state` - Get current state
- `POST /v1/lighting/blackout` - Blackout all lighting
- `POST /v1/lighting/channel/{channel}` - Set single channel
- `POST /v1/osc/send` - Send OSC message
- `GET /v1/cues/*` - Cue management endpoints
- `GET /v1/presets/*` - Preset management endpoints
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/lighting/scene` ❌ MISMATCH (actual: `/v1/lighting/set`)
- `POST /api/v1/lighting/blackout` ❌ MISMATCH (missing `/api`)
- `GET /api/v1/lighting/status` ❌ MISMATCH (actual: `/v1/lighting/state`)

**Correction:** Routes use `/v1/lighting/*` pattern without `/api` prefix.

**Files:**
- `services/lighting-control/src/routes/lighting.py` - Routes defined with `/v1/lighting/*` prefix
- `services/lighting-control/src/main.py` - Lines 61-63: Routers included without prefix (routes have `/v1` embedded)

---

### 7. Safety Filter (Port 8006)

**Actual Endpoints:**
- `POST /api/v1/check` - Check content for safety
- `POST /api/v1/check/batch` - Batch safety check
- `POST /api/v1/filter` - Filter content by replacing words
- `POST /api/v1/invoke` - Skill invocation
- `GET /api/v1/policies/*` - Policy management endpoints
- `GET /health/live` - Liveness probe
- `GET /stats` - Operational statistics
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/safety/filter` ❌ MISMATCH (extra `/safety`)
- `GET /api/v1/safety/review-queue` ❌ MISMATCH (not implemented)

**Correction:** The router is included with `prefix="/api/v1"`, and routes are `/check`, `/filter`, not `/safety/filter`.

**Files:**
- `services/safety-filter/src/routes/safety.py` - Routes: `/check`, `/check/batch`, `/filter`
- `services/safety-filter/src/main.py` - Line 109: `app.include_router(safety_router, prefix="/api/v1")`

---

### 8. Operator Console (Port 8007)

**Actual Endpoints:**
- `GET /` - Web UI dashboard
- `WebSocket /ws/events` - Real-time event stream
- `POST /v1/approve` - Submit approval decision
- `POST /v1/override` - Manual override controls
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `GET /api/v1/console/alerts` ❌ NEEDS VERIFICATION
- `GET /api/v1/console/approvals/pending` ❌ NEEDS VERIFICATION

**Note:** Operator Console routes need verification against actual implementation.

---

## Quick Reference: Correct Endpoints

| Service | Port | Key Endpoints |
|---------|------|---------------|
| OpenClaw | 8000 | `POST /v1/orchestrate`, `GET /skills` |
| SceneSpeak | 8001 | `POST /v1/generate` |
| Captioning | 8002 | `POST /api/v1/transcribe`, `WS /api/v1/stream` |
| BSL | 8003 | `POST /api/v1/translate`, `POST /api/v1/translate/batch` |
| Sentiment | 8004 | `POST /api/v1/analyze`, `POST /api/v1/analyze-batch`, `GET /api/v1/trend` |
| Lighting | 8005 | `POST /v1/lighting/set`, `GET /v1/lighting/state` |
| Safety | 8006 | `POST /api/v1/check`, `POST /api/v1/filter` |
| Console | 8007 | `GET /`, `WS /ws/events`, `POST /v1/approve` |

---

## Action Items

1. ✅ **Update `docs/API.md`** - Correct all endpoint paths to match actual implementation
2. ✅ **Update `docs/SERVICE_STATUS.md`** - Fix endpoint references
3. ✅ **Update `Student_Quick_Start.md`** - Fix curl command examples (lines 444, 456, 478)
4. ⚠️ **Consider standardizing** - Either use `/api/v1/` everywhere or `/v1/` everywhere consistently

---

## Standardization Recommendation

**Current State:**
- OpenClaw, SceneSpeak, Lighting, Console: Use `/v1/` (or no `/api` prefix)
- Captioning, BSL, Sentiment, Safety: Use `/api/v1/`

**Recommendation:** Standardize all services to use `/api/v1/` prefix for consistency. This is a more conventional API pattern.

---

*Generated: 2026-02-28*
*Project Chimera - API Documentation Audit*

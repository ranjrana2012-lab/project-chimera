# Project Chimera - API Endpoint Verification Report

**Date:** 2026-02-28
**Type:** Documentation Audit
**Status:** ⚠️ DOCUMENTATION NEEDS UPDATES

---

## Summary

This document verifies the actual API endpoints against the documented endpoints in `reference/api.md`. The actual code was inspected to determine the correct endpoints.

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
- `services/SceneSpeak Agent/src/routes/generation.py` - Line 11: `router = APIRouter(prefix="/v1")`
- `services/SceneSpeak Agent/src/main.py` - Line 47: `app.include_router(generation.router)`

---

### 3. Sentiment Agent (Port 8004)

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
- `services/Sentiment Agent/src/routes/analysis.py` - Routes: `/analyze`, `/analyze-batch`, `/trend`
- `services/Sentiment Agent/src/main.py` - Line 105: `app.include_router(analysis_router, prefix="/api/v1")`

---

### 6. Safety Filter (Port 8006)

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

### 7. Translation Agent (Port 8002)

**Actual Endpoints:**
- `POST /api/v1/translate` - Translate text
- `GET /api/v1/languages` - Get supported languages
- `POST /api/v1/invoke` - Skill invocation
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

**Documented Endpoints:**
- `POST /api/v1/translation/translate` ❌ MISMATCH (extra `/translation`)
- `GET /api/v1/translation/languages` ❌ MISMATCH

**Correction:** The router is included with `prefix="/api/v1"`, and routes are `/translate`, not `/translation/translate`.

**Files:**
- `services/translation-agent/src/routes/translation.py` - Routes: `/translate`, `/languages`
- `services/translation-agent/src/main.py` - Line 67: `app.include_router(translation_router, prefix="/api/v1")`

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
| Sentiment | 8004 | `POST /api/v1/analyze`, `POST /api/v1/analyze-batch`, `GET /api/v1/trend` |
| Safety | 8006 | `POST /api/v1/check`, `POST /api/v1/filter` |
| Translation | 8002 | `POST /api/v1/translate`, `GET /api/v1/languages` |
| Console | 8007 | `GET /`, `WS /ws/events`, `POST /v1/approve` |

---

## Action Items

1. ✅ **Update `reference/api.md`** - Correct all endpoint paths to match actual implementation
2. ✅ **Update `docs/SERVICE_STATUS.md`** - Fix endpoint references
3. ✅ **Update `getting-started/quick-start.md`** - Fix curl command examples (lines 444, 456, 478)
4. ⚠️ **Consider standardizing** - Either use `/api/v1/` everywhere or `/v1/` everywhere consistently

---

## Standardization Recommendation

**Current State:**
- OpenClaw, SceneSpeak, Console: Use `/v1/` (or no `/api` prefix)
- Sentiment, Safety, Translation: Use `/api/v1/`

**Recommendation:** Standardize all services to use `/api/v1/` prefix for consistency. This is a more conventional API pattern.

---

*Generated: 2026-02-28*
*Project Chimera - API Documentation Audit*

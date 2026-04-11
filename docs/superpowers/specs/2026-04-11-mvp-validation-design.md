# Ralph Loop Iteration 30 - MVP Validation & Documentation Refresh

> **Date:** 2026-04-11
> **Status:** Approved Design
> **Iteration:** 30
> **Objective:** Validate 8-service MVP architecture and refresh all GitHub documentation

---

## Executive Summary

**Problem:** Project Chimera has undergone significant architectural changes (emergency MVP rescue slice), but GitHub documentation reflects the old 14-service architecture and includes fictional dependencies.

**Solution:** Ralph Loop Iteration 30 - comprehensive validation of the new 8-service MVP using TDD integration tests, followed by complete documentation overhaul to accurately reflect current state.

**Approach:** Test-then-document per service - validate each service with integration tests, then document what's been verified working.

**Timeline:** ~5 hours total

---

## 1. Scope

### In Scope
- **Testing:** Integration tests for 8 services in `docker-compose.mvp.yml`
- **Documentation:** Complete refresh of README.md and docs/ directory
- **Ralph Loop:** Iteration 30 baseline establishment

### Out of Scope
- New feature development
- Architectural changes beyond validation fixes
- E2E Playwright UI tests (deferred due to complexity/time)
- K8s/Kubernetes configuration

---

## 2. MVP Architecture (8 Services)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Project Chimera MVP                          │
├─────────────────────────────────────────────────────────────────┤
│  Port  Service              Purpose                              │
│  ─────  ────────────────  ────────────                        │
│  8000  openclaw-orchestrator  Main request router               │
│  8001  scenespeak-agent       LLM dialogue (GLM 4.7)           │
│  8004  sentiment-agent        DistilBERT classification          │
│  8005  safety-filter          Content moderation               │
│  8006  translation-agent     Mock translation                │
│  8007  operator-console       Web UI                          │
│  8008  hardware-bridge        DMX mock lighting                │
│  6379  redis                  State/cache                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Testing Strategy

### 3.1 Test Structure

```
tests/integration/mvp/
├── conftest.py                    # Shared fixtures
├── test_docker_compose.py        # Stack validation
├── test_orchestrator_flow.py      # Main synchronous flow
├── test_scenespeak_agent.py       # LLM + GLM 4.7
├── test_sentiment_agent.py        # DistilBERT
├── test_safety_filter.py          # Content moderation
├── test_translation_agent.py     # Mock translation
├── test_hardware_bridge.py        # DMX output
└── test_operator_console.py       # UI health
```

### 3.2 Test Coverage Targets

| Service | Coverage | Focus |
|---------|----------|-------|
| openclaw-orchestrator | 95%+ | Synchronous flow, agent routing |
| scenespeak-agent | 90%+ | GLM API, fallback logic |
| sentiment-agent | 85%+ | Model accuracy, real-time updates |
| safety-filter | 90%+ | Filter rules, caching |
| translation-agent | 80%+ | Mock accuracy |
| hardware-bridge | 85%+ | DMX mapping logic |
| operator-console | 80%+ | Health endpoints, WebSocket |
| **Overall** | **80%+** | **Critical paths 90%+** |

### 3.3 TDD Approach

For each test:
1. **Write failing test** - Test describes expected behavior
2. **Run test, verify FAIL** - Confirms test catches issues
3. **Fix code if needed** - Make minimal changes to pass
4. **Run test, verify PASS** - Confirm fix works
5. **Document** - Write/update service documentation
6. **Commit** - Save progress with clear message

---

## 4. Documentation Overhaul

### 4.1 Current State Problems
- README.md shows 14 services (should be 8)
- docs/ has 30+ files, many outdated
- TRD v2.0 contains fictional dependencies
- 8-week plan documents don't reflect MVP pivot
- No clear "Getting Started" guide

### 4.2 New Documentation Structure

```
README.md                          # Main landing page (rewrite)
docs/
├── MVP_OVERVIEW.md                # NEW: Architecture & quick start
├── GETTING_STARTED.md             # NEW: 5-minute setup
├── API_REFERENCE.md               # Consolidated API docs
├── DEPLOYMENT.md                  # Update for docker-compose.mvp.yml
├── TESTING.md                     # NEW: Test guide
├── DEVELOPMENT.md                  # Update for MVP structure
├── CONTRIBUTING.md                 # (keep existing)
├── archive/                        # NEW: Archive old docs
    │   ├── TRD_PROJECT_CHIMERA_2026-04-11.md
    │   ├── 8-week-plan/
    │   └── old-architecture/
```

### 4.3 README.md Changes

**Badge Updates:**
- Status: "Production Ready" → "MVP - Foundation"
- Services: 14 → 8
- Tests: "594 passing" → "594 passing (MVP validated)"

**Section Updates:**
- Architecture: Complex multi-tier → Simplified Docker Compose
- Quick Start: Links to old guides → `docker compose -f docker-compose.mvp.yml up`
- Service list: 14 services → 8 services with descriptions

### 4.4 Content to Archive

- `TRD_PROJECT_CHIMERA_2026-04-11.md` (fictional dependencies)
- `8-week-plan/` directory (internal planning, not public)
- Old architecture diagrams
- Phase 1/2 completion reports (superseded by MVP)

---

## 5. Service-by-Service Execution Plan

### Service 1: Redis (15 min)
- **Tests:** Health check, basic connectivity
- **Docs:** Infrastructure requirements
- **Files:** None (existing infrastructure)

### Service 2: OpenClaw Orchestrator (45 min)
- **Tests:** `/api/orchestrate` flow, agent routing, WebSocket, webhook
- **Docs:** Orchestration flow, API reference, show state machine
- **Files:** `services/openclaw-orchestrator/main.py`

### Service 3: SceneSpeak Agent (45 min)
- **Tests:** GLM 4.7 API, Nemotron fallback, `/api/generate`, timeout/retry
- **Docs:** LLM fallback chain, env vars, model config
- **Files:** `services/scenespeak-agent/main.py`, `openai_llm.py`

### Service 4: Sentiment Agent (30 min)
- **Tests:** DistilBERT inference, `/api/analyze`, WebSocket, health
- **Docs:** Classification pipeline, model info, real-time updates
- **Files:** `services/sentiment-agent/main.py`, `ml_model.py`

### Service 5: Safety Filter (30 min)
- **Tests:** Content rules, `/api/check`, edge cases, caching
- **Docs:** Safety policy, filter rules, bypass mechanisms
- **Files:** `services/safety-filter/main.py`

### Service 6: Translation Agent (20 min)
- **Tests:** Mock translation, language detection, caching
- **Docs:** Mock note, supported languages, cache config
- **Files:** `services/translation-agent/main.py`

### Service 7: Hardware Bridge (20 min)
- **Tests:** `/dmx/output`, sentiment mapping, channel calculations
- **Docs:** DMX mapping reference, hardware integration notes
- **Files:** `services/echo-agent/main.py`

### Service 8: Operator Console (30 min)
- **Tests:** Health endpoints, show control API, WebSocket
- **Docs:** UI overview, control commands, event types
- **Files:** `services/operator-console/main.py`

---

## 6. Timeline

| Phase | Duration | Deliverable |
|-------|----------|------------|
| **1. Setup** | 15 min | Directory structure, Ralph Loop init |
| **2. Testing** | 2.5 hours | All integration tests passing |
| **3. Documentation** | 1.5 hours | All docs refreshed |
| **4. Finalization** | 30 min | Ralph Loop complete, commits |
| **Total** | **~5 hours** | **MVP tested & documented** |

---

## 7. Success Criteria

### Testing Success
- ✅ All integration tests pass (maintain 594+ baseline)
- ✅ Orchestrator synchronous flow validated
- ✅ GLM 4.7 API connectivity confirmed
- ✅ Target coverage met (80%+ overall, 90%+ critical)

### Documentation Success
- ✅ README.md reflects 8-service MVP
- ✅ docs/archive/ contains outdated content
- ✅ New docs complete (OVERVIEW, GETTING_STARTED, TESTING)
- ✅ No broken links or outdated references
- ✅ Clear getting-started path for users

### Ralph Loop Success
- ✅ Iteration 30 marked complete
- ✅ Progress tracker updated
- ✅ Session summary created
- ✅ Clean git history with descriptive commits

---

## 8. Git Commit Strategy

**Branch:** `main` (validation work, not new features)

**Commits:**
1. `infra: add Ralph Loop Iteration 30 directory structure`
2. `test: add MVP integration tests - docker-compose validation`
3. `test: add integration tests - orchestrator synchronous flow`
4. `test: add integration tests - scenespeak-agent LLM`
5. `test: add integration tests - sentiment-agent`
6. `test: add integration tests - safety-filter`
7. `test: add integration tests - translation-agent`
8. `test: add integration tests - hardware-bridge`
9. `test: add integration tests - operator-console`
10. `docs: archive outdated documentation`
11. `docs: rewrite README.md for MVP focus`
12. `docs: add MVP_OVERVIEW.md`
13. `docs: add GETTING_STARTED.md`
14. `docs: add TESTING.md`
15. `docs: update DEPLOYMENT.md for MVP`
16. `docs: update DEVELOPMENT.md for MVP`
17. `chore: Ralph Loop Iteration 30 - MVP validation complete`

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Docker services fail to start | Pre-flight health checks, graceful degradation |
| GLM API key not configured | Clear error messages, fallback logic |
| Tests take longer than expected | Prioritize critical paths, defer edge cases |
| Documentation breaks links | Link validation script, reference check |
| Ralph loop interrupted | Frequent commits, checkpoint after each phase |

---

## 10. Autonomous Execution Handoff

**What will be done:**
- Execute all phases in order
- Write TDD tests (fail → pass → refactor)
- Document each service as validated
- Run full test suite after changes
- Create descriptive commits
- Update Ralph Loop progress

**What won't be done:**
- Architectural changes (validation only)
- New service creation
- K8s configuration
- Remote pushes without approval

**Completion Evidence:**
- Ralph Loop Iteration 30 complete
- All tests passing
- README.md updated
- docs/ reorganized
- Session summary created

---

*End of Design Document - Approved 2026-04-11*

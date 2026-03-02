# Lighting, Sound and Music Integration Design

**Date:** 2026-03-02
**Status:** Approved
**Author:** Claude (with user approval)

---

## Overview

Merge the existing **Lighting Control** service (port 8005) with **Music Generation** and **Music Orchestration** platforms into a unified **"Lighting, Sound and Music"** service. This creates a single, cohesive component that students can work with, providing coordinated control over theatrical lighting, sound effects, and AI-generated music.

### Goals

1. **Simplify Student Onboarding** - Single service (port 8005) instead of multiple disparate services
2. **Enable Coordinated Cues** - Unified control over lighting + sound + music for theatrical experiences
3. **Consolidate Code** - Merge best code from existing services, deprecate redundant ones
4. **Maintain Functionality** - Preserve all existing capabilities while adding new sound features

---

## Architecture

### Service Design

**New Service Name:** `lighting-sound-music` (or `lsm-service`)
**Port:** 8005
**Type:** Unified FastAPI service with internal modules
**Deployment:** Kubernetes pod (coordinated deployment)

### Code Structure

```
lighting-sound-music/
├── main.py                 # FastAPI app entry point
├── lighting.py             # DMX/sACN control (from lighting-control)
├── sound.py                # Sound effects, playback, mixing (NEW)
├── music.py                # AI generation + playback (consolidated)
├── cues.py                 # Coordinated scene cues (NEW)
├── models.py               # Shared data models
├── requirements.txt
├── Dockerfile
└── tests/
```

### API Routes (Flat Structure)

| Route | Purpose | Source |
|-------|---------|--------|
| `/health/live` | Health check | Standard |
| `/lighting/*` | DMX/sACN stage automation | Existing (lighting-control) |
| `/sound/*` | Sound effects, playback, mixing | NEW |
| `/music/*` | AI generation + playback | Existing (music services) |
| `/cues/*` | Coordinated multi-media scenes | NEW |

---

## Components

### 1. Lighting Module
**Source:** `services/lighting-control`
**Status:** ✅ Existing code, needs extraction

**Features:**
- DMX/sACN protocol support
- Scene presets and fade times
- OSC message handling
- Fixture management

### 2. Sound Module
**Status:** ⚠️ NEW - needs to be built

**Features:**
- Sound effects library and playback
- Volume control and mixing
- Audio file management
- Real-time sound triggering
- Multi-track audio support

### 3. Music Module
**Source:** `services/music-generation` + `services/music-orchestration`
**Status:** ✅ Existing code, needs consolidation

**Features:**
- **AI Music Generation** using ACE-Step-1.5 models (locally downloaded)
- Music playback controls (play, pause, stop, loop)
- Track/playlist management
- Response caching for performance

**ACE-Step-1.5 Integration:**
- Repository: https://github.com/ace-step/ACE-Step-1.5
- Models downloaded locally into the pod
- Loaded at startup by `music.py`
- Used for AI music generation requests

### 4. Cues Module
**Status:** ⚠️ NEW - needs to be built

**Features:**
- Coordinated scenes (lighting + sound + music together)
- Timeline-based execution
- Scene presets for different moods
- Synchronization primitives

---

## Data Flow

```
Client Request (Port 8005)
    │
    ├──> /lighting/*  → lighting.py → DMX/sACN → Stage Lights
    ├──> /sound/*     → sound.py    → Audio Backend → Speakers
    ├──> /music/*     → music.py    → ACE-Step-1.5 → Audio Output
    └──> /cues/*      → cues.py     → Coordinates all three above
```

**Kubernetes Pod Structure:**
```
lsm-service-pod:
├── lighting-sound-music container (port 8005)
│   ├── ACE-Step-1.5 models (mounted volume)
│   ├── Sound effects library (mounted volume)
│   └── Music files library (mounted volume)
```

---

## Migration Strategy

### Phase 1: Preparation (Can start immediately)
- Document current API endpoints for all 3 services
- Create inventory of music/sound assets
- Clone/download ACE-Step-1.5 models locally
- Back up existing working code

### Phase 2: Build New Service (After student onboarding)
- Create new `lighting-sound-music/` service directory
- Extract and migrate lighting code from `lighting-control`
- Consolidate music code from `music-generation` + `music-orchestration`
- Build new sound module from scratch
- Implement cues module
- Integrate ACE-Step-1.5 models

### Phase 3: Deploy & Test
- Deploy new service alongside existing services
- Test all endpoints independently
- Test coordinated cues
- Update documentation and student materials

### Phase 4: Cleanup
- Remove old service directories:
  - `services/lighting-control`
  - `services/music-generation`
  - `services/music-orchestration`
- Update GitHub issues
- Update 8-core-pillars documentation

### Phase 5: Student Handoff
- Update Sprint 0 issues with new service information
- Create onboarding guide for LSM service
- Assign students to the component

---

## Documentation Updates

### All documentation will be updated to reflect this change:

**Core Architecture:**
- `docs/services/core-services.md` - Update "8 Core Pillars" table
- `docs/architecture/README.md` - Update system architecture diagram
- `README.md` - Update service descriptions

**Service-Specific:**
- `docs/services/music-generation.md` - Mark as deprecated
- Create `docs/services/lighting-sound-music.md` - New comprehensive guide
- Update API documentation for all endpoints

**Student-Facing:**
- `docs/getting-started/monday-demo/student-handout.md` - Update component list
- `docs/getting-started/monday-demo/4pm-demo-script.md` - Update demo script
- `docs/getting-started/roles.md` - Update role descriptions
- GitHub Sprint 0 issues - Update component assignments

**Infrastructure:**
- Kubernetes manifests - Update deployment configs
- Docker Compose files - Update service definitions

**All changes committed locally AND pushed to GitHub.**

---

## Updated 8 Core Pillars

| # | Service | Port | Description |
|---|---------|------|-------------|
| 1 | OpenClaw Orchestrator | 8000 | Central control plane |
| 2 | SceneSpeak Agent | 8001 | Dialogue generation |
| 3 | Captioning Agent | 8002 | Speech-to-text |
| 4 | BSL Translation Agent | 8003 | British Sign Language |
| 5 | Sentiment Agent | 8004 | Audience sentiment |
| 6 | **Lighting, Sound & Music** | **8005** | **Unified audio-visual control** |
| 7 | Safety Filter | 8006 | Content moderation |
| 8 | Operator Console | 8007 | Human oversight |

**Note:** Music Generation and Music Orchestration are NO LONGER separate platforms. They are now part of the Lighting, Sound & Music service.

---

## Success Criteria

- [ ] Single service running on port 8005
- [ ] All lighting endpoints functional
- [ ] Sound module working with effects and playback
- [ ] Music generation working with ACE-Step-1.5 models
- [ ] Coordinated cues working across all three
- [ ] All documentation updated
- [ ] Old services removed
- [ ] Students successfully assigned to LSM component

---

*Design approved: 2026-03-02*
*Next step: Implementation plan via writing-plans skill*

# Deprecation Notices - Project Chimera

**Date**: April 9, 2026
**Status**: EFFECTIVE IMMEDIATELY

## Overview

This document lists all components, features, and requirements that have been **deprecated** as part of the architecture reset for the 8-week delivery plan.

---

## CRITICAL DEPRECATIONS

### 1. Kubernetes Deployment (❌ DEPRECATED)

**Affected Files**:
- Any `*.yaml` Kubernetes manifests
- `k3s` setup documentation
- `kubectl` workflow instructions

**Status**: **NOT REQUIRED** for grant closeout
**Alternative**: Use `chimera_core.py` directly

### 2. Docker Microservices (❌ DEPRECATED)

**Affected Services**:
- `services/dmx-controller/` (port 8001)
- `services/audio-controller/` (port 8002)
- `services/bsl-avatar-service/` (port 8003)
- Other auxiliary services

**Status**: **NOT REQUIRED** for grant closeout
**Alternative**: Functionality demonstrated in monolithic form

### 3. Sprint 0 Onboarding (❌ DEPRECATED)

**Affected Issues**:
- Issue #6: Arashdip for BSL Setup
- Issue #8: Mohammad for Lighting Setup  
- Issue #10: Fatma for Console Setup
- Other student assignment issues

**Status**: **CLOSED** - Simplified to solo development
**Alternative**: Focus on core deliverable completion

---

## DEFERRED TO PHASE 2 (Funding Required)

### 1. Live Hardware Integration

**Status**: ⏸️ DEFERRED
**Requirements**: Funding, venue partnership, hardware procurement

**Deferred Components**:
- DMX lighting control
- Audio system control
- Live BSL avatar rendering
- Show control orchestration

### 2. Venue Deployment

**Status**: ⏸️ DEFERRED  
**Requirements**: Venue partnership, production budget

**Deferred Activities**:
- Live venue technical rehearsals
- Public performances
- Venue-specific integration

### 3. Full BSL Avatar

**Status**: ⏸️ DEFERRED
**Requirements**: BSL partnership, avatar development budget

**Deferred Features**:
- 3D avatar rendering
- Real-time sign language generation
- Regional BSL variations

---

## WHAT REMAINS ACTIVE

### ✅ Primary Deliverable

**File**: `services/operator-console/chimera_core.py` (1,077 lines)

**Status**: **ACTIVE** - Core grant deliverable

**Features**:
- Sentiment analysis (DistilBERT + fallback)
- Adaptive dialogue generation (GLM-4.7 + Ollama + mock)
- Adaptive routing engine
- Caption formatting for accessibility

### ✅ Documentation

**Status**: **ACTIVE** - Being updated for 8-week plan

**Documents**:
- Scope statement (`evidence/tech_audit/scope_statement.md`)
- Architecture reset (`evidence/tech_audit/architecture_reset.md`)
- Evidence pack structure (`evidence/`)

---

## MIGRATION GUIDE

### For Users Trying to Run Old Instructions

If you encounter documentation referencing:

1. **"Deploy to Kubernetes"**
   - ❌ Don't follow these instructions
   - ✅ Use: `python services/operator-console/chimera_core.py`

2. **"Start Docker services"**
   - ❌ Don't follow these instructions
   - ✅ Use: `python services/operator-console/chimera_core.py`

3. **"Clone and setup service X"**
   - ❌ Don't follow these instructions
   - ✅ Use: `python services/operator-console/chimera_core.py`

### For Developers

If you're looking for code in deprecated services:

1. **DMX Controller code** → See `services/dmx-controller/` (REFERENCE ONLY)
2. **Audio Controller code** → See `services/audio-controller/` (REFERENCE ONLY)
3. **BSL Service code** → See `services/bsl-avatar-service/` (REFERENCE ONLY)

**Note**: These services are kept for reference but are **not actively developed**.

---

## COMPLIANCE STATEMENT

### Grant Requirements

✅ **Core Innovation Demonstrated**: Adaptive AI based on sentiment analysis
✅ **Technical Deliverable**: Working Python script (chimera_core.py)
✅ **Documentation**: Complete evidence pack
✅ **Demo**: Video demonstration planned
✅ **Budget Tracking**: Evidence folder established

❌ **Live Performance**: Deferred to Phase 2 (funding required)
❌ **Hardware Integration**: Deferred to Phase 2 (funding required)
❌ **Student Collaboration**: Simplified to solo development

### Compliance Assessment

**Overall**: ✅ **COMPLIANT** with simplified scope

The project delivers on the **core grant objectives**:
1. AI-powered adaptive framework ✅
2. Real-time sentiment analysis ✅
3. Adaptive dialogue generation ✅
4. Accessibility considerations ✅

Advanced features (hardware integration, live deployment) are **properly deferred** to Phase 2 with clear justification.

---

## QUESTIONS?

**Q**: Is the project still "AI-powered adaptive live theatre framework"?

**A**: Yes. The core adaptive AI functionality is fully demonstrated. "Live theatre" deployment is deferred to Phase 2.

**Q**: Did we abandon the student collaboration aspect?

**A**: We simplified it. The 8-week plan focuses on solo delivery for grant closeout. Phase 2 will include team building with funding.

**Q**: What happens to the existing service code?

**A**: It's kept for reference and can be revived in Phase 2 with proper funding and team.

**Q**: Is this a scope reduction?

**A**: It's a **scope refinement**. We're focusing on what can be realistically delivered in the grant timeline while maintaining the core innovation.

---

**Approved**: April 9, 2026
**Status**: ACTIVE
**Review Date**: End of 8-week delivery period

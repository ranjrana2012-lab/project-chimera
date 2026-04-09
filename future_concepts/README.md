# Future Concepts - Project Chimera

**Status**: ARCHIVED - Phase 2 Development Candidates
**Date Moved**: 2026-04-09
**Reason**: Strategic pivot to monolithic proof-of-concept for Phase 1

---

## Overview

This directory contains services and components that are **valid architectural designs** but are **out of scope for Phase 1 delivery**. These components represent future development work for Phase 2 or beyond.

## Why These Were Moved

Based on comprehensive technical due-diligence, the following constraints necessitated focusing on a monolithic demonstrator:

1. **Team Capacity**: Student collaboration model did not materialize (Sprint 0 dormant 3+ weeks)
2. **Timeline**: 8-week remaining timeline incompatible with distributed microservices development
3. **Hardware Dependencies**: Physical venue and hardware integration not feasible
4. **Complexity**: DevOps overhead of distributed system exceeds available resources

---

## Archived Services

### 1. BSL Agent (British Sign Language)
**Status**: Dictionary-based prototype (~12 phrases only)
**Original Port**: 8003
**Reason for Archive**:
- No ML model integration
- No linguistic engine
- Dictionary-based translation insufficient for production
- Requires dedicated NLP research for Phase 2

**What Works**:
- HTTP API functional
- Avatar renderer exists (119KB WebGL code)
- Basic phrase matching

**Phase 2 Requirements**:
- Integrate proper ML translation model
- Expand dictionary to full language vocabulary
- Add linguistic context handling
- Real-time avatar animation system

### 2. Captioning Agent
**Status**: Infrastructure exists, not tested with audio
**Original Port**: 8002
**Reason for Archive**:
- Whisper library integrated but untested
- No audio processing pipeline verified
- GPU dependency for model loading
- Requires audio hardware integration

**What Works**:
- HTTP API functional
- Whisper library dependencies installed
- WebSocket endpoints defined

**Phase 2 Requirements**:
- Test with actual audio input
- Verify GPU model loading
- Integrate with real audio sources
- Build end-to-end captioning pipeline

### 3. Lighting/Sound/Music
**Status**: HTTP API works, hardware untested
**Original Port**: 8005
**Reason for Archive**:
- DMX lighting control code exists but unverified
- Audio control code untested
- No hardware integration attempted
- Venue coordination not established

**What Works**:
- HTTP API functional
- DMX controller code exists
- Audio controller code exists

**Phase 2 Requirements**:
- Test with actual DMX lighting hardware
- Verify audio system integration
- Venue deployment and testing
- Real-time show control workflow

### 4. Music Generation
**Status**: ML models integrated, untested in production
**Original Port**: 8011
**Reason for Archive**:
- Meta MusicGen and ACE-Step models integrated
- No verified music output in live context
- Requires significant GPU resources
- Out of scope for Phase 1 text-based demo

**What Works**:
- ML models loaded and functional
- HTTP API operational
- Model inference working

**Phase 2 Requirements**:
- Test in actual performance context
- Integrate with show orchestration
- Optimize for real-time generation
- Build music curation workflow

### 5. Director Agent
**Status**: Conceptual framework only
**Reason for Archive**: Not implemented, requires dedicated director LLM research

### 6. Visual Core
**Status**: Rendering framework incomplete
**Reason for Archive**: Requires dedicated graphics/UX development

### 7. Simulation Engine
**Status**: Show simulation framework incomplete
**Reason for Archive**: Secondary to core adaptive logic

---

## Preserved Architecture

All these services contain **valuable architectural designs** and **working code components**. They are archived here (not deleted) because:

1. **Code Reusability**: All components can be reactivated for Phase 2
2. **Architecture Reference**: Designs inform future development
3. **Grant Documentation**: Demonstrates thorough planning and exploration
4. **Future Funding**: Validated concepts strengthen Phase 2 proposals

---

## Phase 2 Reactivation Plan

When resuming these components, the recommended sequence is:

1. **BSL Agent** (Priority: High)
   - Integrate production ML translation model
   - Expand beyond dictionary-based approach
   - Test with Deaf community stakeholders

2. **Captioning Agent** (Priority: High)
   - Verify Whisper model with real audio
   - Build GPU-optimized pipeline
   - Test in live performance context

3. **Lighting/Sound/Music** (Priority: Medium)
   - Secure venue partnership
   - Test hardware integration
   - Build DMX control workflow

4. **Music Generation** (Priority: Medium)
   - Optimize for real-time performance
   - Integrate with show orchestration
   - Build music curation interface

5. **Director Agent** (Priority: Low)
   - Requires dedicated director model research
   - Dependent on core adaptive logic

---

## Technical Debt

When these services are reactivated, the following technical debt will need addressing:

- **BSL Agent**: Replace dictionary with ML model
- **Captioning Agent**: Add audio pipeline testing
- **Lighting/Sound**: Add hardware verification
- **Music Generation**: Optimize GPU usage
- **All Services**: Add comprehensive E2E tests (currently 49 skipped)

---

## Evidence Pack References

For detailed evidence of each service's actual status, see:
- `evidence/service-health/bsl-agent.md`
- `evidence/service-health/scenespeak-agent.md`
- `evidence/service-health/sentiment-agent.md`
- `evidence/PHASE_1_DELIVERED.md`

---

## Conclusion

These components represent **ambitious, valid architectural visions** that were **ahead of their time** given the project constraints. By archiving them to `future_concepts/`, we:

1. **Honesty**: Accurately reflect what Phase 1 actually delivers
2. **Preserve**: Keep valuable code and designs for future use
3. **Focus**: Concentrate resources on achievable monolithic demonstrator
4. **Compliance**: Ensure grant closeout with defensible scope

**This is not a failure of vision, but a responsible adaptation to reality.**

---

*Archive Date: 2026-04-09*
*Reason: Strategic pivot per STRATEGIC_PIVOT_MANDATE.md*
*Next Review: Phase 2 Planning*

# Comprehensive Documentation Audit & Update Design

**Date:** 2026-03-03
**Status:** ✅ Approved
**Version:** 1.0.0

---

## Overview

Comprehensive documentation audit and update to reflect all completed work through v0.4.0 (WorldMonitor integration), standardize k3s terminology, and ensure accuracy across all 82 documentation files.

---

## Current State Analysis

**Documentation Files:** 82 total markdown files

**Issues Identified:**
1. CHANGELOG.md stops at v0.2.0 (missing v0.3.0 LSM, v0.4.0 WorldMonitor)
2. Inconsistent k3s/k8s/kubernetes terminology
3. Service status outdated
4. WorldMonitor integration not fully integrated into main docs
5. Version badges show v0.2.0 (should be v0.4.0)

---

## Phases

### Phase 1: Critical Updates

**Priority:** CRITICAL

**Files:**
- `CHANGELOG.md` - Root file
- `README.md` - Root file
- `docs/README.md` - Docs hub
- `docs/services/core-services.md`
- `docs/SERVICE_STATUS.md`

**Actions:**
1. Add v0.3.0 section to CHANGELOG:
   - Lighting, Sound & Music (LSM) service
   - Unified audio-visual control
   - 8 core pillars updated (6→5 services)
   - Service status updates

2. Add v0.4.0 section to CHANGELOG:
   - WorldMonitor integration
   - Context-enriched sentiment analysis
   - News sentiment analysis
   - Sidecar pattern deployment
   - API endpoint additions

3. Update version badges:
   - README.md: v0.2.0 → v0.4.0
   - docs/README.md: version references
   - Any service-specific badges

4. Update service status:
   - Sentiment Agent: Add WorldMonitor integration note
   - Lighting → LSM: Update name and description
   - Mark WorldMonitor sidecar as new component

### Phase 2: Terminology Standardization

**Priority:** HIGH

**Scope:** All 82 documentation files

**Rules:**
- **Descriptive text:** Use "k3s" or "k3s cluster"
  - ✅ "Deploy to k3s cluster"
  - ❌ "Deploy to k8s" or "Deploy to kubernetes"

- **API specifications:** Keep Kubernetes API references
  - ✅ `apiVersion: networking.k8s.io/v1` (correct)
  - ✅ `kind: Deployment` (correct)

- **Directory names:** Keep actual directory names
  - ✅ `infrastructure/kubernetes/` (actual directory)
  - ✅ `infrastructure/k8s/` (if actual directory)

- **Commands:** Use kubectl (k3s uses kubectl)
  - ✅ `kubectl apply -f ...`
  - ✅ `kubectl get pods`

**Files to update:**
- `docs/DEPLOYMENT.md` - Multiple k8s references
- `docs/runbooks/README.md#deployment`
- `docs/runbooks/bootstrap-setup.md`
- `docs/docs/reference/architecture.md`
- `docs/quality-platform/DEPLOYMENT.md`
- `docs/music-platform/COMPLETION_SUMMARY.md`
- Any other files with k8s/kubernetes in descriptive text

### Phase 3: New Feature Integration

**Priority:** HIGH

**Updates to Existing Files:**

1. **`docs/DEPLOYMENT.md`**
   - Add WorldMonitor sidecar deployment section
   - Include sidecar pod configuration
   - Add k3s deployment commands for WorldMonitor

2. **`docs/docs/reference/architecture.md`**
   - Add sidecar pattern architecture diagram
   - Document WorldMonitor sidecar responsibilities
   - Update Sentiment Agent section

3. **`docs/guides/README.md`**
   - Add link to WorldMonitor context usage guide
   - Update navigation structure

4. **`docs/api/README.md`**
   - Verify all new endpoints documented:
     - GET /api/v1/context/global
     - GET /api/v1/context/country/{code}
     - WebSocket /api/v1/context/stream
     - POST /api/v1/news/sentiment

**Ensure New Files Are Linked:**
- `docs/services/sentiment-agent-with-worldmonitor.md`
- `docs/guides/worldmonitor-context-usage.md`
- `docs/plans/2026-03-03-worldmonitor-integration-design.md`

### Phase 4: Validation

**Priority:** MEDIUM

**Tasks:**

1. **Link Checking**
   - Check all internal markdown links
   - Verify relative paths resolve correctly
   - Check external links (optional)

2. **Code Example Validation**
   - Verify kubectl commands are accurate
   - Check YAML examples are valid
   - Ensure code blocks have correct language tags

3. **Consistency Verification**
   - Version numbers consistent across docs
   - Service names consistent
   - Port numbers match actual services
   - Badges and links work correctly

4. **Formatting Standards**
   - Apply documentation style guide
   - Ensure consistent heading hierarchy
   - Check list formatting

---

## Implementation Strategy

**Order of Operations:**
1. Start with CHANGELOG (foundational for other updates)
2. Update README and badges (user-facing)
3. Service status updates (quick wins)
4. Terminology standardization (systematic file-by-file)
5. New feature integration (additions to existing files)
6. Validation (final polish)

**Testing After Each Phase:**
- Verify git diff shows expected changes
- Check markdown rendering if possible
- Ensure no unintended deletions

---

## Success Criteria

### Phase 1: Critical Updates
- [ ] CHANGELOG.md has v0.3.0 and v0.4.0 sections
- [ ] README.md version badge shows v0.4.0
- [ ] Service status table reflects current state
- [ ] Sentiment Agent description includes WorldMonitor

### Phase 2: Terminology
- [ ] Zero instances of "k8s" in descriptive text
- [ ] Zero instances of "kubernetes" in descriptive text
- [ ] All descriptive text uses "k3s" or "k3s cluster"
- [ ] API specifications retain "k8s" where appropriate

### Phase 3: Integration
- [ ] DEPLOYMENT.md includes WorldMonitor sidecar
- [ ] architecture.md shows sidecar pattern
- [ ] All new docs linked from navigation hubs
- [ ] API reference complete

### Phase 4: Validation
- [ ] No broken internal links
- [ ] All code examples tested
- [ ] Formatting consistent
- [ ] Cross-references accurate

---

## Files to Modify

**Root Level:**
- CHANGELOG.md
- README.md

**docs/ Root:**
- docs/README.md
- docs/DEPLOYMENT.md
- docs/SERVICE_STATUS.md

**docs/services/:**
- docs/services/core-services.md

**docs/reference/:**
- docs/api/README.md
- docs/docs/reference/architecture.md

**docs/guides/:**
- docs/guides/README.md

**docs/runbooks/:**
- docs/runbooks/README.md#deployment
- docs/runbooks/bootstrap-setup.md

**docs/quality-platform/:**
- docs/quality-platform/DEPLOYMENT.md

**docs/music-platform/:**
- docs/music-platform/COMPLETION_SUMMARY.md

**Plus any other files found during Phase 2 audit**

---

## Estimated Effort

- Phase 1: 30-45 minutes
- Phase 2: 45-60 minutes (systematic search & replace)
- Phase 3: 30-45 minutes
- Phase 4: 20-30 minutes

**Total:** ~2-3 hours

---

**Status:** ✅ Design Approved - Ready for Implementation Planning

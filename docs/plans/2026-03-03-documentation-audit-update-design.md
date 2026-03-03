# Documentation Audit & Update Design

**Date:** 2026-03-03
**Status:** ✅ Approved
**Version:** 1.0.0

---

## Overview

Comprehensive documentation audit and update to reflect all completed work through v0.4.0 (WorldMonitor integration), standardize k3s terminology, and ensure accuracy across all 82 documentation files.

---

## Phases

### Phase 1: Critical Updates

**Files:**
- `CHANGELOG.md`
- `README.md`
- `docs/services/core-services.md`
- `docs/SERVICE_STATUS.md`

**Changes:**
1. Add v0.3.0 (LSM integration) to CHANGELOG
2. Add v0.4.0 (WorldMonitor integration) to CHANGELOG
3. Update version badges (v0.2.0 → v0.4.0)
4. Update service status table with current state
5. Update Sentiment Agent description to include WorldMonitor

### Phase 2: Terminology Standardization

**Scope:** All 82 documentation files

**Rules:**
- Descriptive text: "k3s" or "k3s cluster" (not "k8s" or "kubernetes")
- API specifications: Keep `apiVersion: networking.k8s.io/v1` (legitimate Kubernetes API)
- Directory names: Keep `infrastructure/kubernetes/` (actual directory name)
- Command examples: Use `kubectl` (k3s uses kubectl CLI)

**Files to update:**
- `docs/DEPLOYMENT.md`
- `docs/runbooks/deployment.md`
- `docs/runbooks/bootstrap-setup.md`
- `docs/reference/architecture.md`
- `docs/quality-platform/DEPLOYMENT.md`
- Any other files with k8s/kubernetes references in descriptive text

### Phase 3: New Feature Integration

**Files to update:**
- `docs/DEPLOYMENT.md` - Add WorldMonitor sidecar deployment
- `docs/reference/architecture.md` - Add sidecar pattern diagram
- `docs/guides/README.md` - Link to WorldMonitor usage guide
- `docs/reference/api.md` - Verify all new endpoints documented

**New files to ensure are linked:**
- `docs/services/sentiment-agent-with-worldmonitor.md`
- `docs/guides/worldmonitor-context-usage.md`
- `docs/plans/2026-03-03-worldmonitor-integration-design.md`

### Phase 4: Validation

**Tasks:**
1. Check all internal links (markdown relative links)
2. Verify code examples are accurate
3. Check badge URLs and version numbers
4. Ensure consistent formatting across docs

---

## Success Criteria

- [ ] CHANGELOG includes v0.3.0 and v0.4.0
- [ ] All descriptive text uses "k3s" consistently
- [ ] Service status reflects actual current state
- [ ] WorldMonitor integration fully documented
- [ ] No broken internal links
- [ ] All code examples tested and accurate

---

## Testing Strategy

1. **Link checking** - Use markdown linter to find broken links
2. **Proofreading** - Manual review of all changed files
3. **Cross-reference verification** - Ensure all new docs are linked from hubs
4. **Command validation** - Verify kubectl commands are accurate

---

**Status:** ✅ Design Approved - Ready for Implementation Planning

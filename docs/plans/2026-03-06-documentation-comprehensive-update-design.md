# Documentation Comprehensive Update Design

**Date:** March 6, 2026
**Status:** Design for Approval
**Goal:** Complete documentation synchronization for v0.5.0 release

---

## Overview

A comprehensive update to synchronize all Project Chimera documentation with the current v0.5.0 codebase, including: 7 missing service READMEs, Operator Console dashboard documentation, TODO/FIXME resolution, and version standardization.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION UPDATE PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PHASE 1: SERVICE READMES (7 files)                                    │
│  ├── 01. openclaw-orchestrator/README.md                                │
│  ├── 02. scenespeak-agent/README.md                                    │
│  ├── 03. bsl-agent/README.md                                           │
│  ├── 04. sentiment-agent/README.md                                     │
│  ├── 05. lighting-sound-music/README.md                                │
│  ├── 06. safety-filter/README.md                                       │
│  └── 07. operator-console/README.md                                    │
│                                                                         │
│  PHASE 2: DASHBOARD DOCUMENTATION                                      │
│  ├── 08. docs/guides/operator-console-dashboard.md (NEW user guide)    │
│  └── 09. docs/api/operator-console.md (UPDATE with dashboard info)     │
│                                                                         │
│  PHASE 3: TODO/FIXME RESOLUTION                                        │
│  └── 10. Scan and resolve 32 markers across docs/                      │
│                                                                         │
│  PHASE 4: VERSION STANDARDIZATION                                      │
│  └── 11. Update all version refs to v0.5.0                            │
│                                                                         │
│  PHASE 5: CROSS-REFERENCE VALIDATION                                   │
│  └── 12. Verify and fix all internal links                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### Phase 1: Service README Files (7 comprehensive documents)

**Template Structure (for each service):**
```markdown
# {Service Name}

{Brief 2-3 sentence description}

## Overview
{What this service does, its role in Chimera}

## Quick Start
```bash
# Prerequisites
# Local development setup
# Running tests
```

## Configuration
{Environment variables, ports, dependencies}

## API Endpoints
{Key endpoints with examples}

## Development
{Setup for contributors}

## Testing
{How to run tests, coverage}

## Troubleshooting
{Common issues and solutions}

## Contributing
{Guidelines for contributors}

## License
{MIT - Project Chimera}
```

**Services to create:**
1. `services/openclaw-orchestrator/README.md` - Central orchestrator documentation
2. `services/scenespeak-agent/README.md` - SceneSpeak/LLM agent docs
3. `services/bsl-agent/README.md` - BSL translation agent docs
4. `services/sentiment-agent/README.md` - Sentiment analysis docs
5. `services/lighting-sound-music/README.md` - Stage automation docs
6. `services/safety-filter/README.md` - Content moderation docs
7. `services/operator-console/README.md` - Dashboard/operator console docs

### Phase 2: Dashboard Documentation

**File 1: `docs/guides/operator-console-dashboard.md` (NEW)**
```markdown
# Operator Console Dashboard Guide

## Dashboard Overview
{Introduction to the new single-page dashboard}

## Accessing the Dashboard
{URL: http://localhost:8007, authentication}

## Dashboard Sections
### Service Status Panel
{8 service cards explanation}

### Alerts Console
{How alerts work, acknowledging, filtering}

### Control Panel
{Starting/stopping/restarting services}

### Metrics Charts
{CPU, Memory, Request Rate, Error Rate sparklines}

### Event Feed
{System event log, export functionality}

## WebSocket Connection
{Real-time updates, auto-reconnect behavior}

## Troubleshooting
{Common dashboard issues}
```

**File 2: `docs/api/operator-console.md` (UPDATE)**
- Add new endpoint: `GET /static/dashboard.html`
- Add WebSocket endpoint: `/ws` (not just `/ws/realtime`)
- Update endpoints section with dashboard routes
- Add metrics endpoints: `/metrics`, `/api/services`, `/api/alerts`

### Phase 3: TODO/FIXME Resolution

**Scan and Resolve:**
1. Scan all `docs/*.md` files for TODO/FIXME/XXX/PLACEHOLDER
2. For each marker:
   - If content exists: Replace marker with actual content
   - If outdated: Remove marker and stale reference
   - If future work: Create GitHub issue, replace with link
3. Verify no markers remain

**Categories to address:**
- FIXME markers (8) - High priority
- TODO markers (24) - Medium priority

### Phase 4: Version Standardization

**Update all version references to v0.5.0:**
1. Main `README.md` version badge
2. All API docs version headers
3. Service README version references
4. Architecture documentation
5. Release notes status (v0.5.0 → "current")

**Files to update:**
- `README.md`
- `docs/api/*.md`
- `docs/services/*.md`
- `docs/architecture/*.md`

### Phase 5: Cross-Reference Validation

**Verify all internal links:**
1. Extract all `[](target.md)` references
2. Check each target exists
3. Fix broken links
4. Update relative paths

---

## Implementation Details

### Service README Template
Based on `captioning-agent/README.md` (existing), each service README will include:

1. **Header** - Service name, badge with version, status badges
2. **Overview** - 2-3 sentence description of service purpose
3. **Quick Start** -
   - Prerequisites (Python 3.10+, Docker, etc.)
   - Local setup (clone, venv, dependencies)
   - Run command
4. **Configuration** -
   - Port number
   - Environment variables (.env.example)
   - Dependencies (Kafka, Redis, etc.)
5. **API Endpoints** - Key endpoints with curl examples
6. **Development** -
   - Code structure
   - Adding features
   - Testing setup
7. **Testing** - pytest commands, coverage
8. **Troubleshooting** - Common issues and fixes
9. **Contributing** - Link to CONTRIBUTING.md

### Dashboard Guide Structure
The `docs/guides/operator-console-dashboard.md` will cover:

1. **Getting Started** - Access URL, first login
2. **Dashboard Layout** - Visual guide to sections
3. **Service Status Panel** - Reading health indicators
4. **Alerts Console** - Managing alerts
5. **Control Panel** - Service controls
6. **Metrics Charts** - Understanding sparklines
7. **Event Feed** - Event log interpretation
8. **WebSocket** - Real-time connection behavior
9. **Troubleshooting** - Common issues

### TODO/FIXME Resolution Strategy

**Priority Order:**
1. FIXME markers (High) - Replace or create GitHub issues
2. TODO markers (Medium) - Evaluate and resolve/remove

**Resolution Rules:**
- **If content exists:** Replace marker with actual content
- **If outdated:** Remove marker and reference
- **If future work:** Create GitHub issue, link from doc
- **If unclear:** Remove and clarify with maintainers

---

## Error Handling

### Missing Information
- **Encountered:** Service-specific information unclear
- **Handling:** Check service .env.example, main.py, tests
- **Fallback:** Use generic template with "Contact maintainers" note

### Link Validation Failures
- **Broken internal link:** Update target path
- **Missing target:** Create placeholder or remove link
- **Ambiguous reference:** Clarify and fix

### Version Conflicts
- **Inconsistent versions:** Standardize to v0.5.0
- **Multiple version refs:** Use specific version with note
- **Release timing:** Document as "in development" if unreleased

---

## Testing & Verification

### Pre-Commit Checklist
- [ ] All 7 service READMEs created
- [ ] Dashboard user guide created
- [ ] API docs updated for dashboard
- [ ] All TODO/FIXME markers resolved
- [ ] All version refs set to v0.5.0
- [ ] All internal links validated
- [ ] Markdown syntax verified

### Automated Validation
```bash
# Check for remaining TODO/FIXME
grep -r "TODO\|FIXME\|XXX\|PLACEHOLDER" docs/ --include="*.md"

# Check internal links
bash scripts/check-links.sh

# Count files
find docs -name "*.md" | wc -l  # Should be 152 (145 + 7 new)

# Verify service READMEs
for svc in openclaw-orchestrator scenespeak-agent bsl-agent sentiment-agent lighting-sound-music safety-filter operator-console; do
  [ -f "services/$svc/README.md" ] && echo "✓ $svc" || echo "✗ $svc"
done
```

### Success Criteria
- 7/7 service READMEs created with comprehensive content
- Dashboard user guide created and complete
- Operator Console API docs updated with dashboard info
- 0 TODO/FIXME markers remaining in docs/
- All version references = v0.5.0
- 0 broken internal links
- All changes committed and pushed
- Sync report generated

---

## Files to Create

1. `services/openclaw-orchestrator/README.md`
2. `services/scenespeak-agent/README.md`
3. `services/bsl-agent/README.md`
4. `services/sentiment-agent/README.md`
5. `services/lighting-sound-music/README.md`
6. `services/safety-filter/README.md`
7. `services/operator-console/README.md`
8. `docs/guides/operator-console-dashboard.md`
9. `docs/plans/2026-03-06-documentation-comprehensive-update-design.md` (this file)

## Files to Modify

1. `docs/api/operator-console.md` - Add dashboard documentation
2. `docs/api/*.md` - Version updates to v0.5.0
3. `README.md` - Version badge update
4. `docs/release-notes/v0.5.0.md` - Update status to current
5. Any files with TODO/FIXME markers

---

## Definition of Done

- [ ] Design document written (THIS)
- [ ] Design approved by user
- [ ] Implementation plan created (via writing-plans skill)
- [ ] 7 service READMEs created
- [ ] Dashboard user guide created
- [ ] API docs updated for dashboard
- [ ] All TODO/FIXME markers resolved
- [ ] All version references = v0.5.0
- [ ] All internal links validated
- [ ] Automated validation passes
- [ ] All changes committed
- [ ] Changes pushed to GitHub
- [ ] Final sync report generated

---

*Design Document - Project Chimera v0.5.0 - March 6, 2026*

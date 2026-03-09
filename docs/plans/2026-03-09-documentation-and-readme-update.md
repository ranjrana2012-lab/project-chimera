# Documentation and README Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update Project Chimera's README to accurately reflect current project status and fix critical documentation issues.

**Architecture:** Parallel execution - audit documentation structure while simultaneously preparing README content updates, then synthesize findings and apply fixes.

**Tech Stack:** Markdown, Git, Bash for file operations

---

## Task 1: Audit Documentation Structure

**Files:**
- Read: Various docs in `docs/` directory
- Create: Temporary audit notes

**Step 1: List all documentation files**

Run: `find docs/ -name "*.md" -type f | head -50`
Expected: List of markdown files in docs directory

**Step 2: Validate README documentation link references**

Run: `grep -n "docs/" README.md | head -20`
Expected: List of all docs/ references in README

**Step 3: Check if referenced files exist**

Run: `grep -o "docs/[^\)]*" README.md | while read file; do [ -f "$file" ] && echo "✅ $file" || echo "❌ $file"; done`
Expected: Validation of each referenced file

**Step 4: Check recent progress documents for consistency**

Run: `head -20 E2E-TESTING-PROGRESS.md OVERNIGHT-SUMMARY-2026-03-09.md e2e-session-summary.md`
Expected: Overview of recent progress documentation

**Step 5: Identify quick wins**

Document: Note any obvious issues (typos, broken links, outdated status)

---

## Task 2: Prepare README Status Badges Section

**Files:**
- Modify: `README.md`
- Read: `E2E-TESTING-PROGRESS.md`, `OVERNIGHT-SUMMARY-2026-03-09.md`

**Step 1: Review current service status**

Read: `E2E-TESTING-PROGRESS.md` lines 1-50
Expected: Understanding of which services are working/need fixes

**Step 2: Create status badges markdown**

Add after line 9 (after existing badges):

```markdown
## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| SceneSpeak Agent (8001) | ✅ Working | /api/generate endpoint implemented |
| Captioning Agent (8002) | ✅ Working | WebSocket endpoint implemented |
| BSL Agent (8003) | ⚠️ Needs Fixes | 2 E2E tests failing |
| Sentiment Agent (8004) | ✅ Working | WebSocket + /api/analyze implemented |
| Music Generation (8011) | ✅ Working | All 17 E2E tests passing |
| Safety Filter (8006) | ✅ Working | /api/moderate endpoint implemented |
| Operator Console (8007) | ✅ Working | Show control endpoints implemented |
| OpenClaw Orchestrator (8000) | ✅ Working | /api/skills, /api/show endpoints |
| E2E Tests | ⚠️ In Progress | 82/94 passing (87%) - needs Docker rebuild |
```

**Step 3: Verify markdown formatting**

Run: `head -30 README.md`
Expected: Status badges section properly formatted

---

## Task 3: Create Current Status Section

**Files:**
- Modify: `README.md`

**Step 1: Add Current Status section after Overview (after line 12)**

```markdown
## Current Status

### ✅ Complete & Working

- All 8 core services have `/api/*` endpoints implemented
- WebSocket support for sentiment, captioning, and BSL agents
- Music generation platform fully functional (17/17 tests passing)
- Docker compose setup for local development
- Comprehensive E2E test suite (129 tests)

### ⚠️ Needs Fixes

- BSL Agent: 2 failing E2E tests (validation, renderer info)
- Captioning Agent: 2 failing E2E tests (needs Docker rebuild)
- Docker images need rebuild to pick up recent code changes

### 🚧 In Progress

- E2E test completion (target: 93%+ pass rate)
- UI test timing improvements
- Cross-service workflow integration

### 📋 Next Steps

1. Rebuild Docker services with new API endpoints
2. Fix remaining BSL and Captioning agent E2E failures
3. Improve UI test reliability (timeout adjustments)
4. Complete cross-service workflow tests
```

**Step 2: Verify section placement**

Run: `grep -n "## Current Status" README.md`
Expected: Section appears after Overview

---

## Task 4: Update Roadmap Section

**Files:**
- Modify: `README.md`
- Read: Current roadmap section

**Step 1: Locate current roadmap section**

Run: `grep -n "## Roadmap" README.md`
Expected: Line number of Roadmap section

**Step 2: Replace roadmap content (starting at v0.5.0)**

Replace from line with `### v0.5.0` to end of Roadmap section:

```markdown
## Roadmap

### v0.5.0 (Current - March 2026)

**Completed:**
- ✅ WebSocket endpoints for sentiment, captioning, and BSL agents
- ✅ Complete `/api/*` endpoint implementation across all services
- ✅ Music generation platform with ACE-Step integration
- ✅ Comprehensive E2E test suite (129 tests)
- ✅ WorldMonitor integration for enhanced sentiment analysis

**In Progress:**
- ⚠️ E2E test completion (87% passing, targeting 93%+)
- ⚠️ Docker rebuild to pick up recent code changes

**Recent Commits:**
- `f0a5281` - WebSocket endpoints for sentiment and captioning agents
- `044abf0` - /health, /api/skills, /api/show endpoints to orchestrator
- `b214b08` - /api/generate endpoint to scenespeak-agent
- `e0f4289` - /api/analyze endpoint to sentiment-agent
- `f804466` - /api/moderate endpoint to safety-filter
- `193383d` - Show control endpoints to operator-console

### v0.6.0 (Next - April 2026)

**Planned:**
- Fix remaining BSL Agent E2E failures
- Improve UI test reliability
- Complete cross-service workflow integration
- Enhanced monitoring and alerting
- Multi-scene support

### v1.0.0 (Future - Q2 2026)

**Planned:**
- Production-ready deployment
- Cloud deployment guides (AWS/GCP)
- Public performances
- Complete documentation suite
- Global context enrichment for real-time audience feedback
```

**Step 3: Verify roadmap format**

Run: `sed -n '/^## Roadmap/,/^## /p' README.md | head -50`
Expected: Formatted roadmap with proper sections

---

## Task 5: Add Quick Verification Section

**Files:**
- Modify: `README.md`

**Step 1: Find insertion point (before Documentation section)**

Run: `grep -n "^## Documentation" README.md`
Expected: Line number of Documentation section

**Step 2: Insert Quick Verification section before Documentation**

```markdown
## Quick Verification

Check if all services are running:

```bash
# Health checks for all services
for port in 8000 8001 8002 8003 8004 8006 8007 8011; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq '.' 2>/dev/null || echo "Not responding"
  echo "---"
done
```

Run E2E tests:

```bash
cd tests/e2e
npm test
```

Check Docker status:

```bash
docker compose ps
```

Rebuild services (if needed):

```bash
docker compose build safety-filter operator-console openclaw-orchestrator scenespeak-agent sentiment-agent captioning-agent
docker compose up -d
```

```

**Step 3: Verify code block formatting**

Run: `grep -A 20 "## Quick Verification" README.md`
Expected: Properly formatted code blocks

---

## Task 6: Fix Documentation Link References

**Files:**
- Modify: `README.md`
- Read: Various docs to verify paths

**Step 1: Find all docs/ references**

Run: `grep -n "](docs/" README.md`
Expected: List of all documentation references

**Step 2: Verify each referenced file exists**

For each reference:
```bash
# Check if file exists
[ -f "docs/reference/architecture.md" ] && echo "✅" || echo "❌ docs/reference/architecture.md"
[ -f "docs/reference/api.md" ] && echo "✅" || echo "❌ docs/reference/api.md"
[ -f "docs/reference/runbooks/deployment.md" ] && echo "✅" || echo "❌ docs/reference/runbooks/deployment.md"
```

**Step 3: Update broken links with correct paths**

Based on actual file locations found in Task 1, update any broken references.

**Step 4: Check services documentation links**

Run: `grep -A 10 "### Services Documentation" README.md`
Expected: Services documentation section with links

**Step 5: Verify or fix services docs**

If services docs don't exist at referenced paths, either:
- Create placeholder docs, or
- Remove broken references, or
- Update to correct paths

---

## Task 7: Update GitHub Section with Current Repository

**Files:**
- Modify: `README.md`

**Step 1: Find Community section**

Run: `grep -n "^## Community" README.md`
Expected: Line number of Community section

**Step 2: Update GitHub URLs to actual repository**

Replace repository URLs from `project-chimera/project-chimera` to actual:

```markdown
## Community

- **GitHub:** https://github.com/ranjrana2012-lab/project-chimera
- **Issues:** https://github.com/ranjrana2012-lab/project-chimera/issues
- **Discussions:** https://github.com/ranjrana2012-lab/project-chimera/discussions
```

**Step 3: Verify repository URL**

Run: `git remote get-url origin`
Expected: `https://github.com/ranjrana2012-lab/project-chimera.git`

---

## Task 8: Sync Progress Documents (if inconsistent)

**Files:**
- Read: `E2E-TESTING-PROGRESS.md`, `OVERNIGHT-SUMMARY-2026-03-09.md`, `e2e-session-summary.md`
- Modify: If inconsistencies found

**Step 1: Compare test status across documents**

Run: `grep -i "test.*passing\|tests.*failing" E2E-TESTING-PROGRESS.md OVERNIGHT-SUMMARY-2026-03-09.md e2e-session-summary.md`
Expected: Comparison of test status claims

**Step 2: Check for conflicting information**

Run: `grep -i "next steps\|remaining work" E2E-TESTING-PROGRESS.md OVERNIGHT-SUMMARY-2026-03-09.md`
Expected: Comparison of next steps

**Step 3: Harmonize if inconsistencies found**

If documents disagree on test status or next steps, update to reflect:
- 82/94 tests passing (87%)
- Main blocker: Docker rebuild needed
- After rebuild: Expected 89% pass rate

**Step 4: Ensure consistent commit references**

Verify all documents reference the same recent commits:
- `f0a5281` - WebSocket endpoints
- `044abf0` - Orchestrator endpoints
- `b214b08` - SceneSpeak endpoints
- `e0f4289` - Sentiment endpoints
- `f804466` - Safety filter endpoints
- `193383d` - Operator console endpoints

---

## Task 9: Final Validation

**Files:**
- Validate: `README.md`

**Step 1: Check markdown syntax**

Run: `python3 -m mdjson README.md 2>/dev/null || echo "Markdown validation not available, skipping"`
Expected: No critical markdown syntax errors

**Step 2: Verify all sections exist**

Run: `grep "^## " README.md`
Expected: List of all top-level sections including new ones

**Step 3: Check for TODO/FIXME placeholders**

Run: `grep -i "TODO\|FIXME\|XXX" README.md`
Expected: No placeholder TODOs (or intentional ones)

**Step 4: Verify no broken internal links**

Run: `grep -o "](#[^)]*)" README.md | sort -u`
Expected: List of internal anchor links

**Step 5: Test rendering (if mdv available)**

Run: `mdv README.md 2>/dev/null | head -100 || echo "Markdown preview not available"`
Expected: Formatted preview or skip message

---

## Task 10: Commit and Push Changes

**Files:**
- Commit: All modified files

**Step 1: Review all changes**

Run: `git diff README.md`
Expected: Show all README changes

**Step 2: Check if other docs were modified**

Run: `git status --short`
Expected: List of all modified files

**Step 3: Stage all changes**

Run: `git add README.md E2E-TESTING-PROGRESS.md OVERNIGHT-SUMMARY-2026-03-09.md 2>/dev/null || git add README.md`
Expected: Files staged for commit

**Step 4: Create commit**

Run: `git commit -m "$(cat <<'EOF'
docs: update README with current project status and fix documentation

- Add Project Status badges table showing all services
- Add Current Status section (Complete/Needs Fixes/In Progress/Next Steps)
- Update Roadmap with v0.5.0 achievements (WebSocket endpoints, API completions)
- Add Quick Verification section with health check and testing commands
- Fix broken documentation link references
- Update GitHub repository URLs to actual repository
- Sync progress documentation for consistency

Changes reflect current state as of 2026-03-09:
- 82/94 E2E tests passing (87%)
- All 8 core services have /api/* endpoints
- WebSocket support for sentiment, captioning, and BSL agents
- Main blocker: Docker rebuild needed for new code

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"`

Expected: Commit created successfully

**Step 5: Verify commit**

Run: `git log -1 --stat`
Expected: Show commit details with changed files

**Step 6: Push to GitHub**

Run: `git push origin main`
Expected: Changes pushed to remote repository

**Step 7: Verify on GitHub**

Visit: https://github.com/ranjrana2012-lab/project-chimera
Expected: Updated README visible on repository

---

## Success Criteria Verification

**Step 1: Verify README updates**

Check: `README.md` contains:
- ✅ Project Status badges table
- ✅ Current Status section with 4 subsections
- ✅ Updated Roadmap with v0.5.0 achievements
- ✅ Quick Verification section
- ✅ Fixed documentation links

**Step 2: Verify documentation consistency**

Check: All progress documents agree on:
- ✅ Test pass rate (87%)
- ✅ Recent commits
- ✅ Next steps (Docker rebuild)

**Step 3: Verify GitHub push**

Check: `git status`
Expected: `Your branch is up to date with 'origin/main'`

**Step 4: Final validation**

Run: `grep "^## " README.md | wc -l`
Expected: 12+ sections (original + new sections)

---

## Notes for Implementation

- **YAGNI:** Don't add future features to roadmap - only what's actually planned
- **DRY:** If information appears in multiple docs, keep it consistent
- **Honesty:** Don't overstate completion - be clear about what's in progress
- **TDD:** No tests needed for documentation changes, but validate links work
- **Frequent Commits:** One commit at the end is fine for doc changes

## Troubleshooting

**If documentation links are broken:**
1. Use `find docs/ -name "*.md"` to locate actual file paths
2. Update README references to match actual structure
3. If file doesn't exist, either create placeholder or remove reference

**If git push fails:**
1. Check `git remote -v` for correct repository
2. Ensure you have push access
3. Check `git log` to verify commit was created

**If markdown formatting looks wrong:**
1. Check code block fence formatting (```)
2. Ensure proper nesting of lists and subsections
3. Use `mdv` or similar tool to preview if available

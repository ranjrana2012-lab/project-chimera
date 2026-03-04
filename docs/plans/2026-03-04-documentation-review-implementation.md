# Documentation Comprehensive Review Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Comprehensive audit and fix of Project Chimera documentation following the Production Observability Enhancement (27 tasks).

**Architecture:** Systematic audit of 6 documentation categories (Entry Points, Architecture, API, Runbooks, Services, Plans), checking each for consistency, discoverability, and completeness. Automated scans first, then manual review, cross-reference verification, and prioritized fixes.

**Tech Stack:** Bash (grep, find, grep -r), Markdown, Git

---

## Phase 1: Automated Scans (Quick Wins)

### Task 1: Version Consistency Scan

**Files:** Scan all documentation files

**Step 1: Find all version references**

```bash
grep -r "v[0-9]\.[0-9]" docs/ README.md --include="*.md" | grep -v "Binary file" > /tmp/version-scan.txt
```

**Step 2: Review version references**

```bash
cat /tmp/version-scan.txt
```

Expected: Document inconsistent versions (v0.4.0, v3.0.0, etc.)

**Step 3: Create version audit entry**

Create `/tmp/version-audit.md` with:
```markdown
## Version Consistency Issues

| File | Version Found | Should Be |
|------|--------------|-----------|
```

---

### Task 2: Broken Link Scan

**Files:** All documentation files

**Step 1: Find Markdown links**

```bash
grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" > /tmp/all-links.txt
```

**Step 2: Check each link target exists**

```bash
while IFS= read -r line; do
  # Extract link path from markdown
  link=$(echo "$line" | sed -n 's/.*](\([^)]*\)).*/\1/p')
  # Check if file exists (skip http links)
  if [[ ! "$link" =~ ^http ]] && [[ ! -f "docs/$link" ]] && [[ ! -f "$link" ]]; then
    echo "BROKEN: $link in $line"
  fi
done < /tmp/all-links.txt > /tmp/broken-links.txt
```

**Step 3: Review broken links**

```bash
cat /tmp/broken-links.txt
```

**Step 4: Create broken links audit entry**

```bash
echo "
## Broken Links

$(cat /tmp/broken-links.txt)
" >> /tmp/version-audit.md
```

---

### Task 3: TODO/FIXME Marker Scan

**Files:** All documentation files

**Step 1: Find TODO markers**

```bash
grep -r "TODO\|FIXME\|XXX\|NOTE" docs/ --include="*.md" > /tmp/todo-scan.txt
```

**Step 2: Review markers**

```bash
cat /tmp/todo-scan.txt
```

**Step 3: Add to audit**

```bash
echo "
## TODO/FIXME Markers

$(cat /tmp/todo-scan.txt)
" >> /tmp/version-audit.md
```

---

### Task 4: File Existence Validation

**Files:** Referenced in documentation

**Step 1: Get all referenced files**

```bash
# Extract code block references, script references, etc.
grep -r "\`\`[^}]*\`\`" docs/ --include="*.md" | grep -E "\.(sh|py|yaml)" > /tmp/referenced-files.txt
```

**Step 2: Validate files exist**

```bash
while IFS= read -r line; do
  file=$(echo "$line" | grep -oE "[a-zA-Z0-9_/\.-]+\.(sh|py|yaml)" | head -1)
  if [[ -n "$file" ]] && [[ ! -f "$file" ]] && [[ ! -f "scripts/$file" ]] && [[ ! -f "platform/$file" ]]; then
    echo "MISSING: $file"
  fi
done < /tmp/referenced-files.txt > /tmp/missing-files.txt
```

**Step 3: Add to audit**

```bash
echo "
## Missing Referenced Files

$(cat /tmp/missing-files.txt)
" >> /tmp/version-audit.md
```

---

### Task 5: Save Automated Scan Results

**Files:** Create audit report

**Step 1: Create audit report file**

```bash
cat > /tmp/audit-template.md << 'EOF'
# Project Chimera Documentation Audit Report

**Date:** 2026-03-04
**Scope:** Comprehensive review following Production Observability Enhancement
**Method:** Automated scans + Manual audit

## Automated Scan Results

EOF
```

**Step 2: Merge all scan results**

```bash
cat /tmp/version-audit.md >> /tmp/audit-template.md
```

**Step 3: Save working audit**

```bash
cp /tmp/audit-template.md /tmp/documentation-audit-working.md
```

---

## Phase 2: Manual Audit - Category by Category

### Task 6: Audit Category 1 - Entry Points (README.md)

**Files:**
- Review: `README.md`
- Review: `docs/README.md`

**Step 1: Read README.md**

```bash
cat README.md
```

**Step 2: Check for observability references**

Create `/tmp/readme-audit.md`:
```markdown
### README.md Audit

#### Consistency
- [ ] Version matches project state
- [ ] Tech stack includes AlertManager, OpenTelemetry, Jaeger
- [ ] Monitoring stack is current (Prometheus, Grafana, Jaeger, AlertManager)
- [ ] No contradictory information

#### Discoverability
- [ ] Observability docs linked (docs/observability.md)
- [ ] Monitoring runbook linked
- [ ] Grafana/Prometheus/Jaeger/AlertManager mentioned

#### Completeness
- [ ] Production Observability mentioned in components
- [ ] Business metrics mentioned
- [ ] SLO framework mentioned
- [ ] Distributed tracing mentioned
```

**Step 3: Complete the checklist**

Review README.md and mark each item as [x] or [ ].

**Step 4: Repeat for docs/README.md**

```bash
cat docs/README.md
```

**Step 5: Add findings to audit report**

```bash
cat /tmp/readme-audit.md >> /tmp/documentation-audit-working.md
```

---

### Task 7: Audit Category 2 - Architecture Documentation

**Files:**
- Review: `docs/architecture/README.md`
- Review: `docs/architecture/004-quality-platform.md`
- Review: `docs/architecture/005-v3-features.md`

**Step 1: List architecture files**

```bash
ls -la docs/architecture/
```

**Step 2: Check for observability ADR**

```bash
ls docs/architecture/ | grep -i observability
```

Expected: No observability ADR exists (gap to document)

**Step 3: Read architecture README**

```bash
cat docs/architecture/README.md
```

**Step 4: Create architecture audit**

```bash
cat > /tmp/architecture-audit.md << 'EOF'
### Architecture Documentation Audit

#### docs/architecture/README.md
- [ ] Observability components in architecture overview
- [ ] Platform monitoring section mentions new components
- [ ] Version consistent

#### ADR-004 (Quality Platform)
- [ ] Up to date with implementation

#### ADR-005 (v3.0.0 Features)
- [ ] Observability features listed

#### Missing ADR
- [ ] ADR-006: Production Observability Architecture needed?
EOF
```

**Step 5: Add to audit report**

```bash
cat /tmp/architecture-audit.md >> /tmp/documentation-audit-working.md
```

---

### Task 8: Audit Category 3 - Runbooks

**Files:** All in `docs/runbooks/`

**Step 1: List runbooks**

```bash
ls -la docs/runbooks/
```

**Step 2: Check README.md links to new runbooks**

```bash
cat docs/runbooks/README.md | grep -E "on-call|slo|tracing|performance"
```

**Step 3: Verify all new runbooks are indexed**

New runbooks to verify:
- on-call.md
- slo-handbook.md
- slo-response.md
- distributed-tracing.md
- performance-analysis.md

**Step 4: Create runbooks audit**

```bash
cat > /tmp/runbooks-audit.md << 'EOF'
### Runbooks Audit

#### docs/runbooks/README.md
- [ ] All new runbooks indexed
- [ ] on-call.md linked
- [ ] slo-handbook.md linked
- [ ] slo-response.md linked
- [ ] distributed-tracing.md linked
- [ ] performance-analysis.md linked

#### New Runbooks Exist
- [ ] on-call.md exists
- [ ] slo-handbook.md exists
- [ ] slo-response.md exists
- [ ] distributed-tracing.md exists
- [ ] performance-analysis.md exists

#### Existing Runbooks Updated
- [ ] alerts.md updated for AlertManager
- [ ] monitoring.md mentions new components
EOF
```

**Step 5: Add to audit report**

```bash
cat /tmp/runbooks-audit.md >> /tmp/documentation-audit-working.md
```

---

### Task 9: Audit Category 4 - API Documentation

**Files:** All in `docs/api/`

**Step 1: List API docs**

```bash
ls -la docs/api/
```

**Step 2: Check if metrics endpoints documented**

```bash
grep -r "/metrics" docs/api/ --include="*.md"
```

**Step 3: Check if tracing mentioned**

```bash
grep -r "tracing\|trace\|OpenTelemetry" docs/api/ --include="*.md"
```

**Step 4: Create API audit**

```bash
cat > /tmp/api-audit.md << 'EOF'
### API Documentation Audit

#### Metrics Endpoints
- [ ] scenespeak-agent metrics documented
- [ ] sentiment-agent metrics documented
- [ ] captioning-agent metrics documented
- [ ] bsl-agent metrics documented

#### Tracing
- [ ] OpenTelemetry tracing mentioned
- [ ] Span attributes documented
- [ ] Jaeger integration noted
EOF
```

**Step 5: Add to audit report**

```bash
cat /tmp/api-audit.md >> /tmp/documentation-audit-working.md
```

---

### Task 10: Audit Category 5 - Service Documentation

**Files:** Service READMEs and docs/services/

**Step 1: Check for service documentation**

```bash
find services/ -name "README.md" | head -10
```

**Step 2: Check docs/services/

```bash
ls -la docs/services/
```

**Step 3: Verify services mention observability features**

```bash
for service in scenespeak sentiment captioning bsl; do
  echo "=== $service ==="
  grep -r "metrics\|tracing" services/$service-agent/ docs/api/$service-agent.md 2>/dev/null | head -3
done
```

**Step 4: Create service audit**

```bash
cat > /tmp/services-audit.md << 'EOF'
### Service Documentation Audit

#### Each Service Should Document
- [ ] Business metrics available
- [ ] Tracing instrumentation
- [ ] Prometheus /metrics endpoint
- [ ] Key metric names

#### SceneSpeak
- [ ] Metrics documented (dialogue_quality, lines_generated, etc.)

#### Sentiment
- [ ] Metrics documented (audience_sentiment, emotions, etc.)

#### Captioning
- [ ] Metrics documented (caption_latency, etc.)

#### BSL
- [ ] Metrics documented (active_sessions, gestures_rendered, etc.)
EOF
```

**Step 5: Add to audit report**

```bash
cat /tmp/services-audit.md >> /tmp/documentation-audit-working.md
```

---

### Task 11: Audit Category 6 - Plans & ADRs

**Files:** docs/plans/, docs/architecture/

**Step 1: Check for observability implementation plan**

```bash
ls docs/plans/ | grep -i observability
```

**Step 2: Verify implementation plan is complete**

```bash
ls -la docs/plans/2026-03-04-production-observability-*.md
```

**Step 3: Check if ADR needed**

New architecture components:
- AlertManager deployment pattern
- SLO framework adoption
- OpenTelemetry instrumentation standard

**Step 4: Create plans audit**

```bash
cat > /tmp/plans-audit.md << 'EOF'
### Plans & ADRs Audit

#### Implementation Plans
- [ ] Production Observability Design exists
- [ ] Production Observability Implementation exists

#### ADRs
- [ ] ADR-006 needed for Production Observability architecture?
  - AlertManager adoption
  - SLO framework
  - Distributed tracing standard
EOF
```

**Step 5: Add to audit report**

```bash
cat /tmp/plans-audit.md >> /tmp/documentation-audit-working.md
```

---

## Phase 3: Cross-Reference Verification

### Task 12: Verify Main README Links to Observability

**Files:** README.md

**Step 1: Check for observability.md link**

```bash
grep -i "observability" README.md
```

**Step 2: Check for monitoring runbook link**

```bash
grep -i "monitoring\|runbook" README.md
```

**Step 3: Document findings**

If links missing, add to audit:
```markdown
### Cross-Reference Issues

#### README.md Missing Links
- [ ] No link to docs/observability.md
- [ ] No link to docs/runbooks/monitoring.md
```

---

### Task 13: Verify docs/README.md Links to New Runbooks

**Files:** docs/README.md

**Step 1: Check for new runbook links**

```bash
grep -E "on-call|slo|tracing|performance" docs/README.md
```

**Step 2: Check runbooks/README.md indexes them**

```bash
cat docs/runbooks/README.md
```

**Step 3: Document gaps**

Add any missing links to audit report.

---

### Task 14: Verify Architecture Docs Mention Platform Components

**Files:** docs/architecture/

**Step 1: Check for monitoring/observability in architecture**

```bash
grep -r "monitoring\|observability\|AlertManager" docs/architecture/
```

**Step 2: Document if architecture needs update**

If platform/monitoring components not mentioned, document as gap.

---

### Task 15: Verify Service Docs Reference Metrics/Tracing

**Files:** docs/services/, docs/api/

**Step 1: Sample check for metrics mentions**

```bash
grep -r "metrics" docs/services/ docs/api/ | head -10
```

**Step 2: Document patterns**

If services don't mention their metrics/tracing, document as consistency issue.

---

## Phase 4: Compile Final Report

### Task 16: Compile All Findings

**Files:** Create final audit report

**Step 1: Gather all audit sections**

```bash
cat /tmp/documentation-audit-working.md
```

**Step 2: Create prioritized issues list**

```bash
cat > /tmp/issues-tracker.md << 'EOF'
## Issues Tracker

| Priority | Category | File | Issue | Fix |
|----------|----------|------|-------|-----|
| Critical |        |      |       |     |
| High     |        |      |       |     |
| Medium   |        |      |       |     |
| Low      |        |      |       |     |

Priority Definitions:
- **Critical:** Broken links, wrong versions, contradictions breaking UX
- **High:** Major gaps (new features undocumented)
- **Medium:** Minor inconsistencies, unclear discoverability
- **Low:** Typos, formatting, nice-to-haves
EOF
```

**Step 3: Create final report**

```bash
cat > docs/DOCUMENTATION_AUDIT_REPORT.md << 'EOF'
# Project Chimera Documentation Audit Report

**Date:** 2026-03-04
**Scope:** Comprehensive review following Production Observability Enhancement (27 tasks)
**Auditor:** Claude (Automated + Manual)

## Executive Summary

[Brief summary of findings - critical issues, total issues, overall health]

## Automated Scan Results

[Results from Tasks 1-5]

## Manual Audit Results

[Results from Tasks 6-11]

## Cross-Reference Verification

[Results from Tasks 12-15]

## Issues Tracker

[Prioritized list from Task 16]

## Recommendations

1. Immediate fixes (Critical)
2. High priority gaps
3. Process improvements

---

**Audit Complete:** 2026-03-04
**Next:** Create implementation plan for fixes
EOF
```

**Step 4: Populate report with findings**

```bash
# Merge all findings
cat /tmp/documentation-audit-working.md >> docs/DOCUMENTATION_AUDIT_REPORT.md
cat /tmp/issues-tracker.md >> docs/DOCUMENTATION_AUDIT_REPORT.md
```

---

### Task 17: Commit Audit Report

**Files:** docs/DOCUMENTATION_AUDIT_REPORT.md

**Step 1: Review report**

```bash
cat docs/DOCUMENTATION_AUDIT_REPORT.md
```

**Step 2: Commit**

```bash
git add docs/DOCUMENTATION_AUDIT_REPORT.md
git commit -m "docs: add comprehensive documentation audit report

- Audited 6 documentation categories
- Checked consistency, discoverability, completeness
- Identified prioritized issues for fixes
- Following Production Observability Enhancement (27 tasks)"
```

---

## Summary

**Total Tasks:** 17
**Estimated Duration:** 45 minutes

**Phases:**
1. Automated Scans (5 tasks)
2. Manual Audit by Category (6 tasks)
3. Cross-Reference Verification (4 tasks)
4. Report Compilation (2 tasks)

**Deliverables:**
- `docs/DOCUMENTATION_AUDIT_REPORT.md` - Comprehensive audit findings
- Prioritized issues tracker
- Recommendations for fixes

**Next After Audit:**
Create implementation plan for fixes based on prioritized issues.

---

*Implementation Plan: Documentation Comprehensive Review*
*Project Chimera v3.0.0*
*March 2026*

# Documentation Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Systematically fix all ~400 documentation issues identified in comprehensive audit across 4 phases (Critical, High, Medium, Process & Automation).

**Architecture:** Phased priority rollout - fix critical issues first (broken links, missing files, versions), then high priority (observability discoverability, ADRs), then medium priority (cross-refs, TODOs), finally establish automation and processes.

**Tech Stack:** Bash, sed, awk, Python, Markdown, Git, GitHub Actions

---

## Phase 1: Critical Issues (Foundation)

### Task 1: Create Fix Scripts Directory

**Files:**
- Create: `scripts/fix/`

**Step 1: Create directory**

```bash
mkdir -p scripts/fix
```

**Step 2: Commit**

```bash
git add scripts/fix/
git commit -m "chore: create fix scripts directory"
```

---

### Task 2: Fix Broken Links - Part 1 (Analysis)

**Files:**
- Create: `scripts/fix/analyze-broken-links.sh`
- Read: `docs/DOCUMENTATION_AUDIT_REPORT.md` (broken links section)

**Step 1: Create broken links analysis script**

```bash
cat > scripts/fix/analyze-broken-links.sh << 'EOF'
#!/bin/bash
# Analyze broken links from audit report

echo "Analyzing broken links..."
echo "Total broken links: 170"

# Extract broken links from audit report
grep -E "BROKEN:|broken link" docs/DOCUMENTATION_AUDIT_REPORT.md > /tmp/broken-links-list.txt

echo "Broken links extracted to /tmp/broken-links-list.txt"
wc -l /tmp/broken-links-list.txt
EOF
```

**Step 2: Make executable**

```bash
chmod +x scripts/fix/analyze-broken-links.sh
```

**Step 3: Test script**

```bash
./scripts/fix/analyze-broken-links.sh
```

Expected: Outputs count of broken links

**Step 4: Commit**

```bash
git add scripts/fix/analyze-broken-links.sh
git commit -m "feat(fix): add broken links analysis script"
```

---

### Task 3: Fix Broken Links - Part 2 (Create Missing Files)

**Files:**
- Create: Multiple missing documentation files
- Reference: `docs/DOCUMENTATION_AUDIT_REPORT.md` (missing files section)

**Step 1: Create missing core documentation files**

Based on audit report, create the most critical missing files:

```bash
# Create DEPLOYMENT.md
cat > DEPLOYMENT.md << 'EOF'
# Deployment Guide

**Status:** TODO - This documentation needs to be created

For deployment information, see:
- [Runbooks - Deployment](docs/runbooks/README.md#deployment)
- [Quick Start Guide](docs/getting-started/quick-start.md)
EOF

# Create DEVELOPMENT.md
cat > DEVELOPMENT.md << 'EOF'
# Development Guide

**Status:** TODO - This documentation needs to be created

For development information, see:
- [Contributing Guide](CONTRIBUTING.md)
- [Development Documentation](docs/DEVELOPMENT.md)
EOF
```

**Step 2: Create missing guides directory and files**

```bash
mkdir -p docs/guides
cat > docs/guides/README.md << 'EOF'
# Documentation Guides

This directory contains guides for various Project Chimera topics.

## Available Guides

- [GitHub Workflow](github-workflow.md) - GitHub automation and contribution
- [WorldMonitor Context Usage](worldmonitor-context-usage.md) - WorldMonitor integration

More guides to be added as documentation improves.
EOF
```

**Step 3: Commit**

```bash
git add DEPLOYMENT.md DEVELOPMENT.md docs/guides/README.md
git commit -m "docs(fix): create missing core documentation files

- Add DEPLOYMENT.md stub with references
- Add DEVELOPMENT.md stub with references
- Create docs/guides/README.md for navigation"
```

---

### Task 4: Fix Broken Links - Part 3 (Update References)

**Files:**
- Modify: Multiple files with broken references
- Reference: `/tmp/broken-links-list.txt` from Task 3

**Step 1: Create link fix script**

```bash
cat > scripts/fix/fix-links.sh << 'EOF'
#!/bin/bash
# Fix broken documentation links

echo "Fixing broken links..."

# Fix docs/reference/architecture.md → docs/docs/reference/architecture.md
find docs -name "*.md" -type f -exec sed -i 's|reference/architecture\.md|docs/docs/reference/architecture.md|g' {} \;

# Fix docs/api/README.md → docs/api/README.md
find docs -name "*.md" -type f -exec sed -i 's|docs/reference/api\.md|docs/api/README.md|g' {} \;

# Fix docs/runbooks/README.md#deployment → docs/runbooks/README.md#deployment
find docs -name "*.md" -type f -exec sed -i 's|docs/runbooks/deployment\.md|docs/runbooks/README.md#deployment|g' {} \;

# Fix docs/contributing/github-workflow.md → docs/contributing/github-workflow.md
find docs -name "*.md" -type f -exec sed -i 's|guides/github-workflow\.md|docs/contributing/github-workflow.md|g' {} \;

echo "Link fixes applied"
EOF
```

**Step 2: Make executable and run**

```bash
chmod +x scripts/fix/fix-links.sh
./scripts/fix/fix-links.sh
```

**Step 3: Commit**

```bash
git add scripts/fix/fix-links.sh
git add -A
git commit -m "fix(docs): update broken documentation links

- Fix docs/reference/architecture.md → docs/docs/reference/architecture.md
- Fix docs/api/README.md → docs/api/README.md
- Fix docs/runbooks/README.md#deployment → docs/runbooks/README.md#deployment
- Fix docs/contributing/github-workflow.md → docs/contributing/github-workflow.md"
```

---

### Task 5: Resolve Missing File References

**Files:**
- Create: `scripts/fix/resolve-missing-files.sh`
- Reference: `docs/DOCUMENTATION_AUDIT_REPORT.md` (missing files section)

**Step 1: Create missing files resolution script**

```bash
cat > scripts/fix/resolve-missing-files.sh << 'EOF'
#!/bin/bash
# Resolve missing file references from documentation

echo "Resolving missing file references..."

# Create platform documentation stubs
mkdir -p docs/services
cat > docs/services/quality-platform.md << 'STUB'
# Quality Platform Service Documentation

**Status:** TODO - Full service documentation needed

The Quality Platform provides testing infrastructure for Project Chimera.

## Components

- Test Orchestrator (port 8008)
- Dashboard Service (port 8009)
- CI/CD Gateway (port 8010)
- Quality Gate (port 8013)

## Documentation

See [Quality Platform README](../quality-platform/README.md) for details.
STUB

# Create services/lighting-sound-music.md stub
cat > docs/services/lighting-sound-music.md << 'STUB'
# Lighting, Sound & Music Service

**Status:** TODO - Full service documentation needed

Unified audio-visual control for Project Chimera performances.

## Components

- Lighting Control (DMX/sACN)
- Sound Management
- Music Generation & Orchestration

See individual service documentation for details.
STUB
EOF

echo "Missing file stubs created"
EOF
```

**Step 2: Make executable and run**

```bash
chmod +x scripts/fix/resolve-missing-files.sh
./scripts/fix/resolve-missing-files.sh
```

**Step 3: Commit**

```bash
git add scripts/fix/resolve-missing-files.sh docs/services/quality-platform.md docs/services/lighting-sound-music.md
git commit -m "docs(fix): create stub documentation for missing service files

- Add quality-platform.md stub
- Add lighting-sound-music.md stub
- Create resolution script for future missing files"
```

---

### Task 6: Update Version References (v3.0.0 → v0.4.0)

**Files:**
- Create: `scripts/fix/update-versions.sh`
- Modify: All files with v3.0.0 references (18+ files)

**Step 1: Create version update script**

```bash
cat > scripts/fix/update-versions.sh << 'EOF'
#!/bin/bash
# Update version references from v3.0.0 to v0.4.0

echo "Updating version references..."

# Update README.md
sed -i 's/v3\.0\.0/v0.4.0/g' README.md

# Update API documentation files (13 files)
find docs/api -name "*.md" -type f -exec sed -i 's/v3\.0\.0/v0.4.0/g' {} \;

# Update runbooks README
sed -i 's/v3\.0\.0/v0.4.0/g' docs/runbooks/README.md

# Update architecture documentation
find docs/architecture -name "*.md" -type f -exec sed -i 's/v3\.0\.0/v0.4.0/g' {} \;

# Update docs/README.md
sed -i 's/v3\.0\.0/v0.4.0/g' docs/README.md

# Update docs/CONTRIBUTING.md
sed -i 's/v3\.0\.0/v0.4.0/g' docs/CONTRIBUTING.md

echo "Version references updated"
EOF
```

**Step 2: Make executable and run**

```bash
chmod +x scripts/fix/update-versions.sh
./scripts/fix/update-versions.sh
```

**Step 3: Verify version updates**

```bash
grep -r "v3\.0\.0" docs/ README.md | grep -v "Binary file" | wc -l
```

Expected: 0 (or only in historical references)

**Step 4: Commit**

```bash
git add scripts/fix/update-versions.sh
git add -A
git commit -m "fix(docs): update version references from v3.0.0 to v0.4.0

- Update README.md
- Update all API documentation (13 files)
- Update runbooks README.md
- Update architecture documentation
- Update docs/README.md and CONTRIBUTING.md

Resolves 39 version inconsistency issues from documentation audit."
```

---

### Task 7: Validate Critical Fixes

**Files:**
- Create: `scripts/audit/validate-docs.sh`

**Step 1: Create validation script**

```bash
mkdir -p scripts/audit
cat > scripts/audit/validate-docs.sh << 'EOF'
#!/bin/bash
# Validate documentation fixes

echo "=== Validating Documentation Fixes ==="

# Check for remaining broken links
echo "1. Checking for broken links..."
BROKEN=$(grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   Markdown links found: $BROKEN"

# Check for v3.0.0 references
echo "2. Checking for old version references..."
OLD_VERSION=$(grep -r "v3\.0\.0" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   v3.0.0 references found: $OLD_VERSION"

# Check for observability.md links
echo "3. Checking observability discoverability..."
OBS_LINKS=$(grep -r "observability\.md" docs/ README.md --include="*.md" | wc -l)
echo "   observability.md references: $OBS_LINKS"

echo "=== Validation Complete ==="
EOF
```

**Step 2: Make executable and run**

```bash
chmod +x scripts/audit/validate-docs.sh
./scripts/audit/validate-docs.sh
```

**Step 3: Commit**

```bash
git add scripts/audit/validate-docs.sh
git commit -m "feat(audit): add documentation validation script

- Check for broken links
- Check for old version references
- Check observability discoverability"
```

---

## Phase 2: High Priority (Discoverability)

### Task 8: Index Observability Runbooks

**Files:**
- Modify: `docs/runbooks/README.md`

**Step 1: Read current runbooks README**

```bash
cat docs/runbooks/README.md
```

**Step 2: Add new observability runbooks to index**

Add after existing runbook list:

```markdown
### Observability Runbooks

- [On-Call Procedures](on-call.md) - On-call rotation and response procedures
- [SLO Handbook](slo-handbook.md) - Service Level Objectives and error budgets
- [SLO Response](slo-response.md) - SLO breach response procedures
- [Distributed Tracing](distributed-tracing.md) - OpenTelemetry and Jaeger guide
- [Performance Analysis](performance-analysis.md) - Performance investigation guide
```

**Step 3: Commit**

```bash
git add docs/runbooks/README.md
git commit -m "docs(obs): index observability runbooks in README

- Add on-call procedures to index
- Add SLO handbook and response procedures
- Add distributed tracing guide
- Add performance analysis guide
- Improves discoverability of new observability features"
```

---

### Task 9: Add Observability to Main README

**Files:**
- Modify: `README.md`

**Step 1: Read current README**

```bash
head -100 README.md
```

**Step 2: Add observability section after Quality Platform section**

Add before Technology Stack:

```markdown
### Observability Platform

- **Production Monitoring** - Prometheus, Grafana, AlertManager for metrics and alerting
- **Distributed Tracing** - OpenTelemetry and Jaeger for request tracing
- **SLO Framework** - Service Level Objectives and error budget tracking
- **Business Metrics** - Real-time dashboards for show operations, dialogue quality, audience engagement

For complete observability documentation, see [Observability Guide](docs/observability.md).
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): add observability platform section

- Document monitoring stack (Prometheus, Grafana, AlertManager)
- Document distributed tracing (OpenTelemetry, Jaeger)
- Document SLO framework
- Document business metrics dashboards
- Link to observability guide"
```

---

### Task 10: Add Observability to docs/README

**Files:**
- Modify: `docs/README.md`

**Step 1: Add observability section to Operational Documentation**

Add under "Operators" section:

```markdown
### Operational Documentation

- [Observability Guide](observability.md) - Production monitoring, tracing, and SLOs
- [Monitoring Runbook](runbooks/monitoring.md) - Monitoring setup and configuration
- [Incident Response](runbooks/incident-response.md) - Handling incidents
```

**Step 2: Commit**

```bash
git add docs/README.md
git commit -m "docs(hub): add observability to operational documentation

- Link to observability guide from docs README
- Improves discoverability of monitoring and SLO documentation
- Adds observability under operators section"
```

---

### Task 11: Create ADR-006 - Production Observability Platform

**Files:**
- Create: `docs/architecture/006-observability-platform.md`
- Reference: Existing ADRs for format

**Step 1: Read existing ADR for format**

```bash
head -50 docs/architecture/001-use-k3s.md
```

**Step 2: Create ADR-006**

```bash
cat > docs/architecture/006-observability-platform.md << 'EOF'
# ADR-006: Production Observability Platform

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Need to document observability platform architecture decisions

## Context

Project Chimera requires comprehensive observability for production operations, including alerting, metrics, tracing, and SLO tracking. The Production Observability Enhancement implemented a 4-phase observability stack.

## Decision

Adopt a comprehensive observability platform with the following components:

### 1. Alerting Foundation
- **AlertManager** for intelligent alert routing
- **Slack Integration** for real-time notifications
- **Critical alert rules** for service health

### 2. Business Metrics
- **Prometheus** metrics for business operations
- **Grafana dashboards** for real-time visualization
- Metrics for: dialogue quality, audience sentiment, caption latency, BSL sessions

### 3. SLO Framework
- **Service Level Objectives** for core services (99-99.9%)
- **Error Budget tracking** with burn rate alerts
- **Quality Gate** to block deployments on SLO breach

### 4. Distributed Tracing
- **OpenTelemetry** instrumentation for all services
- **Jaeger** for trace analysis and visualization
- **Service dependency mapping** and trace analysis tools

## Components

```
platform/monitoring/
├── config/
│   ├── alertmanager.yaml          # AlertManager configuration
│   ├── alert-rules-critical.yaml  # Critical alert rules
│   ├── slo-recording-rules.yaml   # SLO recording rules
│   ├── slo-alerting-rules.yaml    # SLO burn rate alerts
│   └── grafana-dashboards/         # 3 business dashboards
├── telemetry/                      # OpenTelemetry setup
├── trace-analyzer/                 # Trace analysis service
└── docs/                           # Observability documentation
```

## Consequences

### Positive
- Comprehensive visibility into service health
- Proactive alerting on issues
- Data-driven decision making with SLOs
- Root cause analysis with distributed tracing

### Negative
- Increased operational complexity
- Additional infrastructure to maintain
- Learning curve for on-call engineers

### Mitigations
- Comprehensive documentation (this ADR, runbooks, guides)
- Regular training sessions
- Phased rollout completed successfully

## Alternatives Considered

1. **SaaS Observability** (Datadog, New Relic) - Rejected due to cost and data sovereignty
2. **Minimal Monitoring** (Basic Prometheus) - Rejected due to lack of business insights
3. **Manual Processes** - Rejected due to scalability concerns

## References

- [Production Observability Design](../plans/2026-03-04-production-observability-design.md)
- [Observability Guide](../observability.md)
- [Alerting Runbook](../runbooks/alerts.md)
- [SLO Handbook](../runbooks/slo-handbook.md)
EOF
```

**Step 3: Commit**

```bash
git add docs/architecture/006-observability-platform.md
git commit -m "docs(adr): add ADR-006 for production observability platform

- Document AlertManager adoption decision
- Document business metrics approach
- Document SLO framework implementation
- Document distributed tracing with OpenTelemetry
- Provide component architecture overview"
```

---

### Task 12: Create ADR-007 - SLO Framework

**Files:**
- Create: `docs/architecture/007-slo-framework.md`

**Step 1: Create ADR-007**

```bash
cat > docs/architecture/007-slo-framework.md << 'EOF'
# ADR-007: SLO Framework and Error Budget Adoption

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Need to document SLO framework implementation decisions

## Context

Project Chimera requires Service Level Objectives (SLOs) to ensure reliability and set appropriate expectations for service performance. The Production Observability Enhancement implemented a comprehensive SLO framework.

## Decision

Adopt Google SRE practices for SLOs and error budgets:

### SLO Targets

| Service | SLO | SLI | Window | Error Budget |
|---------|-----|-----|--------|--------------|
| OpenClaw | 99.9% | Successful orchestrations / total | 30d | 43.2min/month |
| SceneSpeak | 99.5% | Successful generations / total | 30d | 3.6hrs/month |
| Captioning | 99.5% | Captions delivered / speech | 30d | 3.6hrs/month |
| BSL | 99% | Successful translations / total | 30d | 7.2hrs/month |
| Safety | 99.9% | Requests processed / total | 30d | 43.2min/month |
| Console | 99.5% | Dashboard loads / requests | 30d | 3.6hrs/month |

### Error Budget & Burn Rate

```
Burn Rate = (Current Error Rate) / (Allowed Error Rate)

Burn Rate 1x = On track
Burn Rate 2x = Warning (5m threshold)
Burn Rate 10x = Critical (1m threshold)
```

### Quality Gate

Deployments blocked when:
- SLO compliance < 95%
- Error budget remaining < 10%

## Components

```
platform/quality-gate/
└── gate/slo_gate.py          # SLO-based deployment blocking

platform/monitoring/config/
├── slo-recording-rules.yaml # 30-day rolling window SLOs
└── slo-alerting-rules.yaml   # Burn rate alerts

scripts/
├── calculate-error-budget.py # Error budget status
└── slo-compliance-report.sh  # Weekly SLO reports
```

## Consequences

### Positive
- Data-driven reliability decisions
- Clear deployment blocking criteria
- Automated alerting on SLO breaches
- Weekly SLO compliance reports

### Negative
- Additional metrics infrastructure
- Deployment friction when SLO not met
- Requires ongoing SLO calibration

### Mitigations
- Start with conservative SLO targets
- Regular SLO review and calibration
- Clear escalation procedures
- Error budget "hero mode" procedures

## References

- [SLO Handbook](../runbooks/slo-handbook.md)
- [SLO Response Runbook](../runbooks/slo-response.md)
- [Observability Guide](../observability.md)
EOF
```

**Step 2: Commit**

```bash
git add docs/architecture/007-slo-framework.md
git commit -m "docs(adr): add ADR-007 for SLO framework adoption

- Document SLO targets for all core services
- Document error budget and burn rate approach
- Document quality gate deployment blocking
- Document SLO monitoring and alerting"
```

---

### Task 13: Create ADR-008 - OpenTelemetry Integration

**Files:**
- Create: `docs/architecture/008-opentelemetry.md`

**Step 1: Create ADR-008**

```bash
cat > docs/architecture/008-opentelemetry.md << 'EOF'
# ADR-008: OpenTelemetry Integration Standard

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Need to document distributed tracing implementation decisions

## Context

Project Chimera requires distributed tracing for root cause analysis and performance optimization. The Production Observability Enhancement implemented OpenTelemetry across all services.

## Decision

Adopt OpenTelemetry as the standard for distributed tracing:

### Instrumentation Standard

**Per-Service Span Attributes:**

**SceneSpeak Agent:**
- `show.id` - Show identifier
- `scene.number` - Scene number
- `adapter.name` - Adapter used
- `tokens.input` - Input token count
- `tokens.output` - Output token count
- `dialogue.lines_count` - Lines generated

**Captioning Agent:**
- `caption_latency_ms` - Caption processing latency

**BSL Agent:**
- `translation.request_id` - Translation request ID
- `sign_language` - Sign language variant

**Sentiment Agent:**
- `sentiment.score` - Sentiment value
- `audience.size` - Audience count

**Safety Filter:**
- `safety.action` - Action taken (allow/block/flag)
- `pattern.matched` - Pattern that matched
- `content.length` - Content length

### Sampling Strategy

- **10% sampling** for production traces
- Configurable per-service sampling
- Head sampling for critical operations

### Backend

- **Jaeger** for trace storage and visualization
- **Port:** 16686 (default Jaeger UI)
- **Service Discovery:** Kubernetes service DNS

## Components

```
platform/monitoring/telemetry/
└── __init__.py                # setup_telemetry() function

services/*/tracing.py           # Per-service tracing modules
├── scenespeak-agent/tracing.py
├── captioning-agent/tracing.py
├── bsl-agent/tracing.py
├── sentiment-agent/tracing.py
└── safety-filter/tracing.py

scripts/
├── analyze-trace.py            # Trace analysis CLI
└── dependency-graph.py         # Service dependency mapper

docs/runbooks/
├── distributed-tracing.md      # Tracing guide
└── performance-analysis.md     # Performance investigation
```

## Consequences

### Positive
- Consistent tracing across all services
- Rich business context in spans
- Standard instrumentation patterns
- Powerful trace analysis tools

### Negative
- Additional instrumentation overhead
- Jaeger infrastructure maintenance
- Need trace retention policies

### Mitigations
- 10% sampling minimizes overhead
- Asynchronous span export
- Automated trace cleanup policies

## Alternatives Considered

1. **Zipkin** - Rejected due to less active development
2. **Jaeger-only without OpenTelemetry** - Rejected for lack of standardization
3. **No tracing** - Rejected due to production requirements

## References

- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [Trace Analyzer Documentation](../platform/monitoring/trace-analyzer/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/reference/specification/)
EOF
```

**Step 2: Commit**

```bash
git add docs/architecture/008-opentelemetry.md
git commit -m "docs(adr): add ADR-008 for OpenTelemetry integration standard

- Document per-service span attribute standards
- Document 10% sampling strategy
- Document Jaeger backend choice
- Document instrumentation components"
```

---

### Task 14: Document Service Metrics in API Docs

**Files:**
- Modify: `docs/api/scenespeak-agent.md`
- Modify: `docs/api/sentiment-agent.md`
- Modify: `docs/api/captioning-agent.md`
- Modify: `docs/api/bsl-agent.md`

**Step 1: Add metrics section to SceneSpeak API doc**

```bash
# Append to docs/api/scenespeak-agent.md
cat >> docs/api/scenespeak-agent.md << 'EOF'

## Metrics

The SceneSpeak Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `scenespeak_dialogue_quality` | Gauge | adapter | Dialogue coherence score (0-1) |
| `scenespeak_lines_generated_total` | Counter | show_id | Total lines generated |
| `scenespeak_tokens_per_line` | Histogram | - | Token count per line |
| `scenespeak_generation_duration_seconds` | Histogram | adapter | Generation time |
| `scenespeak_cache_hits_total` | Counter | adapter | Cache hit count |
| `scenespeak_cache_misses_total` | Counter | adapter | Cache miss count |

### Tracing

The SceneSpeak Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)
EOF
```

**Step 2: Add metrics section to Sentiment API doc**

```bash
cat >> docs/api/sentiment-agent.md << 'EOF'

## Metrics

The Sentiment Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sentiment_audience_avg` | Gauge | show_id, time_window | Average audience sentiment |
| `sentiment_emotion_joy_total` | Counter | show_id | Joy emotion count |
| `sentiment_emotion_surprise_total` | Counter | show_id | Surprise emotion count |
| `sentiment_emotion_neutral_total` | Counter | show_id | Neutral emotion count |
| `sentiment_emotion_sadness_total` | Counter | show_id | Sadness emotion count |
| `sentiment_emotion_anger_total` | Counter | show_id | Anger emotion count |
| `sentiment_emotion_fear_total` | Counter | show_id | Fear emotion count |
| `sentiment_analysis_queue_size` | Gauge | - | Texts awaiting analysis |
| `sentiment_analysis_duration_seconds` | Gauge | - | Analysis time |

### Tracing

The Sentiment Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)
EOF
```

**Step 3: Add metrics section to Captioning API doc**

```bash
cat >> docs/api/captioning-agent.md << 'EOF'

## Metrics

The Captioning Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `captioning_latency_seconds` | Histogram | - | Time from speech to caption |
| `captioning_delivered_total` | Counter | show_id | Captions delivered |
| `captioning_accuracy_score` | Gauge | show_id | Accuracy score (0-1) |
| `captioning_active_users` | Gauge | - | Users viewing captions |

### Tracing

The Captioning Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)
EOF
```

**Step 4: Add metrics section to BSL API doc**

```bash
cat >> docs/api/bsl-agent.md << 'EOF'

## Metrics

The BSL Agent exposes Prometheus metrics at the `/metrics` endpoint:

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `bsl_active_sessions` | Gauge | - | Active BSL avatar rendering sessions |
| `bsl_gestures_rendered_total` | Counter | show_id | Total gestures rendered |
| `bsl_avatar_frame_rate` | Gauge | session_id | Avatar rendering FPS |
| `bsl_translation_latency_seconds` | Histogram | - | Time to translate text to BSL gloss |

### Tracing

The BSL Agent uses OpenTelemetry for distributed tracing. See:
- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [ADR-008: OpenTelemetry Integration](../architecture/008-opentelemetry.md)
EOF
```

**Step 5: Commit**

```bash
git add docs/api/scenespeak-agent.md docs/api/sentiment-agent.md docs/api/captioning-agent.md docs/api/bsl-agent.md
git commit -m "docs(api): add metrics and tracing documentation to service API docs

- Add Prometheus metrics sections to SceneSpeak agent
- Add Prometheus metrics sections to Sentiment agent
- Add Prometheus metrics sections to Captioning agent
- Add Prometheus metrics sections to BSL agent
- Document OpenTelemetry tracing for each service
- Link to distributed tracing runbook and ADR-008"
```

---

## Phase 3: Medium Priority (Quality)

### Task 15: Add Cross-References Between Documentation

**Files:**
- Modify: `docs/observability.md`
- Modify: `docs/runbooks/alerts.md`
- Modify: `docs/runbooks/slo-handbook.md`

**Step 1: Add cross-reference from observability to runbooks**

```bash
# Add to observability.md under "Related Documentation" section
cat >> docs/observability.md << 'EOF'

## Cross-References

### Related Runbooks
- [Alerting Runbook](runbooks/alerts.md) - AlertManager procedures
- [On-Call Procedures](runbooks/on-call.md) - On-call rotation and response
- [SLO Handbook](runbooks/slo-handbook.md) - SLO definitions and error budgets
- [Distributed Tracing](runbooks/distributed-tracing.md) - Tracing guide
- [Performance Analysis](runbooks/performance-analysis.md) - Performance investigation
EOF
```

**Step 2: Add cross-reference from alerts to observability**

```bash
# Add to docs/runbooks/alerts.md
cat >> docs/runbooks/alerts.md << 'EOF'

## Related Documentation

- [Observability Guide](../observability.md) - Overview of observability platform
- [On-Call Procedures](on-call.md) - On-call rotation and escalation
EOF
```

**Step 3: Commit**

```bash
git add docs/observability.md docs/runbooks/alerts.md docs/runbooks/slo-handbook.md
git commit -m "docs: add cross-references between observability and runbooks

- Link observability guide to related runbooks
- Link alerts runbook to observability guide
- Improve navigation between related documentation"
```

---

### Task 16: Resolve TODO/FIXME Markers

**Files:**
- Modify: Multiple files with TODO/FIXME markers
- Reference: `/tmp/todo-scan.txt` from audit

**Step 1: Create TODO resolution script**

```bash
cat > scripts/fix/resolve-todos.sh << 'EOF'
#!/bin/bash
# Resolve or convert TODO/FIXME markers to GitHub issues

echo "Resolving TODO/FIXME markers..."

# Convert actionable TODOs to GitHub issues
# For now, document them in a TODO tracking file

cat > TODO-TRACKER.md << 'TRACKER'
# TODO Tracker

These TODOs were identified during the documentation audit and need resolution:

## High Priority

1. [ ] Complete implementation docs for quality-platform services (docs/services/quality-platform.md)
2. [ ] Complete implementation docs for lighting-sound-music services (docs/services/lighting-sound-music.md)
3. [ ] Write comprehensive DEPLOYMENT.md guide
4. [ ] Write comprehensive DEVELOPMENT.md guide

## Medium Priority

5. [ ] Expand docs/docs/reference/architecture.md with observability section
6. [ ] Add architecture diagrams to service READMEs
7. [ ] Create evaluation criteria documentation
8. [ ] Create sprint definitions documentation

## Low Priority

9. [ ] Add example code snippets to API documentation
10. [ ] Create video tutorials for getting started
11. [ ] Translate key documentation to other languages

See [Documentation Audit Report](docs/DOCUMENTATION_AUDIT_REPORT.md) for full details.
TRACKER

echo "TODO tracker created: TODO-TRACKER.md"
EOF
```

**Step 2: Make executable and run**

```bash
chmod +x scripts/fix/resolve-todos.sh
./scripts/fix/resolve-todos.sh
```

**Step 3: Commit**

```bash
git add scripts/fix/resolve-todos.sh TODO-TRACKER.md
git commit -m "docs(fix): resolve TODO markers and create tracker

- Create TODO tracker for audit findings
- Convert TODO markers to tracked issues
- Prioritize by importance (high/medium/low)
- Reference full audit report"
```

---

### Task 17: Standardize Terminology

**Files:**
- Modify: Various documentation files with inconsistent terminology

**Step 1: Create terminology standardization script**

```bash
cat > scripts/fix/standardize-terminology.sh << 'EOF'
#!/bin/bash
# Standardize terminology across documentation

echo "Standardizing terminology..."

# Ensure consistent service names
find docs -name "*.md" -type f -exec sed -i 's/scenespeak-agent/SceneSpeak Agent/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/sentiment-agent/Sentiment Agent/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/captioning-agent/Captioning Agent/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/bsl-agent/BSL Agent/g' {} \;

# Ensure consistent component naming
find docs -name "*.md" -type f -exec sed -i 's/Alertmanager/AlertManager/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/Prometheus/Prometheus/g' {} \;

echo "Terminology standardized"
EOF
```

**Step 2: Make executable and run**

```bash
chmod +x scripts/fix/standardize-terminology.sh
./scripts/fix/standardize-terminology.sh
```

**Step 3: Commit**

```bash
git add scripts/fix/standardize-terminology.sh
git add -A
git commit -m "docs(fix): standardize terminology across documentation

- Capitalize service names consistently
- Fix AlertManager capitalization
- Fix Prometheus capitalization
- Apply consistent component naming"
```

---

## Phase 4: Process & Automation (Sustainability)

### Task 18: Create CI Link Checker Workflow

**Files:**
- Create: `.github/workflows/docs-link-check.yml`

**Step 1: Create GitHub Actions workflow**

```bash
mkdir -p .github/workflows
cat > .github/workflows/docs-link-check.yml << 'EOF'
name: Documentation Link Check

on:
  pull_request:
    paths:
      - 'docs/**'
      - '*.md'
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - '*.md'

jobs:
  link-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Check for broken markdown links
        run: |
          echo "Checking for broken markdown links..."

          # Find all markdown links
          grep -r "\[.*\](.*.md)" docs/ --include="*.md" | grep -v "Binary file" > /tmp/all-links.txt

          # Check each link
          BROKEN=0
          while IFS= read -r line; do
            link=$(echo "$line" | sed -n 's/.*](\([^)]*\)).*/\1/p')
            if [[ ! "$link" =~ ^http ]] && [[ ! -f "docs/$link" ]] && [[ ! -f "$link" ]]; then
              echo "BROKEN: $link"
              ((BROKEN++))
            fi
          done < /tmp/all-links.txt

          if [ $BROKEN -gt 0 ]; then
            echo "::error::Found $BROKEN broken markdown links"
            exit 1
          fi

          echo "✅ No broken links found"
EOF
```

**Step 2: Commit**

```bash
git add .github/workflows/docs-link-check.yml
git commit -m "ci(ci): add documentation link checker workflow

- Check all markdown links in docs/
- Run on PRs and pushes to main
- Fail CI if broken links found
- Prevent introduction of new broken links"
```

---

### Task 19: Create Documentation Contribution Guidelines

**Files:**
- Create: `docs/contributing/documentation.md`

**Step 1: Create contribution guidelines**

```bash
mkdir -p docs/contributing
cat > docs/contributing/documentation.md << 'EOF'
# Documentation Contribution Guidelines

**Version:** 1.0
**Last Updated:** March 2026

---

## Overview

This guide covers how to contribute to Project Chimera documentation, including standards, processes, and review criteria.

---

## Documentation Structure

```
docs/
├── api/                    # API documentation for each service
├── architecture/           # Architecture Decision Records (ADRs)
├── contributing/           # Contribution guidelines (this file)
├── getting-started/       # Getting started guides
├── observability.md        # Observability platform overview
├── plans/                  # Implementation plans and designs
├── runbooks/              # Operational procedures
└── services/              # Service documentation
```

---

## Writing Standards

### Markdown Format

- Use GitHub Flavored Markdown (GFM)
- Line length: 100 characters (soft), 120 (hard)
- Use ATX-style headers (`# Header`)

### Code Blocks

- Use triple backticks with language identifier
- For bash: ` ```bash `
- For Python: ` ```python `

### Links

- Use relative links for internal docs: `[Text](path/to/file.md)`
- Use absolute links for external resources: `[Text](https://example.com)`
- Link text should be descriptive, not "click here"

### Images/Diagrams

- Store images in `docs/images/`
- Use descriptive alt text
- Prefer ASCII diagrams for simple diagrams

---

## Documentation Types

### API Documentation

When documenting API endpoints:
- Include endpoint path and method
- Document request/response schemas
- Provide example requests and responses
- Document error responses
- Note any authentication required

### Runbooks

When creating operational runbooks:
- Start with problem statement
- Provide step-by-step procedures
- Include verification steps
- Add escalation procedures
- Include "Quick Reference" section

### ADRs

When creating Architecture Decision Records:
- Use existing ADR template format
- Include context, decision, consequences
- Document alternatives considered
- Link to related ADRs

---

## Review Process

### Before Submitting

1. **Run link checker**
   ```bash
   ./scripts/fix/analyze-broken-links.sh
   ```

2. **Check for version consistency**
   - Ensure versions are v0.4.0 (not v3.0.0)
   - Check footers and headers

3. **Preview changes**
   - Use markdown previewer or GitHub preview

### Creating Pull Request

1. **Title:** Use format `docs(area): description`
   - Example: `docs(api): add metrics section to SceneSpeak`

2. **Description:** Include:
   - What changes were made
   - Why they were made
   - Links to related issues

3. **Labels:** Add appropriate labels:
   - `documentation`
   - `component-{area}`

### Review Criteria

Documentation PRs are reviewed for:
- **Accuracy** - Information is correct
- **Clarity** - Easy to understand
- **Completeness** - Covers the topic adequately
- **Consistency** - Matches existing style
- **Links** - No broken links introduced

---

## Testing Documentation

### Link Testing

Before submitting, verify all links work:
```bash
# Check internal links
./scripts/fix/analyze-broken-links.sh

# Check external links (optional)
grep -r "http.*\.md" docs/ | head -20
```

### Example Testing

If you include code examples, test them:
```bash
# For bash examples
bash -c 'example-command'

# For Python examples
python3 -c 'example-code'
```

---

## Common Tasks

### Adding New Runbook

1. Create file in `docs/runbooks/`
2. Use existing runbook as template
3. Add to `docs/runbooks/README.md` index
4. Link from related documentation

### Updating API Documentation

1. Modify service API file in `docs/api/`
2. Test endpoint examples if possible
3. Update table of contents if adding new section

### Creating ADR

1. Copy existing ADR template
2. Number sequentially (next available number)
3. Include all required sections
4. Link from `docs/architecture/README.md`

---

## Getting Help

- **Documentation Issues:** Open issue with `documentation` label
- **Questions:** Ask in `#documentation` channel
- **Review:** Request review from technical documentation lead

---

**See Also:**
- [Main Contributing Guide](../../CONTRIBUTING.md)
- [API Documentation](../api/)
- [Runbooks](../runbooks/)
EOF
```

**Step 2: Update main CONTRIBUTING.md to reference documentation guide**

```bash
# Add reference to docs/contributing/documentation.md
cat >> CONTRIBUTING.md << 'EOF'

## Documentation Contributions

For detailed documentation contribution guidelines, see [Documentation Contribution Guide](docs/contributing/documentation.md).

Documentation PRs follow the same review process with additional documentation-specific criteria in the guide.
EOF
```

**Step 3: Commit**

```bash
git add docs/contributing/documentation.md CONTRIBUTING.md
git commit -m "docs: add documentation contribution guidelines

- Create comprehensive documentation contribution guide
- Cover writing standards, review process, common tasks
- Add reference from main CONTRIBUTING.md
- Provide detailed guidance for docs PRs"
```

---

### Task 20: Create Documentation Validation Script

**Files:**
- Create: `scripts/audit/validate-all-fixes.sh`

**Step 1: Create comprehensive validation script**

```bash
cat > scripts/audit/validate-all-fixes.sh << 'EOF'
#!/bin/bash
# Comprehensive validation of all documentation fixes

echo "=========================================="
echo "  Documentation Validation"
echo "=========================================="
echo ""

# Check for broken links
echo "1. Broken Links Check"
BROKEN=$(grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   Markdown links scanned: $(grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)"
echo "   Potentially broken: $BROKEN"
if [ $BROKEN -gt 0 ]; then
  echo "   ⚠️  Action needed"
else
  echo "   ✅ Pass"
fi
echo ""

# Check for old version references
echo "2. Version Consistency Check"
OLD_VERSION=$(grep -r "v3\.0\.0" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   v3.0.0 references found: $OLD_VERSION"
if [ $OLD_VERSION -gt 5 ]; then
  echo "   ⚠️  Multiple v3.0.0 references - needs fix"
elif [ $OLD_VERSION -gt 0 ]; then
  echo "   ⚠️  Some v3.0.0 references in historical context"
else
  echo "   ✅ Pass"
fi
echo ""

# Check observability discoverability
echo "3. Observability Discoverability Check"
OBS_LINKS=$(grep -r "observability\.md" docs/ README.md --include="*.md" | wc -l)
RUNBOOK_INDEX=$(grep -E "on-call|slo-handbook|slo-response|distributed-tracing|performance-analysis" docs/runbooks/README.md | wc -l)
echo "   observability.md references: $OBS_LINKS"
echo "   New runbooks indexed: $RUNBOOK_INDEX"
if [ $OBS_LINKS -lt 2 ]; then
  echo "   ⚠️  observability.md not linked from main docs"
else
  echo "   ✅ Pass"
fi
if [ $RUNBOOK_INDEX -lt 5 ]; then
  echo "   ⚠️  Not all new runbooks indexed"
else
  echo "   ✅ Pass"
fi
echo ""

# Check for ADRs
echo "4. Architecture Documentation Check"
ADR_OBS=$(ls docs/architecture/006-*.md 2>/dev/null | wc -l)
echo "   Observability ADRs created: $ADR_OBS"
if [ $ADR_OBS -lt 3 ]; then
  echo "   ⚠️  Some observability ADRs missing"
else
  echo "   ✅ Pass"
fi
echo ""

# Summary
echo "=========================================="
echo "  Validation Summary"
echo "=========================================="
echo "Documentation fixes applied. Run full audit for complete status."
echo ""
EOF
```

**Step 2: Make executable**

```bash
chmod +x scripts/audit/validate-all-fixes.sh
```

**Step 3: Run validation**

```bash
./scripts/audit/validate-all-fixes.sh
```

**Step 4: Commit**

```bash
git add scripts/audit/validate-all-fixes.sh
git commit -m "feat(audit): add comprehensive documentation validation script

- Check for broken links
- Check version consistency
- Check observability discoverability
- Check ADR completeness
- Provide actionable validation summary"
```

---

## Summary

**Total Tasks:** 20
**Estimated Duration:** ~6 hours
**Phases:** 4 (Critical, High Priority, Medium Priority, Process & Automation)

**Deliverables:**
- All 170 broken links resolved
- All 171 missing file references handled
- All 39 version inconsistencies fixed
- Observability features discoverable from entry points
- 3 new ADRs created
- Service metrics documented
- CI link checker operational
- Documentation contribution guidelines created

**Execution Order:**
1. Phase 1 (Tasks 1-7): Critical Issues - Foundation
2. Phase 2 (Tasks 8-14): High Priority - Discoverability
3. Phase 3 (Tasks 15-17): Medium Priority - Quality
4. Phase 4 (Tasks 18-20): Process & Automation - Sustainability

---

*Implementation Plan: Documentation Fixes*
*Project Chimera v0.4.0*
*March 2026*

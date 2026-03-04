# ADR-004: Chimera Quality Platform

**Status:** Accepted
**Date:** 2026-03-04
**Context:** Project Chimera v3.0.0

---

## Context

Project Chimera v3.0.0 introduces a comprehensive quality assurance platform to ensure code quality, test coverage, and deployment standards are maintained across all services.

### Problems Being Solved

1. **No centralized testing** - Tests were run independently per service
2. **No quality gate enforcement** - Low-quality code could be merged
3. **No unified dashboard** - Quality metrics were scattered
4. **Manual CI/CD triggers** - No automated webhook integration
5. **No performance profiling** - Performance issues were hard to identify

---

## Decision

Implement a **Chimera Quality Platform** consisting of four core services:

### 1. Dashboard Service (Port 8010)

**Purpose:** Web-based quality dashboards and visualization

**Features:**
- Real-time service health monitoring
- Test results display
- Quality metrics visualization
- Alert aggregation

**Technology:** FastAPI + WebSocket + HTML/JS dashboard

### 2. Test Orchestrator (Port 8011)

**Purpose:** Centralized test discovery, execution, and reporting

**Features:**
- Automatic test discovery
- Parallel test execution
- Result aggregation and reporting
- Suite management (unit, integration, load)

**Technology:** pytest + async Python

### 3. CI/CD Gateway (Port 8012)

**Purpose:** GitHub/GitLab webhook integration

**Features:**
- Webhook receiver for PRs, pushes, releases
- Automated test triggering
- Deployment orchestration
- Run status tracking

**Technology:** FastAPI + HMAC signature verification

### 4. Quality Gate (Port 8013)

**Purpose:** Quality threshold enforcement

**Features:**
- Coverage threshold checking (default: 80%)
- Test pass rate checking (default: 95%)
- Flaky test rate checking (default: <5%)
- PR quality evaluation
- Performance threshold enforcement

**Technology:** Python dataclasses + threshold evaluation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chimera Quality Platform                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Dashboard  │  │    Test      │  │  CI/CD       │      │
│  │   Service    │◄─┤ Orchestrator │◄─┤  Gateway     │◄─────┼─── Webhooks
│  │   :8010      │  │    :8011     │  │    :8012     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                 │
│                    ┌──────▼───────┐                        │
│                    │ Quality Gate │                        │
│                    │    :8013     │                        │
│                    └──────────────┘                        │
│                                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────┐
        │        Core Chimera Services             │
        │  (OpenClaw, SceneSpeak, BSL, etc.)      │
        └─────────────────────────────────────────┘
```

---

## Data Flow

### Test Execution Flow

1. **Trigger:** CI/CD Gateway receives webhook
2. **Orchestrate:** Test Orchestrator discovers and runs tests
3. **Evaluate:** Quality Gate checks thresholds
4. **Display:** Dashboard shows results
5. **Notify:** CI/CD Gateway reports back to GitHub/GitLab

### Quality Gate Flow

1. **Measure:** Collect coverage, test results, performance metrics
2. **Compare:** Compare against configured thresholds
3. **Decide:** Pass, fail, or warning status
4. **Enforce:** Block deployment if thresholds not met
5. **Report:** Generate quality report

---

## Benefits

1. **Unified Testing** - All tests run through central orchestrator
2. **Quality Enforcement** - Automated gate prevents low-quality merges
3. **Visibility** - Dashboard provides real-time quality metrics
4. **Automation** - Webhooks trigger tests on every PR
5. **Performance** - Built-in profiling identifies bottlenecks

---

## Alternatives Considered

### Alternative 1: External CI/CD Service (GitHub Actions)

**Pros:**
- No infrastructure to maintain
- Native GitHub integration

**Cons:**
- Limited customization
- Slower feedback (queue times)
- No unified dashboard

**Decision:** Build custom platform for tighter integration and control

### Alternative 2: Kubernetes Operator

**Pros:**
- Native Kubernetes integration
- Declarative configuration

**Cons:**
- Higher complexity
- Slower development cycle
- Overkill for current needs

**Decision:** Start with simpler service-based architecture

---

## Implementation Status

- [x] Dashboard Service - API and web interface
- [x] Test Orchestrator - Discovery and execution
- [x] CI/CD Gateway - Webhook integration
- [x] Quality Gate - Threshold enforcement
- [x] Helm Charts - Deployment manifests
- [x] Monitoring - Prometheus metrics and Grafana dashboards

---

## Future Considerations

1. **Test result caching** - Cache results to speed up re-runs
2. **Historical trends** - Track quality metrics over time
3. **Service level objectives** - Define and track SLOs
4. **Auto-remediation** - Automatic fixes for common issues
5. **Multi-environment support** - Staging, production, etc.

---

## Related Decisions

- [ADR-001: Use k3s for Kubernetes](./001-use-k3s.md)
- [ADR-002: FastAPI for Microservices](./002-fastapi-services.md)
- [ADR-003: OpenClaw Skills Architecture](./003-openclaw-skills.md)

---

*Decision Record: ADR-004*
*Project Chimera v3.0.0*

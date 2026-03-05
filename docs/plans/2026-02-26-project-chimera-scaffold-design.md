# Project Chimera Scaffold Design

**Version:** 1.0.0
**Date:** 2026-02-26
**Status:** Approved
**Author:** Technical Architecture Team

---

## Overview

This document defines the complete scaffold design for Project Chimera, a student-run Dynamic Performance Hub that creates live theatre adapting in real time to audience input.

The scaffold follows a **Layered Phase-Based Build** approach, building from infrastructure to services to skills to configuration, ensuring dependencies are in place before dependent components.

---

## 1. Overall Directory Structure

```
project-chimera/
├── .github/
│   ├── workflows/
│   │   ├── ci.yaml                    # Lint, test, security scan
│   │   ├── cd-staging.yaml            # Deploy to staging
│   │   └── cd-production.yaml         # Deploy to production (manual approval)
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
│
├── docs/
│   ├── trd/                           # Technical requirements
│   ├── runbooks/                      # Operational runbooks
│   ├── architecture/                  # Architecture decision records
│   └── api/                           # API documentation
│
├── infrastructure/
│   ├── kubernetes/
│   │   ├── base/                      # Base Kubernetes manifests
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── kustomization.yaml
│   └── terraform/                     # Future infrastructure-as-code
│
├── services/
│   ├── openclaw-orchestrator/
│   ├── SceneSpeak Agent/
│   ├── Captioning Agent/
│   ├── bsl-text2gloss-agent/
│   ├── Sentiment Agent/
│   ├── lighting-control/
│   ├── safety-filter/
│   └── operator-console/
│
├── skills/
│   ├── scenespeak-skill/
│   ├── captioning-skill/
│   ├── bsl-text2gloss-skill/
│   ├── sentiment-skill/
│   ├── lighting-control-skill/
│   ├── safety-filter-skill/
│   └── operator-console-skill/
│
├── models/
│   ├── prompts/                       # Versioned prompts
│   ├── lora-adapters/                 # Fine-tuned adapters
│   └── evaluation/                    # Evaluation scripts
│
├── scripts/
│   ├── setup/                         # Installation scripts
│   ├── training/                      # Training scripts
│   └── operations/                    # Operational utilities
│
├── configs/
│   ├── policies/                      # Policy definitions
│   ├── retention/                     # Data retention configs
│   └── alerts/                        # Alert rule configs
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── load/
│   ├── red-team/
│   └── accessibility/
│
├── docker-compose.local.yml           # Local development stack
├── docker-compose.remote.yml          # Remote-connected mode
├── .env.example                       # Environment template
├── pyproject.toml                     # Project configuration
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt               # Development dependencies
└── README.md
```

---

## 2. Infrastructure Layer (Kubernetes)

### Namespace Design

| Namespace | Purpose | Priority | QoS Class |
|-----------|---------|----------|-----------|
| `live` | Performance-critical services | High | Guaranteed |
| `preprod` | Non-time-critical workloads | Low | Burstable |
| `shared` | Infrastructure services | Medium | Burstable |

### Resource Allocation

**Live Namespace:**

| Service | CPU | Memory | GPU |
|---------|-----|--------|-----|
| openclaw-orchestrator | 4 cores | 16 GB | 1 |
| SceneSpeak Agent | 8 cores | 32 GB | 1 |
| Captioning Agent | 4 cores | 8 GB | 0 |
| Sentiment Agent | 4 cores | 4 GB | 0 |
| bsl-text2gloss-agent | 2 cores | 8 GB | 0 |
| lighting-control | 1 core | 2 GB | 0 |
| safety-filter | 2 cores | 4 GB | 0 |
| operator-console | 1 core | 2 GB | 0 |

**Shared Namespace:**

| Service | CPU | Memory |
|---------|-----|--------|
| redis | 2 cores | 8 GB |
| kafka | 2 cores | 4 GB |
| vector-db | 2 cores | 8 GB |
| prometheus | 1 core | 4 GB |
| grafana | 0.5 core | 1 GB |
| jaeger | 1 core | 2 GB |

### Kubernetes Manifests Structure

```
infrastructure/kubernetes/
├── base/
│   ├── namespaces/
│   ├── priority-classes/
│   ├── secrets/
│   ├── openclaw/
│   ├── redis/
│   ├── kafka/
│   ├── vector-db/
│   ├── monitoring/
│   └── network-policies/
├── overlays/
│   ├── dev/
│   ├── staging/
│   └── production/
└── kustomization.yaml
```

---

## 3. Core Services Architecture

### Service Structure

Each service follows a consistent FastAPI-based structure:

```
services/<service-name>/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration management
│   ├── models/                    # Pydantic models
│   ├── routes/                    # API routes
│   └── core/                      # Business logic
├── tests/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Standard Endpoints

All services expose:
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `POST /invoke` - Skill invocation
- `GET /metrics` - Prometheus metrics

### Special Service Structures

**SceneSpeak Agent:**
- Context builder module
- Prompt composer module
- Inference engine module
- Redis cache integration

**Safety Filter Agent:**
- Multi-layer filtering (pattern matcher, classifier, rule engine)
- Review queue for flagged content

---

## 4. Skills Layer (OpenClaw Integration)

### Skills Summary

| Skill | Input Type | Output Type | Timeout | Caching |
|-------|------------|-------------|---------|---------|
| scenespeak | Scene context | Dialogue + cues | 3000ms | Yes (5m) |
| captioning | Audio stream | Captions + descriptions | 1500ms | No |
| bsl-text2gloss | Text | Gloss notation (text) | 2000ms | Yes (5m) |
| sentiment | Social/sensor stream | Sentiment vector | 500ms | Yes (30s) |
| lighting-control | Action commands | DMX/OSC output | 200ms | No |
| safety-filter | Text content | Decision + category | 200ms | Yes (1h) |
| operator-console | Alerts/approvals | UI updates | 100ms | No |

### Skill Definition Format

```yaml
apiVersion: openclaw.io/v1
kind: Skill
metadata:
  name: <skill-name>
  version: 1.0.0
spec:
  description: "Description"
  inputs:
    - name: <input-name>
      type: <type>
      required: true/false
  outputs:
    - name: <output-name>
      type: <type>
  config:
    timeout: <ms>
    retryPolicy:
      maxRetries: 2
      backoff: exponential
    caching:
      enabled: true/false
      ttl: <seconds>
```

---

## 5. Models Layer

### Directory Structure

```
models/
├── prompts/
│   ├── scenespeak/
│   │   ├── dialogue-generation/
│   │   ├── character-context/
│   │   └── sentiment-adaptation/
│   ├── dramatron/
│   └── safety/
├── lora-adapters/
│   └── scenespeak-7b/
└── evaluation/
    ├── evaluate_perplexity.py
    ├── evaluate_consistency.py
    ├── evaluate_safety.py
    └── evaluate_latency.py
```

### Prompt Template Format

Markdown files with YAML front matter containing version, author, model compatibility, and generation parameters.

### LoRA Adapter Registry

Versioned adapters with metadata including base model, training data hash, and performance metrics.

---

## 6. Configuration Layer

### Policies

- **Content Policy:** Categories (blocked, flagged, warning), patterns, actions
- **Approval Gates:** Trigger conditions, approvers, timeouts
- **Skill Policies:** Rate limits, retry policies, audit levels

### Data Retention

| Data Type | Retention | After Retention |
|-----------|-----------|-----------------|
| Audience audio | 24h | Delete |
| Social posts | 7d | Delete (anonymised) |
| Sentiment data | 30d | Aggregate only |
| Audit logs | 1y | Archive |
| Training data | Permanent | N/A |

### Alerting

Prometheus rules for:
- High latency (p95 > 2s)
- OpenClaw down
- GPU overloaded
- Pod crash looping
- High safety filter rejections

---

## 7. Tests Layer

### Test Categories

```
tests/
├── unit/              # Fast, isolated component tests
├── integration/       # Component interaction tests
├── load/              # Locust-based performance tests
├── red-team/          # Security/adversarial tests
└── accessibility/     # WCAG compliance tests
```

### Load Test Scenarios

| Scenario | Users | Duration | Expected |
|----------|-------|----------|----------|
| Normal load | 10 concurrent | 10 min | p95 < 2s |
| Peak load | 50 concurrent | 5 min | p95 < 3s |
| Stress test | 100 concurrent | 2 min | Graceful degradation |
| Endurance | 10 concurrent | 60 min | No memory leaks |

---

## Design Decisions

1. **OpenClaw gets 1 GPU** - Direct GPU access for model orchestration
2. **BSL skill renamed to bsl-text2gloss** - Outputs gloss notation (text) not video
3. **Kustomize for environments** - Overlays for dev/staging/production
4. **FastAPI for all services** - Consistent, async-capable framework
5. **Prometheus/Grafana for observability** - Industry standard stack

---

## Next Steps

1. Invoke writing-plans skill to create detailed implementation plan
2. Build scaffold layer by layer following the implementation roadmap
3. Begin with infrastructure (Week 1-2), then services, then skills

---

*Document Version: 1.0.0 | Created: 2026-02-26*

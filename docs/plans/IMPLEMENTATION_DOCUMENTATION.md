# Project Chimera - Implementation Documentation

**Date:** 2026-02-26
**For:** Student Team
**Purpose:** Complete guide to how the scaffold was built

---

## Overview

This document explains exactly how the Project Chimera scaffold was built, organized by phase. Use this to understand the structure and continue development.

---

## Phase 1: Root Configuration & CI/CD Foundation

### What Was Built

### Root Configuration Files

**pyproject.toml**
- Project metadata and dependencies
- Tool configurations (black, ruff, mypy, pytest)
- Build system configuration for Python packages

**requirements.txt & requirements-dev.txt**
- Production dependencies: FastAPI, Redis, Kafka, Prometheus, OpenTelemetry
- Development dependencies: pytest, black, ruff, mypy, locust

**.env.example**
- Template for environment variables
- Includes all service endpoints, GPU settings, feature flags

### CI/CD Workflows

**.github/workflows/ci.yaml**
- Runs on every push to master/main/develop
- Linters: ruff, black, mypy
- Tests: pytest with coverage
- Security scan: Trivy vulnerability scanner
- Docker image builds for all services
- Kubernetes manifest validation

**.github/workflows/cd-staging.yaml**
- Deploys to staging on push to develop branch
- Automated rollout verification

**.github/workflows/cd-production.yaml**
- Deploys to production on git tags (v*)
- Requires manual approval
- Includes backup creation before deployment

### Docker Compose Files

**docker-compose.local.yml**
- Local development: Redis, Kafka, Vector DB, Prometheus, Grafana, Jaeger
- Services run locally (not containerized)

**docker-compose.remote.yml**
- Remote-connected mode: Services run locally but connect to remote K8s
- Useful for development against production-like infrastructure

### Test Configuration

**tests/conftest.py & pytest.ini**
- Shared pytest fixtures
- Test markers: unit, integration, load, red_team, accessibility
- Coverage configuration

---

## Phase 2: Infrastructure Layer (Kubernetes)

### Namespace Design

Three namespaces with different QoS classes:

| Namespace | Purpose | QoS Class |
|-----------|---------|-----------|
| live | Performance-critical services | Guaranteed |
| preprod | Non-time-critical workloads | Burstable |
| shared | Infrastructure services | Burstable |

### Shared Services

**Redis** (infrastructure/kubernetes/base/redis/)
- Deployment with persistent volume claim
- ConfigMap with custom redis.conf
- 8 GB storage, 2 core CPU, 2 core CPU limits

**Kafka** (infrastructure/kubernetes/base/kafka/)
- Bitnami Kafka 3.6 in container
- 20 GB storage via NFS
- 2 core CPU, 4 core CPU limits

**Vector DB** (infrastructure/kubernetes/base/vector-db/)
- Milvus vector database
- 20 GB storage, supporting services (etcd, MinIO)

### Monitoring Stack

**Prometheus** (infrastructure/kubernetes/base/monitoring/prometheus/)
- Scrapes all services with prometheus.io annotations
- 20 GB storage for metrics
- RBAC for cluster access

**Grafana** (infrastructure/kubernetes/base/monitoring/grafana/)
- Dashboards ConfigMap for pre-built visualizations
- Prometheus datasource configured

**Jaeger** (infrastructure/kubernetes/base/monitoring/jaeger/)
- Distributed tracing for all services

### Network Policies

**Default-deny** - All namespaces block all traffic by default
**Allow-shared-services** - Live namespace can access shared services
**DNS allow** - All pods can resolve DNS

### Kustomize Overlays

- **dev**: Development configuration
- **staging**: Pre-production testing
- **production**: Production with semantic version tags

---

## Phase 3: OpenClaw Orchestrator Service

### Architecture

```
services/openclaw-orchestrator/
├── src/
│   ├── main.py                    # FastAPI entry point with lifespan
│   ├── config.py                  # Settings with Pydantic
│   ├── models/                    # Request/Response Pydantic models
│   ├── routes/                    # API route modules
│   │   ├── health.py              # /health/live, /ready, /startup
│   │   ├── orchestration.py       # POST /api/v1/orchestration/invoke
│   │   ├── skills.py              # GET/POST /api/v1/skills
│   │   └── pipelines.py           # POST /api/v1/pipelines/execute
│   └── core/                      # Business logic
│       ├── skill_registry.py      # Loads and manages skills
│       ├── pipeline_executor.py    # Executes skill pipelines
│       ├── orchestrator.py         # Invokes skills via HTTP
│       ├── health.py              # Health check implementation
│       └── metrics.py              # Prometheus metrics
```

### Key Features

- **Skill Registry**: Loads skills from YAML files in `/app/skills`
- **Pipeline Executor**: Runs skills sequentially or in parallel
- **Caching**: Redis-backed caching for skill results
- **Metrics**: Custom Prometheus metrics for operations

### Kubernetes Deployment

- 1 GPU, 4 core CPU (requests), 16 GB memory
- 4 core CPU limits
- Health probes on /health/live, /health/ready
- Mounts skills, models, and configs as volumes

---

## Phase 4: AI Agents (SceneSpeak, Captioning, BSL, Sentiment)

### SceneSpeak Agent

```
services/SceneSpeak Agent/
├── src/
│   ├── core/
│   │   ├── handler.py              # Main orchestration
│   │   ├── context_builder.py       # Builds execution context
│   │   ├── prompt_composer.py       # Formats prompts
│   │   ├── inference_engine.py      # LLM inference (placeholder)
│   │   └── cache/
│   │       └── redis_cache.py       # Result caching
```

- **8 cores, 32 GB memory, 1 GPU** (as per your spec)
- Context builder processes scene, dialogue, sentiment
- Prompt composer uses versioned templates
- Caches results with 5-minute TTL

### Captioning Agent

```
services/Captioning Agent/
├── src/
│   └── core/
│       └── transcriber.py         # Whisper integration
```

- **4 cores, 8 GB memory, 0 GPU** (removed GPU per your spec)
- Base64 audio input
- Returns text, language, confidence, timestamp

### BSL-Text2Gloss Agent (Renamed from BSL Avatar)

```
services/bsl-text2gloss-agent/
├── src/
│   └── core/
│       └── gloss_translator.py    # Text to gloss notation
```

- **2 cores, 8 GB memory, 0 GPU** (reduced from 4 cores per your spec)
- Outputs gloss notation (uppercase text), not video
- Example: "HELLO MY NAME TEST"

### Sentiment Agent

```
services/Sentiment Agent/
├── src/
│   └── core/
│       └── sentiment_analyzer.py # Sentiment from text
```

- **4 cores, 4 GB memory, 0 GPU** (increased from 2 cores per your spec)
- Returns sentiment, confidence, emotions
- Supports batch analysis

---

## Phase 5: Control & Safety Services

### Lighting Control

```
services/lighting-control/src/core/
├── dmx_controller.py    # DMX protocol (channel 1-512)
└── osc_controller.py    # OSC protocol
```

- **1 core, 2 GB memory, 0 GPU**
- Approval gates for scene changes (operator, stage-manager)
- Emergency blackout without approval

### Safety Filter

```
services/safety-filter/src/core/
├── layers/
│   ├── pattern_matcher.py    # Regex-based blocking
│   ├── classifier.py          # ML-based classification
│   └── rule_engine.py          # Rule-based evaluation
└── queue/
    └── review_queue.py        # Flagged content queue
```

- **2 cores, 4 GB memory, 0 GPU**
- Three-layer filtering
- Review queue for human review

### Operator Console

```
services/operator-console/src/routes/
├── alerts.py         # Create, acknowledge alerts
└── approvals.py     # Request, decide approvals
```

- **1 core, 2 GB memory, 0 GPU**
- Dashboard with alerts and pending approvals
- System status monitoring

---

## Phase 6: Skills Layer (OpenClaw Integration)

### Skill Definitions

Each skill has a `skill.yaml` following this structure:

```yaml
apiVersion: openclaw.io/v1
kind: Skill
metadata:
  name: <skill-name>
  version: 1.0.0
spec:
  description: "..."
  inputs: [...]
  outputs: [...]
  config:
    timeout: <ms>
    retryPolicy: {...}
    caching: {...}
```

### Skills Created

| Skill | Timeout | Caching | Special |
|-------|---------|---------|---------|
| scenespeak | 3000ms | Yes (5m) | Model routing with fallback |
| captioning | 1500ms | No | Whisper model |
| bsl-text2gloss | 2000ms | Yes (5m) | Gloss notation output |
| sentiment | 500ms | Yes (30s) | Batch support |
| lighting-control | 200ms | No | Approval gates |
| safety-filter | 200ms | Yes (1h) | Review queue |
| operator-console | 100ms | No | Human-in-the-loop |

---

## Phase 7: Models Layer

### Prompt Templates

Located in `models/prompts/` with YAML front matter:

**scenespeak/dialogue-generation/v1.0.0.md**
- System role and instructions
- Template variables for scene, dialogue, sentiment
- Generation parameters (max_tokens: 512, temperature: 0.8)

**Other prompts:**
- character-context, sentiment-adaptation
- dramatron scene-generation
- safety content-review

### LoRA Adapters

```
models/lora-adapters/scenespeak-7b/
├── v1.0.0/
│   ├── adapter_config.json    # Metadata and metrics
│   └── adapter_model.bin     # Placeholder for weights
└── current -> v1.0.0           # Symlink to current version
```

### Evaluation Scripts

**evaluate_perplexity.py** - Model perplexity measurement
**evaluate_consistency.py** - Character voice consistency
**evaluate_safety.py** - Safety policy compliance
**evaluate_latency.py** - Response time benchmarks
**human_evaluation.py** - Human assessment framework

---

## Phase 8: Configuration Layer

### Policies

**configs/policies/**
- scenespeak-policy.yaml - Generation guidelines
- lighting-control-policy.yaml - Safety limits and approval gates
- safety-filter-policy.yaml - Multi-layer filter rules
- content-policy.yaml - General content rules
- approval-gates.yaml - Human approval requirements

### Retention

**configs/retention/data-retention-policy.yaml**
- Audience audio: 24h then delete
- Social posts: 7d then delete (anonymised)
- Audit logs: 2y then archive
- Training data: permanent

### Alerting

**configs/alerts/**
- prometheus-rules.yaml - Alert thresholds (latency, downtime, etc.)
- alertmanager-config.yaml - Routing to receivers (Slack, email)

---

## Phase 9: Tests Layer

### Unit Tests

`tests/unit/`
- test_safety_filter.py - Pattern matching, performance
- test_scenespeak_handler.py - Context building
- test_captioning_handler.py - Transcription
- test_sentiment_handler.py - Sentiment analysis
- test_bsl_text2gloss.py - Gloss translation
- test_lighting_control.py - DMX/OSC control

### Integration Tests

`tests/integration/`
- test_openclaw_skill_invocation.py - End-to-end skill calls
- test_scenespeak_safety_pipeline.py - Content moderation
- test_captioning_bsl_pipeline.py - Caption to gloss flow
- test_fallback_chain.py - Error handling

### Load Tests

`tests/load/`
- locustfile.py - Locust configuration
- test_latency.py - P95 latency benchmarks
- scenarios/normal_load.py - 10 concurrent users
- scenarios/peak_load.py - 50 concurrent users
- scenarios/stress_test.py - 100 concurrent users

### Red Team Tests

`tests/red-team/`
- test_prompt_injection.py - Jailbreak attempts
- test_cases.yaml - Adversarial examples
- Tests for: prompt injection, code injection, character obfuscation

### Accessibility Tests

`tests/accessibility/`
- test_wcag_compliance.py - WCAG standards
- test_caption_feed.py - Caption quality and timing
- test_bsl_display.py - Gloss formatting and consistency

---

## Phase 10: Scripts & Documentation

### Setup Scripts

**scripts/setup/**
- install_dependencies.sh - Python venv, dependencies, .env
- setup_kubernetes.sh - Deploy K8s infrastructure
- verify_environment.sh - Check all dependencies

### Operations Scripts

**scripts/operations/**
- deploy.sh - Deploy to environment
- rollback.sh - Rollback deployment
- backup.sh - Create configuration backup
- restore.sh - Restore from backup

### Training Scripts

**scripts/training/**
- train_lora.py - Train LoRA adapters
- evaluate_model.py - Evaluate trained models

### Documentation

**reference/runbooks/**
- deployment.md - Deployment procedures
- incident-response.md - Incident handling
- monitoring.md - Metrics and alerting

**docs/architecture/**
- 001-use-k3s.md - Why k3s was chosen
- 002-fastapi-services.md - Why FastAPI was chosen
- 003-openclaw-skills.md - Why OpenClaw architecture

**docs/api/**
- openclaw-orchestrator.md - OpenClaw API documentation

### Makefile

Common commands:
- `make dev` - Start local development
- `make test` - Run all tests
- `make build-all` - Build all Docker images
- `make deploy ENV=dev` - Deploy to environment
- `make backup` - Create backup
- `k8s-status` - Check Kubernetes status

---

## How Services Communicate

### Service Endpoints

All services expose standard endpoints:
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `POST /invoke` - Skill invocation (OpenClaw integration)
- `GET /metrics` - Prometheus metrics

### Service Discovery

Services communicate via Kubernetes DNS:
```bash
<service-name>.<namespace>.svc.cluster.local:<port>
```

Examples:
- `SceneSpeak Agent.live.svc.cluster.local:8001`
- `safety-filter.live.svc.cluster.local:8006`
- `redis.shared.svc.cluster.local:6379`

### Skill Invocation Flow

1. OpenClaw receives pipeline request
2. Loads skill definition from `/app/skills/<skill>/skill.yaml`
3. Calls service via `/invoke` endpoint
4. Service processes and returns result
5. OpenClaw caches result (if caching enabled)
6. Returns to caller

---

## Resource Allocations (As Approved)

### Live Namespace

| Service | CPU | Memory | GPU |
|---------|-----|--------|-----|
| openclaw-orchestrator | 4 | 16 GB | **1** |
| SceneSpeak Agent | 8 | 32 GB | 1 |
| Captioning Agent | 4 | 8 GB | 0 |
| Sentiment Agent | 4 | 4 GB | 0 |
| bsl-text2gloss-agent | 2 | 8 GB | 0 |
| lighting-control | 1 | 2 GB | 0 |
| safety-filter | 2 | 4 GB | 0 |
| operator-console | 1 | 2 GB | 0 |

### Shared Namespace

| Service | CPU | Memory |
|---------|-----|--------|
| redis | 2 | 8 GB |
| kafka | 2 | 4 GB |
| vector-db | 2 | 8 GB |
| prometheus | 1 | 4 GB |
| grafana | 0.5 | 1 GB |
| jaeger | 1 | 2 GB |

---

## Git History

The scaffold was created in two commits:

1. **db2fc1e** - Initial design document commit
2. **bf29fc6** - Implementation plan commit
3. **ad827ed** - Full scaffold implementation (225 files, 17,955 lines)

---

## Development Workflow

### For Students

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd Project_Chimera
   make install-deps
   ```

2. **Start Development**
   ```bash
   make dev  # Starts shared services
   # Services run locally, connected to shared infrastructure
   ```

3. **Make Changes**
   - Edit service code in `services/<service-name>/src/`
   - Update skill definitions in `skills/<skill-skill>/`
   - Add tests in `tests/`

4. **Test**
   ```bash
   make test           # All tests
   make test-unit      # Unit only
   make test-integration # Integration only
   ```

5. **Build and Deploy**
   ```bash
   make build-all     # Build Docker images
   make deploy ENV=dev # Deploy to Kubernetes
   ```

### File Naming Conventions

- **Python files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Kubernetes**: `kebab-case.yaml`
- **Dockerfiles**: `Dockerfile` (in service root)

---

## Common Tasks

### Adding a New Service

1. Create directory in `services/<service-name>/`
2. Add `src/main.py`, `src/config.py`
3. Add `Dockerfile`, `requirements.txt`, `pyproject.toml`
4. Create Kubernetes manifests in `infrastructure/kubernetes/base/<service>/`
5. Add skill definition in `skills/<service>-skill/`

### Updating a Skill Definition

1. Edit `skills/<skill-name>-skill/skill.yaml`
2. Reload in OpenClaw: `POST /api/v1/skills/reload`
3. Changes take effect immediately

### Modifying Policies

1. Edit files in `configs/policies/`
2. Apply changes: `kubectl apply -f configs/policies/<policy>.yaml`
3. Services reload policies automatically

---

## Troubleshooting

### Service Won't Start

```bash
kubectl logs -n live <pod-name> --tail=50
kubectl describe pod <pod-name> -n live
```

### GPU Issues

```bash
kubectl exec -n live SceneSpeak Agent-0 -- nvidia-smi
```

### View All Resources

```bash
kubectl get all -n live
kubectl get pods -n shared
```

---

## Design Decisions Documentation

All major design decisions are documented in `docs/architecture/` as ADRs:

- **001-use-k3s.md** - Why k3s was chosen over alternatives
- **002-fastapi-services.md** - Why FastAPI for all microservices
- **003-openclaw-skills.md** - Why OpenClaw skill-based architecture

---

## Next Steps for Students

1. **Set up your environment**
   - Install Python 3.10+
   - Install Docker and kubectl
   - Clone the repository
   - Run `make install-deps`

2. **Familiarize yourself with the structure**
   - Read `README.md`
   - Review the TRD (`TRD_Project_Chimera.md`)
   - Explore the services

3. **Start with a small task**
   - Add a test case
   - Modify a prompt template
   - Update a skill definition

4. **Join the team workflow**
   - Follow the git branch strategy
   - Create feature branches
   - Submit pull requests

---

*This documentation was created on 2026-02-26 during the scaffold build.*

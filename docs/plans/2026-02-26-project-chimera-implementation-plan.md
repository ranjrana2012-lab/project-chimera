# Project Chimera Implementation Plan

**Version:** 1.0.0
**Date:** 2026-02-26
**Status:** Ready for Execution
**Based on:** 2026-02-26-project-chimera-scaffold-design.md (v1.0.0)

---

## Overview

This implementation plan defines the step-by-step approach for building the complete Project Chimera scaffold. The plan follows a **Layered Phase-Based Build** approach, building from infrastructure to services to skills to configuration.

**Build Strategy:** Option A - Layered Phase-Based Build
**Total Phases:** 7
**Estimated Initial Commit:** Complete project scaffold

---

## Phase 1: Root Configuration & CI/CD Foundation

### Objective
Establish project root configuration files and CI/CD pipeline foundation.

### Tasks

#### 1.1 Create Root Configuration Files
- [ ] `pyproject.toml` - Project metadata, tool configurations
- [ ] `requirements.txt` - Production dependencies
- [ ] `requirements-dev.txt` - Development dependencies
- [ ] `.env.example` - Environment variable template
- [ ] `README.md` - Project overview and quick start

#### 1.2 Create CI/CD Workflows
- [ ] `.github/workflows/ci.yaml` - Lint, test, security scan
- [ ] `.github/workflows/cd-staging.yaml` - Deploy to staging
- [ ] `.github/workflows/cd-production.yaml` - Deploy to production (manual approval)
- [ ] `.github/CODEOWNERS` - Code ownership rules
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` - PR template

#### 1.3 Create Docker Compose Files
- [ ] `docker-compose.local.yml` - Local development stack
- [ ] `docker-compose.remote.yml` - Remote-connected mode

#### 1.4 Create Root Tests Configuration
- [ ] `tests/conftest.py` - Shared pytest fixtures
- [ ] `tests/pytest.ini` - Pytest configuration

### Acceptance Criteria
- All root configuration files created
- CI/CD workflows defined (can run on push)
- Docker compose files validate

---

## Phase 2: Infrastructure Layer (Kubernetes)

### Objective
Create complete Kubernetes infrastructure including namespaces, base services, and monitoring.

### Tasks

#### 2.1 Create Base Namespace Configuration
- [ ] `infrastructure/kubernetes/base/namespaces/live-namespace.yaml`
- [ ] `infrastructure/kubernetes/base/namespaces/preprod-namespace.yaml`
- [ ] `infrastructure/kubernetes/base/namespaces/shared-namespace.yaml`

#### 2.2 Create Priority Classes
- [ ] `infrastructure/kubernetes/base/priority-classes/priority-classes.yaml`
  - Defines: high-priority, medium-priority, low-priority

#### 2.3 Create Network Policies
- [ ] `infrastructure/kubernetes/base/network-policies/default-deny.yaml`
- [ ] `infrastructure/kubernetes/base/network-policies/allow-openclaw.yaml`
- [ ] `infrastructure/kubernetes/base/network-policies/allow-shared-services.yaml`

#### 2.4 Create Redis Deployment
- [ ] `infrastructure/kubernetes/base/redis/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/redis/service.yaml`
- [ ] `infrastructure/kubernetes/base/redis/configmap.yaml`

#### 2.5 Create Kafka Deployment
- [ ] `infrastructure/kubernetes/base/kafka/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/kafka/service.yaml`

#### 2.6 Create Vector DB Deployment
- [ ] `infrastructure/kubernetes/base/vector-db/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/vector-db/service.yaml`

#### 2.7 Create Monitoring Stack
- [ ] `infrastructure/kubernetes/base/monitoring/prometheus/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/monitoring/prometheus/service.yaml`
- [ ] `infrastructure/kubernetes/base/monitoring/prometheus/configmap.yaml`
- [ ] `infrastructure/kubernetes/base/monitoring/grafana/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/monitoring/grafana/service.yaml`
- [ ] `infrastructure/kubernetes/base/monitoring/grafana/dashboards-configmap.yaml`
- [ ] `infrastructure/kubernetes/base/monitoring/jaeger/deployment.yaml`

#### 2.8 Create Kustomize Configuration
- [ ] `infrastructure/kubernetes/kustomization.yaml` (base)
- [ ] `infrastructure/kubernetes/overlays/dev/kustomization.yaml`
- [ ] `infrastructure/kubernetes/overlays/staging/kustomization.yaml`
- [ ] `infrastructure/kubernetes/overlays/production/kustomization.yaml`

### Acceptance Criteria
- All namespace manifests are valid
- Shared services (Redis, Kafka, Vector DB) deployments defined
- Monitoring stack (Prometheus, Grafana, Jaeger) deployments defined
- Kustomize overlays for all environments
- Network policies enforce default-deny with explicit allows

---

## Phase 3: Core Services - OpenClaw Orchestrator

### Objective
Create the OpenClaw Orchestrator service - the central control plane.

### Tasks

#### 3.1 Create Service Structure
- [ ] `services/openclaw-orchestrator/src/__init__.py`
- [ ] `services/openclaw-orchestrator/src/main.py` - FastAPI entry point
- [ ] `services/openclaw-orchestrator/src/config.py` - Configuration management

#### 3.2 Create Models
- [ ] `services/openclaw-orchestrator/src/models/__init__.py`
- [ ] `services/openclaw-orchestrator/src/models/requests.py`
- [ ] `services/openclaw-orchestrator/src/models/responses.py`

#### 3.3 Create Routes
- [ ] `services/openclaw-orchestrator/src/routes/__init__.py`
- [ ] `services/openclaw-orchestrator/src/routes/health.py`
- [ ] `services/openclaw-orchestrator/src/routes/orchestration.py`

#### 3.4 Create Core Logic
- [ ] `services/openclaw-orchestrator/src/core/__init__.py`
- [ ] `services/openclaw-orchestrator/src/core/skill_registry.py`
- [ ] `services/openclaw-orchestrator/src/core/pipeline_executor.py`
- [ ] `services/openclaw-orchestrator/src/core/model_orchestrator.py`

#### 3.5 Create Kubernetes Manifests
- [ ] `infrastructure/kubernetes/base/openclaw/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/openclaw/service.yaml`
- [ ] `infrastructure/kubernetes/base/openclaw/configmap.yaml`
- [ ] `infrastructure/kubernetes/base/openclaw/pvc.yaml`

#### 3.6 Create Dockerfile
- [ ] `services/openclaw-orchestrator/Dockerfile`

#### 3.7 Create Tests
- [ ] `services/openclaw-orchestrator/tests/__init__.py`
- [ ] `services/openclaw-orchestrator/tests/conftest.py`
- [ ] `services/openclaw-orchestrator/tests/test_skill_registry.py`
- [ ] `services/openclaw-orchestrator/tests/test_pipeline_executor.py`

### Acceptance Criteria
- OpenClaw service with FastAPI endpoints (/health, /ready, /invoke, /metrics)
- Skill registry for discovering and loading skills
- Pipeline executor for skill chaining
- Kubernetes deployment with GPU resource request
- Unit tests for core components

---

## Phase 4: Core Services - AI Agents

### Objective
Create the SceneSpeak, Captioning, BSL-Text2Gloss, and Sentiment agent services.

### Tasks

#### 4.1 SceneSpeak Agent
- [ ] `services/scenespeak-agent/src/main.py`
- [ ] `services/scenespeak-agent/src/config.py`
- [ ] `services/scenespeak-agent/src/core/handler.py`
- [ ] `services/scenespeak-agent/src/core/context_builder.py`
- [ ] `services/scenespeak-agent/src/core/prompt_composer.py`
- [ ] `services/scenespeak-agent/src/core/inference_engine.py`
- [ ] `services/scenespeak-agent/src/cache/redis_cache.py`
- [ ] `services/scenespeak-agent/Dockerfile`
- [ ] `infrastructure/kubernetes/base/scenespeak/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/scenespeak/service.yaml`

#### 4.2 Captioning Agent
- [ ] `services/captioning-agent/src/main.py`
- [ ] `services/captioning-agent/src/core/handler.py`
- [ ] `services/captioning-agent/src/core/transcriber.py` (Whisper integration)
- [ ] `services/captioning-agent/Dockerfile`
- [ ] `infrastructure/kubernetes/base/captioning/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/captioning/service.yaml`

#### 4.3 BSL-Text2Gloss Agent
- [ ] `services/bsl-text2gloss-agent/src/main.py`
- [ ] `services/bsl-text2gloss-agent/src/core/handler.py`
- [ ] `services/bsl-text2gloss-agent/src/core/gloss_translator.py`
- [ ] `services/bsl-text2gloss-agent/Dockerfile`
- [ ] `infrastructure/kubernetes/base/bsl-text2gloss/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/bsl-text2gloss/service.yaml`

#### 4.4 Sentiment Agent
- [ ] `services/sentiment-agent/src/main.py`
- [ ] `services/sentiment-agent/src/core/handler.py`
- [ ] `services/sentiment-agent/src/core/sentiment_analyzer.py`
- [ ] `services/sentiment-agent/Dockerfile`
- [ ] `infrastructure/kubernetes/base/sentiment/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/sentiment/service.yaml`

### Acceptance Criteria
- All four AI agent services with standard endpoints
- SceneSpeak includes context builder, prompt composer, inference engine
- Captioning includes Whisper integration
- BSL-Text2Gloss outputs gloss notation (text)
- Sentiment includes analyzer with streaming support
- Kubernetes deployments for all services

---

## Phase 5: Core Services - Control & Safety

### Objective
Create the Lighting Control, Safety Filter, and Operator Console services.

### Tasks

#### 5.1 Lighting Control Service
- [ ] `services/lighting-control/src/main.py`
- [ ] `services/lighting-control/src/core/handler.py`
- [ ] `services/lighting-control/src/core/dmx_controller.py`
- [ ] `services/lighting-control/src/core/osc_controller.py`
- [ ] `services/lighting-control/Dockerfile`
- [ ] `infrastructure/kubernetes/base/lighting-control/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/lighting-control/service.yaml`

#### 5.2 Safety Filter Service
- [ ] `services/safety-filter/src/main.py`
- [ ] `services/safety-filter/src/core/handler.py`
- [ ] `services/safety-filter/src/core/layers/pattern_matcher.py`
- [ ] `services/safety-filter/src/core/layers/classifier.py`
- [ ] `services/safety-filter/src/core/layers/rule_engine.py`
- [ ] `services/safety-filter/src/core/queue/review_queue.py`
- [ ] `services/safety-filter/Dockerfile`
- [ ] `infrastructure/kubernetes/base/safety-filter/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/safety-filter/service.yaml`

#### 5.3 Operator Console Service
- [ ] `services/operator-console/src/main.py`
- [ ] `services/operator-console/src/routes/alerts.py`
- [ ] `services/operator-console/src/routes/approvals.py`
- [ ] `services/operator-console/src/core/dashboard.py`
- [ ] `services/operator-console/Dockerfile`
- [ ] `infrastructure/kubernetes/base/operator-console/deployment.yaml`
- [ ] `infrastructure/kubernetes/base/operator-console/service.yaml`

### Acceptance Criteria
- Lighting Control with DMX and OSC protocol support
- Safety Filter with multi-layer filtering and review queue
- Operator Console with alert and approval endpoints
- Kubernetes deployments for all services

---

## Phase 6: Skills Layer (OpenClaw Integration)

### Objective
Create OpenClaw skill definitions for all services.

### Tasks

#### 6.1 SceneSpeak Skill
- [ ] `skills/scenespeak-skill/skill.yaml`
- [ ] `skills/scenespeak-skill/README.md`
- [ ] `skills/scenespeak-skill/tests/test_skill.py`

#### 6.2 Captioning Skill
- [ ] `skills/captioning-skill/skill.yaml`
- [ ] `skills/captioning-skill/README.md`
- [ ] `skills/captioning-skill/tests/test_skill.py`

#### 6.3 BSL-Text2Gloss Skill
- [ ] `skills/bsl-text2gloss-skill/skill.yaml`
- [ ] `skills/bsl-text2gloss-skill/README.md`
- [ ] `skills/bsl-text2gloss-skill/tests/test_skill.py`

#### 6.4 Sentiment Skill
- [ ] `skills/sentiment-skill/skill.yaml`
- [ ] `skills/sentiment-skill/README.md`
- [ ] `skills/sentiment-skill/tests/test_skill.py`

#### 6.5 Lighting Control Skill
- [ ] `skills/lighting-control-skill/skill.yaml`
- [ ] `skills/lighting-control-skill/README.md`
- [ ] `skills/lighting-control-skill/tests/test_skill.py`

#### 6.6 Safety Filter Skill
- [ ] `skills/safety-filter-skill/skill.yaml`
- [ ] `skills/safety-filter-skill/README.md`
- [ ] `skills/safety-filter-skill/tests/test_skill.py`

#### 6.7 Operator Console Skill
- [ ] `skills/operator-console-skill/skill.yaml`
- [ ] `skills/operator-console-skill/README.md`
- [ ] `skills/operator-console-skill/tests/test_skill.py`

### Acceptance Criteria
- All 7 skill definitions follow OpenClaw skill.yaml format
- Each skill includes input/output specifications
- Each skill includes timeout, retry, and caching configuration
- Each skill has a README and test file

---

## Phase 7: Models Layer

### Objective
Create prompt templates, LoRA adapter structure, and evaluation scripts.

### Tasks

#### 7.1 Create Prompt Templates
- [ ] `models/prompts/scenespeak/dialogue-generation/v1.0.0.md`
- [ ] `models/prompts/scenespeak/dialogue-generation/current.md` -> v1.0.0
- [ ] `models/prompts/scenespeak/character-context/v1.0.0.md`
- [ ] `models/prompts/scenespeak/sentiment-adaptation/v1.0.0.md`
- [ ] `models/prompts/dramatron/scene-generation/v1.0.0.md`
- [ ] `models/prompts/safety/content-review/v1.0.0.md`

#### 7.2 Create LoRA Adapter Structure
- [ ] `models/lora-adapters/scenespeak-7b/v1.0.0/adapter_config.json`
- [ ] `models/lora-adapters/scenespeak-7b/v1.0.0/adapter_model.bin` (placeholder)
- [ ] `models/lora-adapters/scenespeak-7b/current` -> v1.0.0
- [ ] `models/lora-adapters/README.md`

#### 7.3 Create Evaluation Scripts
- [ ] `models/evaluation/evaluate_perplexity.py`
- [ ] `models/evaluation/evaluate_consistency.py`
- [ ] `models/evaluation/evaluate_safety.py`
- [ ] `models/evaluation/evaluate_latency.py`

### Acceptance Criteria
- Prompt templates with YAML front matter
- LoRA adapter directory structure with metadata
- Evaluation scripts are executable

---

## Phase 8: Configuration Layer

### Objective
Create policies, retention rules, and alert configurations.

### Tasks

#### 8.1 Create Policy Definitions
- [ ] `configs/policies/scenespeak-policy.yaml`
- [ ] `configs/policies/lighting-control-policy.yaml`
- [ ] `configs/policies/safety-filter-policy.yaml`
- [ ] `configs/policies/content-policy.yaml`
- [ ] `configs/policies/approval-gates.yaml`

#### 8.2 Create Retention Configuration
- [ ] `configs/retention/data-retention-policy.yaml`

#### 8.3 Create Alerting Configuration
- [ ] `configs/alerts/prometheus-rules.yaml`
- [ ] `configs/alerts/alertmanager-config.yaml`

### Acceptance Criteria
- Content policy with blocked/flagged/warning categories
- Approval gates for lighting changes and low safety scores
- Data retention policy for all data types
- Prometheus alert rules for critical scenarios

---

## Phase 9: Tests Layer

### Objective
Create comprehensive test suite across all categories.

### Tasks

#### 9.1 Unit Tests
- [ ] `tests/unit/test_safety_filter.py`
- [ ] `tests/unit/test_scenespeak_handler.py`
- [ ] `tests/unit/test_captioning_handler.py`
- [ ] `tests/unit/test_sentiment_handler.py`
- [ ] `tests/unit/test_bsl_text2gloss.py`
- [ ] `tests/unit/test_lighting_control.py`

#### 9.2 Integration Tests
- [ ] `tests/integration/test_openclaw_skill_invocation.py`
- [ ] `tests/integration/test_scenespeak_safety_pipeline.py`
- [ ] `tests/integration/test_captioning_bsl_pipeline.py`
- [ ] `tests/integration/test_fallback_chain.py`

#### 9.3 Load Tests
- [ ] `tests/load/locustfile.py`
- [ ] `tests/load/test_latency.py`
- [ ] `tests/load/scenarios/normal_load.py`
- [ ] `tests/load/scenarios/peak_load.py`
- [ ] `tests/load/scenarios/stress_test.py`
- [ ] `tests/load/scenarios/endurance.py`

#### 9.4 Red Team Tests
- [ ] `tests/red-team/test_prompt_injection.py`
- [ ] `tests/red-team/test_jailbreak_attempts.py`
- [ ] `tests/red-team/test_adversarial_input.py`
- [ ] `tests/red-team/test_cases.yaml`

#### 9.5 Accessibility Tests
- [ ] `tests/accessibility/test_wcag_compliance.py`
- [ ] `tests/accessibility/test_caption_feed.py`
- [ ] `tests/accessibility/test_bsl_display.py`

### Acceptance Criteria
- Unit tests for all core handlers
- Integration tests for key pipelines
- Load tests for all defined scenarios
- Red team tests for security validation
- Accessibility tests for WCAG compliance

---

## Phase 10: Scripts & Documentation

### Objective
Create operational scripts and supporting documentation.

### Tasks

#### 10.1 Create Setup Scripts
- [ ] `scripts/setup/install_dependencies.sh`
- [ ] `scripts/setup/setup_kubernetes.sh`
- [ ] `scripts/setup/verify_environment.sh`

#### 10.2 Create Operations Scripts
- [ ] `scripts/operations/deploy.sh`
- [ ] `scripts/operations/rollback.sh`
- [ ] `scripts/operations/backup.sh`
- [ ] `scripts/operations/restore.sh`

#### 10.3 Create Training Scripts
- [ ] `scripts/training/train_lora.py`
- [ ] `scripts/training/evaluate_model.py`

#### 10.4 Create Documentation Structure
- [ ] `docs/runbooks/deployment.md`
- [ ] `docs/runbooks/incident-response.md`
- [ ] `docs/runbooks/monitoring.md`
- [ ] `docs/architecture/001-use-k3s.md`
- [ ] `docs/architecture/002-fastapi-services.md`
- [ ] `docs/architecture/003-openclaw-skills.md`
- [ ] `docs/api/openapi.yaml`

### Acceptance Criteria
- All scripts are executable
- Documentation structure established
- API documentation in OpenAPI format

---

## Implementation Order

The phases should be executed in this order:

1. **Phase 1** - Root Configuration & CI/CD Foundation
2. **Phase 2** - Infrastructure Layer (Kubernetes)
3. **Phase 3** - Core Services: OpenClaw Orchestrator
4. **Phase 4** - Core Services: AI Agents
5. **Phase 5** - Core Services: Control & Safety
6. **Phase 6** - Skills Layer
7. **Phase 7** - Models Layer
8. **Phase 8** - Configuration Layer
9. **Phase 9** - Tests Layer
10. **Phase 10** - Scripts & Documentation

---

## Resource Allocation Summary

### Live Namespace (Revised)

| Service | CPU | Memory | GPU |
|---------|-----|--------|-----|
| openclaw-orchestrator | 4 cores | 16 GB | 1 |
| scenespeak-agent | 8 cores | 32 GB | 1 |
| captioning-agent | 4 cores | 8 GB | 0 |
| sentiment-agent | 4 cores | 4 GB | 0 |
| bsl-text2gloss-agent | 2 cores | 8 GB | 0 |
| lighting-control | 1 core | 2 GB | 0 |
| safety-filter | 2 cores | 4 GB | 0 |
| operator-console | 1 core | 2 GB | 0 |

### Shared Namespace

| Service | CPU | Memory |
|---------|-----|--------|
| redis | 2 cores | 8 GB |
| kafka | 2 cores | 4 GB |
| vector-db | 2 cores | 8 GB |
| prometheus | 1 core | 4 GB |
| grafana | 0.5 core | 1 GB |
| jaeger | 1 core | 2 GB |

---

## Success Criteria

The implementation is complete when:

1. All 10 phases have been executed
2. All Kubernetes manifests are valid and can be applied
3. All services have Dockerfiles and can be built
4. All skills have valid skill.yaml definitions
5. All tests are structured correctly
6. The entire scaffold can be committed to version control
7. CI/CD workflows can run on push

---

## Next Steps

1. Execute this implementation plan phase by phase
2. After each phase, verify the output matches the design
3. Commit progress after each phase
4. Create a pull request after Phase 10 completion

---

*Document Version: 1.0.0 | Created: 2026-02-26 | Based on Design v1.0.0*

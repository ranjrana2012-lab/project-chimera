# Student Role Assignments

**Project:** Project Chimera
**Version:** 1.0.0
**Last Updated:** February 2026

---

## Overview

Project Chimera is divided into 10 focus areas. Each student owns one component and is responsible for its development, testing, and documentation.

---

## Role Assignment Matrix

| # | Role | Service | Primary Directory |
|---|------|---------|-------------------|
| 1 | OpenClaw Orchestrator Lead | `openclaw-orchestrator` | `services/openclaw-orchestrator/` |
| 2 | SceneSpeak Agent Lead | `scenespeak-agent` | `services/scenespeak-agent/` |
| 3 | Captioning Agent Lead | `captioning-agent` | `services/captioning-agent/` |
| 4 | BSL Translation Lead | `bsl-text2gloss-agent` | `services/bsl-text2gloss-agent/` |
| 5 | Sentiment Analysis Lead | `sentiment-agent` | `services/sentiment-agent/` |
| 6 | Lighting Control Lead | `lighting-control` | `services/lighting-control/` |
| 7 | Safety Filter Lead | `safety-filter` | `services/safety-filter/` |
| 8 | Operator Console Lead | `operator-console` | `services/operator-console/` |
| 9 | Infrastructure & DevOps Lead | All infrastructure | `infrastructure/` |
| 10 | QA & Documentation Lead | Tests & docs | `tests/`, `docs/` |

---

## Role Details

### Role 1: OpenClaw Orchestrator Lead

**Component:** `openclaw-orchestrator`
**Port:** 8000
**GPU:** 1x NVIDIA GPU
**Resources:** 2-4 CPU, 8-16 GiB RAM

**Responsibilities:**
- Skill routing and execution framework
- Agent coordination and communication
- Policy engine implementation
- Skill lifecycle management
- GPU resource scheduling

**Key Technologies:**
- FastAPI
- Redis (caching, pub/sub)
- Kafka (event streaming)
- Milvus (vector DB for skill matching)
- PyTorch (ML model orchestration)

**Daily Tasks:**
- Monitor orchestrator health: `kubectl logs -f -n live deployment/openclaw-orchestrator`
- Test skill routing: `curl http://localhost:8000/v1/skills`
- Review skill registration logs
- Coordinate with skill owners

**Documentation:**
- `services/openclaw-orchestrator/README.md`
- `docs/api/openclaw-orchestrator.md`

---

### Role 2: SceneSpeak Agent Lead

**Component:** `scenespeak-agent`
**Port:** 8001
**GPU:** 1x NVIDIA GPU
**Resources:** 4-8 CPU, 16-32 GiB RAM

**Responsibilities:**
- LLM-based dialogue generation
- Character context management
- Prompt engineering and optimization
- LoRA adapter training
- Inference latency optimization

**Key Technologies:**
- FastAPI
- PyTorch
- Transformers (Hugging Face)
- vLLM or text-generation-inference
- Redis (caching)

**Daily Tasks:**
- Monitor generation latency
- Test new prompts: `curl -X POST http://localhost:8001/v1/generate -d '{"context": "..."}'`
- Review dialogue quality metrics
- Fine-tune LoRA adapters

**Documentation:**
- `services/scenespeak-agent/README.md`
- `skills/scenespeak-skill/README.md`
- `models/prompts/scenespeak/`

---

### Role 3: Captioning Agent Lead

**Component:** `captioning-agent`
**Port:** 8002
**GPU:** None (CPU inference)
**Resources:** 2-4 CPU, 4-8 GiB RAM

**Responsibilities:**
- Real-time speech-to-text (ASR)
- Live caption generation
- Caption timing and synchronization
- Multiple language support
- Accuracy optimization

**Key Technologies:**
- FastAPI
- Whisper (OpenAI)
- Redis (stream coordination)
- WebSockets (real-time delivery)

**Daily Tasks:**
- Monitor ASR accuracy
- Test caption streaming
- Review latency metrics
- Update language models

**Documentation:**
- `services/captioning-agent/README.md`
- `skills/captioning-skill/README.md`

---

### Role 4: BSL Translation Lead

**Component:** `bsl-text2gloss-agent`
**Port:** 8003
**GPU:** None (CPU inference)
**Resources:** 2 CPU, 4 GiB RAM

**Responsibilities:**
- English-to-BSL gloss translation
- Text normalization preprocessing
- Sign language gloss format
- Translation accuracy
- Integration with avatar (future)

**Key Technologies:**
- FastAPI
- NLP transformers
- BSL-specific models

**Daily Tasks:**
- Test translation: `curl -X POST http://localhost:8003/v1/translate -d '{"text": "..."}'`
- Review translation quality
- Update gloss mappings
- Monitor performance

**Documentation:**
- `services/bsl-text2gloss-agent/README.md`
- `skills/bsl-text2gloss-skill/README.md`

---

### Role 5: Sentiment Analysis Lead

**Component:** `sentiment-agent`
**Port:** 8004
**GPU:** None (CPU inference)
**Resources:** 4 CPU, 8 GiB RAM

**Responsibilities:**
- Real-time sentiment analysis
- Audience emotion detection
- Multi-modal sentiment (text, audio, visual)
- Sentiment aggregation over time
- Trend detection

**Key Technologies:**
- FastAPI
- Transformers (DistilBERT, RoBERTa)
- Redis (sentiment cache)
- Kafka (event streaming)

**Daily Tasks:**
- Monitor sentiment pipeline
- Test analysis: `curl -X POST http://localhost:8004/v1/analyze -d '{"text": "..."}'`
- Review sentiment accuracy
- Tune model thresholds

**Documentation:**
- `services/sentiment-agent/README.md`
- `skills/sentiment-skill/README.md`

---

### Role 6: Lighting Control Lead

**Component:** `lighting-control`
**Port:** 8005
**GPU:** None
**Resources:** 0.5-1 CPU, 512 MiB - 2 GiB RAM

**Responsibilities:**
- DMX/sACN protocol implementation
- Lighting scene management
- OSC message handling
- Fixture control
- Preset management

**Key Technologies:**
- FastAPI
- SACN (sACN protocol)
- Python-OSC
- Redis (state sync)

**Daily Tasks:**
- Test DMX output
- Verify fixture connectivity
- Create lighting presets
- Monitor OSC messages

**Documentation:**
- `services/lighting-control/README.md`
- `skills/lighting-control-skill/README.md`

---

### Role 7: Safety Filter Lead

**Component:** `safety-filter`
**Port:** 8006
**GPU:** None
**Resources:** 1-2 CPU, 2-4 GiB RAM

**Responsibilities:**
- Content moderation
- Profanity filtering
- Safety guardrails
- Policy enforcement
- Audit logging

**Key Technologies:**
- FastAPI
- NLP profanity detection
- Redis (blocklist cache)
- Kafka (audit events)

**Daily Tasks:**
- Review blocked content
- Update filter rules
- Test safety: `curl -X POST http://localhost:8006/v1/check -d '{"content": "..."}'`
- Monitor false positives/negatives

**Documentation:**
- `services/safety-filter/README.md`
- `skills/safety-filter-skill/README.md`
- `models/prompts/safety/`

---

### Role 8: Operator Console Lead

**Component:** `operator-console`
**Port:** 8007
**GPU:** None
**Resources:** 1-2 CPU, 2-4 GiB RAM

**Responsibilities:**
- Human oversight interface
- Real-time monitoring dashboard
- Manual override controls
- WebSocket event streaming
- Alert management

**Key Technologies:**
- FastAPI
- WebSocket (real-time updates)
- Kafka (event consumption)
- HTML/CSS/JavaScript (frontend)

**Daily Tasks:**
- Monitor console performance
- Review alert thresholds
- Update dashboard UI
- Test manual overrides

**Documentation:**
- `services/operator-console/README.md`
- `skills/operator-console-skill/README.md`

---

### Role 9: Infrastructure & DevOps Lead

**Component:** All infrastructure
**Focus:** k3s, Kubernetes, monitoring

**Responsibilities:**
- k3s cluster management
- Kubernetes manifests
- CI/CD pipelines
- Monitoring stack (Prometheus, Grafana, Jaeger)
- Service deployments
- Resource allocation

**Key Technologies:**
- k3s
- Kubernetes
- Kustomize
- Docker
- GitHub Actions
- Prometheus, Grafana, Jaeger

**Daily Tasks:**
- Monitor cluster health: `make bootstrap-status`
- Review Grafana dashboards: http://localhost:3000
- Check resource utilization
- Deploy service updates
- Manage PriorityClasses

**Documentation:**
- `infrastructure/kubernetes/`
- `docs/runbooks/`
- `.github/workflows/`

---

### Role 10: QA & Documentation Lead

**Component:** Tests and documentation
**Focus:** Quality assurance

**Responsibilities:**
- Test suite maintenance
- Coverage tracking
- Documentation updates
- API documentation
- Onboarding guides
- Runbook maintenance

**Key Technologies:**
- pytest
- pytest-cov
- Sphinx (docs)
- Markdown

**Daily Tasks:**
- Run test suite: `make test`
- Review coverage reports
- Update documentation
- Create test plans
- Review PR templates

**Documentation:**
- `tests/`
- `docs/`
- `.github/PULL_REQUEST_TEMPLATE.md`

---

## Coordination

### Weekly Standup Format

Each student reports:
1. What I worked on this week
2. What I plan to work on next week
3. Blockers or dependencies on other roles

### Dependencies

- **Orchestrator (1)** coordinates with all skill owners (2-8)
- **SceneSpeak (2)** provides dialogue to **Captioning (3)** and **Safety Filter (7)**
- **Sentiment (5)** provides context to **SceneSpeak (2)**
- **Lighting (6)** receives cues from **Orchestrator (1)**
- **Infrastructure (9)** supports all service owners
- **QA (10)** reviews all code changes

### Communication Channels

- `#project-chimera-dev` - General development
- `#project-chimera-ops` - Infrastructure issues
- `#project-chimera-reviews` - Code review requests
- Tag `@technical-lead` for urgent issues

---

## First Week Checklist

For All Students:
- [ ] Complete `getting-started/quick-start.md` setup
- [ ] Read assigned component README
- [ ] Run component tests
- [ ] Access component via port-forward
- [ ] Review component documentation

Component-Specific:
- [ ] Understand component architecture
- [ ] Identify one improvement to make
- [ ] Create first feature branch
- [ ] Submit first PR for review

---

## Escalation Path

1. **Check documentation** - Component README, runbooks
2. **Ask peer** - Another student with similar component
3. **Technical Lead** - @technical-lead for blockers
4. **Team meeting** - Discuss in weekly planning

---

*Remember: This is a learning project. Ask questions, experiment, and don't be afraid to make mistakes. The goal is to learn together!*

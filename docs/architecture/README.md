# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for Project Chimera.

**Version:** 3.0.0
**Last Updated:** March 2026

---

## Decision Records

### Infrastructure

### [ADR-001: Use k3s for Kubernetes](001-use-k3s.md)

**Status:** Accepted
**Date:** 2026-02-26
**Context:** Need for lightweight Kubernetes distribution
**Decision:** Use k3s for local development and testing

---

### Service Architecture

### [ADR-002: FastAPI for Microservices](002-fastapi-services.md)

**Status:** Accepted
**Date:** 2026-02-26
**Context:** Need for async-capable web framework
**Decision:** Use FastAPI for all services

### [ADR-003: OpenClaw Skills Architecture](003-openclaw-skills.md)

**Status:** Accepted
**Date:** 2026-02-26
**Context:** Need for modular AI pipeline architecture
**Decision:** Use OpenClaw skill-based orchestration

---

### Platform & Features (v0.5.0)

### [ADR-004: Chimera Quality Platform](004-quality-platform.md)

**Status:** Accepted
**Date:** 2026-03-04
**Context:** Need for centralized quality assurance
**Decision:** Implement Dashboard, Test Orchestrator, CI/CD Gateway, Quality Gate

### [ADR-005: v0.5.0 Feature Enhancements](005-v3-features.md)

**Status:** Accepted
**Date:** 2026-03-04
**Context:** Need for improved AI capabilities and accessibility
**Decision:** LoRA adapters, multi-layer safety, BSL avatar, real-time updates

---

## Specialized Architecture

### [Scene State Machine](scene-state-machine.md)

**Status:** Accepted
**Date:** 2026-02-26
**Context:** Managing scene transitions and state
**Decision:** Hierarchical state machine for scene management

### [Transition Triggers](transition-triggers.md)

**Status:** Accepted
**Date:** 2026-02-26
**Context:** Coordinating transitions between scenes
**Decision:** Event-driven trigger system

---

## Architecture Overview

### Core Services

```
┌─────────────────────────────────────────────────────────────────┐
│                      Project Chimera v0.5.0                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                   Core AI Services                        │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │  OpenClaw (8000)  │ SceneSpeak (8001) │ Captioning (8002)│   │
│  │  BSL (8003)       │ Sentiment (8004)  │ Lighting (8005)   │   │
│  │  Safety (8006)    │ Console (8007)                         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                 Quality Platform (NEW)                    │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │  Dashboard (8010) │ Test Orch (8011) │ CI/CD (8012)        │   │
│  │  Quality Gate (8013)                                        │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    Infrastructure                         │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │  k3s Cluster │ Redis │ Kafka │ Milvus │ Monitoring         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### v0.5.0 Features

| Feature | Service | Description |
|---------|---------|-------------|
| LoRA Adapters | SceneSpeak | Genre-specific dialogue styling |
| Multi-Layer Safety | Safety Filter | Pattern + ML + Context filtering |
| BSL Avatar | BSL Agent | Real-time sign language visualization |
| Real-Time Updates | Console | WebSocket-based live updates |
| Performance Tools | Platform | Profiler, cache, resource monitor |

---

## Decision Categories

### Infrastructure Decisions
- Kubernetes distribution (k3s)
- Service mesh considerations
- Deployment strategies

### Service Architecture Decisions
- Web framework selection (FastAPI)
- Communication patterns (REST, WebSocket)
- Data storage (Redis, Kafka, Milvus)

### AI/ML Decisions
- Model architecture
- Fine-tuning approach (LoRA)
- Safety and moderation

### Quality Decisions
- Testing strategy
- CI/CD automation
- Quality gate thresholds

---

## Decision Process

1. **Propose** - Create ADR with context and options
2. **Discuss** - Team review and feedback
3. **Decide** - Accept, reject, or defer
4. **Implement** - Build according to decision
5. **Review** - Periodically review for updates

---

## Contributing

When proposing a significant architectural change:

1. Create a new ADR file: `XXX-decision-title.md`
2. Use the template from existing ADRs
3. Include context, options, decision, and consequences
4. Submit for team review
5. Update this README when accepted

---

## Related Documentation

- [API Documentation](../api/)
- [Runbooks](../runbooks/)
- [Getting Started](../getting-started/)
- [Implementation Plans](../plans/)

---

*Architecture Decision Records*
*Project Chimera v0.5.0*

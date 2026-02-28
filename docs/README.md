# Project Chimera Documentation

Welcome to the official documentation for Project Chimera, an AI-powered live theatre platform.

## Quick Links

- [Quick Start Guide](../README.md) - Get started in 5 minutes
- [Student Quick Start](../Student_Quick_Start.md) - Detailed setup for students
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute

## Table of Contents

### Getting Started

- [Quick Start Guide](../README.md#quick-start) - Automated bootstrap setup
- [Development Guide](DEVELOPMENT.md) - Setting up your development environment
- [Deployment Guide](DEPLOYMENT.md) - Deploying to production

### Core Documentation

- [Architecture Overview](ARCHITECTURE.md) - System architecture and design
- [API Documentation](API.md) - Complete API reference
- [Technical Requirements](../TRD_Project_Chimera.md) - Full technical specification
- [Quality Platform](quality-platform/README.md) - Testing infrastructure and quality gates

### Operational Guides

- [Monitoring](runbooks/monitoring.md) - Monitoring and alerting setup
- [Incident Response](runbooks/incident-response.md) - Handling incidents
- [Deployment Runbook](runbooks/deployment.md) - Deployment procedures
- [Bootstrap Setup](runbooks/bootstrap-setup.md) - Initial cluster setup

### Reference

- [Student Roles](STUDENT_ROLES.md) - Component ownership and responsibilities
- [Implementation Documentation](plans/IMPLEMENTATION_DOCUMENTATION.md) - How the scaffold was built
- [Quality Platform Design](plans/2026-02-28-chimera-quality-platform-design.md) - Platform architecture
- [Quality Platform Implementation](plans/2026-02-28-chimera-quality-platform-implementation.md) - Implementation details
- [Project Backlog](../Backlog_Project_Chimera.md) - Outstanding work and features

### Architecture Decisions

- [Architecture Decision Records](architecture/README.md) - Key architectural decisions
  - [ADR-001: Use k3s for Kubernetes](architecture/001-use-k3s.md)
  - [ADR-002: FastAPI for Microservices](architecture/002-fastapi-services.md)
  - [ADR-003: OpenClaw Skills Architecture](architecture/003-openclaw-skills.md)

### API Documentation

- [API Index](api/README.md) - All service APIs
  - [OpenClaw Orchestrator](api/openclaw-orchestrator.md)
  - [SceneSpeak Agent](api/scenespeak-agent.md) (coming soon)
  - [Captioning Agent](api/captioning-agent.md) (coming soon)
  - [BSL-Text2Gloss Agent](api/bsl-text2gloss-agent.md) (coming soon)
  - [Sentiment Agent](api/sentiment-agent.md) (coming soon)
  - [Lighting Control](api/lighting-control.md) (coming soon)
  - [Safety Filter](api/safety-filter.md) (coming soon)
  - [Operator Console](api/operator-console.md) (coming soon)

## Documentation Structure

```
docs/
├── README.md                    # This file
├── ARCHITECTURE.md              # System architecture overview
├── API.md                       # Complete API documentation
├── DEVELOPMENT.md               # Development setup guide
├── DEPLOYMENT.md                # Deployment guide
├── STUDENT_ROLES.md             # Student component assignments
├── api/                         # Individual service API docs
│   ├── README.md
│   └── openclaw-orchestrator.md
├── architecture/                # Architecture decision records
│   ├── README.md
│   ├── 001-use-k3s.md
│   ├── 002-fastapi-services.md
│   └── 003-openclaw-skills.md
├── runbooks/                    # Operational procedures
│   ├── README.md
│   ├── bootstrap-setup.md
│   ├── deployment.md
│   ├── monitoring.md
│   └── incident-response.md
└── plans/                       # Implementation plans
    └── IMPLEMENTATION_DOCUMENTATION.md
```

## Key Concepts

### System Overview

Project Chimera is a microservices-based AI theatre platform consisting of:

1. **OpenClaw Orchestrator** - Central control plane coordinating all agents
2. **AI Agents** - Specialized services for dialogue, captioning, translation, and sentiment
3. **Infrastructure** - Kubernetes-based deployment with monitoring and observability
4. **Skills** - Modular OpenClaw skills for theatre-specific functionality

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OpenClaw Orchestrator                      │
│              (Central Control Plane)                        │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┘
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
  SceneSpeak Captioning  BSL  Sentiment Lighting Safety  Operator
    Agent     Agent    Agent   Agent  Control Filter  Console
```

### Technology Stack

- **Framework:** FastAPI (Python 3.10+)
- **Orchestration:** Kubernetes (k3s)
- **Messaging:** Apache Kafka
- **Caching:** Redis
- **Vector DB:** Milvus
- **Monitoring:** Prometheus + Grafana + Jaeger
- **AI/ML:** PyTorch, Transformers, OpenAI Whisper

## Getting Help

### Documentation

- Search the documentation using the search function
- Check the FAQ section in relevant documents
- Review runbooks for operational issues

### Community

- [GitHub Issues](https://github.com/project-chimera/project-chimera/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/project-chimera/project-chimera/discussions) - Community discussions
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute

### Support

For students and contributors:
- See [Student Roles](STUDENT_ROLES.md) for component owners
- Check with your team lead for guidance
- Review runbooks for operational procedures

## Contributing to Documentation

We welcome documentation improvements! To contribute:

1. Fork the repository
2. Make your changes
3. Submit a pull request

See [Contributing Guidelines](../CONTRIBUTING.md) for details.

### Documentation Guidelines

- Use clear, concise language
- Include examples where appropriate
- Keep code blocks properly formatted
- Update table of contents when adding sections
- Test all procedures before documenting

### Quality Platform

- [Overview](quality-platform/README.md) - Platform introduction
- [Architecture](quality-platform/ARCHITECTURE.md) - System design
- [API Documentation](quality-platform/API.md) - Service APIs
- [Development](quality-platform/DEVELOPMENT.md) - Contributing guide
- [Deployment](quality-platform/DEPLOYMENT.md) - Deployment guide

## Version Information

- **Current Version:** 0.1.0 (Alpha)
- **Documentation Last Updated:** 2026-02-27
- **Supported Python:** 3.10+
- **Supported Kubernetes:** 1.25+

## License

Project Chimera is released under the MIT License. See [LICENSE](../LICENSE) for details.

---

**Project Chimera** - An AI-powered live theatre platform for universities worldwide.

# Project Chimera Documentation

Welcome to the Project Chimera documentation hub. This is your central resource for learning about, contributing to, and operating the AI-powered live theatre platform.

## Quick Start

**New to the project?** Start with [Quick Start Guide](guides/quick-start.md)

**Want to contribute?** Read [Development Setup](development/setup.md) and [Contributing Guidelines](CONTRIBUTING.md)

**Operating the system?** See [Deployment Guide](DEPLOYMENT.md) and [Runbooks](operations/runbooks/)

## Documentation by Topic

### API Documentation
- [API Endpoint Catalog](api/endpoints.md) - All available endpoints grouped by service
- [OpenAPI Specification](api/openapi.yaml) - Machine-readable API spec
- [Data Schemas](api/schemas.md) - Request/response models
- [BSL Agent API](api/bsl-agent.md) - BSL translation and avatar rendering
- [OpenClaw Orchestrator API](api/openclaw-orchestrator.md) - Central coordination service

### Architecture
- [System Overview](architecture/overview.md) - High-level architecture diagram
- [Services](architecture/services.md) - Service topology and interactions
- [Data Flow](architecture/data-flow.md) - Request/response flows
- [Architecture Decision Records](architecture/adr/) - Technical decisions and rationale

### User Guides
- [Quick Start](guides/quick-start.md) - Get started in 5 minutes
- [BSL Avatar Guides](guides/bsl-avatar/)
  - [Playback Controls](guides/bsl-avatar/playback-controls.md)
  - [Recording](guides/bsl-avatar/recording.md)
  - [Timeline Editor](guides/bsl-avatar/timeline-editor.md)
  - [Animation Library](guides/bsl-avatar/animation-library.md)
- [Usage Scenarios](guides/scenarios/) - Common use case guides
- [Operator Console Dashboard](guides/operator-console-dashboard.md) - Dashboard guide

### Developer Documentation
- [Development Setup](development/setup.md) - Local development environment
- [Testing Guide](development/testing.md) - Unit, integration, E2E tests
- [Contributing](CONTRIBUTING.md) - PR workflow and code review
- [Code Style](standards/python-style.md) - Coding conventions
- [Troubleshooting](development/troubleshooting.md) - Common issues and solutions

### Operations
- [Deployment](DEPLOYMENT.md) - Docker Compose, K3s, CI/CD
- [Monitoring](observability.md) - Prometheus, Grafana, alerts
- [Runbooks](operations/runbooks/) - Incident response procedures
- [Infrastructure](operations/infrastructure/) - K8s, networking, volumes

### Planning & Status
- [Sprint Definitions](planning/sprint-definitions.md) - Current sprint goals
- [Implementation Plans](plans/) - Detailed implementation plans
- [Release Notes](release-notes/) - Version release notes
- [TODO Resolution Log](TODO-RESOLUTION-LOG.md) - Task tracking

## Recent Updates

### 2026-03-12 - BSL Avatar Rendering Complete
- Added 107 BSL animations (phrases, alphabet, numbers, emotions)
- Enhanced avatar viewer with recording, timeline, camera controls
- Performance optimizations: worker pool, caching, streaming
- All 16 BSL E2E tests passing (100%)

### 2026-03-10 - CI/CD Test Fixes
- Fixed SceneSpeak LLM infrastructure issues
- Fixed sentiment agent timeout problems
- Marked 7 SceneSpeak tests as skipped (infrastructure dependent)

### 2026-03-07 - Quality Platform
- Added comprehensive quality gate framework
- Implemented observability platform with OpenTelemetry
- Added SLO framework and runbooks

## Need Help?

- **Quick questions:** Check existing documentation or create an issue
- **Bug reports:** Create an issue with `bug:` label
- **Feature requests:** Create an issue with `enhancement:` label
- **Documentation issues:** Create an issue with `documentation:` label

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| OpenClaw Orchestrator | ✅ Operational | Port 8000 |
| SceneSpeak Agent | ⚠️ Partial | LLM infra issues |
| Captioning Agent | ✅ Operational | Port 8002 |
| BSL Agent | ✅ Operational | Port 8003, 107 animations |
| Sentiment Agent | ✅ Operational | Port 8004 |
| Lighting-Sound-Music | ✅ Operational | Port 8005 |
| Safety Filter | ✅ Operational | Port 8006 |
| Operator Console | ✅ Operational | Port 8007 |
| Autonomous Agent | ✅ Operational | Port 8008, Ralph Engine + GSD Orchestrator |
| Music Generation | ✅ Operational | Port 8011 |

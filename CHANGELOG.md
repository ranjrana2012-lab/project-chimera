# Changelog

All notable changes to Project Chimera will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Enhanced dialogue models with better context understanding
- Multi-scene support and scene transitions
- Improved accessibility features
- Cloud deployment guides
- Production-ready hardening

## [0.1.0] - 2026-02-27

### Added

#### Core Services
- OpenClaw Orchestrator - Central control plane with skill registry
- SceneSpeak Agent - Real-time dialogue generation with Llama 2
- Captioning Agent - Speech-to-text with OpenAI Whisper
- BSL-Text2Gloss Agent - British Sign Language translation
- Sentiment Agent - Audience sentiment analysis
- Lighting Control - DMX/OSC stage automation
- Safety Filter - Multi-layer content moderation
- Operator Console - Human oversight interface

#### Infrastructure
- Kubernetes manifests for k3s deployment
- Bootstrap automation for local development
- Docker builds for all services
- Local container registry setup

#### Monitoring & Observability
- Prometheus metrics collection
- Grafana dashboards
- Jaeger distributed tracing
- Structured JSON logging

#### Documentation
- Complete API documentation
- Architecture overview
- Deployment guides
- Development setup guide
- Student role assignments
- Operational runbooks

#### Testing
- Unit test framework
- Integration test structure
- Load testing infrastructure
- Red team testing for security

#### Open Source
- MIT License
- Contributing guidelines
- Code of conduct
- Security policy
- GitHub issue and PR templates

### Configuration

- Environment-based configuration
- Example `.env` file
- Kubernetes ConfigMaps support
- Secret management guidelines

### Development Tools

- Make targets for common operations
- Pre-commit hooks configuration
- Code formatting with Black
- Linting with Ruff
- Type checking with MyPy

### Security

- Multi-layer content filtering
- Human approval workflows
- Audit logging
- Network policies for Kubernetes
- Security vulnerability reporting

### Accessibility

- WCAG compliance considerations
- Captioning service
- BSL translation service
- Accessibility testing framework

## [0.0.1] - 2026-02-20

### Added
- Initial project scaffold
- Basic service structure
- Development environment setup

---

## Release Notes

### 0.1.0 Highlights

This is the initial alpha release of Project Chimera, an AI-powered live theatre platform.

**Key Features:**
- 8 AI agents for theatre production
- Real-time audience adaptation
- Multi-layer safety filtering
- Built-in accessibility features
- Complete open source documentation

**Known Limitations:**
- Alpha quality - not production ready
- Limited model training data
- Basic UI only
- Single-region deployment only

**Getting Started:**
See the [Quick Start Guide](README.md#quick-start) to get started in 15-20 minutes.

**Contributing:**
We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Support:**
- [GitHub Issues](https://github.com/project-chimera/project-chimera/issues)
- [GitHub Discussions](https://github.com/project-chimera/project-chimera/discussions)
- [Documentation](docs/)

---

## Version Schema

- **Major (X.0.0)**: Breaking changes, major features
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, minor changes

## Release Schedule

- **Alpha:** Monthly releases during active development
- **Beta:** Bi-weekly releases as features stabilize
- **Stable:** Quarterly releases after v1.0.0

## Support Policy

- **Current version:** Full support
- **Previous version:** Security fixes only
- **Older versions:** No support

---

For detailed release information, see:
- [GitHub Releases](https://github.com/project-chimera/project-chimera/releases)
- [Milestone Tracking](https://github.com/project-chimera/project-chimera/milestones)
- [Project Roadmap](https://github.com/project-chimera/project-chimera/wiki/Roadmap)

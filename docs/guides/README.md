# Project Chimera Documentation Hub

Welcome to the Project Chimera documentation hub. This is your central navigation point for all documentation.

## Quick Navigation

### Getting Started
- [Quick Start Guide](../getting-started/quick-start.md) - Get up and running in 10 minutes
- [Student FAQ](../getting-started/faq.md) - Frequently asked questions
- [Office Hours](../getting-started/office-hours.md) - Support schedule

### Core Services
- [Core Services Overview](../services/core-services.md) - The 8 Core Pillars
- [Lighting, Sound & Music](../services/lighting-sound-music.md) - Unified audio-visual control
- [Music Generation](../services/music-generation.md) - AI music platform (now part of LSM)

### Guides
- [GitHub Workflow](./github-workflow.md) - Contribution workflow
- [WorldMonitor Context Usage](./worldmonitor-context-usage.md) - Using global context enrichment
- [Development](../DEVELOPMENT.md) - Development setup and practices
- [Deployment](../DEPLOYMENT.md) - Deployment guide

### Reference
- [API Documentation](../reference/api.md) - Complete API reference
- [Architecture](../reference/architecture.md) - System architecture
- [Standards](../standards/) - Code and documentation standards

### Plans & Designs
- [Implementation Plans](../plans/) - Detailed implementation plans
- [Architecture Decisions](../architecture/) - ADRs and design decisions

### Runbooks
- [Alerts](../runbooks/alerts.md) - Alert response procedures
- [Incident Response](../runbooks/incident-response.md) - Incident handling
- [Monitoring](../runbooks/monitoring.md) - Monitoring procedures

## 8 Core Pillars

| # | Service | Port | Status |
|---|---------|------|--------|
| 1 | [OpenClaw Orchestrator](../services/core-services.md#openclaw-orchestrator) | 8000 | ✅ Production Ready |
| 2 | [SceneSpeak Agent](../services/core-services.md#scenespeak-agent) | 8001 | ✅ Production Ready |
| 3 | [Captioning Agent](../services/core-services.md#captioning-agent) | 8002 | ⚠️ Partial |
| 4 | [BSL Translation Agent](../services/core-services.md#bsl-text2gloss-agent) | 8003 | ⚠️ Partial |
| 5 | [Sentiment Agent](../services/core-services.md#sentiment-agent) | 8004 | ⚠️ Partial |
| 6 | [Lighting, Sound & Music](../services/lighting-sound-music.md) | 8005 | ✅ Production Ready (NEW) |
| 7 | [Safety Filter](../services/core-services.md#safety-filter) | 8006 | ⚠️ Partial |
| 8 | [Operator Console](../services/core-services.md#operator-console) | 8007 | ✅ Production Ready |

## New in Project Chimera

### Lighting, Sound & Music Service (v0.3.0)
Unified audio-visual control service consolidating:
- **Lighting Control** - DMX/sACN management
- **Sound Effects** - Playback and mixing
- **Music Generation** - ACE-Step-1.5 AI music
- **Coordinated Cues** - Multi-media scenes

[Read more](../services/lighting-sound-music.md) | [Migration Guide](../plans/lsm-migration-summary.md)

### WorldMonitor Integration (v0.4.0)
Real-time global context enrichment for sentiment analysis:
- **WorldMonitor Sidecar** - Global events streaming
- **Context-Aware Sentiment** - Enriched analysis with world events
- **News Sentiment Analysis** - Understand current events impact
- **Category Filtering** - Focus on specific event categories

[Read more](./worldmonitor-context-usage.md) | [Architecture](../reference/architecture.md#sidecar-pattern)

## Documentation Structure

```
docs/
├── getting-started/     # New user guides
│   ├── quick-start.md
│   ├── faq.md
│   └── monday-demo/     # Demo preparation materials
├── services/            # Service documentation
│   ├── core-services.md
│   ├── lighting-sound-music.md
│   └── music-generation.md
├── guides/              # How-to guides
│   ├── github-workflow.md
│   ├── worldmonitor-context-usage.md
│   └── README.md        # This file
├── reference/           # Reference documentation
│   ├── api.md
│   └── architecture.md
├── plans/               # Implementation plans
├── runbooks/            # Operational procedures
├── standards/           # Code standards
└── templates/           # Document templates
```

## Contributing to Documentation

When making changes to documentation:
1. Update the relevant documentation file
2. Update this hub if adding new sections
3. Update the [CHANGELOG](../CHANGELOG.md)
4. Follow [Documentation Style Guide](../standards/documentation-style.md)

## Getting Help

- **Quick Questions**: Check the [FAQ](../getting-started/faq.md)
- **Office Hours**: See [schedule](../getting-started/office-hours.md)
- **GitHub Issues**: Create an issue for bugs or feature requests
- **Communication Channels**: See [channels guide](../getting-started/communication-channels.md)

## Version History

- **v0.4.0** (2026-03-03) - WorldMonitor Integration, global context enrichment
- **v0.3.0** (2026-03-02) - LSM Integration, unified audio-visual control
- **v0.2.0** (2026-03-01) - Music generation platform, student automation
- **v0.1.0** (2026-02-28) - Initial 8-core microservices

---

**Next Steps:**
- New to Project Chimera? Start with the [Quick Start Guide](../getting-started/quick-start.md)
- Want to contribute? Read the [GitHub Workflow Guide](./github-workflow.md)
- Need API details? Check the [API Reference](../reference/api.md)

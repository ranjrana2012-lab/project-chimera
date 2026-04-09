# Project Chimera

> **AI-Powered Adaptive Theatre Framework**
> **8-Week Agent Development Plan: April 9 - June 5, 2026**

An open-source AI framework that creates adaptive, audience-responsive theatre experiences using specialized AI agents.

![Version](https://img.shields.io/badge/version-2.0.0--development-blue)
![Status](https://img.shields.io/badge/status-active--development-green)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)

---

## 📋 Current Focus: 8-Week Agent Development Plan

**Timeline**: April 9 - June 5, 2026
**Goal**: Rebuild and test all 7 core agents incrementally
**Approach**: Start simple, progress to complex

### Week 1-2: Foundation (April 9-22)
- Agent framework and base classes
- Health monitoring system
- Testing infrastructure

### Week 3: Echo Agent (April 23-29)
- Simple input/output relay
- Tests entire pipeline

### Week 4: Translation Agent (April 30 - May 6)
- API integration
- Language detection

### Week 5: Sentiment Agent (May 7-13)
- ML model integration (DistilBERT)
- Performance optimization

### Week 6: Dialogue Agent (May 14-20)
- LLM integration
- Adaptive routing

### Week 7: Specialized Agents (May 21-27)
- Caption, Context, Analytics agents

### Week 8: Integration (May 28 - June 5)
- End-to-end testing
- Performance optimization
- Documentation

**See**: [8-Week Development Plan](8_WEEK_PLAN_APRIL_JUNE_2026.md)

---

## Overview

Project Chimera is an AI-powered framework for creating adaptive, audience-responsive theatre experiences. Multiple specialized AI agents work together to generate real-time performances that respond to audience sentiment and input.

### What Makes Project Chimera Unique?

- **Real-Time Adaptation** - Performances change based on audience sentiment
- **Multi-Agent AI** - Specialized agents for dialogue, captioning, translation, sentiment
- **Safety First** - Multi-layer content moderation with human oversight
- **Accessible** - Built-in captioning and translation support
- **Open Source** - Free for universities and educational institutions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Orchestrator                                │
│         (Agent Coordination + Routing)                       │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┐
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
   Echo  Translation  Sentiment  Dialogue  Caption  Context  Analytics
```

---

## Agent Priority (Development Order)

| Agent | Complexity | Week | Description |
|-------|-----------|------|-------------|
| Echo | ⭐ | 3 | Simple input/output relay |
| Translation | ⭐⭐ | 4 | API integration, language detection |
| Sentiment | ⭐⭐⭐ | 5 | ML model, performance optimization |
| Dialogue | ⭐⭐⭐⭐ | 6 | LLM integration, adaptive logic |
| Caption | ⭐⭐ | 7 | Text processing, formatting |
| Context | ⭐⭐⭐ | 7 | State management, persistence |
| Analytics | ⭐⭐ | 7 | Data collection, reporting |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Docker
- Git

### Clone and Setup

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start services (when available)
docker-compose up -d
```

### Verify Installation

```bash
# Check Python version
python --version

# Run prerequisite check
python verify_prerequisites.py

# Run smoke tests
python test_chimera_smoke.py
```

---

## Current Status

### ✅ Working Components
- **Sentiment Analysis** - DistilBERT ML model (~150ms response)
- **Dialogue Generation** - GLM-4.7 LLM integration with fallbacks
- **Adaptive Routing** - 3 strategies (positive/negative/neutral)
- **Caption Formatting** - Terminal + SRT export
- **Export Functionality** - JSON, CSV, SRT formats

### 🔄 In Development
- Agent framework refactoring
- Echo agent (Week 3)
- Translation agent (Week 4)
- Full integration testing (Week 8)

---

## Project Structure

```
project-chimera/
├── services/              # Agent implementations
│   ├── operator-console/  # Main console interface
│   ├── sentiment-agent/    # Sentiment analysis
│   ├── dialogue-agent/     # Dialogue generation
│   └── [other agents]/     # Additional services
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── docs/                  # Documentation
│   ├── api/               # API documentation
│   ├── guides/            # Technical guides
│   └── architecture/      # Architecture docs
├── scripts/               # Utility scripts
├── internal/              # Internal tracking (gitignore'd)
└── 8_WEEK_PLAN_*.md       # Development plan
```

---

## Technology Stack

**Core Framework**: FastAPI (Python 3.12+)
**Communication**: REST + WebSocket
**ML Models**: PyTorch + Transformers
**LLM Integration**: Ollama (local) or API
**Testing**: pytest + pytest-asyncio
**Deployment**: Docker + docker-compose

---

## Development

### Code Quality

```bash
# Run linting
ruff check .

# Format code
ruff format .

# Type checking
mypy services/
```

### Testing

```bash
# Run all tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=services tests/
```

---

## Documentation

### Getting Started
- [8-Week Development Plan](8_WEEK_PLAN_APRIL_JUNE_2026.md) - Current development roadmap
- [Quick Reference](QUICK_REFERENCE_CARD.md) - Quick command reference
- [Student Guide](STUDENT_GUIDE.md) - Learning resources

### Technical
- [Architecture Overview](docs/architecture/overview.md) - System architecture
- [API Documentation](docs/api/README.md) - Complete API reference
- [Development Guide](docs/DEVELOPMENT.md) - Development workflow

---

## Contributing

We welcome contributions from students, researchers, and developers!

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Use Cases

Project Chimera is designed for:

- **University Theatre Programs** - Educational AI theatre projects
- **Experimental Theatre** - Innovative performance experiences
- **Interactive Installations** - Audience-driven installations
- **Research Projects** - AI and creativity research

---

## Community

- **GitHub**: https://github.com/ranjrana2012-lab/project-chimera
- **Issues**: https://github.com/ranjrana2012-lab/project-chimera/issues
- **Discussions**: https://github.com/ranjrana2012-lab/project-chimera/discussions

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Roadmap

### v2.0.0 (Current Development - April-June 2026)

**Focus**: Agent rebuild and integration

- [ ] Week 1-2: Foundation & Infrastructure
- [ ] Week 3: Echo Agent
- [ ] Week 4: Translation Agent
- [ ] Week 5: Sentiment Agent
- [ ] Week 6: Dialogue Agent
- [ ] Week 7: Specialized Agents
- [ ] Week 8: Integration & Testing

### Future Work

- Hardware integration (DMX lighting, audio)
- Enhanced BSL translation
- Real-time captioning with audio
- Student collaboration framework
- Live performance staging

---

**Project Chimera** - An AI-powered adaptive theatre framework for universities worldwide.

For questions, support, or to get involved, please [open an issue](https://github.com/ranjrana2012-lab/project-chimera/issues).

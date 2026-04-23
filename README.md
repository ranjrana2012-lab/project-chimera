# Project Chimera

> An AI-powered live theatre platform creating performances that adapt in real-time to audience input.

[![CI/CD](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)

*Last Updated: April 20, 2026*

## 🚀 Quick Start (Monolithic Demonstrators)

Project Chimera's primary MVP demonstrator is a fully autonomous monolithic Python environment. It incorporates `DistilBERT` sentiment analyzers, Local LLM Generative Scripting, and Live TTS Audio Routing to demonstrate our core intelligent theatre logic. 

You can run the demonstrator either using the traditional Text CLI or our beautifully rendered Local Web Dashboard!

```bash
# Clone repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Setup Environment
cd services/operator-console
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# OPTION 1: Run the beautiful Visual Web Dashboard (Recommended)
python chimera_web.py
# -> Open your browser to http://127.0.0.1:8080

# OPTION 2: Run the local terminal CLI
python chimera_core.py
```

### Try these demonstration inputs:
- *"I am very happy today!"* -> Prompts `momentum_build` dialogue strategy.
- *"I'm feeling anxious and overwhelmed."* -> Prompts `supportive_care` dialogue strategy.
- Type `compare` -> Triggers side-by-side mode.
- Type `caption` -> Triggers accessibility output.

---

## 🏗️ Architecture Pathways

Project Chimera supports two modes of operation:
1. **The MVP Monolith (chimera_core.py)**: The recommended way to run the local demonstrator using local ML models without Docker overhead.
2. **The Microservices Ecosystem (docker-compose)**: Designed for large scale-out deployments utilizing Kafka, Milvus, and containerized agents (see `docs/guides/MVP_OVERVIEW.md` or `docs/guides/DEPLOYMENT.md`).

## 📁 Repository Structure

```
project-chimera/
├── services/
│   ├── operator-console/        # Contains the `chimera_core` Python demonstrator
│   └── shared/                  # Shared utilities and middleware
├── docs/                        # Project Guides & Architecture (e.g. docs/guides)
├── scripts/                     # Helpful developer setup scripts
├── tests/                       # QA and Pytest suites
└── docker-compose.yml           # (Available for scale-out setups)
```

## 🤝 Contributing & Security

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup and guidelines. 

If you discover any security issues, refer to our [SECURITY.md](SECURITY.md) for responsible disclosure. 

## ⚖️ License
MIT License

# Development Guide

**Version:** 1.0.0
**Last Updated:** April 24, 2026

## Overview

This guide covers the workflows that match the current repository layout.

For day-to-day local work, use the monolithic operator-console path first. Use the Docker Compose stacks when you need the broader multi-service wiring.

## Required Tooling

- Python 3.12 or later
- Git
- Docker Desktop / Docker Engine with Docker Compose v2 if you need the secondary containerized workflows

## Local Bootstrap

### 1. Clone the repository

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
```

### 2. Set up the monolith runtime

```bash
cd services/operator-console
python -m venv venv
source venv/bin/activate
# Windows PowerShell:
#   .\venv\Scripts\Activate.ps1
# If that is blocked:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\venv\Scripts\Activate.ps1
# Or use .\venv\Scripts\python.exe directly.
pip install -r requirements.txt
```

### 3. Install broader development dependencies

From the project root:

```bash
pip install -r requirements-dev.txt
```

This adds the tooling needed for repo-wide linting and pytest runs beyond the operator-console monolith.

## Useful Make Targets

The current `Makefile` supports:

```bash
make install-deps
make dev
make lint
make format
make test
make test-unit
make test-integration
```

### What they do

- `make install-deps` installs `requirements-dev.txt`
- `make dev` starts `docker compose -f docker-compose.mvp.yml up -d`
- `make lint` runs `ruff check .`
- `make format` runs `black .`
- `make test` runs `pytest tests/ -v`
- `make test-unit` runs `pytest tests/unit/ -v`
- `make test-integration` runs `pytest tests/integration/ -v`

## Recommended Local Workflow

### Fast monolith check

```bash
# From services/operator-console
python chimera_core.py demo
python chimera_web.py
```

If `8080` is already in use, set `PORT` to a free port before launching `chimera_web.py`.

### Fast validation checks

```bash
# From the project root
python verify_prerequisites.py
pytest tests/unit/test_chimera_core.py -v
pytest tests/e2e/test_chimera_smoke.py -v
pytest tests/unit -v
pytest tests --collect-only -q
```

### Broader containerized check

```bash
docker compose -f docker-compose.mvp.yml config --services
docker compose -f docker-compose.mvp.yml up -d --build
docker compose -f docker-compose.mvp.yml ps
```

Use the containerized path only after the monolith is already working or when you specifically need the service-to-service orchestration.

## Project Areas

```text
project-chimera/
|-- services/
|   |-- operator-console/        # Primary monolithic demonstrator
|   |-- openclaw-orchestrator/   # Containerized orchestration service
|   |-- scenespeak-agent/        # Dialogue generation
|   |-- sentiment-agent/         # Sentiment analysis
|   |-- safety-filter/           # Content moderation
|   |-- translation-agent/       # Translation
|   `-- echo-agent/              # Hardware bridge / DMX simulation
|-- docs/guides/                 # Operator-facing and engineering guides
|-- tests/                       # Unit, integration, e2e, performance suites
|-- docker-compose.mvp.yml       # Multi-service MVP stack
`-- docker-compose.student.yml   # Operator-console-only student sandbox
```

## Testing Expectations

- Use the monolith and focused pytest checks for fast local confidence.
- Install `requirements-dev.txt` before running repo-wide tests from the project root.
- Treat `pytest tests -v` as a broader validation sweep that may include slower or service-heavy suites.
- Use Docker Compose for integration and full-stack scenarios rather than assuming every test is purely local and isolated.

See [TESTING.md](TESTING.md) for the current test breakdown.

## Branch and PR Workflow

```bash
git switch -c codex/your-change
git add .
git commit -m "docs: describe your change"
git push -u origin codex/your-change
```

Open a pull request against `main` and include:

- what changed
- how you validated it
- any remaining environment blockers

## Troubleshooting

### Python or pip not found

Install Python 3.12+ and verify the interpreter is available as `python`.

On Windows, add these directories to your user `Path`, then reopen PowerShell:

- `%LocalAppData%\Programs\Python\Python312`
- `%LocalAppData%\Programs\Python\Python312\Scripts`

Then verify with `python --version` and `pip --version`.

### PowerShell blocks venv activation

If `.\venv\Scripts\Activate.ps1` is blocked, use one of these instead:

- `Set-ExecutionPolicy -Scope Process Bypass`
- `cmd /c venv\Scripts\activate.bat`
- `.\venv\Scripts\python.exe ...`

### Import errors during pytest collection

Use the repository root for repo-wide tests and make sure `requirements-dev.txt` is installed.

### Docker commands fail before services start

That is usually a Docker environment problem rather than an application bug. Confirm the Docker daemon is reachable before debugging the repository itself.

## Related Guides

- [README.md](../../README.md)
- [GETTING_STARTED.md](GETTING_STARTED.md)
- [TESTING.md](TESTING.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)

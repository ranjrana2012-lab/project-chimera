# Testing Guide

**Last Updated:** April 24, 2026

## Overview

Project Chimera has a mix of fast local checks and broader service-heavy suites.

For day-to-day validation, start with the monolithic operator-console checks. Use the broader repo-wide or Docker-backed suites after the monolith is already healthy.

## Test Environment Setup

### Monolith Runtime

```bash
cd services/operator-console
python -m venv venv
source venv/bin/activate
# Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Repo-Wide Test Dependencies

From the project root:

```bash
pip install -r requirements-dev.txt
```

Use the repository root when running top-level `tests/` commands so imports and shared fixtures resolve correctly.

## Recommended Fast Checks

These are the fastest high-signal commands for local validation:

```bash
python verify_prerequisites.py
pytest tests/unit/test_chimera_core.py -v
pytest tests/e2e/test_chimera_smoke.py -v
pytest tests/unit -v
pytest tests --collect-only -q
```

The first three focus on the validated monolithic demonstrator. `pytest tests --collect-only -q` is a useful sanity check before attempting a broader test sweep.

## Test Layers

### 1. Monolith Behavior Checks

Use these to validate the primary operator-console experience:

```bash
# From services/operator-console
python chimera_core.py demo
python chimera_core.py compare "I love this performance"
python chimera_core.py caption "Can you tell me more about the system?"
python chimera_web.py
```

This covers:

- positive, negative, and neutral routing
- compare mode
- caption mode
- export flow
- web dashboard startup and API endpoints

### 2. Focused Pytest Checks

```bash
pytest tests/unit/test_chimera_core.py -v
pytest tests/e2e/test_chimera_smoke.py -v
pytest tests/unit -v
```

These are the best default checks to run before opening a PR that touches the monolith or the test harness.

### 3. Broader Repo Sweep

```bash
pytest tests/ -v
```

Treat this as a larger validation pass. It may include slower, service-heavy, or integration-oriented tests depending on the current repository state.

### 4. Docker-Backed or Service Integration Checks

Some integration and end-to-end workflows assume services are running:

```bash
docker compose -f docker-compose.mvp.yml up -d --build
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

Run these only when Docker is healthy and the stack is intentionally under test.

## Useful Commands

```bash
# Verbose output
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Clear pytest cache
pytest tests/ --cache-clear

# Drop into pdb on failure
pytest tests/ --pdb
```

## Troubleshooting

### Import Errors During Collection

Run the tests from the repository root and make sure `requirements-dev.txt` is installed.

### Service Connection Errors

If tests are trying to reach HTTP services, confirm whether they are meant to be pure unit tests or integration tests. Start the MVP Compose stack only for the latter.

### Docker Engine Errors

If `docker compose` cannot reach the local engine, fix the Docker environment before treating it as a repository-level test failure.

### Port Conflicts During Web Validation

Set `PORT` to a free value before launching `chimera_web.py`.

## Practical Validation Order

For most changes, use this order:

1. `python verify_prerequisites.py`
2. `python chimera_core.py demo`
3. `pytest tests/unit/test_chimera_core.py -v`
4. `pytest tests/e2e/test_chimera_smoke.py -v`
5. `pytest tests/unit -v`
6. `pytest tests --collect-only -q`
7. `pytest tests/ -v` only when the broader sweep is warranted
8. `docker compose -f docker-compose.mvp.yml up -d --build` only when you need the multi-service stack

## Related Guides

- [GETTING_STARTED.md](GETTING_STARTED.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [README.md](../../README.md)

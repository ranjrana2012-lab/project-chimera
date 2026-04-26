# Project Chimera Student Guide

**Last Updated:** April 25, 2026

This guide is for students who want the shortest accurate path to running and testing Project Chimera as it exists today.

## What You Should Run First

Project Chimera supports two kinds of workflows:

1. `services/operator-console` monolithic demonstrator
2. Secondary Docker Compose stacks for broader service wiring

For onboarding, always start with the monolith. It has the clearest setup path and covers the core behaviors:

- sentiment routing
- compare mode
- caption mode
- export flow
- local web dashboard and API

## Minimal Student Workflow

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
cd services/operator-console
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python chimera_core.py demo
python chimera_web.py
```

Windows PowerShell alternatives:

- `.\venv\Scripts\Activate.ps1`
- `Set-ExecutionPolicy -Scope Process Bypass` if PowerShell blocks activation
- `.\venv\Scripts\python.exe ...` if you want to avoid activation entirely

If `8080` is already in use:

```powershell
$env:PORT=18080
python chimera_web.py
```

## What to Validate

### CLI

From `services/operator-console`:

```bash
python chimera_core.py demo
python chimera_core.py "I am very happy today!"
python chimera_core.py "I'm feeling anxious and overwhelmed."
python chimera_core.py "It's an okay experience, nothing special so far."
python chimera_core.py compare "I love this performance"
python chimera_core.py caption "Can you tell me more about the system?"
```

### Web

After `python chimera_web.py` starts, verify:

- `GET /`
- `GET /api/state`
- `POST /api/process`
- `GET /projection`
- `GET /api/export`

## Student Test Flow

From the project root:

```bash
python verify_prerequisites.py
pip install -r requirements-dev.txt
pytest tests/unit/test_chimera_core.py -v
pytest tests/e2e/test_chimera_smoke.py -v
pytest tests/unit -v
pytest tests --collect-only -q
```

Treat `pytest tests -v` as a broader sweep rather than the default first check.

## Secondary Docker Paths

These are valid only after the monolith is healthy:

```bash
docker compose -f docker-compose.mvp.yml config --services
docker compose -f docker-compose.student.yml config --services
docker compose -f docker-compose.mvp.yml up -d --build
docker compose -f docker-compose.student.yml up -d --build
```

If Docker cannot reach the local engine, treat that as an environment blocker before treating it as a repository bug.

If `8080` is already in use for the student sandbox:

```powershell
$env:CHIMERA_STUDENT_PORT=18080
docker compose -f docker-compose.student.yml up -d --build
```

## Windows Checklist

Before following the commands exactly, make sure a fresh PowerShell window can run:

```powershell
python --version
pip --version
git --version
docker compose version
```

If `python --version` fails, add these directories to your user `Path`, then open a new shell:

- `%LocalAppData%\Programs\Python\Python312`
- `%LocalAppData%\Programs\Python\Python312\Scripts`

## Related Guides

- [README.md](../../README.md)
- [GETTING_STARTED.md](GETTING_STARTED.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [TESTING.md](TESTING.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)

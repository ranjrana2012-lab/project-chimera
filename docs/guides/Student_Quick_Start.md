# Student Quick Start

**Version:** 2.1.0
**Last Updated:** April 26, 2026
**Target Audience:** Students joining the active Project Chimera demonstrator

This guide is the short classroom entrypoint. For the full validated setup path,
use `docs/guides/STUDENT_LAPTOP_SETUP.md`.

## Start Immediately

The safest first path is the monolithic operator-console demonstrator. It works
on ordinary laptops and does not require Docker, GPU access, GLM keys, or DGX
hardware.

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

Windows PowerShell:

```powershell
cd services/operator-console
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe chimera_core.py demo
$env:PORT='18080'
.\venv\Scripts\python.exe chimera_web.py
```

Open:

```text
http://127.0.0.1:18080
```

## Demo Inputs

- `I am very happy today!` -> `momentum_build`
- `I'm feeling anxious and overwhelmed.` -> `supportive_care`
- `It's an okay experience, nothing special so far.` -> `standard_response`
- `compare "I love this performance"` -> baseline versus adaptive output
- `caption "Can you tell me more about the system?"` -> accessibility output
- `export` -> JSON and CSV session export

## Optional Student Docker Dashboard

Use Docker only after the Python route works, or when your tutor specifically
asks for container validation.

```bash
docker compose -f docker-compose.student.yml up -d --build
```

Open:

```text
http://127.0.0.1:8080
```

If port `8080` is busy:

```powershell
$env:CHIMERA_STUDENT_PORT='18080'
docker compose -f docker-compose.student.yml up -d --build
```

## Student Focus Areas

To prevent students from overwriting each other's work, the project is split
into three classroom-friendly areas.

### Focus Area 1: AI and Prompt Engineering

You are the brains of the operation. Your job is to make the adaptive responses
feel smarter and more theatrical.

- Where to work: `services/operator-console/chimera_core.py`
- What to improve: `generate_response()`, `select_strategy()`, and heuristic sentiment detection
- How to test: `python chimera_core.py demo`

### Focus Area 2: Full-Stack Web App and UX

You are the face of the operation. Your job is to make the dashboard feel alive
for an audience or operator.

- Where to work: `services/operator-console/chimera_web.py` and `services/operator-console/static/`
- What to improve: dashboard layout, visual feedback, accessibility display, and live polling
- How to test: `python chimera_web.py`, then open the local dashboard

### Focus Area 3: DevOps and Reliability Analytics

You are the shield of the operation. Your job is to keep the demo dependable and
make exported data useful.

- Where to work: `tests/e2e/test_chimera_smoke.py`, `tests/unit/test_chimera_core.py`, and export-related scripts
- What to improve: regression tests, export verification, and small analytics summaries
- How to test: `pytest tests/e2e/test_chimera_smoke.py -v`

## Validated Checks

From the project root:

```bash
python verify_prerequisites.py
pip install -r requirements-dev.txt
pytest tests/unit/test_chimera_core.py -v
pytest tests/e2e/test_chimera_smoke.py -v
pytest tests/unit -v
pytest tests --collect-only -q
```

## Where To Look Next

- `README.md`
- `AGENTS.md`
- `docs/guides/STUDENT_LAPTOP_SETUP.md`
- `docs/guides/GETTING_STARTED.md`
- `docs/guides/TESTING.md`
- `docs/guides/DEPLOYMENT.md`

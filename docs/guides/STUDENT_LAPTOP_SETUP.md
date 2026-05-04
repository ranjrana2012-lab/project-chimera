# Student / Laptop Setup

This is the default Project Chimera route for students, laptop users, Windows,
macOS, WSL, and first-time reviewers. It avoids external credentials, GPU
requirements, and heavyweight multi-service setup.

## What This Path Runs

- Primary CLI demonstrator: `services/operator-console/chimera_core.py`
- Primary web demonstrator: `services/operator-console/chimera_web.py`
- Optional lightweight Docker dashboard: `docker-compose.student.yml`
- Fallback behavior is allowed and expected when no external LLM key is present.

## Required Tools

- Python 3.12
- Git
- Optional: Docker Desktop if using the student container preview

No API keys are required for the local demonstrator.

## Setup

From the repository root:

```powershell
cd services/operator-console
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\..
.\services\operator-console\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

On macOS or Linux:

```bash
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
cd ../..
./services/operator-console/venv/bin/python -m pip install -r requirements-dev.txt
```

## Verify Prerequisites

```powershell
.\services\operator-console\venv\Scripts\python.exe verify_prerequisites.py
```

Expected result:

- Python and required files pass.
- `openai` may warn as optional.

## Run the CLI Demo

```powershell
cd services/operator-console
.\venv\Scripts\python.exe chimera_core.py demo
.\venv\Scripts\python.exe chimera_core.py "I am very happy today!"
.\venv\Scripts\python.exe chimera_core.py "I'm feeling anxious and overwhelmed."
.\venv\Scripts\python.exe chimera_core.py "It's an okay experience, nothing special so far."
.\venv\Scripts\python.exe chimera_core.py compare "I love this performance"
.\venv\Scripts\python.exe chimera_core.py caption "Can you tell me more about the system?"
```

Expected behavior:

- Positive input routes to `momentum_build`.
- Negative or anxious input routes to `supportive_care`.
- Neutral input routes to `standard_response`.
- `compare` shows baseline versus adaptive behavior.
- `caption` produces accessibility caption output.

## Run the Web Dashboard

```powershell
cd services/operator-console
$env:PORT='18080'
.\venv\Scripts\python.exe chimera_web.py
```

Open:

```text
http://127.0.0.1:18080
```

Useful checks:

```powershell
Invoke-RestMethod http://127.0.0.1:18080/api/state
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:18080/api/process -ContentType 'application/json' -Body '{"text":"I am very happy today!"}'
Invoke-RestMethod http://127.0.0.1:18080/api/export
```

## Optional Student Docker Preview

This container is intentionally lightweight and uses the operator-console
heuristic fallback path rather than full local ML setup.

```powershell
docker compose -f docker-compose.student.yml up -d --build
docker compose -f docker-compose.student.yml ps
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

Stop it:

```powershell
docker compose -f docker-compose.student.yml down
```

## Test Commands

From the repository root:

```powershell
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/unit/test_chimera_core.py test_chimera_smoke.py -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/unit -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests --collect-only -q
```

## Student Troubleshooting

- If `python` opens the Microsoft Store, disable Windows App Execution Aliases
  for `python.exe` and `python3.exe`, or call the venv Python directly.
- If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process Bypass`
  or skip activation and call `.\venv\Scripts\python.exe` directly.
- If Docker is unavailable, keep using the monolithic Python path. Docker is
  secondary for students.

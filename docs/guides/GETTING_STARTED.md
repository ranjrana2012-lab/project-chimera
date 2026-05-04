# Getting Started with Project Chimera

This guide focuses on the paths that are current and usable today.

Project Chimera has two profile-specific setup guides:

1. Student / Laptop: `docs/guides/STUDENT_LAPTOP_SETUP.md`
2. DGX Spark / GB10 ARM64: `docs/guides/DGX_SPARK_SETUP.md`

Agents should read `AGENTS.md` first and can run:

```bash
python3 scripts/detect_runtime_profile.py
```

Project Chimera has three main ways to run:

1. The monolithic operator-console demonstrator in `services/operator-console`.
2. The lightweight student dashboard in `docker-compose.student.yml`.
3. The secondary MVP Docker Compose stack in `docker-compose.mvp.yml`, optionally combined with `docker-compose.dgx-spark.yml` on DGX Spark / GB10 ARM64 hardware.

For a first run, start with the monolithic demonstrator. It is the quickest way to validate sentiment routing, caption mode, export, and the local web dashboard without depending on the full container stack.

## Prerequisites

### Required

- Python 3.12 or later
- Git

### Optional

- Docker Desktop / Docker Engine with Docker Compose v2 for the secondary containerized paths
- Docker GPU support through NVIDIA runtime or CDI, plus NGC login where required, for the DGX Spark path
- `GLM_API_KEY` if you want to exercise external GLM-backed flows in the microservice stack

## Recommended First Run: Monolithic Demonstrator

```bash
# Clone the repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Create a local Python environment for the operator console
cd services/operator-console
python3 -m venv venv
source venv/bin/activate
# Windows PowerShell:
#   .\venv\Scripts\Activate.ps1
# If that is blocked by execution policy:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\venv\Scripts\Activate.ps1
# Or call the venv interpreter directly:
#   .\venv\Scripts\python.exe -m pip install -r requirements.txt

# Install monolith dependencies
./venv/bin/python -m pip install -r requirements.txt
```

### Launch the Web Dashboard

```bash
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`.

If port `8080` is already in use, choose another free port and rerun:

```bash
# macOS / Linux
export PORT=18080

# Windows PowerShell
$env:PORT=18080

./venv/bin/python chimera_web.py
```

### CLI Fallback

```bash
./venv/bin/python chimera_core.py
```

### Demo Inputs

- `"I am very happy today!"` -> `momentum_build`
- `"I'm feeling anxious and overwhelmed."` -> `supportive_care`
- `"It's an okay experience, nothing special so far."` -> `standard_response`
- `compare` -> side-by-side baseline vs adaptive output
- `caption` -> SRT accessibility output
- `export` -> session export to JSON and CSV

## Local Validation Commands

After the monolith is installed, these are the highest-signal checks:

```bash
# From services/operator-console
./venv/bin/python chimera_core.py demo
```

```bash
# From the project root
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python -m pip install -r requirements-dev.txt
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_core.py -v
./services/operator-console/venv/bin/python -m pytest test_chimera_smoke.py -v
./services/operator-console/venv/bin/python -m pytest tests/unit -v
./services/operator-console/venv/bin/python -m pytest tests --collect-only -q
```

## Secondary Path: MVP Docker Compose Stack

Use this after the monolith is working or when you specifically need the multi-service wiring.

```bash
docker compose -f docker-compose.mvp.yml config --services
docker compose -f docker-compose.mvp.yml up -d --build
docker compose -f docker-compose.mvp.yml ps
```

For DGX Spark / GB10 ARM64 hosts, use the DGX override instead:

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

Do not use the DGX override on ordinary student laptops.

### Current MVP Service Ports

| Service | URL | Purpose |
|---------|-----|---------|
| OpenClaw Orchestrator | http://localhost:8000 | Core coordination |
| SceneSpeak Agent | http://localhost:8001 | Dialogue generation |
| Translation Agent | http://localhost:8002 | Translation |
| Sentiment Agent | http://localhost:8004 | Sentiment analysis |
| Safety Filter | http://localhost:8006 | Content moderation |
| Operator Console | http://localhost:8007 | Control UI |
| Hardware Bridge | http://localhost:8008 | DMX simulation |
| Redis | localhost:6379 | State management |

### Optional Environment Variables

`GLM_API_KEY` is optional. If it is not set, parts of the secondary stack may fall back to mock or local behavior depending on service configuration.

## Secondary Path: Student Dashboard Sandbox

For an operator-console-only containerized preview:

```bash
docker compose -f docker-compose.student.yml up -d --build
```

This exposes the student dashboard at `http://localhost:8080`.

If port `8080` is already in use, set a different host port:

```powershell
$env:CHIMERA_STUDENT_PORT=18080
docker compose -f docker-compose.student.yml up -d --build
```

## Troubleshooting

### Python Command Not Found

Install Python 3.12+ and make sure the interpreter is available as `python`.

On Windows, add these directories to your user `Path`, then open a new PowerShell window:

- `%LocalAppData%\Programs\Python\Python312`
- `%LocalAppData%\Programs\Python\Python312\Scripts`

Then verify:

```powershell
python --version
pip --version
```

### PowerShell Blocks Activate.ps1

If `.\venv\Scripts\Activate.ps1` is blocked, use one of these options:

- `Set-ExecutionPolicy -Scope Process Bypass` for the current shell only
- `cmd /c venv\Scripts\activate.bat`
- `.\venv\Scripts\python.exe ...` without activating the venv

### Port Already In Use

If the web dashboard does not start on `8080`, set `PORT` to another free port such as `18080`.

### Docker Compose Fails Before Services Start

Start with the monolithic path first. If `docker compose` cannot reach the local Docker engine, fix Docker Desktop or daemon access before treating it as a repository issue.

### GLM Features Unavailable

Leave `GLM_API_KEY` unset for local monolith validation. Add it only if you need the external GLM-backed microservice flows.

## Next Steps

- [README.md](../../README.md) for the main overview
- [DEVELOPMENT.md](DEVELOPMENT.md) for day-to-day workflows
- [TESTING.md](TESTING.md) for test strategy and commands
- [DEPLOYMENT.md](DEPLOYMENT.md) for containerized deployment details

# Getting Started with Project Chimera

This guide focuses on the paths that are current and usable today.

Project Chimera has two main ways to run:

1. The monolithic operator-console demonstrator in `services/operator-console`.
2. The secondary Docker Compose stacks in `docker-compose.mvp.yml` and `docker-compose.student.yml`.

For a first run, start with the monolithic demonstrator. It is the quickest way to validate sentiment routing, caption mode, export, and the local web dashboard without depending on the full container stack.

## Prerequisites

### Required

- Python 3.12 or later
- Git

### Optional

- Docker Desktop / Docker Engine with Docker Compose v2 for the secondary containerized paths
- `GLM_API_KEY` if you want to exercise external GLM-backed flows in the microservice stack

## Recommended First Run: Monolithic Demonstrator

```bash
# Clone the repository
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Create a local Python environment for the operator console
cd services/operator-console
python -m venv venv
source venv/bin/activate
# Windows PowerShell: .\venv\Scripts\Activate.ps1

# Install monolith dependencies
pip install -r requirements.txt
```

### Launch the Web Dashboard

```bash
python chimera_web.py
```

Open `http://127.0.0.1:8080`.

If port `8080` is already in use, choose another free port and rerun:

```bash
# macOS / Linux
export PORT=18080

# Windows PowerShell
$env:PORT=18080

python chimera_web.py
```

### CLI Fallback

```bash
python chimera_core.py
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
python chimera_core.py demo
```

```bash
# From the project root
python verify_prerequisites.py
pip install -r requirements-dev.txt
pytest tests/unit/test_chimera_core.py -v
pytest tests/e2e/test_chimera_smoke.py -v
pytest tests/unit -v
pytest tests --collect-only -q
```

## Secondary Path: MVP Docker Compose Stack

Use this after the monolith is working or when you specifically need the multi-service wiring.

```bash
docker compose -f docker-compose.mvp.yml config --services
docker compose -f docker-compose.mvp.yml up -d --build
docker compose -f docker-compose.mvp.yml ps
```

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

## Troubleshooting

### Python Command Not Found

Install Python 3.12+ and make sure the interpreter is available as `python`.

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

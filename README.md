# Project Chimera

An AI-powered live theatre platform that adapts performance logic in real time
from audience input.

[![CI/CD](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)

Last validated locally: April 26, 2026

## Choose Your Route

Project Chimera now documents two explicit runtime profiles:

| Profile | Use When | Start Here |
| --- | --- | --- |
| Student / Laptop | Students, Windows/macOS/WSL, ordinary laptops, first validation pass, no GPU required | `docs/guides/STUDENT_LAPTOP_SETUP.md` |
| DGX Spark / GB10 ARM64 | NVIDIA DGX Spark / Grace Blackwell ARM64 host with Docker + NVIDIA Container Runtime | `docs/guides/DGX_SPARK_SETUP.md` |

Agents should read `AGENTS.md` first. To auto-detect the likely profile:

```bash
python scripts/detect_runtime_profile.py
```

If detection is ambiguous, use the Student / Laptop route first.

## Student / Laptop Quick Start

This is the default path for most users.

```powershell
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

cd services/operator-console
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

.\venv\Scripts\python.exe chimera_core.py demo
$env:PORT='18080'
.\venv\Scripts\python.exe chimera_web.py
```

Open:

```text
http://127.0.0.1:18080
```

Try:

- `I am very happy today!` -> `momentum_build`
- `I'm feeling anxious and overwhelmed.` -> `supportive_care`
- `It's an okay experience, nothing special so far.` -> `standard_response`
- `compare "I love this performance"` -> baseline versus adaptive output
- `caption "Can you tell me more about the system?"` -> accessibility output

## Optional Student Docker Preview

```powershell
docker compose -f docker-compose.student.yml up -d --build
```

Open:

```text
http://127.0.0.1:8080
```

This container is intentionally lightweight and uses heuristic fallback behavior.

## DGX Spark / GB10 Quick Start

Use this only on a DGX Spark / ARM64 host with NVIDIA Container Runtime and NGC
access configured.

```bash
docker login nvcr.io
python scripts/detect_runtime_profile.py
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

The DGX route uses `services/sentiment-agent/Dockerfile.dgx`, which starts from
an NVIDIA NGC PyTorch image instead of pulling PyTorch from PyPI.

> **Note**: Full integration tests run via `make test` or `pytest tests/integration/` require the `docker-compose.mvp.yml` services to be active and must be executed from *within* the Docker network to resolve internal DNS hostnames (e.g., `openclaw-orchestrator`, `redis`).

## Validated Checks

From the repository root:

```powershell
.\services\operator-console\venv\Scripts\python.exe verify_prerequisites.py
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/unit/test_chimera_core.py tests/e2e/test_chimera_smoke.py -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/unit -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests --collect-only -q
```

With the MVP Compose stack running:

```powershell
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/integration/mvp/test_docker_compose.py -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/integration/mvp/test_sentiment_agent.py tests/integration/mvp/test_hardware_bridge.py tests/integration/mvp/test_translation_agent.py tests/integration/mvp/test_safety_filter.py -v
```

## Repository Structure

```text
project-chimera/
  AGENTS.md                         # Agent route selection rules
  docker-compose.student.yml        # Student/laptop container preview
  docker-compose.mvp.yml            # MVP multi-service stack
  docker-compose.dgx-spark.yml      # DGX Spark / ARM64 override
  docs/guides/
    STUDENT_LAPTOP_SETUP.md
    DGX_SPARK_SETUP.md
  scripts/
    detect_runtime_profile.py
  services/operator-console/
    chimera_core.py
    chimera_web.py
  services/sentiment-agent/
    Dockerfile
    Dockerfile.dgx
```

## External Services

Project Chimera does not require credentials for the default student route.
Advanced LLM features can use `GLM_API_KEY` or a local DGX LLM endpoint, but do
not invent or commit secrets.

## Contributing and Security

See `CONTRIBUTING.md` and `SECURITY.md`.

## License

MIT License

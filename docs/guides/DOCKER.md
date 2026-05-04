# Docker Guide

**Last Updated:** May 4, 2026

Docker is a secondary Project Chimera path. Students should validate the
monolithic operator-console first unless their tutor specifically asks for
container validation.

## Compose Files

| File | Audience | Purpose |
| --- | --- | --- |
| `docker-compose.student.yml` | Students / laptops | Lightweight operator-console dashboard preview |
| `docker-compose.mvp.yml` | Local integration | Multi-service MVP stack with fallback-friendly services |
| `docker-compose.dgx-spark.yml` | DGX Spark / GB10 ARM64 | NVIDIA GPU/ARM64 override for advanced hosts |

## Student / Laptop Container

```powershell
docker compose -f docker-compose.student.yml config --services
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

Stop:

```powershell
docker compose -f docker-compose.student.yml down
```

## MVP Multi-Service Stack

```powershell
docker compose -f docker-compose.mvp.yml config --services
docker compose -f docker-compose.mvp.yml up -d --build
docker compose -f docker-compose.mvp.yml ps
```

Validated service ports:

| Service | Port | Health |
| --- | ---: | --- |
| OpenClaw Orchestrator | 8000 | `/health` |
| SceneSpeak Agent | 8001 | `/health` |
| Translation Agent | 8002 | `/health` |
| Sentiment Agent | 8004 | `/health` |
| Safety Filter | 8006 | `/health` |
| Operator Console | 8007 | `/health` |
| Hardware Bridge | 8008 | `/health` |
| Redis | 6379 | `redis-cli ping` |

Focused validation:

```powershell
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/integration/mvp/test_docker_compose.py -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/integration/mvp/test_sentiment_agent.py tests/integration/mvp/test_hardware_bridge.py tests/integration/mvp/test_translation_agent.py tests/integration/mvp/test_safety_filter.py -v
```

Stop:

```powershell
docker compose -f docker-compose.mvp.yml down
```

## DGX Spark / GB10 ARM64 Stack

Use only on DGX Spark / Grace Blackwell ARM64 hosts with Docker GPU support
through NVIDIA runtime or CDI and NGC login configured where required.

```bash
python3 scripts/detect_runtime_profile.py
docker login nvcr.io
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

Stop:

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml down
```

## Troubleshooting

- If Docker Desktop is not running, fix that before treating failures as repo
  issues.
- If `GLM_API_KEY` is unset, SceneSpeak may report no external LLM. That is
  expected unless you are intentionally testing GLM.
- If the DGX route fails on a laptop, use the student route. The DGX override is
  intentionally hardware-specific.

# Deployment Guide

**Version:** 1.0.0
**Last Updated:** May 4, 2026

## Overview

Project Chimera currently supports three practical deployment paths:

1. A local monolithic demonstrator in `services/operator-console`.
2. A student/laptop Docker sandbox in `docker-compose.student.yml`.
3. A multi-service MVP stack in `docker-compose.mvp.yml`, with an optional DGX Spark / GB10 ARM64 override in `docker-compose.dgx-spark.yml`.

For local previews and rapid validation, use the monolith first. Use Docker Compose when you need the broader service topology.

## Deployment Options

### 1. Local Monolithic Preview

Best for:

- first-run validation
- demos on a single machine
- CLI and dashboard checks
- sentiment, compare, caption, and export workflows

Setup:

```bash
cd services/operator-console
python3 -m venv venv
source venv/bin/activate
# Windows PowerShell:
#   .\venv\Scripts\Activate.ps1
# If that is blocked:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\venv\Scripts\Activate.ps1
# Or use .\venv\Scripts\python.exe directly.
./venv/bin/python -m pip install -r requirements.txt
PORT=18080 ./venv/bin/python chimera_web.py
```

If `8080` is already in use, set `PORT` to another free port before launching the dashboard.

### 2. MVP Docker Compose Stack

Best for:

- service-to-service integration
- orchestration and Redis wiring
- containerized local development

Start-up sequence:

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
docker compose -f docker-compose.mvp.yml config --services
docker compose -f docker-compose.mvp.yml up -d --build
docker compose -f docker-compose.mvp.yml ps
```

### 3. Student Sandbox Stack

Best for:

- containerized operator-console preview only

```bash
docker compose -f docker-compose.student.yml up -d --build
```

This exposes the student dashboard on `http://localhost:8080`.

If `8080` is already in use, set a different host port:

```powershell
$env:CHIMERA_STUDENT_PORT=18080
docker compose -f docker-compose.student.yml up -d --build
```

### 4. DGX Spark / GB10 ARM64 Stack

Best for:

- NVIDIA DGX Spark / Grace Blackwell ARM64 hosts
- GPU-backed sentiment or local LLM experiments
- advanced service integration after the student path is already understood

Prerequisites:

- Docker and Docker GPU support through NVIDIA runtime or CDI
- NGC registry login for `nvcr.io`
- Verified `docker run --rm --gpus all ...` GPU access

```bash
python3 scripts/detect_runtime_profile.py
docker login nvcr.io
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

Do not use this path on student laptops.

## Current MVP Service Map

The current `docker-compose.mvp.yml` exposes:

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

## Environment Variables

### Monolith

`chimera_web.py` supports:

- `HOST` defaulting to `0.0.0.0`
- `PORT` defaulting to `8080`

Example:

```bash
export PORT=18080
./venv/bin/python chimera_web.py
```

### Docker Compose

`GLM_API_KEY` is optional. Leave it unset unless you explicitly need the external GLM-backed flows in the secondary stack.

### DGX Spark

The DGX override also supports:

- `CHIMERA_DGX_PYTORCH_IMAGE`, default `nvcr.io/nvidia/pytorch:25.11-py3`
- `CHIMERA_DGX_MODEL_CACHE`, default `./models/dgx-spark/sentiment`
- `CHIMERA_DGX_LLM_URL`, default `http://host.docker.internal:8012`
- `CHIMERA_DGX_LLM_MODEL`, default `nemotron-3-super-120b-a12b-nvfp4`
- `CHIMERA_DGX_LLM_TIMEOUT`, default `300`

## Verifying a Deployment

### Monolith

```bash
# From services/operator-console
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```

Key endpoints:

- `GET /`
- `GET /api/state`
- `POST /api/process`
- `GET /projection`
- `GET /api/export`

### Docker Compose

```bash
docker compose -f docker-compose.mvp.yml ps
curl http://localhost:8000/health
curl http://localhost:8007/health
curl http://localhost:8008/health
```

If you want a quick port sweep:

```bash
for port in 8000 8001 8002 8004 8006 8007 8008; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health || echo "Service not responding"
done
```

### DGX Spark

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
curl http://localhost:8004/health
docker logs chimera-sentiment-agent --tail 80
```

## Troubleshooting

### Docker Compose Fails Before Services Start

If `docker compose` cannot reach the local engine, fix Docker Desktop or daemon access first. Treat that as an environment issue before treating it as a repository bug.

### Port Conflicts

- For the monolith dashboard, set `PORT` to another free port.
- For Compose, change the host-side port mapping in the relevant compose file.

### Missing External LLM Credentials

Do not invent `GLM_API_KEY`. The monolith can still be validated locally without it, and the Compose stack should only rely on it when you are intentionally testing that integration.

## Operational Commands

```bash
docker compose -f docker-compose.mvp.yml logs -f
docker compose -f docker-compose.mvp.yml restart operator-console
docker compose -f docker-compose.mvp.yml build operator-console
docker compose -f docker-compose.mvp.yml down
docker compose -f docker-compose.mvp.yml down -v
```

## Notes for Production Hardening

The repository contains the MVP Compose stack, but production deployment details still need environment-specific decisions such as:

- external Redis strategy
- secret management
- ingress / TLS
- resource limits
- monitoring stack choice

Keep those decisions separate from the validated local monolith and MVP Compose paths.

## Related Guides

- [GETTING_STARTED.md](GETTING_STARTED.md)
- [STUDENT_LAPTOP_SETUP.md](STUDENT_LAPTOP_SETUP.md)
- [DGX_SPARK_SETUP.md](DGX_SPARK_SETUP.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [TESTING.md](TESTING.md)
- [README.md](../../README.md)

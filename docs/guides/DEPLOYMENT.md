# Deployment Guide

**Version:** 1.0.0
**Last Updated:** April 24, 2026

## Overview

Project Chimera currently supports two practical deployment paths:

1. A local monolithic demonstrator in `services/operator-console`.
2. Secondary Docker Compose stacks for multi-service or sandbox scenarios.

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
python -m venv venv
source venv/bin/activate
# Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python chimera_web.py
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
python chimera_web.py
```

### Docker Compose

`GLM_API_KEY` is optional. Leave it unset unless you explicitly need the external GLM-backed flows in the secondary stack.

## Verifying a Deployment

### Monolith

```bash
# From services/operator-console
python chimera_core.py demo
python chimera_web.py
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
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [TESTING.md](TESTING.md)
- [README.md](../../README.md)

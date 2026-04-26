# Project Chimera Quick Start

**Last Updated:** April 26, 2026
**Status:** Canonical setup pointer

Project Chimera now has two explicit runtime profiles:

- Student / Laptop: ordinary student machines, Windows/macOS/WSL/Linux laptops,
  and first validation runs.
- DGX Spark / GB10 ARM64: NVIDIA DGX Spark or Grace Blackwell hosts with Docker,
  NVIDIA Container Runtime, and NGC access.

Agents should read `AGENTS.md` at the repository root before choosing a route.

## Fastest Student Path

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

## Optional Student Docker Preview

```powershell
docker compose -f docker-compose.student.yml up -d --build
```

Open:

```text
http://127.0.0.1:8080
```

## DGX Spark / GB10 Route

Use only on DGX Spark / ARM64 hosts:

```bash
python scripts/detect_runtime_profile.py
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
```

## Full Guides

- `docs/guides/STUDENT_LAPTOP_SETUP.md`
- `docs/guides/DGX_SPARK_SETUP.md`
- `docs/guides/GETTING_STARTED.md`
- `docs/guides/TESTING.md`
- `docs/guides/DEPLOYMENT.md`

# Project Chimera Agent Routing

This repository has two supported validation routes. Agents should choose the
route from local evidence, not optimism.

## Default Route: Student / Laptop

Use this route when any of these are true:

- The user is a student, reviewer, or first-time setup user.
- The machine is Windows, macOS, WSL, or ordinary Linux laptop/desktop.
- No NVIDIA DGX Spark / GB10 / ARM64 evidence is present.
- Docker or GPU access is unavailable or uncertain.

Primary commands:

```powershell
cd services/operator-console
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe chimera_core.py demo
$env:PORT='18080'; .\venv\Scripts\python.exe chimera_web.py
```

On Linux/macOS hosts, use `python3 -m venv venv` and then call
`./venv/bin/python` explicitly.

For a lightweight container preview:

```powershell
docker compose -f docker-compose.student.yml up -d --build
```

Use `docs/guides/STUDENT_LAPTOP_SETUP.md` for the detailed route.

## Advanced Route: DGX Spark / GB10 ARM64

Use this route only when the host evidence supports it:

- Linux ARM64 / `aarch64`.
- DGX Spark, GB10, or Grace Blackwell hardware is present.
- Docker is available.
- Docker GPU access works with `--gpus all` through NVIDIA runtime or CDI.
- The user has authenticated to NGC if pulling NVIDIA containers.

Primary commands:

```bash
python3 scripts/detect_runtime_profile.py
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
```

Use `docs/guides/DGX_SPARK_SETUP.md` for the detailed route.

## Agent Rules

- Do not invent `GLM_API_KEY`, NGC tokens, local Nemotron endpoints, or cluster
  configuration.
- Do not claim the DGX path works unless it was run on DGX Spark / GB10-class
  hardware.
- If hardware detection is ambiguous, choose the student/laptop route and report
  what evidence is missing.
- Validate the monolithic operator-console path before Docker unless the user
  explicitly asks for DGX or Compose validation.
- Keep generated exports, model caches, and logs out of commits.

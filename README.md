# Project Chimera

An AI-powered live theatre platform that adapts performance logic in real time
from audience input.

[![CI/CD](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)

Last validated locally: May 4, 2026 on Ubuntu 24.04.4 ARM64 / NVIDIA GB10.

Current local sign-off:

- Local operator-console CLI and web route: validated
- Student Docker route: validated on port `8080`
- MVP / DGX Compose route: validated on GB10 with Docker GPU/CDI support
- Kimi host-facing route: validated on `127.0.0.1:8012` and `127.0.0.1:50052`
- Final regression: `737 passed, 96 skipped, 4 warnings`

See `LOCAL_VALIDATION_REPORT.md`, `PATCH_SUMMARY.md`, and
`REMAINING_GAPS.md` for the evidence and caveats behind this status.

## Choose Your Route

Project Chimera now documents two explicit runtime profiles:

| Profile | Use When | Start Here |
| --- | --- | --- |
| Student / Laptop | Students, Windows/macOS/WSL, ordinary laptops, first validation pass, no GPU required | `docs/guides/STUDENT_LAPTOP_SETUP.md` |
| DGX Spark / GB10 ARM64 | NVIDIA DGX Spark / Grace Blackwell ARM64 host with Docker GPU support through NVIDIA runtime or CDI | `docs/guides/DGX_SPARK_SETUP.md` |

Agents should read `AGENTS.md` first. To auto-detect the likely profile:

```bash
python3 scripts/detect_runtime_profile.py
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

Use this only on a DGX Spark / ARM64 host with Docker GPU support and NGC
access configured where required by the images you pull.

```bash
docker login nvcr.io
python3 scripts/detect_runtime_profile.py
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

The DGX route uses `services/sentiment-agent/Dockerfile.dgx`, which starts from
an NVIDIA NGC PyTorch image instead of pulling PyTorch from PyPI.

### Kimi K2.6 Super-Agent (Advanced)

For DGX Spark systems with 128GB GPU VRAM, Project Chimera now supports **Kimi K2.6** 
(Moonshot AI's 1T parameter Mixture-of-Experts model) as a hierarchical super-agent for:
- Long context reasoning (>8K tokens)
- Multimodal processing (images, video, audio)
- Agentic code generation

```bash
# Download Kimi K2.6 model (~70GB)
./scripts/download-kimi-k26.sh

# Start vLLM service
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-vllm

# Wait for vLLM to be ready
./scripts/wait-for-kimi.sh

# Start Kimi super-agent
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-super-agent

# Validate VRAM usage (should be <85GB)
./scripts/validate-kimi-vram.sh
```

Validated host-facing Kimi ports:

- vLLM HTTP/OpenAI-compatible API: `http://127.0.0.1:8012`
- Kimi super-agent gRPC: `127.0.0.1:50052`

See `docs/guides/KIMI_QUICKSTART.md` for complete Kimi K2.6 documentation.

## Monitoring Stack

Project Chimera includes a comprehensive monitoring stack for system health and performance metrics.

### Quick Setup

```bash
# Automated setup
./scripts/setup-monitoring.sh

# Or manually
docker compose -f docker-compose.mvp.yml up -d prometheus netdata
cd services/dashboard && python3 -m uvicorn main:app --port 8013
```

### Access Points

- **Netdata Dashboard**: http://localhost:19999 - Real-time system metrics
- **Prometheus UI**: http://localhost:9090 - Metrics query and exploration
- **Monitoring Dashboard**: http://localhost:8013/monitoring - Unified monitoring view

### Metrics Collected

- CPU usage (system and per-core)
- Memory utilization
- GPU metrics (NVIDIA GPUs)
- Container health and resource usage
- Network I/O
- Disk I/O
- Custom application metrics

### Running Integration Tests

```bash
# Test monitoring stack
pytest tests/integration/test_monitoring_e2e.py -v -m integration
```

> **Note**: Full integration tests run via `make test` or `pytest tests/integration/` require the `docker-compose.mvp.yml` services to be active and must be executed from *within* the Docker network to resolve internal DNS hostnames (e.g., `openclaw-orchestrator`, `redis`).

## Validated Checks

From the repository root:

```powershell
.\services\operator-console\venv\Scripts\python.exe verify_prerequisites.py
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/unit/test_chimera_core.py test_chimera_smoke.py -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/unit -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests --collect-only -q
```

With the MVP Compose stack running:

```powershell
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/integration/mvp/test_docker_compose.py -v
.\services\operator-console\venv\Scripts\python.exe -m pytest tests/integration/mvp/test_sentiment_agent.py tests/integration/mvp/test_hardware_bridge.py tests/integration/mvp/test_translation_agent.py tests/integration/mvp/test_safety_filter.py -v
```

On Linux/macOS, use `./services/operator-console/venv/bin/python` for the same
pytest commands. For a full local regression against a running Kimi/DGX stack:

```bash
KIMI_VLLM_TEST_URL=http://127.0.0.1:8012 \
KIMI_MODEL_TEST_NAME=/model \
KIMI_TEST_TIMEOUT=180 \
KIMI_GRPC_TEST_TARGET=127.0.0.1:50052 \
./services/operator-console/venv/bin/python -m pytest -q -ra
```

## Repository Structure

```text
project-chimera/
  AGENTS.md                         # Agent route selection rules
  docker-compose.student.yml        # Student/laptop container preview
  docker-compose.mvp.yml            # MVP multi-service stack
  docker-compose.dgx-spark.yml      # DGX Spark / ARM64 override
  LOCAL_VALIDATION_REPORT.md        # Latest local sign-off evidence
  PATCH_SUMMARY.md                  # Summary of validation fixes
  REMAINING_GAPS.md                 # Non-blocking caveats and follow-up
  docs/guides/
    STUDENT_LAPTOP_SETUP.md
    DGX_SPARK_SETUP.md
    KIMI_QUICKSTART.md
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

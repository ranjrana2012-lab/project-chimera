# Project Chimera - Quick Start Guide

This guide will get you up and running with Project Chimera as quickly as possible.

## 1. Determine Your Runtime Profile

Run the profile detection script to see which route your environment supports:
```bash
python3 scripts/detect_runtime_profile.py
```
> **Note**: If detection is ambiguous or fails, default to the **Student / Laptop Route**.

---

## 2. Default Route: Student / Laptop
Use this route for Windows/macOS/Linux laptops without specialized NVIDIA GPU environments.

### Local Monolithic Environment Setup
```bash
# 1. Navigate to the operator console
cd services/operator-console

# 2. Setup your virtual environment
python3 -m venv venv

# Windows/Powershell:
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe chimera_core.py demo
$env:PORT='18080'; .\venv\Scripts\python.exe chimera_web.py

# Linux/macOS:
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```
**Access the Web UI**: `http://127.0.0.1:18080`

### Optional: Docker Preview 
For a lightweight, heuristic-only container preview:
```bash
docker compose -f docker-compose.student.yml up -d --build
```
**Access the Web UI**: `http://127.0.0.1:8080`

---

## 3. Advanced Route: NVIDIA DGX Spark / GB10 (ARM64)
Use this route **only** if you are on an NVIDIA DGX Spark / Grace Blackwell host (ARM64), with Docker GPU support (`--gpus all` through NVIDIA runtime or CDI), and NGC Registry access where required by the images you pull.

```bash
# 1. Login to NVIDIA container registry (required for PyTorch base images)
docker login nvcr.io

# 2. Verify your Compose Configuration
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services

# 3. Boot the Multi-Service Application Stack
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build

# 4. Verify Services are Running
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

The Operator Console will be exposed on **port 8007**.
```bash
http://<dgx-host-ip>:8007
```

### 3.1 Kimi K2.6 Super-Agent (DGX Spark Optional)
For DGX Spark systems with 128GB GPU VRAM, enable **Kimi K2.6** super-agent for complex workflows:

```bash
# Download Kimi K2.6 model (~70GB, takes 30-60 minutes)
./scripts/download-kimi-k26.sh

# Start vLLM service (port 8012)
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-vllm

# Wait for vLLM to be healthy
./scripts/wait-for-kimi.sh

# Start Kimi super-agent (gRPC port 50052)
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-super-agent

# Validate VRAM usage (should be <85GB)
./scripts/validate-kimi-vram.sh
```

**What Kimi K2.6 Enables:**
- Long context reasoning (>8K tokens)
- Multimodal processing (images, video, audio)
- Agentic code generation

For complete documentation, see [Kimi K2.6 Quick Start Guide](docs/guides/KIMI_QUICKSTART.md).

Validated host-facing Kimi ports:

- vLLM HTTP/OpenAI-compatible API: `http://127.0.0.1:8012`
- Kimi super-agent gRPC: `127.0.0.1:50052`

Run the host-facing Kimi integration tests from the repository root:

```bash
KIMI_VLLM_TEST_URL=http://127.0.0.1:8012 \
KIMI_MODEL_TEST_NAME=/model \
KIMI_TEST_TIMEOUT=180 \
KIMI_GRPC_TEST_TARGET=127.0.0.1:50052 \
./services/operator-console/venv/bin/python -m pytest tests/integration/kimi -q
```

## Current Validation Snapshot

The latest local sign-off on the DGX/GB10 ARM64 host completed with:

- runtime detection, prerequisites, local CLI/web, student Docker, MVP/DGX,
  Kimi host-facing validation: pass
- final regression: `737 passed, 96 skipped, 4 warnings`

See `LOCAL_VALIDATION_REPORT.md`, `PATCH_SUMMARY.md`, and
`REMAINING_GAPS.md` for details.



## Monitoring Stack

Project Chimera includes a built-in monitoring stack for system health and performance metrics.

### Setup Monitoring

```bash
# Automated setup (recommended)
./scripts/setup-monitoring.sh

# Or manual setup
docker compose -f docker-compose.mvp.yml up -d prometheus netdata
cd services/dashboard
python3 -m uvicorn main:app --port 8013
```

### Access Dashboards

- **Netdata**: http://localhost:19999 - Real-time system metrics (CPU, memory, disk, network)
- **Prometheus**: http://localhost:9090 - Metrics query and exploration
- **Unified Dashboard**: http://localhost:8013/monitoring - Custom monitoring view

### Testing

```bash
# Run monitoring integration tests
pytest tests/integration/test_monitoring_e2e.py -v -m integration
```

## Useful Test Inputs
Once running (in either environment), try passing these input phrases to see how Chimera adapts the theatrical scene:
- `I am very happy today!` -> expected: `momentum_build`
- `I'm feeling anxious and overwhelmed.` -> expected: `supportive_care`
- `compare "I love this performance"` -> shows baseline vs adaptive output
- `caption "Can you tell me more about the system?"` -> enforces accessibility mode

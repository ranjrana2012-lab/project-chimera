# DGX Spark / GB10 ARM64 Setup

This is the advanced Project Chimera route for NVIDIA DGX Spark / GB10-class
ARM64 systems. It is not the default student path.

Use this path only when the host has:

- Linux ARM64 / `aarch64`
- Docker access
- NVIDIA Container Runtime with `--gpus all`
- NGC registry access for NVIDIA containers
- Optional local LLM endpoint or GLM API key if you want full SceneSpeak LLM
  behavior rather than fallback responses

## Why This Path Is Separate

Student and laptop machines should not pull multi-GB GPU containers or require
NVIDIA-specific runtime setup. DGX Spark should use NVIDIA's optimized container
stack instead of generic PyPI CUDA/PyTorch wheels.

NVIDIA documents DGX Spark as an Ubuntu 24.04 ARM64 system with 128 GB unified
memory, NVIDIA Container Runtime for Docker, and Grace Blackwell optimized NGC
containers. See the official DGX Spark docs:

- https://docs.nvidia.com/dgx/dgx-spark-porting-guide/porting/software-requirements.html
- https://docs.nvidia.com/dgx/dgx-spark/ngc.html
- https://build.nvidia.com/spark/pytorch-fine-tune/run-two-sparks

## Profile Detection

Run this from the repository root:

```bash
python scripts/detect_runtime_profile.py
```

Use the DGX Spark path only if it reports `dgx-spark` or if you manually verify
the missing evidence.

## Host Prerequisites

```bash
uname -m
docker --version
docker compose version
nvidia-smi
docker info --format '{{json .Runtimes}}'
```

Expected:

- `uname -m` is `aarch64` or `arm64`.
- Docker commands work without `sudo`, or you intentionally use `sudo`.
- `nvidia-smi` reports the NVIDIA GPU.
- Docker runtimes include `nvidia`.

If Docker permission fails:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## NGC Authentication

The DGX sentiment image uses an NGC PyTorch base image.

```bash
docker login nvcr.io
```

Use username:

```text
$oauthtoken
```

Use your NGC API key as the password. Do not commit the key.

## GPU Container Smoke Test

```bash
docker run --rm --gpus all nvcr.io/nvidia/pytorch:25.11-py3 \
  python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

If this fails, fix the DGX/NVIDIA runtime before testing Project Chimera.

## Single DGX Spark Compose Path

From the repository root:

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

If you use `.env.dgx-spark`, add `--env-file .env.dgx-spark` before the
`-f` flags.

Health checks:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8001/health
curl -fsS http://127.0.0.1:8002/health
curl -fsS http://127.0.0.1:8004/health
curl -fsS http://127.0.0.1:8006/health
curl -fsS http://127.0.0.1:8007/health
curl -fsS http://127.0.0.1:8008/health
```

Run the MVP integration checks:

```bash
python -m pytest tests/integration/mvp/test_docker_compose.py -v
python -m pytest tests/integration/mvp/test_sentiment_agent.py \
  tests/integration/mvp/test_hardware_bridge.py \
  tests/integration/mvp/test_translation_agent.py \
  tests/integration/mvp/test_safety_filter.py -v
```

Stop the stack:

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml down
```

## Optional LLM Configuration

Without credentials or a local LLM endpoint, SceneSpeak health should report the
LLM as unavailable and use fallback behavior.

You can start from the example environment file:

```bash
cp .env.dgx-spark.example .env.dgx-spark
```

For local DGX LLM routing:

```bash
export CHIMERA_DGX_LLM_URL=http://host.docker.internal:8012
export CHIMERA_DGX_LLM_MODEL=nemotron-3-super-120b-a12b-nvfp4
export CHIMERA_DGX_LLM_TIMEOUT=300
```

For GLM routing:

```bash
export GLM_API_KEY=your_key_here
```

Do not commit `.env` files or API keys.

## Dual DGX Spark Notes

Two connected DGX Spark systems are a cluster topology, not a magic single
larger process. This repository currently provides:

- A single-host DGX Compose override for one DGX Spark.
- Service-level HTTP boundaries that can be distributed later.
- Documentation for validating the stack before multi-node work.

For two connected Sparks, first follow NVIDIA's two-Spark networking and Docker
Swarm guidance, then decide which Chimera services should be placed on which
node. Do not claim memory or GPU pooling unless the specific model runtime and
orchestration layer prove it.

Suggested first split after single-host validation:

- Primary Spark: `openclaw-orchestrator`, `operator-console`, `redis`
- GPU Spark: local LLM runtime and `sentiment-agent`
- Either node: `safety-filter`, `translation-agent`, `hardware-bridge`

Record the exact hostnames, advertised addresses, and health endpoint results
when validating any dual-Spark deployment.

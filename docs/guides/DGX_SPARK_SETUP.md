# DGX Spark / GB10 ARM64 Setup

This is the advanced Project Chimera route for NVIDIA DGX Spark / GB10-class
ARM64 systems. It is not the default student path.

Maintainer validation has covered the DGX/MVP route, Kimi host-facing HTTP/gRPC,
and Docker GPU/CDI support on compatible hardware. Treat those results as
hardware-specific evidence, not as the default public setup path.

Use this path only when the host has:

- Linux ARM64 / `aarch64`
- Docker access
- Docker GPU access with `--gpus all` through NVIDIA runtime or CDI
- NGC registry access for NVIDIA containers
- Optional local LLM endpoint or GLM API key if you want full SceneSpeak LLM
  behavior rather than fallback responses

## Why This Path Is Separate

Student and laptop machines should not pull multi-GB GPU containers or require
NVIDIA-specific runtime setup. DGX Spark should use NVIDIA's optimized container
stack instead of generic PyPI CUDA/PyTorch wheels.

NVIDIA documents DGX Spark as an Ubuntu 24.04 ARM64 system with 128 GB unified
memory, NVIDIA GPU-enabled Docker support, and Grace Blackwell optimized NGC
containers. See the official DGX Spark docs:

- https://docs.nvidia.com/dgx/dgx-spark-porting-guide/porting/software-requirements.html
- https://docs.nvidia.com/dgx/dgx-spark/ngc.html
- https://build.nvidia.com/spark/pytorch-fine-tune/run-two-sparks

## Profile Detection

Run this from the repository root:

```bash
python3 scripts/detect_runtime_profile.py
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
docker info
```

Expected:

- `uname -m` is `aarch64` or `arm64`.
- Docker commands work without `sudo`, or you intentionally use `sudo`.
- `nvidia-smi` reports the NVIDIA GPU.
- Docker runtimes include `nvidia`, or Docker reports NVIDIA CDI devices such
  as `nvidia.com/gpu=all`. The authoritative check is that `docker run
  --gpus all ...` can see the GPU.

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
./services/operator-console/venv/bin/python -m pytest tests/integration/mvp/test_docker_compose.py -v
./services/operator-console/venv/bin/python -m pytest tests/integration/mvp/test_sentiment_agent.py \
  tests/integration/mvp/test_hardware_bridge.py \
  tests/integration/mvp/test_translation_agent.py \
  tests/integration/mvp/test_safety_filter.py -v
```

Stop the stack:

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml down
```

## Optional LLM Configuration

Without external credentials, SceneSpeak can use the local OpenAI-compatible
vLLM endpoint when the DGX/Kimi stack is running. If no GLM key or local LLM is
available, fallback behavior is expected.

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

## Kimi K2.6 Super-Agent (Optional)

For DGX Spark systems with 128GB GPU VRAM, you can enable **Kimi K2.6** as a hierarchical 
super-agent that handles complex workflows requiring long context reasoning, multimodal 
processing, or agentic coding capabilities.

### Prerequisites

- 128GB GPU VRAM (DGX Spark GB10 specification)
- ~70GB free disk space for Kimi K2.6 model (Native INT4 quantized)
- All MVP services running

### Setup Kimi K2.6

```bash
# 1. Download Kimi K2.6 model
./scripts/download-kimi-k26.sh

# 2. Start vLLM service (runs on port 8012)
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-vllm

# 3. Wait for vLLM to be healthy
./scripts/wait-for-kimi.sh

# 4. Start Kimi super-agent (gRPC on port 50052)
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-super-agent

# 5. Validate VRAM usage
./scripts/validate-kimi-vram.sh
```

### VRAM Allocation

| Component | VRAM Usage |
|-----------|------------|
| Kimi K2.6 (Native INT4) | ~70 GB |
| KV Cache | ~10 GB |
| Chimera Agents | ~10-20 GB |
| **Headroom** | ~23 GB |

### Delegation Triggers

Nemo Claw automatically delegates to Kimi K2.6 when:
- **LONG_CONTEXT**: Request exceeds 8K tokens
- **MULTIMODAL**: Request contains images, video, or audio
- **AGENTIC_CODING**: Keywords like "create agent", "write script", "implement function"

### Configuration

Edit `config/kimi-super-agent/config.yaml` to customize:
- Model settings (temperature, top_p, max_tokens)
- Memory allocation (gpu_memory_fraction, kv_cache_size)
- Delegation thresholds (long_context_threshold_tokens)
- Chimera agent endpoints and timeouts

For complete documentation, see `docs/guides/KIMI_QUICKSTART.md`.

Validated host-facing endpoints:

```bash
curl -fsS http://127.0.0.1:8012/v1/models
KIMI_VLLM_TEST_URL=http://127.0.0.1:8012 \
KIMI_MODEL_TEST_NAME=/model \
KIMI_TEST_TIMEOUT=180 \
KIMI_GRPC_TEST_TARGET=127.0.0.1:50052 \
./services/operator-console/venv/bin/python -m pytest tests/integration/kimi -q
```

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

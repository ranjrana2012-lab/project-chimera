# Kimi K2.6 Super-Agent Quick Start

This guide covers setting up and running the Kimi K2.6 super-agent on NVIDIA DGX Spark GB10.

## Prerequisites

- DGX Spark GB10 with 128GB GPU VRAM
- Docker GPU support available through NVIDIA runtime or CDI
- NGC registry access configured
- Project Chimera cloned

## Step 1: Download Kimi K2.6 Model

```bash
cd /path/to/Project_Chimera
./scripts/download-kimi-k26.sh
```

Expected output: Model downloaded to `./models/kimi/`

## Step 2: Start vLLM Service

```bash
docker compose -f docker-compose.mvp.yml \
               -f docker-compose.dgx-spark.yml \
               up -d kimi-vllm
```

Wait for vLLM to be ready:

```bash
./scripts/wait-for-kimi.sh
```

## Step 3: Start Kimi Super-Agent

```bash
docker compose -f docker-compose.mvp.yml \
               -f docker-compose.dgx-spark.yml \
               up -d kimi-super-agent
```

## Step 4: Validate Setup

```bash
# Check VRAM usage
./scripts/validate-kimi-vram.sh

# Check service health
docker compose logs kimi-super-agent | tail -20

# Confirm host-facing vLLM endpoint
curl -fsS http://127.0.0.1:8012/v1/models
```

## Step 5: Test Delegation

```bash
# Run integration tests against the published local Kimi endpoints.
# Use the operator/test venv because the full integration harness depends on
# repo-level test dependencies.
KIMI_VLLM_TEST_URL=http://127.0.0.1:8012 \
KIMI_GRPC_TEST_TARGET=127.0.0.1:50052 \
KIMI_MODEL_TEST_NAME=/model \
KIMI_TEST_TIMEOUT=180 \
./services/operator-console/venv/bin/python -m pytest tests/integration/kimi/ -v
```

Validated host-facing ports:

- `127.0.0.1:8012` for the OpenAI-compatible vLLM HTTP API
- `127.0.0.1:50052` for Kimi super-agent gRPC

## Configuration

Edit `config/kimi-super-agent/config.yaml` to customize:

- Model settings (temperature, top_p, max_tokens)
- Memory allocation
- Delegation thresholds
- Agent endpoints

## Troubleshooting

**VRAM exceeded threshold:**
- Reduce `KIMI_GPU_MEMORY_FRACTION`
- Stop other GPU-intensive processes

**vLLM not starting:**
- Check model files are present
- Verify GPU is accessible: `nvidia-smi`
- Check logs: `docker compose logs kimi-vllm`

**Delegation not working:**
- Verify Nemo Claw can reach Kimi: `docker compose logs nemoclaw-orchestrator`
- Check gRPC connectivity

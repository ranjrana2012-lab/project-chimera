#!/bin/bash
# Deploy Nemotron 3 Super 120B using vLLM Docker
set -e

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/nemotron-vllm.log"
MODEL_CACHE="$PROJECT_ROOT/models/nemotron"
MODEL_NAME="nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4"
SERVICE_PORT="${NEMOTRON_PORT:-8012}"
VLLM_IMAGE="vllm/vllm-openai:latest"

# Create directories
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$MODEL_CACHE"

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

log "=== Nemotron vLLM Docker Deployment ==="

# Check if port is available
if ss -tlnp 2>/dev/null | grep -q ":$SERVICE_PORT"; then
    log "Checking if Nemotron vLLM is already running..."
    if docker ps -f name=nemotron-vllm --format "{{.Names}}" | grep -q nemotron-vllm; then
        log "Nemotron vLLM Docker already running on port $SERVICE_PORT"
        exit 0
    fi
    log "ERROR: Port $SERVICE_PORT occupied by another process"
    exit 1
fi

# Stop existing container if running
if docker ps -a -q -f name=nemotron-vllm | grep -q .; then
    log "Stopping existing nemotron-vllm container..."
    docker stop nemotron-vllm 2>/dev/null || true
    docker rm nemotron-vllm 2>/dev/null || true
fi

# Pull latest vLLM image
log "Pulling vLLM Docker image: $VLLM_IMAGE"
docker pull "$VLLM_IMAGE"

# Start vLLM Docker container
log "Starting vLLM Docker container with Nemotron 3 Super 120B..."
log "Model: $MODEL_NAME"
log "Port: $SERVICE_PORT"
log "This will take several minutes to load the model..."

docker run -d \
    --name nemotron-vllm \
    --restart unless-stopped \
    --gpus all \
    -p "$SERVICE_PORT:8000" \
    -v "$MODEL_CACHE:/root/.cache/huggingface" \
    -e VLLM_USE_MODELSCOPE=false \
    -e HF_HOME=/root/.cache/huggingface \
    "$VLLM_IMAGE" \
    "$MODEL_NAME" \
    --served-model-name nvidia/nemotron-3-super \
    --dtype auto \
    --kv-cache-dtype fp8 \
    --tensor-parallel-size 1 \
    --pipeline-parallel-size 1 \
    --trust-remote-code \
    --gpu-memory-utilization 0.6 \
    --enable-chunked-prefill \
    --max-num-seqs 512 \
    --host 0.0.0.0 \
    --port 8000

VLLM_PID=$(docker inspect -f '{{.State.Pid}}' nemotron-vllm 2>/dev/null || echo "unknown")
log "vLLM Docker started with PID: $VLLM_PID"

# Wait and health check
log "Waiting for service to start (this may take 10-30 minutes for first run)..."
MAX_WAIT=1800  # 30 minutes
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 10
    WAITED=$((WAITED + 10))

    if curl -s "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
        log "=== Nemotron vLLM deployment complete ==="
        log "Service running on port $SERVICE_PORT"
        log "Model: $MODEL_NAME"
        log "Container: nemotron-vllm"
        exit 0
    fi

    if ! docker ps -f name=nemotron-vllm --format "{{.Status}}" | grep -q "Up"; then
        log "ERROR: vLLM container died"
        docker logs nemotron-vllm | tail -100 >> "$LOG_FILE"
        exit 1
    fi

    if [ $((WAITED % 60)) -eq 0 ]; then
        log "Still waiting... (${WAITED}s/${MAX_WAIT}s)"
        # Show recent logs every minute
        docker logs nemotron-vllm --tail 5 >> "$LOG_FILE"
    fi
done

log "WARNING: Service did not start within expected time"
log "Check logs: docker logs -f nemotron-vllm"
exit 1

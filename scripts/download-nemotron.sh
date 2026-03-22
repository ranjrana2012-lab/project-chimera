#!/bin/bash
# Set PATH for cron compatibility
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/nemotron-download.log"
DATA_DIR="$PROJECT_ROOT/models/nemotron/data"
ENV_FILE="$PROJECT_ROOT/.env.nemotron"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# NGC API Key (from env or prompt)
if [ -z "$NGC_API_KEY" ]; then
    echo "Error: NGC_API_KEY not set. Please set it in $ENV_FILE or environment."
    exit 1
fi

# Nemotron Image (verify exact name before first run)
NEMOTRON_IMAGE="${NEMOTRON_IMAGE:-nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest}"

# Create directories
mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

log "=== Starting Nemotron Download ==="

# Check disk space
REQUIRED_SPACE_GB=200
AVAILABLE_SPACE_GB=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$AVAILABLE_SPACE_GB" -lt "$REQUIRED_SPACE_GB" ]; then
    log "ERROR: Insufficient disk space. Need ${REQUIRED_SPACE_GB}GB, have ${AVAILABLE_SPACE_GB}GB"
    exit 1
fi

# NGC Login
log "Logging into NGC registry..."
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin

# Pull image
log "Starting Docker pull: $NEMOTRON_IMAGE"
log "This will take several hours (estimated 12 hours on slow connection)..."
docker pull "$NEMOTRON_IMAGE"

# Verify image
log "Verifying downloaded image..."
if docker inspect "$NEMOTRON_IMAGE" >/dev/null 2>&1; then
    log "Image verified successfully"
else
    log "ERROR: Image verification failed"
    exit 1
fi

# Stop existing container if running
if docker ps -q -f name=nemotron-local | grep -q .; then
    log "Stopping existing nemotron-local container..."
    docker stop nemotron-local || true
    docker rm nemotron-local || true
fi

# Check if port is available
NEMOTRON_PORT="${NEMOTRON_PORT:-8012}"
if ss -tlnp 2>/dev/null | grep -q ":$NEMOTRON_PORT"; then
    log "WARNING: Port $NEMOTRON_PORT is already in use. Checking if Nemotron is already running..."
    if docker ps -f name=nemotron-local --format "{{.Names}}" | grep -q nemotron-local; then
        log "Nemotron container already running. Skipping start."
        exit 0
    fi
    log "ERROR: Port $NEMOTRON_PORT occupied by another process"
    exit 1
fi

# Start container
log "Starting Nemotron container..."
docker run -d \
    --name nemotron-local \
    --gpus all \
    --restart unless-stopped \
    -p "$NEMOTRON_PORT:8000" \
    -v "$DATA_DIR:/models" \
    -e GPU_ID=0 \
    -e MODEL_NAME=nemotron-3-super-120b-a12b-nvfp4 \
    "$NEMOTRON_IMAGE"

# Health check
log "Performing health check..."
sleep 10
if docker ps -f name=nemotron-local --format "{{.Status}}" | grep -q "Up"; then
    log "=== Nemotron deployment complete ==="
    log "Container running on port $NEMOTRON_PORT"
    log "Image: $NEMOTRON_IMAGE"
    log "Data directory: $DATA_DIR"
else
    log "ERROR: Container failed to start"
    docker logs nemotron-local | tail -50 >> "$LOG_FILE"
    exit 1
fi

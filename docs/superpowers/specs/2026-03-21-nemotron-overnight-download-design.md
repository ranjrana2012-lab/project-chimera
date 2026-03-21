# Nemotron Overnight Download & Deployment Design

> **Status:** Approved
> **Created:** 2026-03-21
> **Author:** Claude + ranj

## Goal

Schedule an overnight download of NVIDIA Nemotron-3-Super-120B model from NGC registry, starting at midnight. The system will automatically pull the Docker image and start the inference service for use as a local LLM fallback in the NemoClaw Orchestrator.

## Background

- **System:** NVIDIA DGX Spark GB10 ARM64
- **Current local LLM:** Ollama with llama3:instruct (4.7GB)
- **Target model:** `nemotron-3-super-120b-a12b-nvfp4`
- **Internet:** Slow connection, ~12 hours to download
- **Disk available:** 2.1TB free
- **RAM:** 121GB total, 87GB available
- **Schedule:** Start download at 00:05 (midnight + 5min buffer)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Cron Scheduler                         │
│                    (midnight trigger)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              download-nemotron.sh Script                     │
│  1. Login to NGC with API key                               │
│  2. Docker pull nvcr.io/nvidia/nemotron-3-super-120b...     │
│  3. Verify image integrity                                  │
│  4. Start Nemotron container                                 │
│  5. Log all activities                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Nemotron Container                          │
│         Running on port 8000 (or configured port)           │
│         Volume: /home/ranj/Project_Chimera/models/nemotron  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Cron Job Entry

```cron
5 0 * * * /home/ranj/Project_Chimera/scripts/download-nemotron.sh >> /home/ranj/Project_Chimera/logs/nemotron-download.log 2>&1
```

- Runs at 00:05 daily (5 minutes after midnight for buffer)
- Executes bash script with full logging
- Captures both stdout and stderr

### 2. Download Script (`scripts/download-nemotron.sh`)

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/nemotron-download.log"
DATA_DIR="$PROJECT_ROOT/models/nemotron/data"
NGC_API_KEY="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"

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
log "Starting Docker pull (this will take several hours)..."
docker pull nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest

# Verify image
log "Verifying downloaded image..."
if docker inspect nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest >/dev/null 2>&1; then
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

# Start container
log "Starting Nemotron container..."
docker run -d \
    --name nemotron-local \
    --gpus all \
    --restart unless-stopped \
    -p 8000:8000 \
    -v "$DATA_DIR:/models" \
    -e GPU_ID=0 \
    -e MODEL_NAME=nemotron-3-super-120b-a12b-nvfp4 \
    nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest

# Health check
log "Performing health check..."
sleep 10
if docker ps -f name=nemotron-local --format "{{.Status}}" | grep -q "Up"; then
    log "=== Nemotron deployment complete ==="
    log "Container running on port 8000"
else
    log "ERROR: Container failed to start"
    docker logs nemotron-local | tail -50 >> "$LOG_FILE"
    exit 1
fi
```

### 3. Nemotron Service Configuration

**Docker Run Parameters:**
- `--name nemotron-local` - Container name
- `--gpus all` - GPU access
- `--restart unless-stopped` - Auto-restart policy
- `-p 8000:8000` - Port mapping (host:container)
- `-v $DATA_DIR:/models` - Model data volume
- `-e GPU_ID=0` - GPU device ID
- `-e MODEL_NAME=nemotron-3-super-120b-a12b-nvfp4` - Model name

### 4. Privacy Router Integration

**Update `llm/privacy_router.py`:**
- Add `NEMOTRON_LOCAL` backend option
- Route to Nemotron at `http://localhost:8000`
- Fallback chain: GLM-4.7 → GLM-4.7-FlashX → Nemotron → Ollama

**Update `config.py`:**
```python
nemotron_enabled: bool = True  # Use Nemotron as local fallback
nemotron_endpoint: str = "http://localhost:8000"
```

## Data Flow

```
Cron (00:05) → Script Start → NGC Login → Docker Pull (~12 hours)
                                              ↓
                                       Verify Image
                                              ↓
                                    Start Container
                                              ↓
                                   Health Check
                                              ↓
                                    Ready State (morning)
```

## Error Handling

| Error Type | Detection | Handling |
|------------|-----------|----------|
| Network interruption | Docker pull fails | Docker auto-resumes |
| Authentication failure | `docker login` returns non-zero | Log error, exit gracefully |
| Insufficient disk space | Pre-check before download | Log error, exit |
| Port 8000 conflict | Check before starting | Stop existing container |
| GPU unavailable | Runtime error | Log warning, continue |
| Container startup fails | Health check fails | Log container logs, exit |

## Storage

```
/home/ranj/Project_Chimera/
├── models/
│   └── nemotron/
│       └── data/           # Model weights and runtime data
├── scripts/
│   └── download-nemotron.sh
└── logs/
    └── nemotron-download.log
```

## Testing

1. **Pre-download validation:**
   - Verify NGC API key works: `docker login nvcr.io -u '$oauthtoken'`
   - Check disk space has 200GB+ available
   - Verify port 8000 is available

2. **Post-download verification:**
   - Check container is running: `docker ps -f name=nemotron-local`
   - Verify health endpoint: `curl http://localhost:8000/health`
   - Test inference: `curl -X POST http://localhost:8000/generate`

3. **Integration testing:**
   - Update Privacy Router to use Nemotron endpoint
   - Run orchestrator test with Nemotron fallback
   - Verify end-to-end orchestration flow

## Success Criteria

- [ ] Cron job scheduled for 00:05
- [ ] Script is executable and has correct permissions
- [ ] Download completes overnight
- [ ] Nemotron container is running in the morning
- [ ] Health check passes
- [ ] Privacy Router can connect to Nemotron
- [ ] Test inference request succeeds

## Open Questions

1. **Exact NGC image name:** Need to verify the full image path on NGC registry
2. **Nemotron API format:** Does it use OpenAI-compatible `/v1/completions` or custom API?
3. **Memory requirements:** 120B model with nvfp4 quantization - verify 87GB available RAM is sufficient

## References

- NVIDIA NGC: https://catalog.ngc.nvidia.com/
- Nemotron documentation: https://docs.nvidia.com/ai-enterprise/nemotron/
- Current orchestrator: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/`

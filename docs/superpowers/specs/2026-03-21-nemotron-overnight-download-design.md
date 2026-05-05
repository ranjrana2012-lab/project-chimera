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

# Check if port 8000 is available
if ss -tlnp | grep -q ':8000'; then
    log "WARNING: Port 8000 is already in use. Checking if Nemotron is already running..."
    if docker ps -f name=nemotron-local --format "{{.Names}}" | grep -q nemotron-local; then
        log "Nemotron container already running. Skipping start."
        exit 0
    fi
    log "ERROR: Port 8000 occupied by another process"
    exit 1
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
    "$NEMOTRON_IMAGE"

# Health check
log "Performing health check..."
sleep 10
if docker ps -f name=nemotron-local --format "{{.Status}}" | grep -q "Up"; then
    log "=== Nemotron deployment complete ==="
    log "Container running on port 8000"
    log "Image: $NEMOTRON_IMAGE"
    log "Data directory: $DATA_DIR"
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
# Nemotron Configuration (local fallback)
nemotron_enabled: bool = True  # Use Nemotron as local fallback
nemotron_endpoint: str = "http://localhost:8000"
nemotron_model: str = "nemotron-3-super-120b-a12b-nvfp4"
nemotron_timeout: int = 120  # seconds
nemotron_max_retries: int = 2
```

**Fallback Logic:**
```python
def route(self, prompt: str, task_type: str = "default") -> LLMBackend:
    # 1. Try GLM-4.7 (primary)
    # 2. If credit exhausted, try GLM-4.7-FlashX (fast)
    # 3. If Z.AI unavailable, try Nemotron (local)
    # 4. If Nemotron unavailable, try Ollama (final fallback)
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
   - Verify NGC API key works: `echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin`
   - Check disk space has 200GB+ available: `df -BG /home/ranj/Project_Chimera`
   - Verify port 8000 is available: `ss -tlnp | grep :8000` (should return nothing)

2. **Post-download verification:**
   - Check container is running: `docker ps -f name=nemotron-local`
   - Verify health endpoint: `curl http://localhost:8000/health` (expected: `{"status":"healthy"}` or similar)
   - Check container logs: `docker logs nemotron-local --tail 50`

3. **API format testing:**
   - Try OpenAI-compatible format: `curl http://localhost:8000/v1/models`
   - Try Nemotron-specific format: `curl http://localhost:8000/api/models`
   - Test inference with discovered format

4. **Integration testing:**
   - Update Privacy Router to use Nemotron endpoint
   - Run orchestrator test with Nemotron fallback
   - Verify end-to-end orchestration flow

## Manual Trigger

For testing or manual execution (outside of cron):

```bash
# Run the script immediately
./scripts/download-nemotron.sh

# Or run with custom image
NEMOTRON_IMAGE="custom/image:name" ./scripts/download-nemotron.sh
```

## Rollback Procedure

If the download fails or container doesn't start:

1. Check logs: `tail -100 /home/ranj/Project_Chimera/logs/nemotron-download.log`
2. Stop failed container: `docker stop nemotron-local && docker rm nemotron-local`
3. Clean up partial data if needed: `rm -rf /home/ranj/Project_Chimera/models/nemotron/data/*`
4. Retry manually: `./scripts/download-nemotron.sh`

## Success Criteria

- [ ] Cron job scheduled for 00:05
- [ ] Script is executable and has correct permissions
- [ ] Download completes overnight
- [ ] Nemotron container is running in the morning
- [ ] Health check passes
- [ ] Privacy Router can connect to Nemotron
- [ ] Test inference request succeeds

## Open Questions

1. **Exact NGC image name:** The exact image path on NGC registry will be verified during implementation by:
   - Logging into NGC with the provided API key
   - Running `nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest` pull
   - If pull fails, searching NGC catalog for the correct image name
   - The `NEMOTRON_IMAGE` environment variable allows overriding the default

2. **Nemotron API format:** NVIDIA Nemotron containers typically support OpenAI-compatible API (`/v1/completions` or `/v1/chat/completions`). During implementation:
   - Test the health endpoint first: `http://localhost:8000/health` or `http://localhost:8000/v1/models`
   - Try a simple generation request to verify the exact API format
   - Update `NemotronClient` in `llm/nemotron_client.py` to match the actual API

3. **Memory requirements:** The 120B model with nvfp4 (4-bit) quantization requires approximately:
   - 120B parameters × 0.5 bytes (fp4) ≈ 60GB for model weights
   - 20-30GB for activation cache and runtime overhead
   - **Total estimate: 80-90GB RAM**
   - With 87GB available, this should be sufficient but may be tight
   - If memory issues occur, consider reducing batch size or using a smaller model

## Environment Variables

Create `/home/ranj/Project_Chimera/.env.nemotron`:

```bash
# NGC API Key (required)
NGC_API_KEY=nvapi-REDACTED

# Nemotron Docker Image (optional, override if different)
NEMOTRON_IMAGE=nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest

# Nemotron Service Port (optional, default 8000)
NEMOTRON_PORT=8000
```

**Security Note:** The `.env.nemotron` file should be:
- Added to `.gitignore` to prevent committing credentials
- Owned by the user with restricted permissions (`chmod 600 .env.nemotron`)
- Sourced by the download script at runtime

## References

- NVIDIA NGC: https://catalog.ngc.nvidia.com/
- Nemotron documentation: https://docs.nvidia.com/ai-enterprise/nemotron/
- Current orchestrator: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/`

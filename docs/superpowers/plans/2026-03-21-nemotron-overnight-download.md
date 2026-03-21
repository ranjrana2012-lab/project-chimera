# Nemotron Overnight Download & Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Schedule and deploy overnight download of NVIDIA Nemotron-3-Super-120B model from NGC, with automatic service startup and Privacy Router integration.

**Architecture:** Cron job triggers bash script at midnight → NGC Docker login → Pull Nemotron image (~12 hours) → Start container → Health check → Ready for inference. Privacy Router updated with Nemorton as fallback between Z.AI and Ollama.

**Tech Stack:** Bash scripting, Docker, cron, Python (pydantic-settings), NVIDIA NGC registry

---

## File Structure

```
/home/ranj/Project_Chimera/
├── .env.nemotron                    # NEW: NGC credentials and config
├── scripts/
│   └── download-nemotron.sh         # NEW: Download and deployment script
├── services/nemoclaw-orchestrator/
│   ├── llm/
│   │   ├── __init__.py              # MODIFY: Export NEMOTRON_LOCAL
│   │   ├── privacy_router.py        # MODIFY: Add Nemorton backend
│   │   └── nemotron_client.py       # MODIFY: Update for new endpoint
│   └── config.py                    # MODIFY: Add Nemotron config
└── docs/superpowers/
    └── plans/
        └── 2026-03-21-nemotron-overnight-download.md  # This file
```

---

## Task 1: Create Environment File for NGC Credentials

**Files:**
- Create: `/home/ranj/Project_Chimera/.env.nemotron`

- [ ] **Step 1: Create the environment file**

```bash
cat > /home/ranj/Project_Chimera/.env.nemotron << 'EOF'
# NGC API Key (required)
NGC_API_KEY=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

# Nemotron Docker Image (optional, override if different)
NEMOTRON_IMAGE=nvcr.io/nvidia/nemotron-3-super-120b-a12b-nvfp4:latest

# Nemotron Service Port (optional, default 8000)
NEMOTRON_PORT=8000
EOF
```

- [ ] **Step 2: Set restrictive permissions**

Run: `chmod 600 /home/ranj/Project_Chimera/.env.nemotron`
Expected: No error, permissions set to rw-------

- [ ] **Step 3: Verify .gitignore covers .env files**

Run: `grep -q "*.env" /home/ranj/Project_Chimera/.gitignore && echo "OK" || echo "NOT FOUND"`
Expected: OK

- [ ] **Step 4: Verify file was created correctly**

Run: `cat /home/ranj/Project_Chimera/.env.nemotron`
Expected: File contains NGC_API_KEY, NEMOTRON_IMAGE, NEMOTRON_PORT

- [ ] **Step 5: Commit**

```bash
cd /home/ranj/Project_Chimera
git add .gitignore
git add .env.nemotron
git commit -m "feat: add Nemotron environment file with NGC credentials"
```

---

## Task 2: Create Download Script

**Files:**
- Create: `/home/ranj/Project_Chimera/scripts/download-nemotron.sh`

- [ ] **Step 1: Create scripts directory**

Run: `mkdir -p /home/ranj/Project_Chimera/scripts`
Expected: Directory created (no error if exists)

- [ ] **Step 2: Create the download script**

```bash
cat > /home/ranj/Project_Chimera/scripts/download-nemotron.sh << 'SCRIPT'
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
if ss -tlnp 2>/dev/null | grep -q ':8000'; then
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
    -p "${NEMOTRON_PORT:-8000}:8000" \
    -v "$DATA_DIR:/models" \
    -e GPU_ID=0 \
    -e MODEL_NAME=nemotron-3-super-120b-a12b-nvfp4 \
    "$NEMOTRON_IMAGE"

# Health check
log "Performing health check..."
sleep 10
if docker ps -f name=nemotron-local --format "{{.Status}}" | grep -q "Up"; then
    log "=== Nemotron deployment complete ==="
    log "Container running on port ${NEMOTRON_PORT:-8000}"
    log "Image: $NEMOTRON_IMAGE"
    log "Data directory: $DATA_DIR"
else
    log "ERROR: Container failed to start"
    docker logs nemotron-local | tail -50 >> "$LOG_FILE"
    exit 1
fi
SCRIPT
```

- [ ] **Step 3: Make script executable**

Run: `chmod +x /home/ranj/Project_Chimera/scripts/download-nemotron.sh`
Expected: No error

- [ ] **Step 4: Verify script syntax**

Run: `bash -n /home/ranj/Project_Chimera/scripts/download-nemotron.sh`
Expected: No output (syntax OK)

- [ ] **Step 5: Commit**

```bash
cd /home/ranj/Project_Chimera
git add scripts/download-nemotron.sh
git commit -m "feat: add Nemotron download and deployment script"
```

---

## Task 3: Test NGC Authentication

**Files:**
- None (validation task)

- [ ] **Step 1: Test NGC login with provided API key**

Run: `echo "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" | docker login nvcr.io -u '$oauthtoken' --password-stdin`
Expected: `Login Succeeded`

- [ ] **Step 2: If login fails, verify the exact image name on NGC**

Run: Search NGC catalog at https://catalog.ngc.nvidia.com/ for "nemotron"
Note: Update `.env.nemotron` NEMOTRON_IMAGE if different

- [ ] **Step 3: Verify disk space**

Run: `df -BG /home/ranj/Project_Chimera | tail -1 | awk '{print $4}'`
Expected: 200+ GB available

- [ ] **Step 4: Verify port 8000 availability**

Run: `ss -tlnp | grep :8000`
Expected: No output (port available)

---

## Task 4: Create Cron Job Entry

**Files:**
- Modify: System crontab (via crontab -e)

- [ ] **Step 1: Export current crontab (backup)**

Run: `crontab -l > /tmp/crontab-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true`
Expected: Backup created

- [ ] **Step 2: Add cron entry**

Run: `(crontab -l 2>/dev/null; echo "5 0 * * * /home/ranj/Project_Chimera/scripts/download-nemotron.sh >> /home/ranj/Project_Chimera/logs/nemotron-download.log 2>&1") | crontab -`
Expected: No error

- [ ] **Step 3: Verify cron entry was added**

Run: `crontab -l | grep download-nemotron`
Expected: `5 0 * * * /home/ranj/Project_Chimera/scripts/download-nemotron.sh >> /home/ranj/Project_Chimera/logs/nemotron-download.log 2>&1`

- [ ] **Step 4: Document the cron setup**

Create documentation file:
```bash
cat > /home/ranj/Project_Chimera/docs/nemotron-cron.md << 'EOF'
# Nemotron Cron Job

The Nemotron download is scheduled via cron to run at 00:05 (5 minutes after midnight).

## View Cron Job

```bash
crontab -l | grep download-nemotron
```

## Remove Cron Job

```bash
crontab -l | grep -v download-nemotron | crontab -
```

## Test Manually

```bash
/home/ranj/Project_Chimera/scripts/download-nemotron.sh
```

## Logs

View logs: `tail -f /home/ranj/Project_Chimera/logs/nemotron-download.log`
EOF
```

- [ ] **Step 5: Commit**

```bash
cd /home/ranj/Project_Chimera
git add docs/nemotron-cron.md
git commit -m "docs: add Nemotron cron job documentation"
```

---

## Task 5: Update Config with Nemorton Settings

**Files:**
- Modify: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/config.py`

- [ ] **Step 1: Read current config.py**

Run: `head -30 /home/ranj/Project_Chimera/services/nemoclaw-orchestrator/config.py`
Expected: See current Settings class structure

- [ ] **Step 2: Add Nemotron configuration fields**

Add after line 29 (after zai_thinking_enabled):

```python
# Nemotron Configuration (local fallback, after Z.AI)
nemotron_enabled: bool = True
nemotron_endpoint: str = "http://localhost:8000"
nemotron_model: str = "nemotron-3-super-120b-a12b-nvfp4"
nemotron_timeout: int = 120
nemotron_max_retries: int = 2
```

- [ ] **Step 3: Verify syntax**

Run: `cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator && python -c "from config import Settings; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator
git add config.py
git commit -m "feat: add Nemorton configuration to Settings"
```

---

## Task 6: Update Privacy Router for Nemorton Backend

**Files:**
- Modify: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/llm/privacy_router.py`

- [ ] **Step 1: Read current LLMBackend enum**

Run: `grep -A 5 "class LLMBackend" /home/ranj/Project_Chimera/services/nemoclaw-orchestrator/llm/privacy_router.py`
Expected: See current enum with ZAI_ and OLLAMA_LOCAL values

- [ ] **Step 2: Add NEMOTRON_LOCAL to LLMBackend enum**

After `OLLAMA_LOCAL = "ollama_local"` add:

```python
    NEMOTRON_LOCAL = "nemotron_local"
```

- [ ] **Step 3: Update RouterConfig to include nemotron settings**

Add to RouterConfig dataclass after zai_thinking_enabled:

```python
    # Nemorton Configuration
    nemotron_enabled: bool = True
    nemotron_endpoint: str = "http://localhost:8000"
    nemotron_model: str = "nemotron-3-super-120b-a12b-nvfp4"
    nemotron_timeout: int = 120
    nemotron_max_retries: int = 2
```

- [ ] **Step 4: Update PrivacyRouter.__init__ to instantiate NemotronClient**

Find the OllamaClient initialization and add NemotronClient before it:

```python
# Local Nemotron client (fallback before Ollama)
if config.nemotron_enabled:
    from llm.nemotron_client import NemotronClient
    self.nemotron_client = NemotronClient(
        endpoint=config.nemotron_endpoint,
        model=config.nemotron_model,
        timeout=config.nemotron_timeout
    )
else:
    self.nemotron_client = None
```

- [ ] **Step 5: Update route() method for Nemotron fallback**

Modify the route method to include Nemotron in the fallback chain:

```python
def route(self, prompt: str, task_type: str = "default") -> LLMBackend:
    # Check if Z.AI is available (not marked as exhausted)
    if not self.credit_cache.is_available():
        logger.debug("Z.AI marked exhausted, routing to local Nemotron/Ollama")
        # Try Nemotron first, then Ollama
        if self.nemotron_client and self._is_nemotron_available():
            return LLMBackend.NEMOTRON_LOCAL
        return LLMBackend.OLLAMA_LOCAL

    # Select Z.AI model based on task type
    return self._select_zai_model(task_type)

def _is_nemotron_available(self) -> bool:
    """Check if Nemotron service is available"""
    try:
        import httpx
        response = httpx.get(f"{self.config.nemotron_endpoint}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
```

- [ ] **Step 6: Update generate() method to handle NEMOTRON_LOCAL**

Add to the backend handling in generate():

```python
# Nemotron fallback
elif backend == LLMBackend.NEMOTRON_LOCAL:
    return self._generate_with_nemotron(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )
```

- [ ] **Step 7: Add _generate_with_nemotron method**

```python
def _generate_with_nemotron(
    self,
    prompt: str,
    max_tokens: int,
    temperature: float,
    **kwargs
) -> Dict[str, Any]:
    """Generate using local Nemotron client"""
    logger.debug("Routing to local Nemotron")

    for attempt in range(self.config.nemotron_max_retries + 1):
        try:
            result = self.nemotron_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            result["backend"] = LLMBackend.NEMOTRON_LOCAL.value
            return result
        except Exception as e:
            if attempt < self.config.nemotron_max_retries:
                logger.warning(f"Nemotron attempt {attempt + 1} failed: {e}, retrying...")
                continue
            logger.error(f"Nemotron generation failed after {self.config.nemotron_max_retries} retries: {e}")
            raise
```

- [ ] **Step 8: Update error fallback to try Nemotron before Ollama**

In the exception handler, update the fallback logic:

```python
# Attempt fallback to Nemotron, then Ollama
if backend != LLMBackend.NEMOTRON_LOCAL and self.config.nemotron_enabled and self.nemotron_client:
    logger.info("Attempting fallback to Nemotron")
    try:
        return self._generate_with_nemotron(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    except Exception as e:
        logger.warning(f"Nemotron fallback failed: {e}")

if backend != LLMBackend.OLLAMA_LOCAL and self.config.cloud_fallback_enabled:
    logger.info("Attempting fallback to Ollama")
    return self._generate_with_ollama(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )
```

- [ ] **Step 9: Update close() method to close NemotronClient**

Add to close() method:

```python
def close(self):
    """Close all clients"""
    self.zai_client.close()
    if hasattr(self, 'nemotron_client') and self.nemotron_client:
        self.nemotron_client.close()
    self.local_client.close()
    self.credit_cache.close()
```

- [ ] **Step 10: Verify syntax**

Run: `cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator && python -c "from llm.privacy_router import PrivacyRouter; print('OK')"`
Expected: OK

- [ ] **Step 11: Commit**

```bash
cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator
git add llm/privacy_router.py
git commit -m "feat: integrate Nemorton as local fallback in PrivacyRouter

- Add NEMOTRON_LOCAL to LLMBackend enum
- Add Nemorton health check and routing
- Fallback chain: GLM-4.7 → GLM-4.7-FlashX → Nemotron → Ollama
- Add retry logic for Nemorton requests"
```

---

## Task 7: Update NemotronClient for New Endpoint

**Files:**
- Modify: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/llm/nemotron_client.py`

- [ ] **Step 1: Read current NemotronClient**

Run: `cat /home/ranj/Project_Chimera/services/nemoclaw-orchestrator/llm/nemotron_client.py`
Expected: See current NemotronClient implementation

- [ ] **Step 2: Update NemotronClient to support OpenAI-compatible API**

Replace or update the generate() method to try both OpenAI and Nemotron-specific formats:

```python
def generate(
    self,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    timeout: int = 120,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate text using Nemotron API

    Tries OpenAI-compatible format first, then Nemotron-specific format.
    """
    try:
        client = self._get_client()

        # Try OpenAI-compatible format first
        try:
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            response = client.post(
                f"{self.endpoint}/v1/chat/completions",
                json=request_params,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()

            return {
                "text": data["choices"][0]["message"]["content"],
                "model_used": self.model,
                "backend": "nemotron_local",
                "usage": data.get("usage", {})
            }
        except Exception as e:
            logger.debug(f"OpenAI format failed: {e}, trying Nemotron format")

            # Try Nemotron-specific format
            request_params = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            response = client.post(
                f"{self.endpoint}/generate",
                json=request_params,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()

            return {
                "text": data.get("text", data.get("output", "")),
                "model_used": self.model,
                "backend": "nemotron_local",
                "usage": data.get("usage", {})
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Nemotron request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Nemotron generation error: {e}")
        raise
```

- [ ] **Step 3: Add timeout parameter to __init__**

Update the __init__ signature:

```python
def __init__(self, endpoint: str = "http://localhost:8000", model: str = "nemotron-3-super-120b-a12b-nvfp4", timeout: int = 120):
    self.endpoint = endpoint.rstrip("/")
    self.model = model
    self.timeout = timeout
    self._client: Optional[httpx.Client] = None
```

- [ ] **Step 4: Update _get_client to use timeout**

```python
def _get_client(self) -> httpx.Client:
    """Get or create HTTP client"""
    if self._client is None:
        self._client = httpx.Client(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    return self._client
```

- [ ] **Step 5: Verify syntax**

Run: `cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator && python -c "from llm.nemotron_client import NemotronClient; print('OK')"`
Expected: OK

- [ ] **Step 6: Commit**

```bash
cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator
git add llm/nemotron_client.py
git commit -m "feat: update NemotronClient for OpenAI-compatible API

- Try OpenAI /v1/chat/completions format first
- Fall back to Nemotron-specific /generate format
- Add configurable timeout parameter"
```

---

## Task 8: Update LLM Module Exports

**Files:**
- Modify: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/llm/__init__.py`

- [ ] **Step 1: Read current exports**

Run: `cat /home/ranj/Project_Chimera/services/nemoclaw-orchestrator/llm/__init__.py`
Expected: See current export list

- [ ] **Step 2: Ensure NEMOTRON_LOCAL is exported via LLMBackend**

The LLMBackend enum should already include NEMOTRON_LOCAL from Task 6, so this step just verifies it's exported.

- [ ] **Step 3: Verify imports work**

Run: `cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator && python -c "from llm import LLMBackend; print(LLMBackend.NEMOTRON_LOCAL)"`
Expected: `nemotron_local`

---

## Task 9: Update Docker Compose for Nemorton Reference

**Files:**
- Modify: `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/docker-compose.yml`

- [ ] **Step 1: Read current docker-compose.yml**

Run: `head -50 /home/ranj/Project_Chimera/services/nemoclaw-orchestrator/docker-compose.yml`
Expected: See current service definitions

- [ ] **Step 2: Add Nemorton environment variables**

Add to nemoclaw-orchestrator environment section (after ZAI_THINKING_ENABLED):

```yaml
      # Nemotron Configuration (local fallback)
      NEMOTRON_ENABLED: "true"
      NEMOTRON_ENDPOINT: http://host.docker.internal:8000
      NEMOTRON_MODEL: nemotron-3-super-120b-a12b-nvfp4
      NEMOTRON_TIMEOUT: 120
      NEMOTRON_MAX_RETRIES: 2
```

- [ ] **Step 3: Verify YAML syntax**

Run: `docker compose -f /home/ranj/Project_Chimera/services/nemoclaw-orchestrator/docker-compose.yml config > /dev/null`
Expected: No error

- [ ] **Step 4: Commit**

```bash
cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator
git add docker-compose.yml
git commit -m "feat: add Nemorton environment variables to docker-compose"
```

---

## Task 10: Manual Test Run (Before Scheduled Cron)

**Files:**
- None (validation task)

- [ ] **Step 1: Verify NGC authentication**

Run: `cat /home/ranj/Project_Chimera/.env.nemotron | grep NGC_API_KEY | cut -d= -f2 | docker login nvcr.io -u '$oauthtoken' --password-stdin`
Expected: `Login Succeeded`

- [ ] **Step 2: Verify script is executable**

Run: `ls -la /home/ranj/Project_Chimera/scripts/download-nemotron.sh`
Expected: `-rwxr-xr-x` or similar with execute permission

- [ ] **Step 3: Do a quick validation run (cancel actual pull)**

Note: This will test the script logic without pulling the full image. For a full test, you'd need to run the complete script which takes ~12 hours.

- [ ] **Step 4: Check cron schedule**

Run: `crontab -l | grep download-nemotron`
Expected: Shows scheduled time (00:05)

---

## Task 11: Post-Deployment Verification (After Morning)

**Files:**
- None (verification task - run after download completes)

- [ ] **Step 1: Check container is running**

Run: `docker ps -f name=nemotron-local`
Expected: Container listed with status "Up"

- [ ] **Step 2: Check logs**

Run: `tail -50 /home/ranj/Project_Chimera/logs/nemotron-download.log`
Expected: Shows "=== Nemotron deployment complete ==="

- [ ] **Step 3: Verify health endpoint**

Run: `curl -s http://localhost:8000/health || curl -s http://localhost:8000/v1/models || curl -s http://localhost:8000/`
Expected: JSON response indicating service is healthy

- [ ] **Step 4: Test API format**

Run: `curl -s http://localhost:8000/v1/models 2>/dev/null | head -20`
Expected: Either models list or error indicating actual endpoint

- [ ] **Step 5: Rebuild orchestrator with new config**

Run:
```bash
cd /home/ranj/Project_Chimera/services/nemoclaw-orchestrator
docker compose build nemoclaw-orchestrator
docker compose up -d nemoclaw-orchestrator
```
Expected: Container rebuilds and starts

- [ ] **Step 6: Test orchestrator health**

Run: `curl -s http://localhost:9000/health/live`
Expected: `{"status":"alive","service":"nemoclaw-orchestrator"}`

- [ ] **Step 7: Test orchestration with Nemotron fallback**

Run:
```bash
curl -s -X POST http://localhost:9000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, respond briefly."}' | jq .
```
Expected: Response with backend indicating Nemotron or Ollama

---

## Success Criteria Checklist

After completion, verify:

- [ ] `.env.nemotron` exists with restrictive permissions (600)
- [ ] `scripts/download-nemotron.sh` is executable
- [ ] Cron job scheduled for 00:05
- [ ] NGC authentication works
- [ ] Privacy Router includes NEMOTRON_LOCAL backend
- [ ] NemotronClient updated for OpenAI-compatible API
- [ ] docker-compose.yml includes Nemotron environment variables
- [ ] Container running after download (morning check)
- [ ] Health endpoint responds
- [ ] Orchestrator can connect to Nemotron
- [ ] End-to-end orchestration works with Nemotron fallback

---

## Rollback Procedure

If something goes wrong:

1. **Remove cron job:**
   ```bash
   crontab -l | grep -v download-nemotron | crontab -
   ```

2. **Stop Nemotron container:**
   ```bash
   docker stop nemotron-local && docker rm nemotron-local
   ```

3. **Revert code changes:**
   ```bash
   cd /home/ranj/Project_Chimera
   git log --oneline -10
   git revert <commit-hash>
   ```

4. **Clean up data (optional):**
   ```bash
   rm -rf /home/ranj/Project_Chimera/models/nemotron/data/*
   ```

---

## References

- Spec: `docs/superpowers/specs/2026-03-21-nemotron-overnight-download-design.md`
- NGC Catalog: https://catalog.ngc.nvidia.com/
- Nemotron Docs: https://docs.nvidia.com/ai-enterprise/nemotron/

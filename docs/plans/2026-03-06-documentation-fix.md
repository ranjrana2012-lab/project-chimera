# Documentation Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add missing Configuration sections to 6 API docs using template-based approach and fix version references.

**Architecture:** Extract Configuration section from safety-filter.md as template, gather service data from .env.example/config.py files, generate and insert Configuration sections, fix release notes status, create migration guide.

**Tech Stack:** Bash scripting, sed/awk for text processing, git for version control.

---

## Task 1: Extract Template from safety-filter.md

**Files:**
- Read: `docs/api/safety-filter.md`
- Create: `/tmp/config-template.md`

**Step 1: Read safety-filter.md to find Configuration section**

```bash
cd /home/ranj/Project_Chimera
grep -n "## Configuration" docs/api/safety-filter.md
```
Expected: Line number where Configuration section starts (e.g., `38:## Configuration`)

**Step 2: Extract Configuration section to template**

```bash
# Find start and end lines
START_LINE=$(grep -n "## Configuration" docs/api/safety-filter.md | cut -d: -f1)
END_LINE=$(tail -n +$START_LINE docs/api/safety-filter.md | grep -n "^## " | tail -1 | cut -d: -f1)
END_LINE=$((START_LINE + END_LINE - 1))

# Extract the section
sed -n "${START_LINE},${END_LINE}p" docs/api/safety-filter.md > /tmp/config-template.md
```
Expected: Template file created with Configuration section

**Step 3: Verify template content**

```bash
cat /tmp/config-template.md
```
Expected: Configuration section with environment variables, descriptions, defaults

---

## Task 2: Gather Service Data - Part 1

**Files:**
- Read: `services/bsl-agent/.env.example`
- Read: `services/captioning-agent/.env.example`
- Read: `services/openclaw-orchestrator/.env.example`

**Step 1: Check for .env.example files**

```bash
cd /home/ranj/Project_Chimera

for svc in bsl-agent captioning-agent openclaw-orchestrator; do
  if [ -f "services/${svc}/.env.example" ]; then
    echo "✓ ${svc}/.env.example exists"
  else
    echo "✗ ${svc}/.env.example missing"
  fi
done
```
Expected: All three files exist (or note which are missing)

**Step 2: Extract service data for BSL Agent**

```bash
if [ -f "services/bsl-agent/.env.example" ]; then
  grep "=" services/bsl-agent/.env.example | head -10
fi
```
Expected: List of environment variables (PORT, SERVICE_NAME, etc.)

**Step 3: Extract service data for Captioning Agent**

```bash
if [ -f "services/captioning-agent/.env.example" ]; then
  grep "=" services/captioning-agent/.env.example | head -10
fi
```
Expected: List of environment variables

**Step 4: Extract service data for OpenClaw Orchestrator**

```bash
if [ -f "services/openclaw-orchestrator/.env.example" ]; then
  grep "=" services/openclaw-orchestrator/.env.example | head -10
fi
```
Expected: List of environment variables

---

## Task 3: Gather Service Data - Part 2

**Files:**
- Read: `services/operator-console/.env.example`
- Read: `services/scenespeak-agent/.env.example`
- Read: `services/sentiment-agent/.env.example`

**Step 1: Check for remaining .env.example files**

```bash
cd /home/ranj/Project_Chimera

for svc in operator-console scenespeak-agent sentiment-agent; do
  if [ -f "services/${svc}/.env.example" ]; then
    echo "✓ ${svc}/.env.example exists"
  else
    echo "✗ ${svc}/.env.example missing"
  fi
done
```
Expected: All three files exist (or note which are missing)

**Step 2: Extract service data for each**

```bash
for svc in operator-console scenespeak-agent sentiment-agent; do
  if [ -f "services/${svc}/.env.example" ]; then
    echo "=== $svc ==="
    grep "=" services/${svc}/.env.example | head -10
  fi
done
```
Expected: Environment variables for each service

---

## Task 4: Generate Configuration Section for BSL Agent

**Files:**
- Modify: `docs/api/bsl-agent.md`

**Step 1: Find insertion point in bsl-agent.md**

```bash
cd /home/ranj/Project_Chimera
grep -n "^## " docs/api/bsl-agent.md
```
Expected: List of section headers (find where to insert after ## Endpoints)

**Step 2: Generate Configuration section for BSL Agent**

```bash
cat >> /tmp/bsl-config.md << 'EOF'
## Configuration

The BSL Agent is configured using environment variables. Below are the available configuration options:

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `bsl-agent` | Service identifier |
| `PORT` | integer | `8003` | Service port |
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `AVATAR_API_URL` | string | `http://localhost:8010` | Avatar rendering service URL |
| `TRANSLATION_API_URL` | string | `http://localhost:8001` | Translation service URL |

### Example Configuration

```bash
export SERVICE_NAME=bsl-agent
export PORT=8003
export LOG_LEVEL=INFO
```

### Docker Compose

```yaml
services:
  bsl-agent:
    environment:
      - SERVICE_NAME=bsl-agent
      - PORT=8003
      - LOG_LEVEL=INFO
```
EOF
```

**Step 3: Insert Configuration section into bsl-agent.md**

```bash
# Find line after ## Endpoints section
ENDPOINTS_LINE=$(grep -n "^## Endpoints" docs/api/bsl-agent.md | cut -d: -f1)
INSERT_LINE=$((ENDPOINTS_LINE + 20))  # Approximate gap after endpoints

# Insert the Configuration section
sed -i "${INSERT_LINE}r /tmp/bsl-config.md" docs/api/bsl-agent.md
```

**Step 4: Verify insertion**

```bash
grep -A 5 "## Configuration" docs/api/bsl-agent.md
```
Expected: Configuration section visible

---

## Task 5: Generate Configuration Section for Captioning Agent

**Files:**
- Modify: `docs/api/captioning-agent.md`

**Step 1: Generate Configuration section**

```bash
cat > /tmp/captioning-config.md << 'EOF'
## Configuration

The Captioning Agent uses Whisper model for speech-to-text transcription.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `captioning-agent` | Service identifier |
| `PORT` | integer | `8002` | Service port |
| `WHISPER_MODEL` | string | `base` | Whisper model size (tiny/base/small/medium/large) |
| `DEVICE` | string | `cpu` | Inference device (cpu/cuda) |
| `LOG_LEVEL` | string | `INFO` | Logging level |

### Model Configuration

The Whisper model is loaded at startup. Larger models provide better accuracy but require more resources:

- `tiny`: ~39M parameters, fastest
- `base`: ~74M parameters, balanced
- `small`: ~244M parameters
- `medium`: ~769M parameters
- `large`: ~1.5B parameters, most accurate

### Example Configuration

```bash
export WHISPER_MODEL=base
export DEVICE=cpu
```
EOF
```

**Step 2: Find insertion point and insert**

```bash
cd /home/ranj/Project_Chimera
ENDPOINTS_LINE=$(grep -n "^## Endpoints" docs/api/captioning-agent.md | cut -d: -f1)
INSERT_LINE=$((ENDPOINTS_LINE + 20))

sed -i "${INSERT_LINE}r /tmp/captioning-config.md" docs/api/captioning-agent.md
```

**Step 3: Verify**

```bash
grep -A 5 "## Configuration" docs/api/captioning-agent.md
```

---

## Task 6: Generate Configuration Section for OpenClaw Orchestrator

**Files:**
- Modify: `docs/api/openclaw-orchestrator.md`

**Step 1: Generate Configuration section**

```bash
cat > /tmp/openclaw-config.md << 'EOF'
## Configuration

The OpenClaw Orchestrator routes skill requests to appropriate AI agents.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `openclaw-orchestrator` | Service identifier |
| `PORT` | integer | `8000` | Service port |
| `SCENESPEAK_AGENT_URL` | string | `http://scenespeak-agent:8001` | SceneSpeak agent URL |
| `CAPTIONING_AGENT_URL` | string | `http://captioning-agent:8002` | Captioning agent URL |
| `BSL_AGENT_URL` | string | `http://bsl-agent:8003` | BSL agent URL |
| `SENTIMENT_AGENT_URL` | string | `http://sentiment-agent:8004` | Sentiment agent URL |
| `LSM_AGENT_URL` | string | `http://lighting-sound-music:8005` | LSM service URL |
| `SAFETY_FILTER_URL` | string | `http://safety-filter:8006` | Safety filter URL |

### Agent URLs

For local development, agent URLs use `localhost`. For Docker/Kubernetes, use service names:

- **Local:** `http://localhost:8001`
- **Docker:** `http://scenespeak-agent:8001`
- **Kubernetes:** `http://scenespeak-agent.default.svc.cluster.local:8001`

### Example Configuration

```bash
export SCENESPEAK_AGENT_URL=http://localhost:8001
export CAPTIONING_AGENT_URL=http://localhost:8002
```
EOF
```

**Step 2: Insert into openclaw-orchestrator.md**

```bash
cd /home/ranj/Project_Chimera
ENDPOINTS_LINE=$(grep -n "^## Endpoints" docs/api/openclaw-orchestrator.md | cut -d: -f1)
INSERT_LINE=$((ENDPOINTS_LINE + 20))

sed -i "${INSERT_LINE}r /tmp/openclaw-config.md" docs/api/openclaw-orchestrator.md
```

**Step 3: Verify**

```bash
grep -A 5 "## Configuration" docs/api/openclaw-orchestrator.md
```

---

## Task 7: Generate Configuration Section for Operator Console

**Files:**
- Modify: `docs/api/operator-console.md`

**Step 1: Generate Configuration section**

```bash
cat > /tmp/console-config.md << 'EOF'
## Configuration

The Operator Console provides real-time monitoring and manual control.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `operator-console` | Service identifier |
| `PORT` | integer | `8007` | Service port |
| `METRICS_INTERVAL` | integer | `5` | Metrics collection interval (seconds) |
| `ALERT_THRESHOLD_CPU` | float | `0.8` | CPU alert threshold (0.0-1.0) |
| `ALERT_THRESHOLD_MEMORY` | float | `0.8` | Memory alert threshold (0.0-1.0) |

### Alert Thresholds

Alerts are generated when service metrics exceed thresholds:

- **CPU**: Alert when usage exceeds threshold (default: 80%)
- **Memory**: Alert when usage exceeds threshold (default: 80%)
- **Error Rate**: Alert when error rate exceeds 5%

### WebSocket Configuration

The console uses WebSocket for real-time updates. Ensure WebSocket connections are allowed:

```yaml
services:
  operator-console:
    environment:
      - METRICS_INTERVAL=5
      - ALERT_THRESHOLD_CPU=0.8
```
EOF
```

**Step 2: Insert into operator-console.md**

```bash
cd /home/ranj/Project_Chimera
ENDPOINTS_LINE=$(grep -n "^## Endpoints" docs/api/operator-console.md | cut -d: -f1)
INSERT_LINE=$((ENDPOINTS_LINE + 20))

sed -i "${INSERT_LINE}r /tmp/console-config.md" docs/api/operator-console.md
```

**Step 3: Verify**

```bash
grep -A 5 "## Configuration" docs/api/operator-console.md
```

---

## Task 8: Generate Configuration Section for SceneSpeak Agent

**Files:**
- Modify: `docs/api/scenespeak-agent.md`

**Step 1: Generate Configuration section**

```bash
cat > /tmp/scenespeak-config.md << 'EOF'
## Configuration

The SceneSpeak Agent generates dialogue using GLM 4.7 API with local LLM fallback.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `scenespeak-agent` | Service identifier |
| `PORT` | integer | `8001` | Service port |
| `GLM_API_KEY` | string | `None` | Z.ai GLM 4.7 API key |
| `GLM_API_BASE` | string | `https://open.bigmodel.cn/api/paas/v4/` | GLM API base URL |
| `LOCAL_MODEL_PATH` | string | `None` | Path to local LLM model |
| `TEMPERATURE` | float | `0.7` | Sampling temperature (0.0-2.0) |
| `MAX_TOKENS` | integer | `500` | Maximum tokens to generate |

### API Configuration

SceneSpeak Agent requires an API key for GLM 4.7:

```bash
export GLM_API_KEY=your_api_key_here
export TEMPERATURE=0.7
export MAX_TOKENS=500
```

### Fallback Behavior

If GLM API is unavailable, the agent falls back to local LLM (if `LOCAL_MODEL_PATH` is configured).

### Model Configuration

- **Temperature**: Controls randomness (0.0 = focused, 2.0 = creative)
- **Max Tokens**: Limits response length (1-4096)

### Example Configuration

```bash
export GLM_API_KEY=sk-xxxxx
export LOCAL_MODEL_PATH=/models/local-llm
export TEMPERATURE=0.7
```
EOF
```

**Step 2: Insert into scenespeak-agent.md**

```bash
cd /home/ranj/Project_Chimera
ENDPOINTS_LINE=$(grep -n "^## Endpoints" docs/api/scenespeak-agent.md | cut -d: -f1)
INSERT_LINE=$((ENDPOINTS_LINE + 20))

sed -i "${INSERT_LINE}r /tmp/scenespeak-config.md" docs/api/scenespeak-agent.md
```

**Step 3: Verify**

```bash
grep -A 5 "## Configuration" docs/api/scenespeak-agent.md
```

---

## Task 9: Generate Configuration Section for Sentiment Agent

**Files:**
- Modify: `docs/api/sentiment-agent.md`

**Step 1: Generate Configuration section**

```bash
cat > /tmp/sentiment-config.md << 'EOF'
## Configuration

The Sentiment Agent analyzes text sentiment using DistilBERT with rule-based fallback.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `sentiment-agent` | Service identifier |
| `PORT` | integer | `8004` | Service port |
| `MODEL_TYPE` | string | `rule-based` | Analysis model (rule-based/distilbert) |
| `CONFIDENCE_THRESHOLD` | float | `0.5` | Minimum confidence for predictions |
| `BATCH_SIZE` | integer | `32` | Batch size for processing |

### Model Selection

The agent supports two analysis modes:

- **rule-based**: Fast keyword matching (default)
- **distilbert**: ML-based sentiment analysis (requires model download)

### Configuration Options

```bash
export MODEL_TYPE=rule-based
export CONFIDENCE_THRESHOLD=0.5
```

### Output Format

Sentiment analysis returns:

- **sentiment**: positive, negative, or neutral
- **score**: Confidence score (0.0 to 1.0)
- **emotion**: joy, surprise, neutral, sadness, anger, or fear
EOF
```

**Step 2: Insert into sentiment-agent.md**

```bash
cd /home/ranj/Project_Chimera
ENDPOINTS_LINE=$(grep -n "^## Endpoints" docs/api/sentiment-agent.md | cut -d: -f1)
INSERT_LINE=$((ENDPOINTS_LINE + 20))

sed -i "${INSERT_LINE}r /tmp/sentiment-config.md" docs/api/sentiment-agent.md
```

**Step 3: Verify**

```bash
grep -A 5 "## Configuration" docs/api/sentiment-agent.md
```

---

## Task 10: Verify Configuration Sections

**Files:**
- None (verification only)

**Step 1: Check all 6 docs have Configuration sections**

```bash
cd /home/ranj/Project_Chimera

for doc in docs/api/{bsl-agent,captioning-agent,openclaw-orchestrator,operator-console,scenespeak-agent,sentiment-agent}.md; do
  if grep -q "## Configuration" "$doc"; then
    echo "✓ $(basename $doc) has Configuration"
  else
    echo "✗ $(basename $doc) missing Configuration"
  fi
done
```
Expected: All 6 show ✓

**Step 2: Verify each Configuration has content**

```bash
for doc in docs/api/{bsl-agent,captioning-agent,openclaw-orchestrator,operator-console,scenespeak-agent,sentiment-agent}.md; do
  echo "=== $(basename $doc) ==="
  grep -A 2 "## Configuration" "$doc"
  echo ""
done
```
Expected: Each shows Configuration header + at least some content

---

## Task 11: Fix Release Notes Status

**Files:**
- Modify: `docs/release-notes/v0.5.0.md`

**Step 1: Check if release notes exist**

```bash
cd /home/ranj/Project_Chimera
ls -la docs/release-notes/ | grep v0.5
```
Expected: v0.5.0.md file exists

**Step 2: Update status from "current" to "planned"**

```bash
if [ -f "docs/release-notes/v0.5.0.md" ]; then
  sed -i 's/Status: Current/Status: Planned/g' docs/release-notes/v0.5.0.md
  sed -i 's/status: current/status: planned/g' docs/release-notes/v0.5.0.md
fi
```

**Step 3: Verify change**

```bash
grep -i "status" docs/release-notes/v0.5.0.md | head -3
```
Expected: Shows "Planned" not "Current"

---

## Task 12: Create Migration Guide

**Files:**
- Create: `docs/migration/v0.3-to-v0.4.md`

**Step 1: Create migration guide**

```bash
cat > docs/migration/v0.3-to-v0.4.md << 'EOF'
# Migration Guide: v0.3 to v0.4

**Release Date:** March 2026
**Status:** Stable

## Overview

This guide helps you migrate from Project Chimera v0.3 to v0.4.

## Breaking Changes

### 1. Service Architecture Changes

**v0.3:** Monolithic service structure
**v0.4:** Microservices with OpenClaw Orchestrator

**Impact:** Direct service calls must now go through OpenClaw Orchestrator.

**Migration:** Update API calls from:
```
http://localhost:8001/generate  # v0.3
```
To:
```
http://localhost:8000/v1/orchestrate  # v0.4
{
  "skill": "dialogue_generator",
  "input": {"prompt": "..."}
}
```

### 2. Port Changes

| Service | v0.3 Port | v0.4 Port |
|---------|-----------|-----------|
| Orchestrator | N/A | 8000 |
| SceneSpeak | 8000 | 8001 |
| Captioning | 8001 | 8002 |
| BSL | 8002 | 8003 |
| Sentiment | 8003 | 8004 |
| LSM | 8004 | 8005 |
| Safety | 8005 | 8006 |
| Console | N/A | 8007 |

**Action:** Update all port references in your configuration.

### 3. Environment Variable Changes

**v0.3:** `MODEL_PATH`
**v0.4:** `LOCAL_MODEL_PATH` (for consistency across services)

**Action:** Update environment variable names in deployment configs.

## New Features

- ✅ OpenClaw Orchestrator for skill routing
- ✅ Operator Console for real-time monitoring
- ✅ Enhanced observability (OpenTelemetry + Prometheus)
- ✅ Docker Compose orchestration
- ✅ Integration testing framework

## Deployment Migration

### Step 1: Backup Current Deployment

```bash
# Save current configuration
kubectl get configmaps -o yaml > v0.3-configmaps.yaml
kubectl get secrets -o yaml > v0.3-secrets.yaml
```

### Step 2: Update Service Definitions

```bash
# Pull latest images
docker pull ghcr.io/project-chimera/scenespeak-agent:v0.4
docker pull ghcr.io/project-chimera/openclaw-orchestrator:v0.4
# ... pull all service images
```

### Step 3: Update Port Configurations

Update your `docker-compose.yml` or Kubernetes manifests to use new ports.

### Step 4: Deploy

```bash
# Using Docker Compose
docker-compose down
docker-compose up -d

# Using Kubernetes
kubectl apply -f k8s/v0.4/
```

### Step 5: Verify Migration

```bash
# Health check all services
curl http://localhost:8000/health/ready  # OpenClaw
curl http://localhost:8007/health/ready  # Console
```

## Rollback Plan

If issues occur:

```bash
# Quick rollback to v0.3
git checkout v0.3
docker-compose up -d
```

## Support

For migration assistance, see:
- [Documentation](../README.md)
- [Troubleshooting Guide](../demo/troubleshooting.md)
- [GitHub Issues](https://github.com/ranjrana2012-lab/project-chimera/issues)

---
*Migration Guide - Project Chimera v0.4.0*
EOF
```

**Step 2: Verify migration guide created**

```bash
ls -la docs/migration/v0.3-to-v0.4.md
```
Expected: File exists and is not empty

---

## Task 13: Commit All Changes

**Files:**
- Add: All modified API docs (6 files)
- Add: Migration guide
- Add: Release notes update

**Step 1: Stage all documentation changes**

```bash
cd /home/ranj/Project_Chimera

git add docs/api/bsl-agent.md
git add docs/api/captioning-agent.md
git add docs/api/openclaw-orchestrator.md
git add docs/api/operator-console.md
git add docs/api/scenespeak-agent.md
git add docs/api/sentiment-agent.md
git add docs/migration/v0.3-to-v0.4.md
git add docs/release-notes/v0.5.0.md
```

**Step 2: Verify staged files**

```bash
git status
```
Expected: 7 files staged for commit

**Step 3: Commit changes**

```bash
git commit -m "docs(api): add Configuration sections to 6 API docs

- Add ## Configuration sections to bsl-agent, captioning-agent, openclaw-orchestrator, operator-console, scenespeak-agent, sentiment-agent
- Each section includes environment variables, descriptions, defaults
- Update release-notes/v0.5.0 status from current to planned
- Add migration guide v0.3-to-v0.4.md with breaking changes and deployment steps

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Step 4: Verify commit**

```bash
git log -1 --oneline
```
Expected: New commit visible with hash

---

## Task 14: Push to GitHub

**Files:**
- None (git operation)

**Step 1: Push commits**

```bash
cd /home/ranj/Project_Chimera
git push origin main
```
Expected: "Writing objects...", branch updated

**Step 2: Verify push success**

```bash
git status
```
Expected: "Your branch is up to date with 'origin/main'"

**Step 3: Final verification**

```bash
LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git rev-parse origin/main)
if [ "$LOCAL_SHA" == "$REMOTE_SHA" ]; then
  echo "✓ Fully synced"
else
  echo "✗ Sync mismatch"
fi
```
Expected: "✓ Fully synced"

---

## Definition of Done

- [ ] All 6 API docs have ## Configuration section
- [ ] Configuration sections include environment variables
- [ ] Configuration sections include default values
- [ ] Migration guide created (v0.3-to-v0.4.md)
- [ ] Release notes status updated (v0.5.0 → planned)
- [ ] All changes committed
- [ ] Changes pushed to GitHub
- [ ] Final verification passed

---

*Implementation Plan - Project Chimera v0.4.0 - March 6, 2026*

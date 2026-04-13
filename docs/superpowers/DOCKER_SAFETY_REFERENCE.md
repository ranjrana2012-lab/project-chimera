# Docker Safety Reference

> **Purpose:** Quick reference for safe Docker operations in Project Chimera

---

## Pre-Flight Checklist

Before ANY Docker operation:

```bash
# 1. Check .dockerignore exists
ls services/*/Dockerfile | xargs -I {} sh -c 'echo "=== {} ===" && cat $(dirname {})/.dockerignore 2>/dev/null || echo "NO .dockerignore!"'

# 2. Check current disk usage
docker system df

# 3. Check for port conflicts (with fallback)
if command -v ss >/dev/null 2>&1; then
    ss -tuln | grep -E ':(8000|8001|8002|8004|8006|8007|8008|6379)'
else
    netstat -tuln | grep -E ':(8000|8001|8002|8004|8006|8007|8008|6379)' 2>/dev/null || lsof -iTCP -sTCP:LISTEN | grep -E ':(8000|8001|8002|8004|8006|8007|8008|6379)'
fi

# 4. Verify only specific service targeted
# (manual check - confirm you're not building entire stack)
```

---

## Forbidden Commands

🚨 **NEVER run these without explicit user approval:**

```bash
docker build *
docker buildx build *
docker compose build *
docker compose up --build *
podman build *
```

---

## Cleanup Commands

```bash
# Check disk usage
docker system df

# Remove dangling images (safe)
docker image prune -f

# Remove stopped containers (safe)
docker container prune -f

# Remove unused volumes (careful!)
docker volume prune -f

# Remove build cache (common bloat source)
docker builder prune -a -f

# Nuclear: clean everything (use with caution)
# ⚠️  WARNING: This will remove ALL stopped containers and volumes - ensure data is backed up!
docker system prune -a --volumes -f
```

---

## Understanding `docker system df`

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          10        5         2.5GB     1.2GB (48%)
Containers      8         3         450MB     200MB (44%)
Local Volumes   15        8         3.1GB     800MB (26%)
Build Cache     50        0         1.8GB     1.8GB (100%)  ← COMMON BLOAT SOURCE
```

**Key:**
- SIZE = total space used
- RECLAIMABLE = safe to free
- ACTIVE = currently in use (don't delete)

---

## Project Chimera Service Ports

```
services/
├── openclaw-orchestrator/  (port 8000)
├── scenespeak-agent/       (port 8001)
├── translation-agent/      (port 8002) - not running
├── sentiment-agent/        (port 8004)
├── safety-filter/          (port 8006)
├── operator-console/       (port 8007)
├── hardware-bridge/        (port 8008)
└── redis/                  (port 6379)
```

**Note:** Some services (like `translation-agent`) may not be running in all deployments.

---

## .dockerignore Examples

Prevent bloat by excluding unnecessary files from build context:

**Example for Python services:**
```
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.env
.git/
.pytest_cache/
.coverage
```

**Example for Node.js services:**
```
node_modules/
npm-debug.log
.env
.git/
dist/
```

---

## What Causes Bloat

| Source | Typical Size | Prevention |
|--------|--------------|-------------|
| Build cache | 1-5GB | Prune regularly, use .dockerignore |
| Dangling images | 500MB-2GB | `docker image prune -f` after builds |
| Old layers | 100MB-1GB each | Tag images, prune old versions |
| Volume data | Variable | Don't mount build artifacts |

---

## Emergency: Disk Full

If disk fills up:

```bash
# 1. Stop all Docker
docker compose down

# 2. Check usage
docker system df

# 3. Clean build cache (usually the culprit)
docker builder prune -a -f

# 4. Clean dangling images
docker image prune -a -f

# 5. If still full, nuclear option
docker system prune -a --volumes -f

# 6. Verify
df -h
docker system df
```

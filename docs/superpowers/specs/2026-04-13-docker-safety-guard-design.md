# Docker Safety Guard Design

**Date:** 2026-04-13
**Project:** Project Chimera
**Status:** Approved
**Priority:** CRITICAL

---

## Problem Statement

The Ralph Loop has twice caused Docker bloat that filled the hard drive. This happens when:
- Building without proper `.dockerignore` files (includes venv, node_modules, cache files)
- Building entire compose stack instead of single services
- Not checking Docker disk usage before/after operations

## Solution: Three-Layer Protection

### Layer 1: Hard Gate (Forbidden Commands)

Commands that MUST NEVER be run without explicit user permission:

```
🚨 FORBIDDEN WITHOUT EXPLICIT APPROVAL 🚨

- docker build *
- docker buildx build *
- docker compose build *
- docker compose up --build *
- podman build *
```

**Required workflow if build seems necessary:**
1. STOP immediately
2. Explain exactly WHY you think a build is necessary
3. Ask user for permission to proceed
4. Only build the SPECIFIC service needed (not entire stack)

### Layer 2: Pre-flight Checklist

Before ANY Docker operation (even allowed ones like `docker compose up`), you MUST verify:

```
☐ .dockerignore exists in each service being built
☐ Build context is minimal (no venv, __pycache__, node_modules, .git)
☐ Check current Docker disk usage: docker system df
☐ Verify no port conflicts with existing services
☐ Confirm only specific service(s) targeted, not entire stack
```

### Layer 3: Post-Operation Cleanup

After any Docker build operation:

```
☐ Check new disk usage: docker system df
☐ Prune dangling images if >500MB: docker image prune -f
☐ Confirm no unexpected bloat occurred
☐ If bloat detected, investigate and clean immediately
```

---

## Docker Disk Usage Reference

### Understanding `docker system df`

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          10        5         2.5GB     1.2GB (48%)
Containers      8         3         450MB     200MB (44%)
Local Volumes   15        8         3.1GB     800MB (26%)
Build Cache     0         0         0B        0B
```

**Key columns:**
- **SIZE**: Total space used
- **RECLAIMABLE**: Space that can be freed safely
- **ACTIVE**: Currently in use (don't delete)

### Cleanup Commands

```bash
# Check current usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused containers
docker container prune -f

# Remove unused volumes
docker volume prune -f

# Remove build cache (common bloat source)
docker builder prune -a -f

# Nuclear option: clean everything unused
docker system prune -a --volumes -f
```

### What Causes Bloat

| Source | Typical Size | Prevention |
|--------|--------------|-------------|
| Build cache | 1-5GB | Use `.dockerignore`, prune regularly |
| Dangling images | 500MB-2GB | `docker image prune -f` after builds |
| Old layers | 100MB-1GB each | Tag images meaningfully, prune old versions |
| Volume data | Variable | Don't mount build artifacts as volumes |

---

## Integration Into Ralph Loop Master Prompt

This safety guard should be inserted into the master prompt as a prominent section:

**Location:** After "Project Context" and "Current System Architecture", before "What Needs To Be Done"

**Heading:** `⚠️ CRITICAL CONSTRAINTS - DO NOT VIOLATE`

This placement ensures the AI sees the constraints before it sees any tasks, making it impossible to miss.

---

## Success Criteria

- ✅ No Docker bloat incidents occur
- ✅ Pre-flight checklist is followed before every Docker operation
- ✅ Post-operation cleanup is performed after every build
- ✅ Hard disk remains stable during Ralph Loop execution
- ✅ `docker system df` shows RECLAIMABLE staying under 2GB

---

## Enforcement Strategy

The Ralph Loop should be programmed to:

1. **Self-query before Docker operations:** "Is this operation allowed? Have I completed the pre-flight checklist?"

2. **Explicit confirmation:** For any build-related operation, output: "⚠️ Docker build requested. Checking pre-flight checklist..." and show each item being verified

3. **Automatic post-check:** After any Docker operation, automatically run `docker system df` and report the change

---

## Appendix: Project Chimera Service Ports

Reference for port conflict checking:

```
services/
├── openclaw-orchestrator/  (port 8000) - Main orchestration
├── scenespeak-agent/       (port 8001) - LLM dialogue generation
├── translation-agent/      (port 8002) - Translation (not running)
├── sentiment-agent/        (port 8004) - DistilBERT sentiment analysis
├── safety-filter/          (port 8006) - Content safety
├── operator-console/       (port 8007) - Web UI
├── hardware-bridge/        (port 8008) - DMX lighting
└── redis/                  (port 6379) - Message broker
```

Before starting any service, verify its port isn't already in use:

```bash
# Check if port is in use
lsof -i :8000  # or whatever port
# or
netstat -tuln | grep 8000
```

---

**Design Status:** ✅ Approved
**Next Step:** Integrate into Ralph Loop Master Prompt

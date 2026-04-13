# Docker Build Context Optimization Design

> **Date:** 2026-04-13
> **Status:** Approved
> **Priority:** High

## Problem

Docker builds use `context: .` which includes **84GB** of files, but each service only needs ~50-200MB. This causes:
- Slow builds (1.65GB+ build context transfer)
- Massive build cache pollution (184GB+ cache)
- Unnecessary disk I/O

### Audit Findings

| Directory | Size | Needed? | Reason |
|-----------|------|---------|--------|
| models/ | 75GB | ❌ | Runtime-only via host.docker.internal |
| .git/ | 4.1GB | ❌ | Never in containers |
| venv/ | 548MB | ❌ | Containers install own deps |
| future_concepts/ | 371MB | ❌ | Experimental |
| integrations/ | 240MB | ❌ | External (bettafish, mirofish) |
| platform/ | 82MB | ❌ | Not in MVP |
| tests/ | 52MB | ❌ | Test files |
| htmlcov/ | 9.5MB | ❌ | Coverage reports |
| docs/ | 5MB | ❌ | Documentation |
| services/shared/ | ~50MB | ✅ | Shared code |
| services/{name}/ | ~10-100MB | ✅ | Service code |

## Solution

### 1. Root .dockerignore

Create `.dockerignore` at project root to exclude unnecessary files from ALL builds:

```dockerignore
# Model weights (runtime-only, accessed via host.docker.internal)
models/

# Python development
venv/
.venv/
__pycache__/
*.py[cod]
*.pyo
*.pyd

# Git
.git/
.gitignore

# CI/CD (not needed in images)
.github/
.gitlab-ci.yml

# Documentation
docs/
*.md
!README.md

# Testing
tests/
htmlcov/
.pytest_cache/
.coverage
final_test_env/

# Experimental/unused
future_concepts/
integrations/
platform/

# IDE
.vscode/
.cursor/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Docker (don't include docker files in builds)
docker-compose*.yml
!docker-compose.mvp.yml
Dockerfile
*/Dockerfile
.dockerignore
```

**Expected impact:** Build context reduced from ~84GB to ~4GB.

### 2. Shared Code Access

Use **PYTHONPATH** approach (already proven in openclaw-orchestrator):

```dockerfile
# In each service's Dockerfile
ENV PYTHONPATH=/app:$PYTHONPATH
COPY services/shared/ /app/shared/
```

**Alternative considered:** Install shared as package via setup.py - rejected as YAGNI.

### 3. Per-Service Contexts

**Decision:** NOT implementing per-service build contexts (`context: services/{name}`) at this time.

**Reasoning:**
- Root .dockerignore handles 90% of the problem
- Per-service contexts add complexity for marginal gain
- Can add later if specific services need further optimization

### 4. CI/CD Compatibility

Root `.dockerignore` works identically in:
- Local development
- GitHub Actions
- Any Docker-based CI/CD

No special handling needed.

### 5. Validation

**Post-implementation checks:**

1. **Build context size**
   ```bash
   # Verify < 5GB
   docker buildx build --progress=plain -f services/scenespeak-agent/Dockerfile . 2>&1 | grep context
   ```

2. **Build all services**
   ```bash
   docker compose -f docker-compose.mvp.yml build
   ```

3. **Health checks**
   ```bash
   docker compose -f docker-compose.mvp.yml up -d
   docker compose -f docker-compose.mvp.yml ps
   ```

4. **Docker Safety Guard integration**
   - Add `.dockerignore` check to `scripts/docker-preflight-check.sh`
   - Warn if missing

## Success Criteria

- [ ] Root `.dockerignore` created
- [ ] Build context < 5GB per service
- [ ] All MVP services build successfully
- [ ] All services pass health checks
- [ ] Pre-flight check script validates .dockerignore

## Files to Modify

1. **Create:** `.dockerignore` (project root)
2. **Modify:** `scripts/docker-preflight-check.sh` - Add .dockerignore validation
3. **Verify:** All service Dockerfiles have PYTHONPATH set correctly

## Related Work

- Docker Safety Guard (2026-04-13) - Pre/post build checks
- openclaw-orchestrator PYTHONPATH fix - Template for other services

# Ralph Loop Startup Checklist

**Mandatory First Steps for Any Ralph Loop Session:**

## 1. Load Master Prompt

```bash
cat .claude/RALPH_LOOP_MASTER_PROMPT.md
```

This provides:
- Project context (Phase 1 complete, MVP validated)
- CRITICAL Docker safety constraints
- Work style guidelines
- Success criteria

## 2. Run Pre-Flight Check

```bash
./scripts/docker-preflight-check.sh
```

This checks:
- .dockerignore files exist
- Current Docker disk usage
- Port conflicts

## 3. Check Current State

```bash
git status
docker system df
```

## 4. Ask User

"What would you like me to work on first?"

---

**CRITICAL: Docker Build Safety**

These commands are FORBIDDEN without explicit approval:
- docker build *
- docker buildx build *
- docker compose build *
- docker compose up --build *

**If build is needed, ask with this format:**

```
🔔 DOCKER BUILD REQUEST
Service: <service-name>
Build Context: <path>
Estimated Size: <du -sh output>
.dockerignore: <yes/no>
Reason: <why build is needed>
Permission to proceed? (yes/no)
```

---

**After ANY Docker Build:**

```bash
./scripts/docker-postbuild-check.sh
```

This shows:
- Current Docker disk usage
- Reclaimable space warning
- Cleanup recommendations

---

**Documentation Reference:**
- Docker Safety: `docs/superpowers/DOCKER_SAFETY_REFERENCE.md`
- MVP Overview: `docs/MVP_OVERVIEW.md`
- Testing: `docs/TESTING.md`

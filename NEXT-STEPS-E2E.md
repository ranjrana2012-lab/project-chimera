# E2E Testing - Next Steps (2026-03-09)

## Current Status

- **Test Results**: 71/129 API tests passing (55%)
- **Root Cause**: Docker containers running old code, need rebuild + restart
- **Code Status**: All changes committed and pushed to GitHub

## Services with New Code (Need Rebuild)

The following services have new `/api/*` endpoints but containers haven't picked up the changes:

1. **safety-filter** (8006) - Added `/api/moderate`, `/health`, `/health/model_info`
2. **operator-console** (8007) - Added `/api/show/*` endpoints
3. **openclaw-orchestrator** (8000) - Added `/api/skills`, `/api/show/*`
4. **scenespeak-agent** (8001) - Added `/api/generate`, `/health/model_info`
5. **sentiment-agent** (8004) - Added `/api/analyze`, `/health/model_info`
6. **captioning-agent** (8002) - Fixed `segments` field

## Why Tests Are Failing

```bash
# Current behavior (old code)
$ curl http://localhost:8006/api/moderate
{"detail":"Not Found"}  # 404 - endpoint doesn't exist in old code

# Expected behavior (new code)
$ curl http://localhost:8006/api/moderate
# Should return 200 with moderation response
```

## Fix: Rebuild and Restart

Run these commands to pick up the new code:

```bash
# Step 1: Build new images (takes 2-5 minutes)
cd /home/ranj/Project_Chimera
sudo docker compose build safety-filter operator-console openclaw-orchestrator scenespeak-agent sentiment-agent captioning-agent

# Step 2: Restart services with new images (instant)
sudo docker compose up -d

# Step 3: Verify services picked up new code
curl http://localhost:8006/health/model_info
curl http://localhost:8007/api/show/status
curl http://localhost:8000/api/skills
```

## Expected Improvement After Rebuild

| Service | Current | After Rebuild |
|---------|---------|---------------|
| safety-filter | 0/10 passing | 10/10 passing |
| operator-console | 0/12 passing | 12/12 passing |
| orchestrator | 0/8 passing | 8/8 passing |
| scenespeak-agent | 0/8 passing | 8/8 passing |
| sentiment-agent | 0/11 passing | 11/11 passing |
| **Total** | **71/129 (55%)** | **~115/129 (89%)** |

## After Rebuild: Run Tests

```bash
cd /home/ranj/Project_Chimera/tests/e2e
npm run test -- --grep "@api" --reporter=list
```

## Remaining Work (After Rebuild)

These will still need work:

1. **WebSocket Tests** - sentiment-agent needs WebSocket endpoint
2. **UI Tests** - timing issues
3. **Cross-Service Tests** - full integration workflow
4. **BSL Agent** - 2 failing tests
5. **Captioning Agent** - 2 tests (may fix after rebuild)

## Commits Ready

All code is in the repository:
- `e0f4289` - sentiment-agent /api/analyze
- `b214b08` - scenespeak-agent /api/generate
- `044abf0` - orchestrator /api/skills
- `193383d` - operator-console show control
- `f804466` - safety-filter /api/moderate
- `0782d99` - captioning-agent segments fix

Just need rebuild to activate.

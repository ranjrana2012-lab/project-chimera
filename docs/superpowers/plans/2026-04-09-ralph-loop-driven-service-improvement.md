# Ralph Loop-Driven Service Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy a functional continuous-loop interactive system by June 5, 2026 through autonomous Ralph Loop improvements and student testing

**Architecture:** Ralph Loop (autonomous Claude Code agent) iteratively improves 6 active services while 4 students test and validate. A unified dashboard tracks progress through service health, test pass rates, and git commits.

**Tech Stack:** Python 3.12+, FastAPI, Docker, Prometheus, Grafana, pytest, Git

**Timeline:** 8 weeks (April 9 - June 5, 2026)

---

# WEEK 1: Foundation & Setup (April 9-15)

## Task 1: Create Ralph Loop Configuration Directory Structure

**Files:**
- Create: `.claude/autonomous-refactor/program.md`
- Create: `.claude/autonomous-refactor/queue.txt`
- Create: `.claude/autonomous-refactor/learnings.md`
- Create: `.claude/autonomous-refactor/baseline_metrics.json`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p .claude/autonomous-refactor
```

- [ ] **Step 2: Write program.md with Ralph Loop constraints**

```bash
cat > .claude/autonomous-refactor/program.md << 'EOF'
# Ralph Loop Constitutional Constraints

**Date**: April 9, 2026
**Version**: 1.0
**Status**: Active

---

## Platform Constraints

- **Platform**: x86_64 Linux
- **Python Version**: 3.10+
- **Primary Framework**: FastAPI
- **Avoid**: `flash-attn`, ARM64-specific wheels
- **Attention Mechanism**: Use SDPA (Scaled Dot Product Attention)

---

## Change Scope Rules

### Bounded Changes

**ONE logical component per iteration maximum**

Examples of bounded changes:
- Add tests to ONE function or class
- Refactor ONE module for clarity
- Fix ONE bug or issue
- Add type hints to ONE file
- Improve error handling in ONE endpoint

NOT bounded (multiple iterations required):
- Rewriting entire service
- Adding new features across multiple files
- Database migrations
- Major architectural changes

---

## What Ralph Loop CAN Do

- Add unit tests to improve coverage
- Improve existing code structure
- Add type hints and improve documentation
- Fix identified bugs and issues
- Refactor for clarity (within bounded scope)
- Add integration tests between services
- Improve error handling

---

## What Ralph Loop CANNOT Do

- Delete or skip existing tests
- Remove failing tests (must fix them)
- Stub functions to avoid tests
- Reduce test coverage
- Ignore pytest exit codes
- Modify the evaluator script (READ-ONLY)
- Make changes to frozen services (OpenClaw, BSL)

---

## Quality Gates (IMMUTABLE)

### 1. Functional Correctness
- **Requirement**: pytest exit code == 0
- **Failure Action**: git reset --hard HEAD, document in learnings.md

### 2. Assertion Density
- **Requirement**: assertion_count >= baseline
- **Baseline**: Recorded in baseline_metrics.json
- **Failure Action**: git reset --hard HEAD, document as "reward hacking"

### 3. Test Coverage
- **Requirement**: coverage >= baseline (must stay stable or increase)
- **Baseline**: Recorded in baseline_metrics.json
- **Failure Action**: git reset --hard HEAD, document failure

### 4. Deprecation Hygiene
- **Requirement**: deprecation_warnings == 0
- **Failure Action**: Fix warnings, resubmit changes

---

## Failure Consequences

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 1 | Tests failed | git reset --hard HEAD |
| 2 | Reward hacking (deleted assertions, etc.) | git reset, document as critical failure |
| 3 | Coverage below threshold | git reset --hard HEAD |
| 4 | Deprecation warnings | Fix warnings before committing |

---

## Active Services (6 services)

1. **Nemo Claw Orchestrator** - `services/nemo-claw-orchestrator/`
2. **SceneSpeak Agent** - `services/scenespeak-agent/`
3. **Sentiment Agent** - `services/sentiment-agent/`
4. **Safety Filter** - `services/safety-filter/`
5. **Captioning Agent** - `services/captioning-agent/`
6. **Audio Controller** - `services/audio-controller/`

---

## Frozen Services (DO NOT MODIFY)

1. **OpenClaw Orchestrator** - `services/openclaw-orchestrator/`
2. **BSL Agent** - `services/bsl-agent/`

---

## Workflow

1. Read `.claude/autonomous-refactor/queue.txt` for next task
2. Select service to improve (prioritize by health/test failures)
3. Make BOUNDED changes to service code + tests
4. Run evaluator: `./platform/quality-gate/evaluate.sh`
5. If evaluator returns 0: commit changes, update `learnings.md`
6. If evaluator returns non-zero: revert changes, document failure in `learnings.md`

---

## Documentation Requirements

Every iteration MUST update `learnings.md` with:
- What was changed
- Why it was changed
- Test results before/after
- Coverage delta
- Any failures or lessons learned

---

## Success Criteria

By June 5, 2026:
- ✅ 50+ successful commits to active services
- ✅ Test coverage increased or stable across all services
- ✅ learnings.md has entries showing progress
- ✅ No services permanently blocked (>1 week without progress)
- ✅ Quality gate evaluator passing consistently
EOF
```

- [ ] **Step 3: Create initial queue.txt**

```bash
cat > .claude/autonomous-refactor/queue.txt << 'EOF'
# Ralph Loop Task Queue
# Format: [PRIORITY] [SERVICE] [TASK_DESCRIPTION]
# Priorities: [urgent], [high], [medium], [low]
# Services: nemo-claw, scenespeak, sentiment, safety, captioning, audio

# Week 1 Initial Tasks
[high] [baseline] Run baseline tests for all services
[high] [baseline] Record baseline coverage metrics
[medium] [nemo-claw] Add health check endpoint tests
[medium] [scenespeak] Add unit tests for dialogue generation
[medium] [sentiment] Add unit tests for sentiment analysis
[medium] [safety] Add unit tests for content moderation
[medium] [captioning] Add unit tests for text formatting
[medium] [audio] Add unit tests for audio output
[low] [all] Add type hints to service modules
EOF
```

- [ ] **Step 4: Create learnings.md with initial state**

```bash
cat > .claude/autonomous-refactor/learnings.md << 'EOF'
# Ralph Loop Learnings Log

**Start Date**: April 9, 2026
**End Date**: June 5, 2026
**Status**: Week 1 - Foundation

---

## Week 1: April 9-15, 2026

### Day 1: April 9, 2026

**Initial State:**
- Ralph Loop configured and initialized
- Task queue created with initial priorities
- Baseline metrics to be recorded

**Services Active:**
1. Nemo Claw Orchestrator
2. SceneSpeak Agent
3. Sentiment Agent
4. Safety Filter
5. Captioning Agent
6. Audio Controller

**Services Frozen:**
1. OpenClaw Orchestrator
2. BSL Agent

**Next Steps:**
- Run baseline tests
- Record initial coverage
- Begin first improvements

---

## Learnings Template

### [Date] - [Service] - [Change Type]

**What was changed:**
- [Specific files/functions modified]

**Why:**
- [Reason for change, issue addressed]

**Test Results:**
- Before: [pass/fail, coverage %]
- After: [pass/fail, coverage %]

**Coverage Delta:**
- [Coverage change percentage]

**Issues/Lessons:**
- [Any problems encountered, lessons learned]

---
EOF
```

- [ ] **Step 5: Create baseline_metrics.json**

```bash
cat > .claude/autonomous-refactor/baseline_metrics.json << 'EOF'
{
  "timestamp": "2026-04-09T00:00:00Z",
  "services": {
    "nemo-claw-orchestrator": {
      "health_status": "unknown",
      "test_pass_rate": 0,
      "coverage_percent": 0,
      "assertion_count": 0,
      "deprecation_warnings": 0
    },
    "scenespeak-agent": {
      "health_status": "unknown",
      "test_pass_rate": 0,
      "coverage_percent": 0,
      "assertion_count": 0,
      "deprecation_warnings": 0
    },
    "sentiment-agent": {
      "health_status": "unknown",
      "test_pass_rate": 0,
      "coverage_percent": 0,
      "assertion_count": 0,
      "deprecation_warnings": 0
    },
    "safety-filter": {
      "health_status": "unknown",
      "test_pass_rate": 0,
      "coverage_percent": 0,
      "assertion_count": 0,
      "deprecation_warnings": 0
    },
    "captioning-agent": {
      "health_status": "unknown",
      "test_pass_rate": 0,
      "coverage_percent": 0,
      "assertion_count": 0,
      "deprecation_warnings": 0
    },
    "audio-controller": {
      "health_status": "unknown",
      "test_pass_rate": 0,
      "coverage_percent": 0,
      "assertion_count": 0,
      "deprecation_warnings": 0
    }
  },
  "overall": {
    "total_services": 6,
    "healthy_services": 0,
    "average_coverage": 0,
    "total_assertions": 0
  }
}
EOF
```

- [ ] **Step 6: Commit Ralph Loop configuration**

```bash
git add .claude/autonomous-refactor/
git commit -m "feat: initialize Ralph Loop autonomous agent configuration

- Add program.md with constitutional constraints
- Add queue.txt for task management
- Add learnings.md for progress tracking
- Add baseline_metrics.json for baseline recording

Active services: 6 (nemo-claw, scenespeak, sentiment, safety, captioning, audio)
Frozen services: 2 (openclaw, bsl)"
```

---

## Task 2: Create Service Health Check Aggregator

**Files:**
- Create: `services/health-aggregator/main.py`
- Create: `services/health-aggregator/requirements.txt`
- Create: `services/health-aggregator/Dockerfile`
- Create: `services/health-aggregator/tests/test_health.py`

- [ ] **Step 1: Create service directory**

```bash
mkdir -p services/health-aggregator/tests
```

- [ ] **Step 2: Write requirements.txt**

```bash
cat > services/health-aggregator/requirements.txt << 'EOF'
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.28.0
pydantic==2.10.0
pytest==8.3.0
pytest-asyncio==0.24.0
EOF
```

- [ ] **Step 3: Write main.py health aggregator**

```bash
cat > services/health-aggregator/main.py << 'EOF'
"""Health Check Aggregator Service

Polls all active services and aggregates their health status.
Provides unified health endpoint for dashboard consumption.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
from typing import Dict, List
from datetime import datetime
import os

app = FastAPI(title="Health Aggregator", version="1.0.0")

# Service configuration
ACTIVE_SERVICES = {
    "nemo-claw-orchestrator": os.getenv("NEMO_CLAW_URL", "http://localhost:8001/health"),
    "scenespeak-agent": os.getenv("SCENESPEAK_URL", "http://localhost:8002/health"),
    "sentiment-agent": os.getenv("SENTIMENT_URL", "http://localhost:8003/health"),
    "safety-filter": os.getenv("SAFETY_URL", "http://localhost:8004/health"),
    "captioning-agent": os.getenv("CAPTIONING_URL", "http://localhost:8005/health"),
    "audio-controller": os.getenv("AUDIO_URL", "http://localhost:8006/health"),
}

FROZEN_SERVICES = {
    "openclaw-orchestrator": os.getenv("OPENCLAW_URL", "http://localhost:8010/health"),
    "bsl-agent": os.getenv("BSL_URL", "http://localhost:8011/health"),
}


class ServiceHealth(BaseModel):
    """Individual service health status"""
    name: str
    status: str  # "healthy", "unhealthy", "unknown", "frozen"
    response_time_ms: float | None = None
    last_check: str
    error: str | None = None


class HealthAggregate(BaseModel):
    """Aggregated health for all services"""
    timestamp: str
    active_services: Dict[str, ServiceHealth]
    frozen_services: Dict[str, ServiceHealth]
    summary: Dict[str, int]


async def check_service_health(name: str, url: str, is_frozen: bool = False) -> ServiceHealth:
    """Check health of a single service"""
    start_time = datetime.now()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                return ServiceHealth(
                    name=name,
                    status="frozen" if is_frozen else "healthy",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now().isoformat()
                )
            else:
                return ServiceHealth(
                    name=name,
                    status="unhealthy",
                    response_time_ms=round(response_time, 2),
                    last_check=datetime.now().isoformat(),
                    error=f"HTTP {response.status_code}"
                )

    except asyncio.TimeoutError:
        return ServiceHealth(
            name=name,
            status="unhealthy",
            last_check=datetime.now().isoformat(),
            error="Timeout"
        )
    except Exception as e:
        return ServiceHealth(
            name=name,
            status="unknown",
            last_check=datetime.now().isoformat(),
            error=str(e)
        )


@app.get("/health")
async def health_aggregate():
    """Get aggregated health status of all services"""

    # Check active services
    active_tasks = [
        check_service_health(name, url, is_frozen=False)
        for name, url in ACTIVE_SERVICES.items()
    ]

    # Check frozen services
    frozen_tasks = [
        check_service_health(name, url, is_frozen=True)
        for name, url in FROZEN_SERVICES.items()
    ]

    active_results = await asyncio.gather(*active_tasks)
    frozen_results = await asyncio.gather(*frozen_tasks)

    active_services = {r.name: r for r in active_results}
    frozen_services = {r.name: r for r in frozen_results}

    # Calculate summary
    healthy_count = sum(1 for s in active_services.values() if s.status == "healthy")
    unhealthy_count = sum(1 for s in active_services.values() if s.status == "unhealthy")
    unknown_count = sum(1 for s in active_services.values() if s.status == "unknown")

    summary = {
        "total_active": len(ACTIVE_SERVICES),
        "healthy": healthy_count,
        "unhealthy": unhealthy_count,
        "unknown": unknown_count,
        "frozen": len(FROZEN_SERVICES)
    }

    return HealthAggregate(
        timestamp=datetime.now().isoformat(),
        active_services=active_services,
        frozen_services=frozen_services,
        summary=summary
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Health Aggregator",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Get aggregated health status"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
EOF
```

- [ ] **Step 4: Write Dockerfile**

```bash
cat > services/health-aggregator/Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8012

CMD ["python", "main.py"]
EOF
```

- [ ] **Step 5: Write test file FIRST (TDD)**

```bash
cat > services/health-aggregator/tests/test_health.py << 'EOF'
"""Tests for health aggregator service"""

import pytest
from httpx import AsyncClient
from main import app, check_service_health


@pytest.mark.asyncio
async def test_health_aggregate_all_healthy(mocker):
    """Test health aggregation when all services are healthy"""

    # Mock successful health checks
    async def mock_check_healthy(name, url, is_frozen=False):
        from main import ServiceHealth
        return ServiceHealth(
            name=name,
            status="frozen" if is_frozen else "healthy",
            response_time_ms=50.0,
            last_check="2026-04-09T12:00:00"
        )

    mocker.patch("main.check_service_health", side_effect=mock_check_healthy)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "timestamp" in data
    assert "active_services" in data
    assert "frozen_services" in data
    assert "summary" in data

    # Check summary counts
    assert data["summary"]["total_active"] == 6
    assert data["summary"]["healthy"] == 6
    assert data["summary"]["unhealthy"] == 0
    assert data["summary"]["frozen"] == 2


@pytest.mark.asyncio
async def test_health_aggregate_mixed_status(mocker):
    """Test health aggregation with mixed service status"""

    call_count = 0

    async def mock_check_mixed(name, url, is_frozen=False):
        from main import ServiceHealth
        nonlocal call_count
        call_count += 1

        # Make every third service unhealthy
        if call_count % 3 == 0:
            return ServiceHealth(
                name=name,
                status="unhealthy",
                response_time_ms=100.0,
                last_check="2026-04-09T12:00:00",
                error="HTTP 500"
            )

        return ServiceHealth(
            name=name,
            status="frozen" if is_frozen else "healthy",
            response_time_ms=50.0,
            last_check="2026-04-09T12:00:00"
        )

    mocker.patch("main.check_service_health", side_effect=mock_check_mixed)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Should have some unhealthy services
    assert data["summary"]["unhealthy"] > 0


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns service info"""

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "Health Aggregator"
    assert "version" in data
    assert "endpoints" in data
EOF
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd services/health-aggregator
pip install -q -r requirements.txt
pytest tests/test_health.py -v

# Expected output: All tests PASS
```

- [ ] **Step 7: Commit health aggregator service**

```bash
git add services/health-aggregator/
git commit -m "feat: add health aggregator service for dashboard polling

- Polls 6 active services + 2 frozen services
- Provides unified /health endpoint
- Returns aggregated status with summary
- Includes tests for aggregation logic"
```

---

## Task 3: Create Dashboard Service

**Files:**
- Create: `services/dashboard/main.py`
- Create: `services/dashboard/requirements.txt`
- Create: `services/dashboard/static/dashboard.html` (SECURE - no innerHTML)
- Create: `services/dashboard/Dockerfile`

- [ ] **Step 1: Create dashboard directory**

```bash
mkdir -p services/dashboard/static
```

- [ ] **Step 2: Write requirements.txt**

```bash
cat > services/dashboard/requirements.txt << 'EOF'
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.28.0
pydantic==2.10.0
jinja2==3.1.4
aiofiles==24.1.0
pytest==8.3.0
pytest-asyncio==0.24.0
EOF
```

- [ ] **Step 3: Write dashboard main.py**

```bash
cat > services/dashboard/main.py << 'EOF'
"""Project Chimera Dashboard

Unified tracking for Ralph Loop progress, service health, and student testing.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import asyncio
from typing import Dict, List
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

app = FastAPI(title="Project Chimera Dashboard", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# External services
HEALTH_AGGREGATOR_URL = os.getenv("HEALTH_AGGREGATOR_URL", "http://localhost:8012/health")
REPO_ROOT = Path(__file__).parent.parent.parent

# Cache for dashboard data
dashboard_cache = {
    "last_update": None,
    "data": None
}


class DashboardData(BaseModel):
    """Complete dashboard data"""
    timestamp: str
    services: Dict[str, Dict]
    git_commits: List[Dict]
    test_summary: Dict[str, int]
    daily_summary: str


async def get_service_health() -> Dict:
    """Get service health from aggregator"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(HEALTH_AGGREGATOR_URL)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Error fetching health: {e}")

    return {
        "active_services": {},
        "frozen_services": {},
        "summary": {}
    }


async def get_git_commits(limit: int = 20) -> List[Dict]:
    """Get recent git commits"""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%H|%an|%s|%ci"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "message": parts[2],
                        "date": parts[3]
                    })

        return commits
    except Exception as e:
        print(f"Error fetching git log: {e}")
        return []


def get_ralph_loop_status() -> Dict:
    """Get Ralph Loop status from files"""
    try:
        # Read learnings
        learnings_path = REPO_ROOT / ".claude" / "autonomous-refactor" / "learnings.md"
        learnings = ""
        if learnings_path.exists():
            learnings = learnings_path.read_text()[-500:]  # Last 500 chars

        # Read queue
        queue_path = REPO_ROOT / ".claude" / "autonomous-refactor" / "queue.txt"
        queue_items = []
        if queue_path.exists():
            for line in queue_path.read_text().split("\n"):
                if line.strip() and not line.startswith("#"):
                    queue_items.append(line)

        # Read baseline
        baseline_path = REPO_ROOT / ".claude" / "autonomous-refactor" / "baseline_metrics.json"
        baseline = {}
        if baseline_path.exists():
            baseline = json.loads(baseline_path.read_text())

        return {
            "learnings_preview": learnings,
            "queue_length": len(queue_items),
            "queue_items": queue_items[:10],  # First 10
            "baseline_metrics": baseline
        }
    except Exception as e:
        print(f"Error reading Ralph Loop status: {e}")
        return {}


async def update_dashboard_data() -> DashboardData:
    """Update and return complete dashboard data"""

    # Get service health
    health_data = await get_service_health()

    # Get git commits
    git_commits = await get_git_commits(20)

    # Get Ralph Loop status
    ralph_loop_status = get_ralph_loop_status()

    # Calculate test summary from health data
    test_summary = {
        "total": len(health_data.get("active_services", {})),
        "healthy": health_data.get("summary", {}).get("healthy", 0),
        "unhealthy": health_data.get("summary", {}).get("unhealthy", 0),
        "unknown": health_data.get("summary", {}).get("unknown", 0)
    }

    # Generate daily summary
    today = datetime.now().strftime("%Y-%m-%d")
    today_commits = [c for c in git_commits if c["date"].startswith(today)]

    daily_summary = f"Today ({today}): {len(today_commits)} commits. "
    daily_summary += f"Services: {test_summary['healthy']}/{test_summary['total']} healthy. "
    daily_summary += f"Ralph Loop queue: {ralph_loop_status.get('queue_length', 0)} tasks."

    return DashboardData(
        timestamp=datetime.now().isoformat(),
        services=health_data,
        git_commits=git_commits,
        test_summary=test_summary,
        daily_summary=daily_summary
    )


@app.get("/api/dashboard", response_model=DashboardData)
async def dashboard_api():
    """API endpoint for dashboard data"""
    data = await update_dashboard_data()
    return data


@app.get("/", response_class=HTMLResponse)
async def dashboard_ui():
    """Render dashboard UI"""

    template_path = Path(__file__).parent / "static" / "dashboard.html"
    template = template_path.read_text()

    return template


@app.get("/health")
async def health():
    """Dashboard health check"""
    return {"status": "healthy", "service": "dashboard"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
EOF
```

- [ ] **Step 4: Write SECURE dashboard HTML template (no innerHTML, uses textContent)**

```bash
cat > services/dashboard/static/dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Chimera Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e1a;
            color: #e0e6ed;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #1e293b; }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header .subtitle { color: #94a3b8; font-size: 14px; }
        .daily-summary {
            background: #1e293b;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border-left: 4px solid #3b82f6;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
        }
        .card h2 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .service-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 12px;
        }
        .service-card {
            background: #0f172a;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #334155;
        }
        .service-card.healthy { border-color: #22c55e; }
        .service-card.unhealthy { border-color: #ef4444; }
        .service-card.unknown { border-color: #f59e0b; }
        .service-card.frozen { border-color: #6366f1; opacity: 0.7; }
        .service-name {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 6px;
            word-break: break-word;
        }
        .service-status {
            font-size: 11px;
            color: #94a3b8;
        }
        .service-status.healthy { color: #22c55e; }
        .service-status.unhealthy { color: #ef4444; }
        .commit-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .commit-item {
            padding: 10px;
            border-bottom: 1px solid #334155;
            font-size: 13px;
        }
        .commit-item:last-child { border-bottom: none; }
        .commit-hash {
            font-family: monospace;
            color: #3b82f6;
            font-size: 11px;
        }
        .commit-message { margin: 4px 0; word-break: break-word; }
        .commit-meta { font-size: 11px; color: #64748b; }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #94a3b8; font-size: 13px; }
        .metric-value { font-weight: 600; }
        .metric-value.healthy { color: #22c55e; }
        .metric-value.unhealthy { color: #ef4444; }
        .queue-item {
            padding: 8px;
            background: #0f172a;
            border-radius: 4px;
            margin-bottom: 8px;
            font-size: 12px;
            font-family: monospace;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.urgent { background: #dc2626; }
        .badge.high { background: #f59e0b; }
        .badge.medium { background: #3b82f6; }
        .badge.frozen { background: #6366f1; }
        #lastUpdate {
            text-align: center;
            color: #64748b;
            font-size: 12px;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 id="title">Project Chimera Dashboard</h1>
            <p class="subtitle" id="subtitle">Ralph Loop Autonomous Development • 8-Week Cycle</p>
        </div>

        <div class="daily-summary">
            <strong>Daily Summary:</strong> <span id="dailySummary">Loading...</span>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Service Health</h2>
                <div class="service-grid" id="serviceGrid">
                    <div class="service-card">
                        <div class="service-name">Loading...</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Test Summary</h2>
                <div id="testSummary">
                    <div class="metric">
                        <span class="metric-label">Total Active Services</span>
                        <span class="metric-value" id="totalServices">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Healthy</span>
                        <span class="metric-value healthy" id="healthyServices">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Unhealthy</span>
                        <span class="metric-value unhealthy" id="unhealthyServices">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Frozen</span>
                        <span class="metric-value" id="frozenServices">-</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Ralph Loop Queue</h2>
                <div id="queueList">
                    <div class="queue-item">Loading...</div>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Recent Git Commits</h2>
                <div class="commit-list" id="commitList">
                    <div class="commit-item">Loading...</div>
                </div>
            </div>
        </div>

        <div id="lastUpdate">Last update: Loading...</div>
    </div>

    <script>
        // Helper function to safely set text content (prevents XSS)
        function setText(elementId, text) {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = text;
            }
        }

        // Helper function to create element with safe content
        function createElementWithContent(tag, className, textContent) {
            const element = document.createElement(tag);
            if (className) element.className = className;
            if (textContent !== undefined) element.textContent = textContent;
            return element;
        }

        async function loadDashboard() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();

                // Update daily summary (using textContent for security)
                setText('dailySummary', data.daily_summary);

                // Update service grid (build DOM safely)
                const serviceGrid = document.getElementById('serviceGrid');
                serviceGrid.innerHTML = ''; // Clear existing

                // Active services
                for (const [name, service] of Object.entries(data.services.active_services || {})) {
                    const card = createElementWithContent('div', 'service-card', '');
                    card.classList.add(service.status || 'unknown');

                    const nameEl = createElementWithContent('div', 'service-name', name);
                    const statusEl = createElementWithContent('div', 'service-status', service.status || 'unknown');
                    statusEl.classList.add(service.status || 'unknown');

                    card.appendChild(nameEl);
                    card.appendChild(statusEl);
                    serviceGrid.appendChild(card);
                }

                // Frozen services
                for (const [name, service] of Object.entries(data.services.frozen_services || {})) {
                    const card = createElementWithContent('div', 'service-card frozen', '');
                    const nameEl = createElementWithContent('div', 'service-name', '');
                    nameEl.textContent = name + ' ';

                    const badge = createElementWithContent('span', 'badge frozen', 'FROZEN');
                    nameEl.appendChild(badge);

                    const statusEl = createElementWithContent('div', 'service-status', service.status || 'unknown');

                    card.appendChild(nameEl);
                    card.appendChild(statusEl);
                    serviceGrid.appendChild(card);
                }

                // Update test summary
                setText('totalServices', data.test_summary.total || 0);
                setText('healthyServices', data.test_summary.healthy || 0);
                setText('unhealthyServices', data.test_summary.unhealthy || 0);
                setText('frozenServices', data.services.frozen_services ? Object.keys(data.services.frozen_services).length : 0);

                // Update commits (build DOM safely)
                const commitList = document.getElementById('commitList');
                commitList.innerHTML = '';

                for (const commit of data.git_commits || []) {
                    const commitItem = createElementWithContent('div', 'commit-item', '');

                    const hashEl = createElementWithContent('div', 'commit-hash', commit.hash);
                    const messageEl = createElementWithContent('div', 'commit-message', commit.message);
                    const metaEl = createElementWithContent('div', 'commit-meta', `${commit.author} • ${commit.date}`);

                    commitItem.appendChild(hashEl);
                    commitItem.appendChild(messageEl);
                    commitItem.appendChild(metaEl);
                    commitList.appendChild(commitItem);
                }

                if (!data.git_commits || data.git_commits.length === 0) {
                    commitList.appendChild(createElementWithContent('div', 'commit-item', 'No commits yet'));
                }

                // Update queue (build DOM safely)
                const queueList = document.getElementById('queueList');
                queueList.innerHTML = '';

                for (const item of (data.services.queue_items || [])) {
                    const priorityMatch = item.match(/\[(urgent|high|medium|low)\]/i);
                    const priority = priorityMatch ? priorityMatch[1].toLowerCase() : 'medium';

                    const queueItem = createElementWithContent('div', 'queue-item', '');
                    const badge = createElementWithContent('span', `badge ${priority}`, priority);
                    queueItem.appendChild(badge);
                    queueItem.appendChild(document.createTextNode(' ' + item));
                    queueList.appendChild(queueItem);
                }

                if (!data.services.queue_items || data.services.queue_items.length === 0) {
                    queueList.appendChild(createElementWithContent('div', 'queue-item', 'Queue empty'));
                }

                // Update timestamp
                setText('lastUpdate', 'Last update: ' + new Date(data.timestamp).toLocaleString());

            } catch (error) {
                console.error('Error loading dashboard:', error);
                setText('dailySummary', 'Error loading dashboard data');
            }
        }

        // Load dashboard on page load
        loadDashboard();

        // Refresh every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
EOF
```

Note: The dashboard HTML now uses:
- `textContent` instead of `innerHTML` for all text updates
- `createElement` and DOM methods instead of HTML strings
- No unsafe HTML insertion, preventing XSS vulnerabilities

- [ ] **Step 5: Write Dockerfile**

```bash
cat > services/dashboard/Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY static/ ./static/

EXPOSE 8013

CMD ["python", "main.py"]
EOF
```

- [ ] **Step 6: Commit dashboard service**

```bash
git add services/dashboard/
git commit -m "feat: add dashboard service for Ralph Loop tracking

- UI shows service health, test summary, commits, queue
- Polls health aggregator every 30s
- Displays Ralph Loop status from files
- Daily summary generation
- SECURE: Uses textContent instead of innerHTML to prevent XSS"
```

---

## Task 4: Create Student Service Assignment Tracker

**Files:**
- Create: `.claude/student-assignments.md`

- [ ] **Step 1: Create assignments tracker file**

```bash
cat > .claude/student-assignments.md << 'EOF'
# Student Service Assignments

**Date**: April 9, 2026
**Status**: Week 1 - Selection Phase

---

## Instructions

Each student should select **2 services** from the 6 active services listed below.

Services are assigned on a first-come, first-served basis. Please add your name next to the services you choose.

---

## Active Services Available for Assignment

1. **Nemo Claw Orchestrator**
   - Location: `services/nemo-claw-orchestrator/`
   - Responsibility: Central coordination and routing
   - Complexity: High (orchestration logic)
   - Student: ___ (OPEN)

2. **SceneSpeak Agent**
   - Location: `services/scenespeak-agent/`
   - Responsibility: Dialogue generation (GLM-4.7)
   - Complexity: High (LLM integration)
   - Student: ___ (OPEN)

3. **Sentiment Agent**
   - Location: `services/sentiment-agent/`
   - Responsibility: Emotion analysis (DistilBERT ML)
   - Complexity: Medium (ML model)
   - Student: ___ (OPEN)

4. **Safety Filter**
   - Location: `services/safety-filter/`
   - Responsibility: Content moderation
   - Complexity: Medium (rule-based)
   - Student: ___ (OPEN)

5. **Captioning Agent**
   - Location: `services/captioning-agent/`
   - Responsibility: Text formatting and accessibility
   - Complexity: Low (text processing)
   - Student: ___ (OPEN)

6. **Audio Controller**
   - Location: `services/audio-controller/`
   - Responsibility: Sound output and integration
   - Complexity: Medium (audio processing)
   - Student: ___ (OPEN)

---

## Student Responsibilities

Once you've selected your 2 services, you are responsible for:

1. **Daily Testing**
   - Run tests for both services daily
   - Test via web interface (Operator Console)
   - Test via CLI interface
   - Document results

2. **Validation**
   - Verify Ralph Loop changes don't break functionality
   - Test new features added by Ralph Loop
   - Report regressions immediately

3. **Bug Reporting**
   - Add issues to `.claude/autonomous-refactor/queue.txt`
   - Tag with urgency: [urgent], [high], [medium], [low]
   - Include steps to reproduce

4. **Improvement Suggestions**
   - Suggest features or enhancements
   - Add to queue.txt for Ralph Loop to implement
   - Discuss with team first

5. **Documentation**
   - Keep service docs up to date
   - Document any manual workarounds
   - Update README for your services

---

## Assignment Log

**When assigning yourself to services, add an entry here:**

### [Student Name] - [Date]

**Services Selected:**
1. [Service Name]
2. [Service Name]

**Contact:** [email/discord/slack]

---

## Current Assignments Summary

| Student | Service 1 | Service 2 | Status |
|---------|-----------|-----------|--------|
| (None) | (Open) | (Open) | Awaiting assignments |

---

## Notes

- Frozen services (OpenClaw, BSL) are NOT available for assignment
- Students can swap services if both parties agree
- If conflicts arise, discuss as team and reassign if needed
- Document any service swaps in this file
EOF
```

- [ ] **Step 2: Commit assignment tracker**

```bash
git add .claude/student-assignments.md
git commit -m "feat: add student service assignment tracker

- 6 active services available for assignment
- Each student selects 2 services
- First-come, first-served basis
- Includes responsibilities and assignment log"
```

---

## Task 5: Update Docker Compose for New Services

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Check if docker-compose.yml exists**

```bash
# Check if docker-compose.yml exists
if [ -f docker-compose.yml ]; then
    echo "Existing docker-compose.yml found"
else
    echo "No docker-compose.yml found, creating new one"
fi
```

- [ ] **Step 2: Add new services to docker-compose.yml**

```bash
# Append or create docker-compose.yml with new services
cat >> docker-compose.yml << 'EOF'

# Health Aggregator Service (Week 1)
health-aggregator:
  build: ./services/health-aggregator
  container_name: chimera-health-aggregator
  ports:
    - "8012:8012"
  environment:
    - NEMO_CLAW_URL=http://nemo-claw-orchestrator:8001/health
    - SCENESPEAK_URL=http://scenespeak-agent:8002/health
    - SENTIMENT_URL=http://sentiment-agent:8003/health
    - SAFETY_URL=http://safety-filter:8004/health
    - CAPTIONING_URL=http://captioning-agent:8005/health
    - AUDIO_URL=http://audio-controller:8006/health
    - OPENCLAW_URL=http://openclaw-orchestrator:8010/health
    - BSL_URL=http://bsl-agent:8011/health
  networks:
    - chimera-network
  restart: unless-stopped

# Dashboard Service (Week 1)
dashboard:
  build: ./services/dashboard
  container_name: chimera-dashboard
  ports:
    - "8013:8013"
  environment:
    - HEALTH_AGGREGATOR_URL=http://health-aggregator:8012/health
  networks:
    - chimera-network
  restart: unless-stopped
  depends_on:
    - health-aggregator
EOF
```

- [ ] **Step 3: Commit docker-compose updates**

```bash
git add docker-compose.yml
git commit -m "feat: add health aggregator and dashboard to docker-compose

- Health aggregator on port 8012
- Dashboard on port 8013
- Both services on chimera-network
- Dashboard depends on health aggregator"
```

---

## Task 6: Run Baseline Tests and Record Metrics

**Files:**
- Create: `scripts/run_baseline_tests.sh`
- Modify: `.claude/autonomous-refactor/baseline_metrics.json`
- Modify: `.claude/autonomous-refactor/learnings.md`

- [ ] **Step 1: Create baseline test runner script**

```bash
cat > scripts/run_baseline_tests.sh << 'EOF'
#!/bin/bash
# Run baseline tests for all active services and record metrics

set -e

echo "=== Project Chimera Baseline Test Runner ==="
echo "Date: $(date -Iseconds)"
echo ""

RESULTS_DIR=".claude/autonomous-refactor/baseline_results"
mkdir -p "$RESULTS_DIR"

# Array of active services
declare -A SERVICES=(
    ["nemo-claw-orchestrator"]="services/nemo-claw-orchestrator"
    ["scenespeak-agent"]="services/scenespeak-agent"
    ["sentiment-agent"]="services/sentiment-agent"
    ["safety-filter"]="services/safety-filter"
    ["captioning-agent"]="services/captioning-agent"
    ["audio-controller"]="services/audio-controller"
)

TOTAL_TESTS=0
PASSED_TESTS=0
TOTAL_ASSERTIONS=0

echo "Testing services..."
echo "===================="

for SERVICE_NAME in "${!SERVICES[@]}"; do
    SERVICE_PATH="${SERVICES[$SERVICE_NAME]}"
    echo ""
    echo "Testing: $SERVICE_NAME"
    echo "Path: $SERVICE_PATH"

    if [ ! -d "$SERVICE_PATH" ]; then
        echo "  ⚠️  Service directory not found, skipping"
        continue
    fi

    cd "$SERVICE_PATH" || continue

    # Check for tests directory
    if [ ! -d "tests" ] && [ ! -d "test" ]; then
        echo "  ⚠️  No tests directory found"
        cd - > /dev/null
        continue
    fi

    # Run pytest with coverage
    if pytest -v --tb=short --cov=. --cov-report=term-missing 2>&1 | tee "$RESULTS_DIR/${SERVICE_NAME}_baseline.txt"; then
        echo "  ✅ Tests passed"
        ((PASSED_TESTS++))
    else
        echo "  ❌ Tests failed"
    fi

    ((TOTAL_TESTS++))

    cd - > /dev/null
done

echo ""
echo "=== Baseline Summary ==="
echo "Total services tested: $TOTAL_TESTS"
echo "Services passing: $PASSED_TESTS"
echo ""

# Update baseline metrics JSON
python3 << PYTHON_SCRIPT
import json
from pathlib import Path
from datetime import datetime

baseline_file = Path(".claude/autonomous-refactor/baseline_metrics.json")
results_dir = Path(".claude/autonomous-refactor/baseline_results")

# Read existing baseline
if baseline_file.exists():
    with open(baseline_file) as f:
        baseline = json.load(f)
else:
    baseline = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "overall": {}
    }

# Update timestamp
baseline["timestamp"] = datetime.now().isoformat()
baseline["overall"]["total_services_tested"] = $TOTAL_TESTS
baseline["overall"]["services_passing"] = $PASSED_TESTS

# Parse results from each service log
for result_file in results_dir.glob("*_baseline.txt"):
    service_name = result_file.stem.replace("_baseline", "")

    if service_name not in baseline["services"]:
        baseline["services"][service_name] = {}

    # Look for coverage percentage
    import re
    content = result_file.read_text()
    coverage_match = re.search(r'(\d+)%', content)
    if coverage_match:
        baseline["services"][service_name]["coverage_percent"] = int(coverage_match.group(1))

    # Look for passed/failed tests
    passed_match = re.search(r'(\d+) passed', content)
    if passed_match:
        baseline["services"][service_name]["tests_passed"] = int(passed_match.group(1))

    failed_match = re.search(r'(\d+) failed', content)
    if failed_match:
        baseline["services"][service_name]["tests_failed"] = int(failed_match.group(1))

# Save updated baseline
with open(baseline_file, 'w') as f:
    json.dump(baseline, f, indent=2)

print(f"✅ Updated baseline_metrics.json")
print(json.dumps(baseline, indent=2))
PYTHON_SCRIPT

echo ""
echo "Baseline complete. Results saved to:"
echo "  - .claude/autonomous-refactor/baseline_metrics.json"
echo "  - .claude/autonomous-refactor/baseline_results/"
EOF

chmod +x scripts/run_baseline_tests.sh
```

- [ ] **Step 2: Run baseline tests**

```bash
./scripts/run_baseline_tests.sh
```

- [ ] **Step 3: Update learnings.md with baseline results**

```bash
# Add baseline results to learnings
cat >> .claude/autonomous-refactor/learnings.md << 'EOF'

### Baseline Test Results - April 9, 2026

**Tests Run:**
- Total services: 6
- Services tested: [actual count from run]
- Services passing: [actual count from run]
- Services failing: [actual count from run]

**Coverage Baseline:**
- nemo-claw-orchestrator: [X]%
- scenespeak-agent: [X]%
- sentiment-agent: [X]%
- safety-filter: [X]%
- captioning-agent: [X]%
- audio-controller: [X]%

**Next Steps:**
- Prioritize services with lowest coverage
- Add tests to untested services
- Fix failing tests
- Document any blockers
EOF
```

- [ ] **Step 4: Commit baseline test infrastructure**

```bash
git add scripts/run_baseline_tests.sh .claude/autonomous-refactor/baseline_metrics.json .claude/autonomous-refactor/learnings.md
git commit -m "feat: add baseline test runner and record initial metrics

- Script runs tests on all 6 active services
- Records coverage and pass/fail rates
- Updates baseline_metrics.json
- Results saved to baseline_results/
- Week 1 foundation complete"
```

---

# WEEK 2-8: Remaining Implementation

**Note:** The implementation plan continues with:
- Week 2-3: Ralph Loop Iteration 1 (Autonomous agent improvements)
- Week 4-5: Ralph Loop Iteration 2 (Integration tests)
- Week 6-7: Continuous Loop Implementation (CLI interface)
- Week 8: Final Integration & Demo (30-minute test, documentation, release)

**Remaining tasks to be executed by Ralph Loop autonomous agent following the same pattern as Week 1 tasks.**

---

# IMPLEMENTATION COMPLETE

**Week 1 Foundation:** All 6 tasks defined with complete code
**Remaining Weeks:** Ralph Loop continues autonomous improvements

**Total Tasks:** 6 (Week 1) + autonomous iterations (Weeks 2-8)
**Estimated Duration:** 8 weeks
**Success Criteria:** All Week 8 completion requirements met

**Plan Location:** `docs/superpowers/plans/2026-04-09-ralph-loop-driven-service-improvement.md`
EOF

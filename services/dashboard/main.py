"""
Project Chimera Dashboard Service
Tracks Ralph Loop progress, service health, git commits, and student testing.
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from prometheus_api_client import PrometheusConnect


class MetricsCache:
    """Simple in-memory cache for metrics with staleness tracking."""

    _cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
    _timestamps: Dict[str, datetime] = {}

    @classmethod
    def get(cls, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value if not expired (30s TTL)."""
        if key not in cls._cache:
            return None

        age = datetime.now() - cls._timestamps.get(key, datetime.now())
        if age > timedelta(seconds=30):
            return None

        return cls._cache[key].copy()

    @classmethod
    def set(cls, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache with current timestamp."""
        cls._cache[key] = value.copy()
        cls._timestamps[key] = datetime.now()

    @classmethod
    def mark_stale(cls, key: str) -> None:
        """Mark cached value as stale."""
        if key in cls._cache:
            cls._cache[key]["stale"] = True


# Initialize Prometheus client
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
prometheus = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)


async def query_prometheus(
    query: str,
    span: str = "5m",
    step: str = "15s"
) -> Optional[Dict[str, Any]]:
    """Query Prometheus with caching and error handling.

    Args:
        query: PromQL query string
        span: Time range (e.g., "5m", "1h")
        step: Query step interval

    Returns:
        Dict with 'value' (current value) and 'data' (time series), or None
    """
    cache_key = f"prom:{query}:{span}"

    # Check cache first
    cached = MetricsCache.get(cache_key)
    if cached is not None:
        return cached

    try:
        # Query Prometheus
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=5)  # Simplified parsing

        result = prometheus.custom_query_range(
            query=query,
            start_time=start_time,
            end_time=end_time,
            step=step
        )

        if not result:
            return {"value": 0.0, "data": [], "stale": False}

        # Extract latest value
        latest = result[-1]
        value = float(latest.value[1]) if latest.value[1] else 0.0

        response = {
            "value": round(value, 2),
            "data": [{"timestamp": r.value[0], "value": float(r.value[1])} for r in result],
            "stale": False
        }

        # Cache the result
        MetricsCache.set(cache_key, response)
        return response

    except (TimeoutError, ConnectionError) as e:
        # Return cached with stale flag
        MetricsCache.mark_stale(cache_key)
        cached = MetricsCache.get(cache_key)
        if cached:
            return cached
        return {"value": 0.0, "data": [], "stale": True, "error": str(e)}
    except Exception as e:
        return {"value": 0.0, "data": [], "stale": True, "error": str(e)}


# Configuration
app = FastAPI(title="Project Chimera Dashboard")
HEALTH_AGGREGATOR_URL = os.getenv(
    "HEALTH_AGGREGATOR_URL",
    "http://localhost:8012/health"
)

# Calculate repository root
REPO_ROOT = Path(__file__).parent.parent.parent
RALPH_LOOP_DIR = REPO_ROOT / "services" / "ralph-loop"

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Models
class DashboardData(BaseModel):
    timestamp: str
    services: Dict[str, Dict[str, str]]
    git_commits: List[Dict[str, str]]
    test_summary: Dict[str, int]
    daily_summary: str


# Helper functions
async def get_service_health() -> Dict[str, Dict[str, str]]:
    """Fetch service health status from health aggregator."""
    services = {
        "dashboard": {"status": "healthy", "url": "localhost:8013"},
        "health_aggregator": {"status": "unknown", "url": "localhost:8012"},
        "ralph_loop": {"status": "unknown", "url": "localhost:8010"},
        "sentiment": {"status": "unknown", "url": "localhost:8008"},
        "testing": {"status": "unknown", "url": "localhost:8011"},
        "chimera_core": {"status": "unknown", "url": "localhost:8000"},
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(HEALTH_AGGREGATOR_URL)
            if response.status_code == 200:
                data = response.json()
                for service_name, service_data in data.get("services", {}).items():
                    if service_name in services:
                        services[service_name]["status"] = service_data.get("status", "unknown")
    except Exception as e:
        print(f"Error fetching health data: {e}")

    return services


async def get_git_commits() -> List[Dict[str, str]]:
    """Get recent git commits."""
    commits = []
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n")[:20]:
                if line:
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1]
                        })
                    else:
                        commits.append({
                            "hash": line[:7],
                            "message": line[8:] if len(line) > 8 else ""
                        })
    except Exception as e:
        print(f"Error fetching git commits: {e}")

    return commits


def get_ralph_loop_status() -> Dict[str, any]:
    """Read Ralph Loop status files."""
    status = {
        "queue": [],
        "learnings": "",
        "metrics": {}
    }

    try:
        # Read queue.txt
        queue_file = RALPH_LOOP_DIR / "queue.txt"
        if queue_file.exists():
            with open(queue_file, 'r') as f:
                status["queue"] = [line.strip() for line in f if line.strip()]

        # Read learnings.md (last 500 chars)
        learnings_file = RALPH_LOOP_DIR / "learnings.md"
        if learnings_file.exists():
            with open(learnings_file, 'r') as f:
                content = f.read()
                status["learnings"] = content[-500:] if len(content) > 500 else content

        # Read baseline_metrics.json
        metrics_file = RALPH_LOOP_DIR / "baseline_metrics.json"
        if metrics_file.exists():
            import json
            with open(metrics_file, 'r') as f:
                status["metrics"] = json.load(f)
    except Exception as e:
        print(f"Error reading Ralph Loop status: {e}")

    return status


async def get_test_summary() -> Dict[str, int]:
    """Get test summary from testing service."""
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8011/health")
            if response.status_code == 200:
                data = response.json()
                summary["total"] = data.get("total_tests", 0)
                summary["passed"] = data.get("passed_tests", 0)
                summary["failed"] = data.get("failed_tests", 0)
                summary["skipped"] = data.get("skipped_tests", 0)
    except Exception as e:
        print(f"Error fetching test summary: {e}")

    return summary


def generate_daily_summary(services: Dict, test_summary: Dict, ralph_status: Dict) -> str:
    """Generate daily summary string."""
    healthy_count = sum(1 for s in services.values() if s.get("status") == "healthy")
    total_count = len(services)
    queue_length = len(ralph_status.get("queue", []))
    test_pass_rate = (
        f"{(test_summary['passed'] / test_summary['total'] * 100):.1f}%"
        if test_summary['total'] > 0 else "N/A"
    )

    return (
        f"Services: {healthy_count}/{total_count} healthy | "
        f"Tests: {test_summary['passed']}/{test_summary['total']} passed ({test_pass_rate}) | "
        f"Ralph Queue: {queue_length} items | "
        f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


async def update_dashboard_data() -> DashboardData:
    """Aggregate all dashboard data."""
    services = await get_service_health()
    git_commits = await get_git_commits()
    test_summary = await get_test_summary()
    ralph_status = get_ralph_loop_status()
    daily_summary = generate_daily_summary(services, test_summary, ralph_status)

    return DashboardData(
        timestamp=datetime.now().isoformat(),
        services=services,
        git_commits=git_commits,
        test_summary=test_summary,
        daily_summary=daily_summary
    )


# Routes
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dashboard"}


@app.get("/api/dashboard")
async def api_dashboard():
    """Dashboard data API endpoint."""
    return await update_dashboard_data()


@app.get("/api/metrics/summary")
async def metrics_summary():
    """Combined system + app metrics summary."""
    # Query system metrics from Prometheus
    cpu_usage = await query_prometheus("system.cpu.total_pct")
    gpu_usage = await query_prometheus("nvidia_gpu_utilization")
    mem_usage = await query_prometheus("system.memory.used_pct")

    # Get application health from existing aggregator
    app_health = await get_service_health()

    return {
        "system": {
            "cpu": cpu_usage or {"value": 0, "stale": True},
            "gpu": gpu_usage or {"value": 0, "stale": True},
            "memory": mem_usage or {"value": 0, "stale": True}
        },
        "applications": app_health,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve dashboard HTML page."""
    index_file = static_dir / "dashboard.html"
    if index_file.exists():
        with open(index_file, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)

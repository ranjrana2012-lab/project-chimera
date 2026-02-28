"""API routes for Dashboard."""
from fastapi import APIRouter, Query, WebSocket
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


class RunSummary(BaseModel):
    """Summary of a test run."""
    run_id: str
    commit_sha: str
    branch: str
    status: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: int
    coverage_pct: float
    mutation_score: float


@router.get("/runs")
async def list_runs(
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0)
):
    """List test runs."""
    # TODO: Query from database
    return {
        "runs": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/runs/{run_id}/summary")
async def get_run_summary(run_id: str) -> RunSummary:
    """Get summary statistics for a test run."""
    # TODO: Query from database and calculate

    # Mock data for now
    return RunSummary(
        run_id=run_id,
        commit_sha="abc123",
        branch="main",
        status="completed",
        total=500,
        passed=485,
        failed=12,
        skipped=3,
        duration_seconds=245,
        coverage_pct=94.2,
        mutation_score=97.8
    )


@router.get("/trends")
async def get_trends(
    metric: str = Query(..., description="Metric to trend"),
    days: int = Query(30, ge=1, le=365, description="Number of days")
):
    """Get historical trend data for a metric."""
    # TODO: Query aggregated daily summaries

    # Mock data
    trends = []
    for i in range(min(days, 30)):
        trends.append({
            "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "value": 90 + (i % 8)
        })

    return {"metric": metric, "days": days, "data": trends}


@router.websocket("/ws/runs/{run_id}")
async def websocket_run_updates(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for live test execution updates."""
    await websocket.accept()

    try:
        await websocket.send_json({"type": "connected", "run_id": run_id})
        await websocket.close()
    except Exception:
        pass

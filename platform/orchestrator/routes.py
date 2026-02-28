"""API routes for Test Orchestrator."""
from fastapi import APIRouter, BackgroundTasks, Query, WebSocket
from pydantic import BaseModel
from typing import List, Optional
from orchestrator.scheduler import TestScheduler
from orchestrator.executor import ParallelExecutor

router = APIRouter(prefix="/api/v1", tags=["orchestrator"])
scheduler = TestScheduler()
executor = ParallelExecutor()


class StartRunRequest(BaseModel):
    """Request to start a test run."""
    commit_sha: str
    branch: str
    test_filter: Optional[List[str]] = None
    full_suite: bool = True


class RunResponse(BaseModel):
    """Response for starting a test run."""
    run_id: str
    status: str
    message: str


@router.post("/run/start", response_model=RunResponse)
async def start_test_run(request: StartRunRequest, background_tasks: BackgroundTasks):
    """Start a new test run for a commit."""

    # Create scheduled run
    run = await scheduler.schedule_run(
        commit_sha=request.commit_sha,
        branch=request.branch,
        test_filter=request.test_filter,
        full_suite=request.full_suite
    )

    return RunResponse(
        run_id=run.id,
        status=run.status,
        message=f"Test run {run.id} started for commit {request.commit_sha}"
    )


@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    """Get status of a test run."""
    # TODO: Implement fetching from database
    return {"run_id": run_id, "status": "running", "progress": 0}


@router.get("/tests/discover")
async def discover_tests(path: str = Query("tests/", description="Path to search for tests")):
    """Discover all tests in the codebase."""
    from orchestrator.discovery import TestDiscovery

    discovery = TestDiscovery()
    tests = await discovery.discover_tests(path)

    return {
        "total": len(tests),
        "tests": [t.test_id for t in tests[:100]]  # First 100
    }


@router.websocket("/ws/run/{run_id}")
async def websocket_run_updates(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for live test execution updates."""
    await websocket.accept()

    try:
        # For now, just send a simple message
        await websocket.send_json({"type": "connected", "run_id": run_id})
        await websocket.close()
    except Exception:
        pass

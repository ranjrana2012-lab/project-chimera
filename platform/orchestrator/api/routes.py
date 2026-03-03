"""
REST API for Test Orchestrator.

Provides endpoints for test execution and results.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy classes for degraded mode
    class FastAPI:
        pass
    class HTTPException(Exception):
        pass
    class BackgroundTasks:
        pass
    class Query:
        def __init__(self, default=None, **kwargs):
            self.default = default

from core.discovery import TestDiscovery
from core.executor import ParallelExecutor, ExecutionConfig
from core.aggregator import ResultAggregator
from storage.history import TestHistoryStorage, TestRunRecord

logger = logging.getLogger(__name__)


# Pydantic models for API
class RunTestsRequest(BaseModel):
    """Request to run tests."""
    services: Optional[List[str]] = Field(default=None, description="Services to test (empty = all)")
    test_pattern: Optional[str] = Field(default=None, description="Test pattern filter")
    parallel: bool = Field(default=True, description="Run tests in parallel")
    max_workers: int = Field(default=4, ge=1, le=8, description="Max parallel workers")
    timeout: int = Field(default=300, ge=10, description="Per-service timeout (seconds)")
    coverage: bool = Field(default=False, description="Enable coverage collection")

    model_config = {"extra": "allow"}


class TestRunResponse(BaseModel):
    """Response for test run initiation."""
    run_id: str
    status: str
    message: str


class TestResultResponse(BaseModel):
    """Response for test results."""
    run_id: str
    status: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    success_rate: float
    by_service: Dict[str, Any]
    timestamp: str


class TestListResponse(BaseModel):
    """Response for test list."""
    services: Dict[str, int]
    total_tests: int
    timestamp: str


# Global state
test_runs: Dict[str, Dict[str, Any]] = {}
discovery: Optional[TestDiscovery] = None
executor: Optional[ParallelExecutor] = None
aggregator: Optional[ResultAggregator] = None
storage: Optional[TestHistoryStorage] = None


def create_app(
    services_path: str = "services",
    db_config: Optional[Dict[str, Any]] = None
) -> FastAPI:
    """
    Create FastAPI application.

    Args:
        services_path: Path to services directory
        db_config: Optional database configuration

    Returns:
        FastAPI application
    """
    if not FASTAPI_AVAILABLE:
        logger.error("FastAPI not available - cannot create API")
        return None  # type: ignore

    global discovery, executor, aggregator, storage

    app = FastAPI(
        title="Test Orchestrator API",
        description="REST API for test execution and results",
        version="1.0.0"
    )

    # Initialize components
    discovery = TestDiscovery(services_path=services_path)
    executor = ParallelExecutor(services_path=services_path)
    aggregator = ResultAggregator()

    if db_config:
        storage = TestHistoryStorage(**db_config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager."""
        logger.info("Test Orchestrator API starting")
        yield
        logger.info("Test Orchestrator API shutting down")
        if storage:
            storage.close()

    app.router.lifespan_context = lifespan

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "Test Orchestrator API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @app.get("/api/v1/tests", response_model=TestListResponse)
    async def list_tests():
        """List all discovered tests."""
        catalog = discovery.build_catalog()

        services = {}
        for service_name, service_tests in catalog.services.items():
            services[service_name] = service_tests.total_count

        return TestListResponse(
            services=services,
            total_tests=catalog.total_tests,
            timestamp=catalog.discovered_at
        )

    @app.post("/api/v1/run-tests", response_model=TestRunResponse)
    async def run_tests(request: RunTestsRequest, background_tasks: BackgroundTasks):
        """Run tests and return run ID."""
        import uuid

        run_id = f"run-{uuid.uuid4().hex[:8]}"

        # Store run info
        test_runs[run_id] = {
            "run_id": run_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "request": request.model_dump()
        }

        # Execute tests in background
        background_tasks.add_task(
            execute_tests_background,
            run_id,
            request
        )

        return TestRunResponse(
            run_id=run_id,
            status="running",
            message=f"Test execution started for {len(request.services) if request.services else 'all'} services"
        )

    @app.get("/api/v1/results/{run_id}", response_model=TestResultResponse)
    async def get_results(run_id: str):
        """Get results for a test run."""
        if run_id not in test_runs:
            raise HTTPException(status_code=404, detail="Run not found")

        run_info = test_runs[run_id]

        if run_info["status"] == "running":
            raise HTTPException(status_code=202, detail="Tests still running")

        return TestResultResponse(
            run_id=run_id,
            status=run_info["status"],
            total_tests=run_info.get("total_tests", 0),
            passed=run_info.get("passed", 0),
            failed=run_info.get("failed", 0),
            skipped=run_info.get("skipped", 0),
            duration_seconds=run_info.get("duration_seconds", 0.0),
            success_rate=run_info.get("success_rate", 0.0),
            by_service=run_info.get("by_service", {}),
            timestamp=run_info.get("completed_at", run_info["started_at"])
        )

    @app.get("/api/v1/status")
    async def get_status():
        """Get status of all test runs."""
        return {
            "active_runs": len([r for r in test_runs.values() if r["status"] == "running"]),
            "total_runs": len(test_runs),
            "runs": list(test_runs.keys())
        }

    @app.delete("/api/v1/results/{run_id}")
    async def delete_results(run_id: str):
        """Delete test run results."""
        if run_id not in test_runs:
            raise HTTPException(status_code=404, detail="Run not found")

        del test_runs[run_id]

        if storage:
            storage.delete_run(run_id)

        return {"message": f"Run {run_id} deleted"}

    return app


async def execute_tests_background(
    run_id: str,
    request: RunTestsRequest
) -> None:
    """
    Execute tests in background.

    Args:
        run_id: Run identifier
        request: Test run request
    """
    global executor, aggregator, storage

    logger.info(f"Starting background test execution for {run_id}")

    try:
        # Build execution config
        config = ExecutionConfig(
            max_workers=request.max_workers,
            service_isolation=True,
            timeout_seconds=request.timeout,
            enable_coverage=request.coverage,
            parallel=request.parallel
        )

        # Update executor config
        executor.config = config

        # Execute tests
        results = executor.execute_all(
            services=request.services,
            test_pattern=request.test_pattern
        )

        # Aggregate results
        aggregated = aggregator.aggregate_run(run_id, results)

        # Update run info
        test_runs[run_id].update({
            "status": "completed" if all(r.success for r in results.values()) else "failed",
            "total_tests": aggregated.total_tests,
            "passed": aggregated.passed,
            "failed": aggregated.failed,
            "skipped": aggregated.skipped,
            "duration_seconds": aggregated.duration_seconds,
            "success_rate": aggregated.success_rate,
            "by_service": {
                svc: r.to_dict()
                for svc, r in results.items()
            },
            "completed_at": datetime.now(timezone.utc).isoformat()
        })

        # Store in database if available
        if storage:
            # Store run record
            run_record = TestRunRecord(
                run_id=run_id,
                timestamp=test_runs[run_id]["started_at"],
                total_tests=aggregated.total_tests,
                passed=aggregated.passed,
                failed=aggregated.failed,
                skipped=aggregated.skipped,
                duration_seconds=aggregated.duration_seconds
            )
            storage.store_run(run_record)

            # Store individual results
            from storage.history import TestResultRecord
            result_records = []
            for service, result in results.items():
                for test_name in result.output.split():  # Simplified - would parse actual results
                    if test_name.startswith("test_"):
                        result_records.append(
                            TestResultRecord(
                                run_id=run_id,
                                service=service,
                                test_name=test_name,
                                status="passed" if result.success else "failed",
                                duration_ms=int(result.duration_seconds * 1000)
                            )
                        )
                        break  # Just one per service for now

            if result_records:
                storage.store_results(result_records)

        logger.info(f"Background test execution completed for {run_id}")

    except Exception as e:
        logger.error(f"Error in background execution for {run_id}: {e}")
        test_runs[run_id].update({
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat()
        })


# Convenience function to get app instance
_app_instance = None

def get_app(
    services_path: str = "services",
    db_config: Optional[Dict[str, Any]] = None
) -> Optional[FastAPI]:
    """Get or create app instance."""
    global _app_instance

    if _app_instance is None:
        _app_instance = create_app(services_path, db_config)

    return _app_instance

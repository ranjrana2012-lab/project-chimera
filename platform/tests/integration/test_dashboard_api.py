"""Integration tests for Dashboard API."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from httpx import AsyncClient, ASGITransport
from dashboard.main import dashboard_app


@pytest.mark.asyncio
async def test_get_runs_lists_test_runs():
    """Test GET /api/v1/runs lists test runs."""
    transport = ASGITransport(app=dashboard_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/runs?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "runs" in data


@pytest.mark.asyncio
async def test_get_run_summary():
    """Test GET /api/v1/runs/{run_id}/summary returns summary."""
    transport = ASGITransport(app=dashboard_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        run_id = "test-run-id"
        response = await client.get(f"/api/v1/runs/{run_id}/summary")

        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert "total" in data
        assert "coverage_pct" in data


@pytest.mark.asyncio
async def test_health_check():
    """Test GET /health returns health status."""
    transport = ASGITransport(app=dashboard_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dashboard"

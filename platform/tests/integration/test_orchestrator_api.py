"""Integration tests for Orchestrator API."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from httpx import AsyncClient, ASGITransport
from orchestrator.main import orchestrator_app

@pytest.mark.asyncio
async def test_post_run_starts_test_run():
    """Test POST /api/v1/run/start starts a test run."""
    transport = ASGITransport(app=orchestrator_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/run/start",
            json={
                "commit_sha": "abc123",
                "branch": "main"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_get_discover_tests():
    """Test GET /api/v1/tests/discover lists tests."""
    transport = ASGITransport(app=orchestrator_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tests/discover?path=tests/")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] > 0

@pytest.mark.asyncio
async def test_health_check():
    """Test GET /health returns health status."""
    transport = ASGITransport(app=orchestrator_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "orchestrator"

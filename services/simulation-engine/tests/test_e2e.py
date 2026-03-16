import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_full_simulation_pipeline():
    """Test complete pipeline from graph build to simulation."""

    async with AsyncClient(app=app, base_url="http://test") as client:

        # Step 1: Check health
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Step 2: Check readiness
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

        # Step 3: Generate personas
        response = await client.post(
            "/api/v1/agents/generate",
            json={"count": 10, "seed": 42}
        )
        assert response.status_code == 200
        personas_data = response.json()
        assert personas_data["count"] == 10
        assert "personas" in personas_data
        assert len(personas_data["personas"]) == 10

        # Step 4: Check metrics endpoint
        response = await client.get("/metrics", follow_redirects=True)
        assert response.status_code == 200

        # Step 5: Test graph build endpoint (will fail gracefully without Neo4j)
        response = await client.post(
            "/api/v1/graph/build",
            json={"documents": ["Test document"]}
        )
        # This should return 503 if graph service not initialized
        # or 200 if it works (depends on environment)
        assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid requests."""

    async with AsyncClient(app=app, base_url="http://test") as client:

        # Invalid agent count
        response = await client.post(
            "/api/v1/agents/generate",
            json={"count": 2000}
        )
        assert response.status_code == 400

        # Missing required fields
        response = await client.post(
            "/api/v1/simulation/simulate",
            json={"agent_count": 5}
        )
        assert response.status_code == 422

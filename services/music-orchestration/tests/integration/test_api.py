import pytest
from httpx import AsyncClient, ASGITransport

from music_orchestration.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_generate_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/music/generate",
            json={
                "prompt": "upbeat electronic",
                "use_case": "marketing",
                "duration_seconds": 30
            },
            headers={"Authorization": "Bearer test-token"}
        )

    assert response.status_code in [200, 202]

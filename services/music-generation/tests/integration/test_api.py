import pytest
from httpx import AsyncClient, ASGITransport

from music_generation.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_generate_endpoint():
    # Manually trigger lifespan for testing
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/generate", json={
                "model_name": "musicgen",
                "prompt": "upbeat electronic",
                "duration_seconds": 30
            })

        assert response.status_code == 200
        assert "request_id" in response.json()

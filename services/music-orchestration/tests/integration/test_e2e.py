import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from music_orchestration.main import app


@pytest.mark.asyncio
async def test_full_generation_flow():
    """Test complete flow from request to response"""

    # 1. Generate music
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/music/generate",
            json={
                "prompt": "test upbeat music",
                "use_case": "marketing",
                "duration_seconds": 30
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code in [200, 202]
        data = response.json()
        assert "request_id" in data

        # 2. Check status (if generating)
        if data["status"] == "generating":
            status_response = await client.get(f"/api/v1/music/{data['music_id']}")
            assert status_response.status_code == 200

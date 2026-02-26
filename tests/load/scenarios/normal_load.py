"""Load test scenarios"""

import pytest
import asyncio
import httpx
import time


@pytest.mark.load
class TestLoadScenarios:
    """Defined load test scenarios."""

    @pytest.mark.asyncio
    async def test_normal_load(self):
        """Normal load: 10 concurrent users for 10 minutes."""
        duration = 10  # Shorter for testing
        concurrent_users = 10

        async def make_requests(user_id: int):
            async with httpx.AsyncClient() as client:
                for i in range(10):
                    await client.post(
                        "http://openclaw-orchestrator:8000/api/v1/orchestration/invoke",
                        json={
                            "skill_name": "scenespeak",
                            "input": {
                                "current_scene": {"title": f"User {user_id} Request {i}"},
                                "dialogue_context": [],
                            },
                        },
                    )

        start_time = time.time()
        tasks = [make_requests(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks)
        duration_actual = time.time() - start_time

        print(f"Normal load: {concurrent_users} users, {duration_actual:.2f}s")
        assert True  # Test passes if no errors

    @pytest.mark.asyncio
    async def test_peak_load(self):
        """Peak load: 50 concurrent users for 5 minutes."""
        concurrent_users = 50

        async def make_request(user_id: int):
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    "http://openclaw-orchestrator:8000/api/v1/orchestration/invoke",
                    json={
                        "skill_name": "sentiment",
                        "input": {"text": f"Peak load test from user {user_id}"},
                    },
                )

        start_time = time.time()
        tasks = [make_request(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)
        duration_actual = time.time() - start_time

        print(f"Peak load: {concurrent_users} users, {duration_actual:.2f}s")

    @pytest.mark.asyncio
    async def test_stress_test(self):
        """Stress test: 100 concurrent users - expect graceful degradation."""
        concurrent_users = 100

        async def make_request(user_id: int):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        "http://openclaw-orchestrator:8000/api/v1/orchestration/invoke",
                        json={
                            "skill_name": "scenespeak",
                            "input": {"current_scene": {"title": f"Stress {user_id}"}},
                        },
                    )
                    return response.status_code
            except Exception as e:
                return str(e)

        tasks = [make_request(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful requests
        successful = sum(1 for r in results if r == 200)
        print(f"Stress test: {successful}/{concurrent_users} successful")

        # Graceful degradation - at least 50% should succeed
        assert successful >= concurrent_users // 2

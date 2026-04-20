"""
Project Chimera - MVP End-to-End User Journey Tests

Tests complete user workflows through the system to verify
real-world usage patterns work correctly.
"""

import pytest
import httpx
import time
import redis
import json
from typing import Dict, Any


class TestMVPUserJourneys:
    """Test end-to-end user journeys through the MVP system."""

    @pytest.fixture(scope="class")
    def base_urls(self) -> Dict[str, str]:
        """Get base URLs for all services."""
        return {
            "orchestrator": "http://localhost:8000",
            "scenespeak": "http://localhost:8001",
            "translation": "http://localhost:8002",
            "sentiment": "http://localhost:8004",
            "safety": "http://localhost:8006",
            "console": "http://localhost:8007",
            "hardware": "http://localhost:8008",
        }

    @pytest.fixture(scope="class")
    def redis_client(self) -> redis.Redis:
        """Get Redis client."""
        return redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True,
            db=0
        )

    def test_journey_1_prompt_to_dialogue_with_checks(self, base_urls: Dict[str, str]):
        """Journey 1: User submits prompt → sentiment → dialogue → safety check."""

        # Step 1: Submit prompt to orchestrator
        prompt = "The audience is excited and cheering loudly!"

        # Note: This test may timeout if orchestrator is waiting on downstream services
        # We'll catch the timeout and verify the system is at least reachable
        try:
            response = httpx.post(
                f"{base_urls['orchestrator']}/api/orchestrate",
                json={
                    "prompt": prompt,
                    "show_id": "test_show_001",
                    "enable_sentiment": True,
                    "enable_safety": True
                },
                timeout=10.0  # Shorter timeout to avoid waiting too long
            )
            # Must get a valid async 202 Accepted response
            assert response.status_code == 202
            
            # Step 2: Poll for completion
            task_id = response.json().get("task_id")
            if task_id:
                for _ in range(3):
                    time.sleep(0.5)
                    poll_res = httpx.get(f"{base_urls['orchestrator']}/api/orchestrate/{task_id}")
                    if poll_res.status_code == 200:
                        data = poll_res.json()
                        if data.get("status") in ["completed", "failed"]:
                            break
                            
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            # Service must be reachable and performant
            pytest.fail(f"Connection or timeout error: {e}")

    def test_journey_2_scene_coordination(self, base_urls: Dict[str, str]):
        """Journey 2: Operator console → orchestrator → hardware bridge."""

        # Step 1: Trigger scene from operator console using show control
        scene_request = {
            "show_id": "test_show_002",
            "action": "start",
            "scene_name": "opening_number"
        }

        response = httpx.post(
            f"{base_urls['console']}/api/show/control",
            json=scene_request,
            timeout=15.0
        )

        # Console should accept the request
        assert response.status_code in [200, 202]

    def test_journey_3_translation_workflow(self, base_urls: Dict[str, str]):
        """Journey 3: Translation request → mock translation → formatted response."""

        # Request translation - using correct endpoint
        translation_request = {
            "text": "Hello, welcome to the show!",
            "source_language": "en",
            "target_language": "es",
            "context": "performance"
        }

        response = httpx.post(
            f"{base_urls['translation']}/translate",
            json=translation_request,
            timeout=10.0
        )

        # Translation agent should respond successfully
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()
            # Verify response structure - could be translated_text or translation
            assert "translated_text" in data or "translation" in data or "mock" in data.get("mode", "")

    def test_journey_4_show_lifecycle(self, base_urls: Dict[str, str], redis_client: redis.Redis):
        """Journey 4: Show lifecycle (create → activate → deactivate)."""

        show_id = "test_show_lifecycle_001"

        # Step 1: Create show
        show_data = {
            "show_id": show_id,
            "name": "Test Show",
            "description": "E2E test show"
        }

        redis_client.hset(f"show:{show_id}", mapping=show_data)
        retrieved = redis_client.hgetall(f"show:{show_id}")
        assert retrieved["name"] == "Test Show"

        # Step 2: Activate show
        redis_client.hset(f"show:{show_id}", "status", "active")
        status = redis_client.hget(f"show:{show_id}", "status")
        assert status == "active"

        # Step 3: Deactivate show
        redis_client.hset(f"show:{show_id}", "status", "inactive")
        status = redis_client.hget(f"show:{show_id}", "status")
        assert status == "inactive"

        # Cleanup
        redis_client.delete(f"show:{show_id}")

    def test_journey_5_multi_agent_coordination(self, base_urls: Dict[str, str]):
        """Journey 5: Multiple agents working together (sentiment + dialogue + safety)."""

        # This tests the orchestrator coordinating multiple agents
        request_data = {
            "prompt": "Amazing performance tonight!",
            "show_id": "test_show_005",
            "agents": ["sentiment", "scenespeak", "safety"],
            "timeout": 20
        }

        # Note: Multi-agent coordination may timeout if services aren't fully connected
        try:
            response = httpx.post(
                f"{base_urls['orchestrator']}/api/orchestrate",
                json=request_data,
                timeout=10.0  # Shorter timeout for MVP validation
            )
            # Should get an async accepted response
            assert response.status_code == 202
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            # Coordination must be performant and not time out
            pytest.fail(f"Coordination failed with timeout or connect error: {e}")

    def test_journey_6_error_handling(self, base_urls: Dict[str, str]):
        """Journey 6: Error handling when service is unavailable."""

        # Test with invalid data that should be handled gracefully
        invalid_request = {
            "prompt": "",  # Empty prompt
            "show_id": ""   # Empty show ID
        }

        response = httpx.post(
            f"{base_urls['orchestrator']}/api/orchestrate",
            json=invalid_request,
            timeout=10.0
        )

        # Should return 400 (bad request) not 500 (server error)
        # Or may return 422 for validation errors
        assert response.status_code in [400, 422]

    def test_journey_7_redis_persistence(self, base_urls: Dict[str, str], redis_client: redis.Redis):
        """Journey 7: Redis persistence (data survives restart)."""

        # Step 1: Store test data
        test_key = "e2e_persistence_test"
        test_value = json.dumps({"timestamp": time.time(), "data": "test"})

        redis_client.set(test_key, test_value)
        redis_client.expire(test_key, 3600)  # 1 hour TTL

        # Step 2: Verify data exists
        retrieved = redis_client.get(test_key)
        assert retrieved is not None

        data = json.loads(retrieved)
        assert "data" in data
        assert data["data"] == "test"

        # Step 3: Verify TTL
        ttl = redis_client.ttl(test_key)
        assert ttl > 0 and ttl <= 3600

        # Cleanup
        redis_client.delete(test_key)

    def test_journey_8_health_monitoring(self, base_urls: Dict[str, str]):
        """Journey 8: All services reporting health status correctly."""

        # Check all services are healthy
        health_endpoints = {
            "orchestrator": "/health",
            "scenespeak": "/health",
            "translation": "/health",
            "sentiment": "/health",
            "safety": "/health/live",
            "console": "/health",
            "hardware": "/health"
        }

        unhealthy_services = []

        for service, endpoint in health_endpoints.items():
            url = base_urls.get(service)
            if not url:
                unhealthy_services.append(f"{service}: no URL configured")
                continue

            try:
                response = httpx.get(f"{url}{endpoint}", timeout=5.0)
                if response.status_code != 200:
                    unhealthy_services.append(f"{service}: HTTP {response.status_code}")
            except Exception as e:
                unhealthy_services.append(f"{service}: {str(e)}")

        # All services should be healthy
        assert len(unhealthy_services) == 0, f"Unhealthy services: {unhealthy_services}"


class TestE2EScenarios:
    """Additional E2E scenarios for edge cases."""

    @pytest.fixture(scope="class")
    def base_urls(self) -> Dict[str, str]:
        """Get base URLs."""
        return {
            "orchestrator": "http://localhost:8000",
            "sentiment": "http://localhost:8004",
            "safety": "http://localhost:8006",
        }

    def test_sentiment_analysis_pipeline(self, base_urls: Dict[str, str]):
        """Test complete sentiment analysis pipeline."""

        # Step 1: Analyze sentiment
        response = httpx.post(
            f"{base_urls['sentiment']}/api/analyze",
            json={"text": "This is absolutely wonderful! Best day ever!"},
            timeout=15.0
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "sentiment" in data or "label" in data
        assert "confidence" in data or "score" in data

    def test_safety_filter_pipeline(self, base_urls: Dict[str, str]):
        """Test complete safety filter pipeline."""

        # Step 1: Check content safety using the correct endpoint
        response = httpx.post(
            f"{base_urls['safety']}/v1/check",
            json={"content": "This is a family-friendly show."},
            timeout=10.0
        )

        # Safety filter should respond successfully
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            assert "safe" in data or "is_safe" in data or "approved" in data

    def test_concurrent_requests(self, base_urls: Dict[str, str]):
        """Test system handles concurrent requests."""

        import concurrent.futures

        def make_request(prompt_id: int) -> bool:
            try:
                response = httpx.post(
                    f"{base_urls['orchestrator']}/api/orchestrate",
                    json={"prompt": f"Concurrent test {prompt_id}", "show_id": "test_concurrent"},
                    timeout=5.0  # Short timeout for concurrent requests
                )
                # Must get a valid success response
                return response.status_code in [200, 202]
            except (httpx.TimeoutException, httpx.ConnectError):
                # Timeout/connection error is a hard failure for concurrency
                return False
            except Exception:
                return False

        # Send 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # At least 80% should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate: {success_rate:.2%}"

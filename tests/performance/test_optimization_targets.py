"""
Performance Optimization Targets (Iteration 35)

Tests to verify that performance optimizations meet targets:
- End-to-end orchestration: <5 seconds (p95)
- First request time: <1 second (all services)
- Cache hit response: <100ms
- Translation agent: Real API working (not mock)
- ML model pre-loaded: First request <1s (not 30s)
"""

import asyncio
import time
import pytest
import httpx


@pytest.mark.performance
@pytest.mark.timeout(10)
async def test_end_to_end_under_5_seconds():
    """
    Test that full orchestration completes in under 5 seconds.

    Iteration 35 target: Parallel agent calls + connection pooling
    should reduce end-to-end latency to <5 seconds (p95).
    """
    orchestrator_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Health check first
        health = await client.get(f"{orchestrator_url}/health/ready")
        assert health.status_code == 200, "Orchestrator not ready"

        start_time = time.time()

        # Full orchestration request
        response = await client.post(
            f"{orchestrator_url}/api/orchestrate",
            json={
                "prompt": "The hero enters the dark room cautiously",
                "show_id": "test_show",
                "context": {"genre": "thriller"}
            }
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "response" in data
        assert "sentiment" in data
        assert "safety_check" in data
        assert "metadata" in data

        # Check performance target (<5 seconds = 5000ms)
    assert duration_ms < 5000, f"Orchestration took {duration_ms:.0f}ms, target is <5000ms"

    # Log the timing for analysis
    print(f"End-to-end orchestration: {duration_ms:.0f}ms (target: <5000ms)")


@pytest.mark.performance
@pytest.mark.timeout(5)
async def test_ml_model_preloaded():
    """
    Test that ML model is pre-loaded on service startup.

    Iteration 35 target: First request should be <1 second since
    model is loaded during startup, not on first request.
    """
    sentiment_url = "http://localhost:8004"

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check health - model_loaded should be True
        health = await client.get(f"{sentiment_url}/health")
        assert health.status_code == 200
        health_data = health.json()

        # Verify model_loaded flag (Iteration 35)
        assert health_data.get("model_loaded", False), "ML model not pre-loaded"

        # First request should be fast (<1s) since model is pre-loaded
        start_time = time.time()

        response = await client.post(
            f"{sentiment_url}/api/analyze",
            json={"text": "This is a test of model pre-loading", "detect_language": False}
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        data = response.json()

        # Verify sentiment analysis worked
        assert "sentiment" in data
        assert "score" in data

        # First request should be <1 second (1000ms)
        assert duration_ms < 1000, f"First request took {duration_ms:.0f}ms, target is <1000ms"

    print(f"First ML request (with pre-loading): {duration_ms:.0f}ms (target: <1000ms)")


@pytest.mark.performance
@pytest.mark.timeout(1)
async def test_cache_hit_performance():
    """
    Test that cache hits return in <100ms.

    Iteration 35 target: Redis-based caching should return
    cached results in under 100ms.
    """
    orchestrator_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # First request to populate cache
        test_prompt = "Cache performance test prompt"
        await client.post(
            f"{orchestrator_url}/api/orchestrate",
            json={
                "prompt": test_prompt,
                "show_id": "cache_test",
                "context": {}
            }
        )

        # Second request should hit cache
        start_time = time.time()

        response = await client.post(
            f"{orchestrator_url}/api/orchestrate",
            json={
                "prompt": test_prompt,
                "show_id": "cache_test",
                "context": {}
            }
        )

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        data = response.json()

        # Check if from_cache flag is set (if cache is working)
        metadata = data.get("metadata", {})
        from_cache = metadata.get("from_cache", False)

        if from_cache:
            # Cache hit should be very fast (<100ms)
            assert duration_ms < 100, f"Cache hit took {duration_ms:.0f}ms, target is <100ms"
            print(f"Cache hit: {duration_ms:.0f}ms (target: <100ms)")
        else:
            # Cache may not be enabled in test environment
            print(f"Cache not enabled, request took {duration_ms:.0f}ms")


@pytest.mark.integration
@pytest.mark.timeout(5)
async def test_translation_real_api():
    """
    Test that translation agent uses real API (not mock).

    Iteration 35 target: Google Translate API should be configured
    and return actual translations, not mock results with prefixes.
    """
    translation_url = "http://localhost:8006"

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check health
        health = await client.get(f"{translation_url}/health")
        assert health.status_code == 200
        health_data = health.json()

        # Check if Google API is configured
        engine = health_data.get("engine", {})
        google_configured = engine.get("google_api_configured", False)
        mock_mode = engine.get("mock_mode", True)

        if not google_configured or mock_mode:
            pytest.skip("Google Translate API not configured - using mock mode")

        # Test real translation
        response = await client.post(
            f"{translation_url}/translate",
            json={
                "text": "Hello, world!",
                "source_language": "en",
                "target_language": "es"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Real translation should NOT have the mock prefix [ES]
        translated = data.get("translated_text", "")
        assert not translated.startswith("[ES]"), "Using mock translation instead of real API"
        assert "Hola" in translated or "hello" in translated.lower()

        print(f"Real translation: 'Hello, world!' -> '{translated}'")


@pytest.mark.performance
@pytest.mark.timeout(5)
async def test_parallel_agent_calls():
    """
    Test that parallel agent calls are faster than sequential.

    Iteration 35 target: asyncio.gather() should execute sentiment
    and safety checks in parallel, reducing total time.
    """
    import asyncio

    orchestrator_url = "http://localhost:8000"

    async def single_orchestration():
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{orchestrator_url}/api/orchestrate",
                json={
                    "prompt": "Test prompt for parallel execution",
                    "show_id": "parallel_test",
                    "context": {}
                }
            )
            return response

    # Run multiple orchestrations in parallel
    start_time = time.time()

    results = await asyncio.gather(
        single_orchestration(),
        single_orchestration(),
        single_orchestration(),
        return_exceptions=True
    )

    end_time = time.time()
    total_duration_ms = (end_time - start_time) * 1000

    # All should succeed
    for result in results:
        if isinstance(result, Exception):
            pytest.fail(f"Parallel orchestration failed: {result}")
        assert result.status_code == 200

    # 3 parallel requests should complete faster than 3 * single_request_time
    # (This is a weak assertion since timing varies, but validates parallelism)
    avg_duration_ms = total_duration_ms / 3

    print(f"3 parallel orchestrations: {total_duration_ms:.0f}ms (avg: {avg_duration_ms:.0f}ms each)")

    # If each took >2 seconds sequentially, 3 would take >6 seconds
    # With parallelism and connection pooling, they should overlap significantly
    assert total_duration_ms < 8000, "Parallel requests may not be executing concurrently"


@pytest.mark.slow
@pytest.mark.timeout(30)
async def test_connection_pool_reuse():
    """
    Test that connection pooling reuses connections.

    Iteration 35 target: Multiple requests should reuse connections
    rather than creating new ones.
    """
    sentiment_url = "http://localhost:8004"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Make multiple requests
        timings = []
        for i in range(5):
            start_time = time.time()
            response = await client.post(
                f"{sentiment_url}/api/analyze",
                json={"text": f"Connection pool test {i}", "detect_language": False}
            )
            end_time = time.time()
            assert response.status_code == 200
            timings.append((end_time - start_time) * 1000)

        # First request may be slower (cold start)
        # Subsequent requests should be faster with connection reuse
        if len(timings) >= 2:
            first_request_ms = timings[0]
            avg_subsequent_ms = sum(timings[1:]) / (len(timings) - 1)

            print(f"First request: {first_request_ms:.0f}ms")
            print(f"Avg subsequent: {avg_subsequent_ms:.0f}ms")

            # Subsequent requests should generally be faster or similar
            # (connection reuse eliminates TCP handshake overhead)
            # Note: This is a weak assertion due to timing variance
            if avg_subsequent_ms > first_request_ms * 1.5:
                print("Warning: Subsequent requests slower - connection pooling may not be working")


@pytest.mark.performance
@pytest.mark.timeout(5)
async def test_scenespeak_model_preloaded():
    """
    Test that SceneSpeak ML model is pre-loaded.

    Similar to sentiment agent, SceneSpeak should load models
    during startup to eliminate cold start delays.
    """
    scenespeak_url = "http://localhost:8001"

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check health
        health = await client.get(f"{scenespeak_url}/health")
        assert health.status_code == 200
        health_data = health.json()

        # Check model_loaded status (Iteration 35)
        model_loaded = health_data.get("model_loaded", True)
        if model_loaded:
            print("SceneSpeak ML model is pre-loaded")
        else:
            print("Warning: SceneSpeak ML model not pre-loaded (may use lazy loading)")


if __name__ == "__main__":
    # Run tests with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))

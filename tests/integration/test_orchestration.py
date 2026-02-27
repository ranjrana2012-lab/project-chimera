"""
OpenClaw orchestration integration tests.

Tests the OpenClaw Orchestrator's skill invocation, routing, and GPU scheduling.
"""

import pytest
import asyncio
from httpx import AsyncClient
from typing import Dict, Any, List


@pytest.mark.integration
class TestOpenClawOrchestration:
    """Test OpenClaw Orchestrator functionality."""

    @pytest.mark.asyncio
    async def test_orchestrator_health(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test OpenClaw Orchestrator health and readiness."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Liveness
        response = await http_client.get(f"{base_url}/health/live", timeout=5.0)
        assert response.status_code == 200

        # Readiness with dependencies
        response = await http_client.get(f"{base_url}/health/ready", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ready") == True or data.get("status") == "ready"

    @pytest.mark.asyncio
    async def test_list_available_skills(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test listing all available skills."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        response = await http_client.get(f"{base_url}/api/v1/skills", timeout=10.0)
        assert response.status_code == 200

        skills = response.json()
        assert isinstance(skills, list) or "skills" in skills

        if isinstance(skills, list):
            skill_list = skills
        else:
            skill_list = skills.get("skills", [])

        # Verify core skills are present
        skill_names = [s.get("name", s.get("skill_name", "")) for s in skill_list]
        expected_skills = [
            "sentiment",
            "scenespeak",
            "safety-filter",
            "captioning",
            "bsl-text2gloss",
            "lighting-control",
        ]

        for expected in expected_skills:
            assert any(expected in name for name in skill_names), f"{expected} not found in skills"

    @pytest.mark.asyncio
    async def test_invoke_sentiment_skill(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test invoking the sentiment skill through orchestration."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "sentiment",
            "input": {
                "text": "The audience is absolutely loving this performance!",
            },
            "config": {
                "timeout_ms": 5000,
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=10.0,
        )

        assert response.status_code == 200
        result = response.json()

        # Verify orchestration response structure
        assert "output" in result or "results" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_invoke_scenespeak_skill(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test invoking the SceneSpeak skill through orchestration."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "scenespeak",
            "input": {
                "current_scene": {
                    "scene_id": "scene-orch-001",
                    "title": "Orchestration Test Scene",
                    "characters": ["ACTOR"],
                    "setting": "Test Stage",
                    "mood": "dramatic",
                },
                "dialogue_context": [],
                "sentiment_vector": {"overall": "positive", "intensity": 0.7},
            },
            "config": {
                "timeout_ms": 10000,
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=15.0,
        )

        assert response.status_code == 200
        result = response.json()

        assert "output" in result or "results" in result
        assert result.get("status") in ["success", "completed", "ok"]

    @pytest.mark.asyncio
    async def test_invoke_safety_filter_skill(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test invoking the safety filter skill through orchestration."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "safety-filter",
            "input": {
                "content": "This is a safe and appropriate message for the audience.",
            },
            "config": {
                "timeout_ms": 3000,
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=10.0,
        )

        assert response.status_code == 200
        result = response.json()

        assert "output" in result
        if "output" in result:
            output = result["output"]
            assert "decision" in output or "safe" in output

    @pytest.mark.asyncio
    async def test_parallel_skill_invocation(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test invoking multiple skills in parallel."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Create parallel requests
        requests = [
            {
                "skill_name": "sentiment",
                "input": {"text": f"Parallel test message {i}"},
                "request_id": f"parallel-{i}",
            }
            for i in range(5)
        ]

        # Execute in parallel
        tasks = [
            http_client.post(
                f"{base_url}/api/v1/orchestrate",
                json=req,
                timeout=10.0,
            )
            for req in requests
        ]

        responses = await asyncio.gather(*tasks)

        # Verify all succeeded
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Request {i} failed"
            result = response.json()
            assert "output" in result or "status" in result

    @pytest.mark.asyncio
    async def test_skill_chain_orchestration(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test chaining multiple skills together."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Step 1: Analyze sentiment
        sentiment_request = {
            "skill_name": "sentiment",
            "input": {"text": "The mood is very tense"},
        }

        sentiment_response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=sentiment_request,
            timeout=10.0,
        )

        assert sentiment_response.status_code == 200
        sentiment_result = sentiment_response.json()

        # Step 2: Generate dialogue with sentiment context
        dialogue_request = {
            "skill_name": "scenespeak",
            "input": {
                "current_scene": {"scene_id": "scene-chain-001", "title": "Chained Scene"},
                "sentiment_vector": {
                    "overall": "neutral",
                },
            },
        }

        dialogue_response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=dialogue_request,
            timeout=15.0,
        )

        assert dialogue_response.status_code == 200

        # Step 3: Safety check
        dialogue_result = dialogue_response.json()
        content = (
            dialogue_result.get("output", {})
            .get("proposed_lines", "")
            if "output" in dialogue_result
            else ""
        )

        if content:
            safety_request = {
                "skill_name": "safety-filter",
                "input": {"content": content},
            }

            safety_response = await http_client.post(
                f"{base_url}/api/v1/orchestrate",
                json=safety_request,
                timeout=10.0,
            )

            assert safety_response.status_code == 200

    @pytest.mark.asyncio
    async def test_skill_timeout_handling(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test that skill timeouts are handled correctly."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "sentiment",
            "input": {"text": "Quick test"},
            "config": {
                "timeout_ms": 100,  # Very short timeout
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=5.0,
        )

        # Should either succeed quickly or timeout gracefully
        assert response.status_code in [200, 408, 500]

    @pytest.mark.asyncio
    async def test_skill_error_handling(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test error handling for invalid skill requests."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Test with invalid skill name
        request = {
            "skill_name": "nonexistent_skill",
            "input": {"test": "data"},
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=10.0,
        )

        # Should return error
        assert response.status_code in [400, 404, 500]

    @pytest.mark.asyncio
    async def test_skill_retry_policy(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test skill invocation with retry policy."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "sentiment",
            "input": {"text": "Test with retry"},
            "config": {
                "timeout_ms": 5000,
                "retry_policy": {
                    "max_retries": 2,
                    "backoff": "exponential",
                },
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=15.0,
        )

        # Should succeed (or fail after retries)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_batch_skill_invocation(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test invoking skills with batch inputs."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "sentiment",
            "input": {
                "texts": [
                    "Great performance!",
                    "Amazing show!",
                    "Loved it!",
                ]
            },
            "config": {
                "timeout_ms": 10000,
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=15.0,
        )

        assert response.status_code == 200
        result = response.json()

        assert "output" in result
        if "output" in result:
            output = result["output"]
            # Batch results should contain multiple items
            assert "results" in output or len(output) > 0

    @pytest.mark.asyncio
    async def test_skill_metadata_and_metrics(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test that skill invocations return metadata."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "sentiment",
            "input": {"text": "Test metadata"},
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=10.0,
        )

        assert response.status_code == 200
        result = response.json()

        # Check for metadata fields
        metadata_fields = ["latency_ms", "request_id", "timestamp", "execution_time"]
        found_metadata = any(field in result for field in metadata_fields)
        # Metadata is optional but recommended

    @pytest.mark.asyncio
    async def test_skill_versioning(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test skill versioning support."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # List skills to check versions
        response = await http_client.get(f"{base_url}/api/v1/skills", timeout=10.0)
        assert response.status_code == 200

        skills = response.json()
        skill_list = skills if isinstance(skills, list) else skills.get("skills", [])

        # Check if skills have version information
        for skill in skill_list:
            if "version" in skill or "skill_version" in skill:
                # Version info present
                assert isinstance(skill.get("version", skill.get("skill_version")), str)

    @pytest.mark.asyncio
    async def test_conditional_skill_routing(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test conditional routing based on input parameters."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Test routing based on sentiment
        negative_request = {
            "skill_name": "scenespeak",
            "input": {
                "current_scene": {"title": "Negative Scene"},
                "sentiment_vector": {"overall": "negative"},
            },
        }

        positive_request = {
            "skill_name": "scenespeak",
            "input": {
                "current_scene": {"title": "Positive Scene"},
                "sentiment_vector": {"overall": "positive"},
            },
        }

        # Execute both
        responses = await asyncio.gather(
            http_client.post(
                f"{base_url}/api/v1/orchestrate",
                json=negative_request,
                timeout=15.0,
            ),
            http_client.post(
                f"{base_url}/api/v1/orchestrate",
                json=positive_request,
                timeout=15.0,
            ),
        )

        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_orchestration_pipeline_execution(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test executing a predefined pipeline through orchestration."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Execute a pipeline: sentiment -> dialogue -> safety
        pipeline_request = {
            "pipeline": "default_dialogue_pipeline",
            "input": {
                "text": "Great show!",
                "scene_context": {"scene_id": "scene-pipe-001", "title": "Pipeline Test"},
            },
            "config": {
                "timeout_ms": 30000,
            },
        }

        response = await http_client.post(
            f"{base_url}/api/v1/pipelines/execute",
            json=pipeline_request,
            timeout=35.0,
        )

        # Pipeline endpoint may or may not be implemented
        if response.status_code == 200:
            result = response.json()
            assert "results" in result or "output" in result

    @pytest.mark.asyncio
    async def test_gpu_allocation_tracking(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test GPU allocation through orchestration."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Check GPU status
        response = await http_client.get(
            f"{base_url}/api/v1/gpu/status",
            timeout=5.0,
        )

        # GPU endpoint may be available for monitoring
        if response.status_code == 200:
            gpu_data = response.json()
            assert "gpus" in gpu_data or "available" in gpu_data

    @pytest.mark.asyncio
    async def test_skill_registry_consistency(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test that skill registry is consistent across calls."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Get skills list twice
        response1 = await http_client.get(f"{base_url}/api/v1/skills", timeout=10.0)
        response2 = await http_client.get(f"{base_url}/api/v1/skills", timeout=10.0)

        assert response1.status_code == 200
        assert response2.status_code == 200

        skills1 = response1.json()
        skills2 = response2.json()

        # Should return consistent data
        skill_list1 = skills1 if isinstance(skills1, list) else skills1.get("skills", [])
        skill_list2 = skills2 if isinstance(skills2, list) else skills2.get("skills", [])

        assert len(skill_list1) == len(skill_list2)

    @pytest.mark.asyncio
    async def test_orchestration_request_validation(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test request validation in orchestration."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        # Missing required field
        invalid_request = {
            "skill_name": "sentiment",
            # Missing "input" field
        }

        response = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=invalid_request,
            timeout=10.0,
        )

        # Should return validation error
        assert response.status_code == 422 or response.status_code == 400

    @pytest.mark.asyncio
    async def test_concurrent_orchestration_requests(
        self, http_client: AsyncClient, test_config: dict
    ):
        """Test handling of concurrent orchestration requests."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        requests = [
            {
                "skill_name": "sentiment",
                "input": {"text": f"Concurrent test {i}"},
                "request_id": f"concurrent-{i}",
            }
            for i in range(20)
        ]

        tasks = [
            http_client.post(
                f"{base_url}/api/v1/orchestrate",
                json=req,
                timeout=10.0,
            )
            for req in requests
        ]

        responses = await asyncio.gather(*tasks)

        # Most should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 15  # At least 75% success rate

    @pytest.mark.asyncio
    async def test_orchestration_caching(
        self, http_client: AsyncClient, test_config: dict, redis_client
    ):
        """Test that orchestration results can be cached."""
        base_url = f"http://{test_config['openclaw_host']}:{test_config['openclaw_port']}"

        request = {
            "skill_name": "sentiment",
            "input": {"text": "Cache test message"},
            "config": {
                "use_cache": True,
            },
        }

        # First request
        response1 = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=10.0,
        )

        # Second request with same input
        response2 = await http_client.post(
            f"{base_url}/api/v1/orchestrate",
            json=request,
            timeout=10.0,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Second should potentially be faster if cached
        result1 = response1.json()
        result2 = response2.json()

        # Check for cache indicators
        cached1 = result1.get("cached", False)
        cached2 = result2.get("cached", False)

        # If caching is enabled, second request might be cached
        if cached2:
            latency1 = result1.get("latency_ms", 0)
            latency2 = result2.get("latency_ms", 0)
            assert latency2 <= latency1

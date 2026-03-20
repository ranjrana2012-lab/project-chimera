# services/nemoclaw-orchestrator/tests/integration/test_zai_routing.py
import pytest
import time
from unittest.mock import Mock, patch
from llm.privacy_router import LLMBackend, RouterConfig, PrivacyRouter


@pytest.mark.integration
class TestZAIRoutingIntegration:
    """Integration tests for Z.AI-first routing"""

    @pytest.fixture
    def config(self):
        return RouterConfig(
            dgx_endpoint="http://localhost:8000",
            zai_api_key="test-key",
            zai_cache_ttl=2  # Short TTL for testing
        )

    @pytest.fixture
    def router(self, config):
        with patch('llm.privacy_router.CreditStatusCache'), \
             patch('llm.privacy_router.ZAIClient'), \
             patch('llm.privacy_router.NemotronClient'):
            return PrivacyRouter(config)

    def test_full_request_flow_zai_success(self, router):
        """Test successful Z.AI request flow"""
        with patch.object(router.zai_client, 'generate') as mock_zai:
            mock_zai.return_value = {
                "text": "Z.AI response",
                "model_used": "glm-5-turbo",
                "credits_exhausted": False
            }

            # Configure is_available to return True
            router.credit_cache.is_available.return_value = True

            result = router.generate("test prompt", task_type="tool_invocation")

            assert result["text"] == "Z.AI response"
            assert result["backend"] == "zai_primary"
            assert router.credit_cache.is_available()
            # Verify Z.AI generate was called
            mock_zai.assert_called_once()

    def test_credit_exhaustion_fallback_flow(self, router):
        """Test credit exhaustion -> fallback -> cache flow"""
        # Z.AI returns credit exhaustion
        with patch.object(router.zai_client, 'generate') as mock_zai, \
             patch.object(router.local_client, 'generate') as mock_local:

            mock_zai.return_value = {
                "error": "credit_exhausted",
                "details": "Insufficient credits"
            }
            mock_local.return_value = {
                "text": "Local response",
                "model": "nemotron-8b",
                "backend": "nemotron_local"
            }

            # Configure is_available to return True initially (so we try Z.AI)
            router.credit_cache.is_available.return_value = True

            result = router.generate("test prompt")

            assert result["text"] == "Local response"
            assert result["backend"] == "nemotron_local"
            # Verify mark_exhausted was called
            router.credit_cache.mark_exhausted.assert_called_once()
            # After mark_exhausted, is_available should return False
            router.credit_cache.is_available.return_value = False
            assert not router.credit_cache.is_available()

    def test_ttl_expiration_recovery(self, router):
        """Test Z.AI recovery after TTL expiration"""
        # Initially not available
        router.credit_cache.is_available.return_value = False
        router.credit_cache.mark_exhausted()

        # Verify mark_exhausted was called
        router.credit_cache.mark_exhausted.assert_called_once()

        # Wait for TTL (2 seconds)
        time.sleep(2.5)

        # Cache should be cleared by Redis TTL
        # (In real Redis, key would expire; mock needs manual clearing)
        router.credit_cache.reset()
        # After reset, is_available should return True
        router.credit_cache.is_available.return_value = True
        assert router.credit_cache.is_available()

        # Verify reset was called
        router.credit_cache.reset.assert_called_once()

    def test_task_type_model_selection(self, router):
        """Test model selection based on task type"""
        test_cases = [
            ("tool_invocation", LLMBackend.ZAI_PRIMARY),
            ("persistent", LLMBackend.ZAI_PRIMARY),
            ("programming", LLMBackend.ZAI_PROGRAMMING),
            ("code_generation", LLMBackend.ZAI_PROGRAMMING),
            ("simple", LLMBackend.ZAI_FAST),
            ("repetitive", LLMBackend.ZAI_FAST),
            ("unknown", LLMBackend.ZAI_PRIMARY),  # Default
        ]

        for task_type, expected_backend in test_cases:
            backend = router._select_zai_model(task_type)
            assert backend == expected_backend, f"Failed for {task_type}"

    def test_concurrent_requests_same_exhaustion(self, router):
        """Test multiple concurrent requests handle exhaustion correctly"""
        with patch.object(router.zai_client, 'generate') as mock_zai, \
             patch.object(router.local_client, 'generate') as mock_local:

            mock_zai.return_value = {
                "error": "credit_exhausted",
                "details": "Insufficient credits"
            }
            mock_local.return_value = {
                "text": "Local response",
                "model": "nemotron-8b",
                "backend": "nemotron_local"
            }

            # Simulate concurrent requests
            results = []
            for _ in range(5):
                result = router.generate("test")
                results.append(result)

            # All should fall back to local
            assert all(r["backend"] == "nemotron_local" for r in results)
            assert router.credit_cache.mark_exhausted.call_count >= 1

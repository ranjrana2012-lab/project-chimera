# services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py
import pytest
from unittest.mock import Mock, patch
from llm.privacy_router import LLMBackend, RouterConfig, PrivacyRouter


class TestRouterConfig:
    def test_creates_config_with_zai_defaults(self):
        config = RouterConfig(dgx_endpoint="http://localhost:8000")
        assert config.zai_primary_model == "glm-5-turbo"
        assert config.zai_programming_model == "glm-4.7"
        assert config.zai_fast_model == "glm-4.7-flashx"
        assert config.zai_cache_ttl == 3600
        assert config.zai_thinking_enabled is True


class TestLLMBackend:
    def test_backend_enum_values(self):
        assert LLMBackend.ZAI_PRIMARY.value == "zai_primary"
        assert LLMBackend.ZAI_PROGRAMMING.value == "zai_programming"
        assert LLMBackend.ZAI_FAST.value == "zai_fast"
        assert LLMBackend.NEMOTRON_LOCAL.value == "nemotron_local"


class TestPrivacyRouter:
    @pytest.fixture
    def config(self):
        return RouterConfig(
            dgx_endpoint="http://localhost:8000",
            zai_api_key="test-key"
        )

    @pytest.fixture
    def mock_zai_client(self):
        with patch('llm.privacy_router.ZAIClient') as mock:
            yield mock

    @pytest.fixture
    def mock_nemotron_client(self):
        with patch('llm.privacy_router.NemotronClient') as mock:
            yield mock

    @pytest.fixture
    def mock_credit_cache(self):
        with patch('llm.privacy_router.CreditStatusCache') as mock:
            yield mock

    @pytest.fixture
    def router(self, config, mock_zai_client, mock_nemotron_client, mock_credit_cache):
        return PrivacyRouter(config)

    def test_router_initializes(self, router):
        assert router.zai_client is not None
        assert router.local_client is not None
        assert router.credit_cache is not None

    def test_select_zai_model_for_tool_invocation(self, router):
        backend = router._select_zai_model("tool_invocation")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_select_zai_model_for_programming(self, router):
        backend = router._select_zai_model("programming")
        assert backend == LLMBackend.ZAI_PROGRAMMING

    def test_select_zai_model_for_simple_tasks(self, router):
        backend = router._select_zai_model("simple")
        assert backend == LLMBackend.ZAI_FAST

    def test_select_zai_model_for_orchestration(self, router):
        backend = router._select_zai_model("orchestration")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_select_zai_model_for_default(self, router):
        backend = router._select_zai_model("default")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_select_zai_model_for_unknown_task(self, router):
        backend = router._select_zai_model("unknown_task")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_select_zai_model_for_code_generation(self, router):
        backend = router._select_zai_model("code_generation")
        assert backend == LLMBackend.ZAI_PROGRAMMING

    def test_select_zai_model_for_debugging(self, router):
        backend = router._select_zai_model("debugging")
        assert backend == LLMBackend.ZAI_PROGRAMMING

    def test_select_zai_model_for_repetitive(self, router):
        backend = router._select_zai_model("repetitive")
        assert backend == LLMBackend.ZAI_FAST

    def test_select_zai_model_for_quick(self, router):
        backend = router._select_zai_model("quick")
        assert backend == LLMBackend.ZAI_FAST

    def test_select_zai_model_for_classification(self, router):
        backend = router._select_zai_model("classification")
        assert backend == LLMBackend.ZAI_FAST

    def test_route_returns_zai_when_available(self, router, mock_credit_cache):
        mock_credit_cache.return_value.is_available.return_value = True
        backend = router.route("test", "default")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_route_returns_nemotron_when_exhausted(self, router, mock_credit_cache):
        mock_credit_cache.return_value.is_available.return_value = False
        backend = router.route("test", "default")
        assert backend == LLMBackend.NEMOTRON_LOCAL

    def test_route_returns_zai_programming_for_programming_task(self, router, mock_credit_cache):
        mock_credit_cache.return_value.is_available.return_value = True
        backend = router.route("test", "programming")
        assert backend == LLMBackend.ZAI_PROGRAMMING

    def test_route_returns_zai_fast_for_simple_task(self, router, mock_credit_cache):
        mock_credit_cache.return_value.is_available.return_value = True
        backend = router.route("test", "simple")
        assert backend == LLMBackend.ZAI_FAST

    @patch('llm.privacy_router.time')
    def test_generate_with_zai_primary(self, mock_time, router, mock_zai_client):
        mock_time.time.return_value = 0.0
        mock_zai_client.return_value.generate.return_value = {
            "text": "response",
            "model_used": "glm-5-turbo",
            "credits_exhausted": False
        }

        result = router.generate("test", task_type="tool_invocation")

        assert result["text"] == "response"
        assert result["backend"] == "zai_primary"

    @patch('llm.privacy_router.time')
    def test_generate_with_zai_programming(self, mock_time, router, mock_zai_client):
        mock_time.time.return_value = 0.0
        mock_zai_client.return_value.generate.return_value = {
            "text": "code response",
            "model_used": "glm-4.7",
            "credits_exhausted": False
        }

        result = router.generate("test", task_type="programming")

        assert result["text"] == "code response"
        assert result["backend"] == "zai_programming"

    @patch('llm.privacy_router.time')
    def test_generate_with_zai_fast(self, mock_time, router, mock_zai_client):
        mock_time.time.return_value = 0.0
        mock_zai_client.return_value.generate.return_value = {
            "text": "fast response",
            "model_used": "glm-4.7-flashx",
            "credits_exhausted": False
        }

        result = router.generate("test", task_type="simple")

        assert result["text"] == "fast response"
        assert result["backend"] == "zai_fast"

    @patch('llm.privacy_router.time')
    def test_generate_falls_back_on_credit_exhaustion(self, mock_time, router, mock_zai_client, mock_nemotron_client):
        mock_time.time.return_value = 0.0

        # Z.AI returns credit exhaustion
        mock_zai_client.return_value.generate.return_value = {
            "error": "credit_exhausted",
            "details": "Insufficient credits"
        }

        # Nemotron returns success
        mock_nemotron_client.return_value.generate.return_value = {
            "text": "local response",
            "model": "nemotron-8b",
            "backend": "nemotron_local"
        }

        result = router.generate("test", task_type="tool_invocation")

        assert result["text"] == "local response"
        assert result["backend"] == "nemotron_local"

    @patch('llm.privacy_router.time')
    def test_generate_with_nemotron_when_forced(self, mock_time, router, mock_nemotron_client):
        mock_time.time.return_value = 0.0
        mock_nemotron_client.return_value.generate.return_value = {
            "text": "local response",
            "model": "nemotron-8b"
        }

        result = router.generate(
            "test",
            force_backend=LLMBackend.NEMOTRON_LOCAL
        )

        assert result["text"] == "local response"
        assert result["backend"] == "nemotron_local"

    @patch('llm.privacy_router.time')
    def test_generate_with_nemotron_when_exhausted(self, mock_time, router, mock_credit_cache, mock_nemotron_client):
        mock_time.time.return_value = 0.0
        mock_credit_cache.return_value.is_available.return_value = False
        mock_nemotron_client.return_value.generate.return_value = {
            "text": "local response",
            "model": "nemotron-8b"
        }

        result = router.generate("test")

        assert result["text"] == "local response"
        assert result["backend"] == "nemotron_local"

    @patch('llm.privacy_router.time')
    def test_generate_falls_back_on_unknown_backend(self, mock_time, router, mock_nemotron_client):
        mock_time.time.return_value = 0.0
        mock_nemotron_client.return_value.generate.return_value = {
            "text": "local response",
            "model": "nemotron-8b"
        }

        # Unknown backend should fall back to Nemotron when cloud_fallback_enabled is True
        result = router.generate("test", force_backend="unknown_backend")

        assert result["text"] == "local response"
        assert result["backend"] == "nemotron_local"

    @patch('llm.privacy_router.time')
    def test_generate_raises_on_unknown_backend_when_fallback_disabled(self, mock_time):
        config = RouterConfig(
            dgx_endpoint="http://localhost:8000",
            zai_api_key="test-key",
            cloud_fallback_enabled=False
        )

        with patch('llm.privacy_router.ZAIClient') as mock_zai:
            with patch('llm.privacy_router.NemotronClient') as mock_nemotron:
                with patch('llm.privacy_router.CreditStatusCache') as mock_cache:
                    mock_time.time.return_value = 0.0
                    router = PrivacyRouter(config)

                    with pytest.raises(ValueError, match="Unknown backend"):
                        router.generate("test", force_backend="unknown_backend")

    @patch('llm.privacy_router.time')
    def test_close_closes_all_clients(self, mock_time, router, mock_zai_client, mock_nemotron_client, mock_credit_cache):
        mock_time.time.return_value = 0.0

        router.close()

        mock_zai_client.return_value.close.assert_called_once()
        mock_nemotron_client.return_value.close.assert_called_once()
        mock_credit_cache.return_value.close.assert_called_once()

    @patch('llm.privacy_router.time')
    def test_context_manager(self, mock_time, config):
        mock_time.time.return_value = 0.0

        with patch('llm.privacy_router.ZAIClient') as mock_zai:
            with patch('llm.privacy_router.NemotronClient') as mock_nemotron:
                with patch('llm.privacy_router.CreditStatusCache') as mock_cache:
                    with PrivacyRouter(config) as router:
                        assert router is not None

                    mock_zai.return_value.close.assert_called_once()
                    mock_nemotron.return_value.close.assert_called_once()
                    mock_cache.return_value.close.assert_called_once()

    def test_config_with_custom_zai_settings(self):
        config = RouterConfig(
            dgx_endpoint="http://localhost:8000",
            zai_api_key="custom-key",
            zai_primary_model="custom-primary",
            zai_programming_model="custom-programming",
            zai_fast_model="custom-fast",
            zai_cache_ttl=7200,
            zai_thinking_enabled=False
        )

        assert config.zai_api_key == "custom-key"
        assert config.zai_primary_model == "custom-primary"
        assert config.zai_programming_model == "custom-programming"
        assert config.zai_fast_model == "custom-fast"
        assert config.zai_cache_ttl == 7200
        assert config.zai_thinking_enabled is False

    def test_config_legacy_fields(self):
        config = RouterConfig(
            dgx_endpoint="http://localhost:8000",
            local_ratio=0.5,
            cloud_fallback_enabled=False
        )

        assert config.local_ratio == 0.5
        assert config.cloud_fallback_enabled is False

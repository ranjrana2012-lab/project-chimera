# services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm.privacy_router import LLMBackend, RouterConfig, PrivacyRouter


class TestRouterConfig:
    def test_creates_config_with_defaults(self):
        config = RouterConfig(dgx_endpoint="http://localhost:8000")
        assert config.dgx_endpoint == "http://localhost:8000"
        assert config.local_ratio == 0.95
        assert config.cloud_fallback_enabled is True

    def test_validates_local_ratio_bounds(self):
        with pytest.raises(ValueError):
            RouterConfig(dgx_endpoint="http://localhost:8000", local_ratio=1.5)

        with pytest.raises(ValueError):
            RouterConfig(dgx_endpoint="http://localhost:8000", local_ratio=-0.1)


class TestLLMBackend:
    def test_backend_enum_values(self):
        assert LLMBackend.NEMOTRON_LOCAL.value == "nemotron_local"
        assert LLMBackend.CLOUD_GUARDED.value == "cloud_guarded"
        assert LLMBackend.FALLBACK.value == "fallback"


class TestPrivacyRouter:
    @pytest.fixture
    def config(self):
        return RouterConfig(
            dgx_endpoint="http://localhost:8000",
            local_ratio=0.95,
            cloud_fallback_enabled=True
        )

    @pytest.fixture
    def router(self, config):
        return PrivacyRouter(config)

    def test_router_initializes(self, router):
        assert router.config is not None
        assert router.local_client is not None
        assert router.cloud_client is not None

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_route_returns_local_when_available(self, mock_cloud, mock_local, config):
        mock_local_client = Mock()
        mock_local_client.is_available.return_value = True
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        # Force local routing by setting random to return low value
        with patch('llm.privacy_router.random.random', return_value=0.9):
            backend = router.route("test prompt")
            assert backend == LLMBackend.NEMOTRON_LOCAL

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_route_returns_cloud_when_ratio_exceeded(self, mock_cloud, mock_local, config):
        mock_local_client = Mock()
        mock_local_client.is_available.return_value = True
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        # Force cloud routing by setting random to return high value
        with patch('llm.privacy_router.random.random', return_value=0.96):
            backend = router.route("test prompt")
            assert backend == LLMBackend.CLOUD_GUARDED

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_route_returns_cloud_when_local_unavailable(self, mock_cloud, mock_local, config):
        mock_local_client = Mock()
        mock_local_client.is_available.return_value = False
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        backend = router.route("test prompt")
        assert backend == LLMBackend.CLOUD_GUARDED

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_generate_uses_local_backend(self, mock_cloud, mock_local, config):
        mock_local_client = Mock()
        mock_local_client.is_available.return_value = True
        mock_local_client.generate.return_value = {
            "text": "local response",
            "model": "nemotron-8b",
            "backend": "nemotron_local"
        }
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        result = router.generate(
            prompt="test prompt",
            force_backend=LLMBackend.NEMOTRON_LOCAL
        )

        assert result["text"] == "local response"
        assert result["backend"] == "nemotron_local"
        mock_local_client.generate.assert_called_once()

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_generate_uses_cloud_backend(self, mock_cloud, mock_local, config):
        mock_cloud_client = Mock()
        mock_cloud_client.generate.return_value = {
            "text": "cloud response",
            "model": "claude-3-haiku-20240307",
            "backend": "cloud_guarded",
            "pii_stripped": True
        }
        mock_cloud.return_value = mock_cloud_client

        mock_local_client = Mock()
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        result = router.generate(
            prompt="test prompt",
            force_backend=LLMBackend.CLOUD_GUARDED
        )

        assert result["text"] == "cloud response"
        assert result["backend"] == "cloud_guarded"
        assert result["pii_stripped"] is True
        mock_cloud_client.generate.assert_called_once()

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_generate_falls_back_to_cloud_on_local_failure(self, mock_cloud, mock_local, config):
        mock_cloud_client = Mock()
        mock_cloud_client.generate.return_value = {
            "text": "cloud fallback response",
            "model": "claude-3-haiku-20240307",
            "backend": "cloud_guarded",
            "pii_stripped": True
        }
        mock_cloud.return_value = mock_cloud_client

        mock_local_client = Mock()
        mock_local_client.generate.side_effect = Exception("Local failed")
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        result = router.generate(
            prompt="test prompt",
            force_backend=LLMBackend.NEMOTRON_LOCAL
        )

        assert result["text"] == "cloud fallback response"
        mock_cloud_client.generate.assert_called_once()

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_generate_raises_when_no_fallback_available(self, mock_cloud, mock_local):
        config = RouterConfig(
            dgx_endpoint="http://localhost:8000",
            local_ratio=0.95,
            cloud_fallback_enabled=False
        )

        mock_local_client = Mock()
        mock_local_client.generate.side_effect = Exception("Local failed")
        mock_local.return_value = mock_local_client

        router = PrivacyRouter(config)

        with pytest.raises(Exception):
            router.generate(
                prompt="test prompt",
                force_backend=LLMBackend.NEMOTRON_LOCAL
            )

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_close_closes_all_clients(self, mock_cloud, mock_local, config):
        mock_local_client = Mock()
        mock_cloud_client = Mock()
        mock_local.return_value = mock_local_client
        mock_cloud.return_value = mock_cloud_client

        router = PrivacyRouter(config)
        router.close()

        mock_local_client.close.assert_called_once()
        mock_cloud_client.close.assert_called_once()

    @patch('llm.nemotron_client.NemotronClient')
    @patch('llm.guarded_cloud.GuardedCloudClient')
    def test_context_manager(self, mock_cloud, mock_local, config):
        mock_local_client = Mock()
        mock_cloud_client = Mock()
        mock_local.return_value = mock_local_client
        mock_cloud.return_value = mock_cloud_client

        with PrivacyRouter(config) as router:
            assert router is not None

        mock_local_client.close.assert_called_once()
        mock_cloud_client.close.assert_called_once()

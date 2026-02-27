"""Unit tests for SceneSpeak Agent configuration."""
import os
import pytest
from pathlib import Path


class TestSettings:
    """Test Settings model."""

    def test_default_values(self):
        """Test Settings default values."""
        # Import here to avoid import errors if file doesn't exist yet
        from services.scenespeak_agent.config import settings

        assert settings.app_name == "scenespeak-agent"
        assert settings.app_version == "1.0.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8001
        assert settings.debug is False

    def test_model_configuration(self):
        """Test model configuration defaults."""
        from services.scenespeak_agent.config import settings

        assert settings.model_name == "mistralai/Mistral-7B-Instruct-v0.2"
        assert settings.device == "cuda"
        assert settings.quantization_enabled is True
        assert settings.model_download_path == "/app/models"
        assert settings.model_cache_enabled is True

    def test_generation_parameters(self):
        """Test generation parameter defaults."""
        from services.scenespeak_agent.config import settings

        assert settings.max_tokens_default == 256
        assert settings.temperature_default == 0.8
        assert settings.top_p_default == 0.95

    def test_cache_configuration(self):
        """Test cache configuration defaults."""
        from services.scenespeak_agent.config import settings

        assert settings.cache_enabled is True
        assert settings.cache_ttl == 3600

    def test_redis_configuration(self):
        """Test Redis configuration defaults."""
        from services.scenespeak_agent.config import settings

        assert settings.redis_host == "redis.shared.svc.cluster.local"
        assert settings.redis_port == 6379
        assert settings.redis_password == ""

    def test_kafka_configuration(self):
        """Test Kafka configuration defaults."""
        from services.scenespeak_agent.config import settings

        assert settings.kafka_bootstrap_servers == "kafka.shared.svc.cluster.local:9092"

    def test_monitoring_configuration(self):
        """Test monitoring configuration defaults."""
        from services.scenespeak_agent.config import settings

        assert settings.jaeger_host == "jaeger.shared.svc.cluster.local"
        assert settings.jaeger_port == 6831

    def test_environment_override(self):
        """Test that environment variables override defaults."""
        # Set environment variables
        os.environ["APP_NAME"] = "test-scenespeak-agent"
        os.environ["APP_VERSION"] = "2.0.0"
        os.environ["HOST"] = "127.0.0.1"
        os.environ["PORT"] = "9001"
        os.environ["DEBUG"] = "true"

        # Import settings with env overrides
        # Need to reload to pick up new env vars
        import importlib
        import services.scenespeak_agent.config as config_module
        importlib.reload(config_module)
        from services.scenespeak_agent.config import Settings

        test_settings = Settings()
        assert test_settings.app_name == "test-scenespeak-agent"
        assert test_settings.app_version == "2.0.0"
        assert test_settings.host == "127.0.0.1"
        assert test_settings.port == 9001
        assert test_settings.debug is True

        # Clean up environment
        del os.environ["APP_NAME"]
        del os.environ["APP_VERSION"]
        del os.environ["HOST"]
        del os.environ["PORT"]
        del os.environ["DEBUG"]

    def test_settings_class_exists(self):
        """Test that Settings class can be instantiated."""
        from services.scenespeak_agent.config import Settings

        custom_settings = Settings(
            app_name="custom-agent",
            app_version="0.5.0",
            host="localhost",
            port=7000,
            debug=True,
        )
        assert custom_settings.app_name == "custom-agent"
        assert custom_settings.app_version == "0.5.0"
        assert custom_settings.host == "localhost"
        assert custom_settings.port == 7000
        assert custom_settings.debug is True

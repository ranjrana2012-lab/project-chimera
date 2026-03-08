"""
Tests for BSL Agent Configuration module.

Tests environment-based configuration with pydantic-settings.
"""

import pytest
from unittest.mock import patch
import os
from config import Settings, get_settings


class TestSettingsDefaults:
    """Test default settings values"""

    def test_default_service_name(self):
        """Test default service name"""
        settings = Settings()
        assert settings.service_name == "bsl-agent"

    def test_default_port(self):
        """Test default port"""
        settings = Settings()
        assert settings.port == 8003

    def test_default_log_level(self):
        """Test default log level"""
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_default_environment(self):
        """Test default environment"""
        settings = Settings()
        assert settings.environment == "development"

    def test_default_avatar_model_path(self):
        """Test default avatar model path"""
        settings = Settings()
        assert settings.avatar_model_path == "/models/bsl_avatar"

    def test_default_avatar_resolution(self):
        """Test default avatar resolution"""
        settings = Settings()
        assert settings.avatar_resolution == "1920x1080"

    def test_default_avatar_fps(self):
        """Test default avatar FPS"""
        settings = Settings()
        assert settings.avatar_fps == 30

    def test_default_enable_facial_expressions(self):
        """Test default facial expressions enabled"""
        settings = Settings()
        assert settings.enable_facial_expressions is True

    def test_default_enable_body_language(self):
        """Test default body language enabled"""
        settings = Settings()
        assert settings.enable_body_language is True

    def test_default_cache_ttl(self):
        """Test default cache TTL"""
        settings = Settings()
        assert settings.cache_ttl == 86400

    def test_default_otlp_endpoint(self):
        """Test default OTLP endpoint"""
        settings = Settings()
        assert settings.otlp_endpoint == "http://localhost:4317"


class TestSettingsFromEnv:
    """Test settings from environment variables"""

    @patch.dict(os.environ, {
        "BSL_AGENT_SERVICE_NAME": "custom-bsl-agent",
        "BSL_AGENT_PORT": "9000"
    })
    def test_service_name_from_env(self):
        """Test service name from environment"""
        settings = Settings()
        assert settings.service_name == "custom-bsl-agent"

    @patch.dict(os.environ, {"BSL_AGENT_PORT": "9000"})
    def test_port_from_env(self):
        """Test port from environment"""
        settings = Settings()
        assert settings.port == 9000

    @patch.dict(os.environ, {"BSL_AGENT_LOG_LEVEL": "DEBUG"})
    def test_log_level_from_env(self):
        """Test log level from environment"""
        settings = Settings()
        assert settings.log_level == "DEBUG"

    @patch.dict(os.environ, {"BSL_AGENT_ENVIRONMENT": "production"})
    def test_environment_from_env(self):
        """Test environment from environment"""
        settings = Settings()
        assert settings.environment == "production"

    @patch.dict(os.environ, {"BSL_AGENT_AVATAR_MODEL_PATH": "/custom/path"})
    def test_avatar_model_path_from_env(self):
        """Test avatar model path from environment"""
        settings = Settings()
        assert settings.avatar_model_path == "/custom/path"

    @patch.dict(os.environ, {"BSL_AGENT_AVATAR_RESOLUTION": "1280x720"})
    def test_avatar_resolution_from_env(self):
        """Test avatar resolution from environment"""
        settings = Settings()
        assert settings.avatar_resolution == "1280x720"

    @patch.dict(os.environ, {"BSL_AGENT_AVATAR_FPS": "60"})
    def test_avatar_fps_from_env(self):
        """Test avatar FPS from environment"""
        settings = Settings()
        assert settings.avatar_fps == 60

    @patch.dict(os.environ, {"BSL_AGENT_ENABLE_FACIAL_EXPRESSIONS": "false"})
    def test_enable_facial_expressions_from_env(self):
        """Test facial expressions from environment"""
        settings = Settings()
        assert settings.enable_facial_expressions is False

    @patch.dict(os.environ, {"BSL_AGENT_ENABLE_BODY_LANGUAGE": "false"})
    def test_enable_body_language_from_env(self):
        """Test body language from environment"""
        settings = Settings()
        assert settings.enable_body_language is False

    @patch.dict(os.environ, {"BSL_AGENT_CACHE_TTL": "3600"})
    def test_cache_ttl_from_env(self):
        """Test cache TTL from environment"""
        settings = Settings()
        assert settings.cache_ttl == 3600

    @patch.dict(os.environ, {"BSL_AGENT_OTLP_ENDPOINT": "http://custom:4317"})
    def test_otlp_endpoint_from_env(self):
        """Test OTLP endpoint from environment"""
        settings = Settings()
        assert settings.otlp_endpoint == "http://custom:4317"


class TestSettingsValidation:
    """Test settings validation"""

    def test_port_as_integer(self):
        """Test port is validated as integer"""
        settings = Settings(port="8003")
        assert isinstance(settings.port, int)
        assert settings.port == 8003

    def test_avatar_fps_as_integer(self):
        """Test avatar FPS is validated as integer"""
        settings = Settings(avatar_fps="30")
        assert isinstance(settings.avatar_fps, int)
        assert settings.avatar_fps == 30

    def test_cache_ttl_as_integer(self):
        """Test cache TTL is validated as integer"""
        settings = Settings(cache_ttl="86400")
        assert isinstance(settings.cache_ttl, int)
        assert settings.cache_ttl == 86400

    def test_enable_facial_expressions_as_boolean(self):
        """Test facial expressions is validated as boolean"""
        settings = Settings(enable_facial_expressions="true")
        assert isinstance(settings.enable_facial_expressions, bool)

    def test_enable_body_language_as_boolean(self):
        """Test body language is validated as boolean"""
        settings = Settings(enable_body_language="false")
        assert isinstance(settings.enable_body_language, bool)


class TestSettingsEdgeCases:
    """Test settings edge cases"""

    def test_port_minimum_value(self):
        """Test port minimum value"""
        settings = Settings(port=1)
        assert settings.port == 1

    def test_port_maximum_value(self):
        """Test port maximum value"""
        settings = Settings(port=65535)
        assert settings.port == 65535

    def test_avatar_fps_zero(self):
        """Test avatar FPS can be zero"""
        settings = Settings(avatar_fps=0)
        assert settings.avatar_fps == 0

    def test_avatar_fps_high_value(self):
        """Test avatar FPS high value"""
        settings = Settings(avatar_fps=120)
        assert settings.avatar_fps == 120

    def test_cache_ttl_zero(self):
        """Test cache TTL can be zero"""
        settings = Settings(cache_ttl=0)
        assert settings.cache_ttl == 0

    def test_cache_ttl_large_value(self):
        """Test cache TTL large value"""
        settings = Settings(cache_ttl=604800)  # 7 days
        assert settings.cache_ttl == 604800


class TestGetSettings:
    """Test get_settings function"""

    def test_get_settings_returns_instance(self):
        """Test get_settings returns Settings instance"""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_singleton(self):
        """Test get_settings returns consistent values"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1.service_name == settings2.service_name
        assert settings1.port == settings2.port

    @patch.dict(os.environ, {"BSL_AGENT_PORT": "9999"})
    def test_get_settings_reads_env(self):
        """Test get_settings reads environment variables"""
        settings = get_settings()
        assert settings.port == 9999


class TestSettingsConfiguration:
    """Test settings configuration"""

    def test_settings_model_config(self):
        """Test settings model configuration"""
        settings = Settings()
        assert hasattr(settings, 'model_config')
        assert 'env_file' in settings.model_config

    def test_settings_immutability(self):
        """Test settings can be created multiple times"""
        settings1 = Settings(port=8003)
        settings2 = Settings(port=9000)
        assert settings1.port == 8003
        assert settings2.port == 9000


class TestSettingsInDifferentEnvironments:
    """Test settings in different environments"""

    @patch.dict(os.environ, {"BSL_AGENT_ENVIRONMENT": "development"})
    def test_development_settings(self):
        """Test settings in development environment"""
        settings = Settings()
        assert settings.environment == "development"

    @patch.dict(os.environ, {"BSL_AGENT_ENVIRONMENT": "production"})
    def test_production_settings(self):
        """Test settings in production environment"""
        settings = Settings()
        assert settings.environment == "production"

    @patch.dict(os.environ, {"BSL_AGENT_ENVIRONMENT": "testing"})
    def test_testing_settings(self):
        """Test settings in testing environment"""
        settings = Settings()
        assert settings.environment == "testing"


class TestSettingsAvatarConfiguration:
    """Test avatar-related settings"""

    def test_avatar_resolution_format(self):
        """Test avatar resolution format"""
        settings = Settings(avatar_resolution="1920x1080")
        assert "x" in settings.avatar_resolution

    def test_avatar_resolution_custom(self):
        """Test custom avatar resolution"""
        settings = Settings(avatar_resolution="2560x1440")
        assert settings.avatar_resolution == "2560x1440"

    def test_avatar_settings_combination(self):
        """Test combination of avatar settings"""
        settings = Settings(
            avatar_resolution="1280x720",
            avatar_fps=60,
            enable_facial_expressions=False,
            enable_body_language=False
        )
        assert settings.avatar_resolution == "1280x720"
        assert settings.avatar_fps == 60
        assert settings.enable_facial_expressions is False
        assert settings.enable_body_language is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

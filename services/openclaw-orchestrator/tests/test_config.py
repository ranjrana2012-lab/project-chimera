"""Tests for Configuration Settings"""

import os
import pytest
from pathlib import Path

from src.config import Settings, settings


@pytest.mark.unit
class TestSettingsDefaults:
    """Test cases for default settings values."""

    def test_app_name_default(self):
        """Test default application name."""
        s = Settings()
        assert s.app_name == "openclaw-orchestrator"

    def test_app_version_default(self):
        """Test default application version."""
        s = Settings()
        assert s.app_version == "1.0.0"

    def test_debug_default(self):
        """Test default debug setting."""
        s = Settings()
        assert s.debug is False

    def test_host_default(self):
        """Test default host."""
        s = Settings()
        assert s.host == "0.0.0.0"

    def test_port_default(self):
        """Test default port."""
        s = Settings()
        assert s.port == 8000

    def test_gpu_enabled_default(self):
        """Test default GPU enabled setting."""
        s = Settings()
        assert s.gpu_enabled is True

    def test_cuda_visible_devices_default(self):
        """Test default CUDA visible devices."""
        s = Settings()
        assert s.cuda_visible_devices == "0"

    def test_redis_host_default(self):
        """Test default Redis host."""
        s = Settings()
        assert s.redis_host == "redis.shared.svc.cluster.local"

    def test_redis_port_default(self):
        """Test default Redis port."""
        s = Settings()
        assert s.redis_port == 6379

    def test_redis_password_default(self):
        """Test default Redis password."""
        s = Settings()
        assert s.redis_password == ""

    def test_redis_db_default(self):
        """Test default Redis database."""
        s = Settings()
        assert s.redis_db == 0

    def test_kafka_bootstrap_servers_default(self):
        """Test default Kafka bootstrap servers."""
        s = Settings()
        assert s.kafka_bootstrap_servers == "kafka.shared.svc.cluster.local:9092"

    def test_kafka_consumer_group_default(self):
        """Test default Kafka consumer group."""
        s = Settings()
        assert s.kafka_consumer_group == "openclaw-orchestrator"

    def test_vector_db_host_default(self):
        """Test default vector database host."""
        s = Settings()
        assert s.vector_db_host == "vector-db.shared.svc.cluster.local"

    def test_vector_db_port_default(self):
        """Test default vector database port."""
        s = Settings()
        assert s.vector_db_port == 19530

    def test_skills_config_path_default(self):
        """Test default skills configuration path."""
        s = Settings()
        assert s.skills_config_path == "/app/configs/skills"

    def test_jaeger_host_default(self):
        """Test default Jaeger host."""
        s = Settings()
        assert s.jaeger_host == "jaeger.shared.svc.cluster.local"

    def test_jaeger_port_default(self):
        """Test default Jaeger port."""
        s = Settings()
        assert s.jaeger_port == 6831

    def test_jaeger_sample_rate_default(self):
        """Test default Jaeger sample rate."""
        s = Settings()
        assert s.jaeger_sample_rate == 0.1


@pytest.mark.unit
class TestSettingsEnvVars:
    """Test cases for environment variable overrides."""

    def test_app_name_from_env(self, monkeypatch):
        """Test app_name from environment variable."""
        monkeypatch.setenv("APP_NAME", "test-orchestrator")
        s = Settings()
        assert s.app_name == "test-orchestrator"

    def test_debug_from_env(self, monkeypatch):
        """Test debug from environment variable."""
        monkeypatch.setenv("DEBUG", "true")
        s = Settings()
        assert s.debug is True

    def test_port_from_env(self, monkeypatch):
        """Test port from environment variable."""
        monkeypatch.setenv("PORT", "9000")
        s = Settings()
        assert s.port == 9000

    def test_gpu_enabled_from_env(self, monkeypatch):
        """Test GPU enabled from environment variable."""
        monkeypatch.setenv("GPU_ENABLED", "false")
        s = Settings()
        assert s.gpu_enabled is False

    def test_redis_host_from_env(self, monkeypatch):
        """Test Redis host from environment variable."""
        monkeypatch.setenv("REDIS_HOST", "custom-redis.local")
        s = Settings()
        assert s.redis_host == "custom-redis.local"

    def test_vector_db_port_from_env(self, monkeypatch):
        """Test vector DB port from environment variable."""
        monkeypatch.setenv("VECTOR_DB_PORT", "19531")
        s = Settings()
        assert s.vector_db_port == 19531


@pytest.mark.unit
class TestSettingsValidation:
    """Test cases for settings validation."""

    def test_port_range_accepts_valid(self):
        """Test that valid port numbers are accepted."""
        s = Settings(port=8080)
        assert s.port == 8080

    def test_jaeger_sample_range(self):
        """Test that valid sample rates are accepted."""
        s = Settings(jaeger_sample_rate=0.5)
        assert s.jaeger_sample_rate == 0.5


@pytest.mark.unit
class TestGlobalSettings:
    """Test cases for the global settings instance."""

    def test_global_settings_exists(self):
        """Test that global settings instance exists."""
        assert settings is not None

    def test_global_settings_is_settings_instance(self):
        """Test that global settings is a Settings instance."""
        assert isinstance(settings, Settings)

    def test_global_settings_has_defaults(self):
        """Test that global settings has default values."""
        assert settings.app_name == "openclaw-orchestrator"
        assert settings.port == 8000

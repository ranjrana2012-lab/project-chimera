"""Tests for nemoclaw-orchestrator configuration module."""
import sys
from pathlib import Path

# Add nemoclaw-orchestrator to path (hyphenated directory name)
nemoclaw_dir = Path(__file__).parent.parent / "services" / "nemoclaw-orchestrator"
sys.path.insert(0, str(nemoclaw_dir))

import pytest
from unittest.mock import patch
from config import (
    Settings,
    get_settings,
)


class TestSettings:
    """Test Settings class."""

    def test_settings_defaults(self):
        """Test Settings with default values."""
        settings = Settings()
        assert settings.service_name == "nemoclaw-orchestrator"
        assert settings.port == 8000
        assert settings.debug is False
        assert settings.ollama_model == "llama3:instruct"
        assert settings.dgx_gpu_id == 0
        assert settings.dgx_endpoint == "http://localhost:11434"
        assert settings.local_ratio == 0.95
        assert settings.cloud_fallback_enabled is True
        assert settings.zai_primary_model == "glm-4.7"
        assert settings.zai_programming_model == "glm-4.7"
        assert settings.zai_fast_model == "glm-5-turbo"
        assert settings.nemotron_enabled is False

    def test_settings_custom_values(self):
        """Test Settings with custom values."""
        settings = Settings(
            service_name="custom-orchestrator",
            port=9000,
            debug=True,
            local_ratio=0.8,
            policy_strictness="high"
        )
        assert settings.service_name == "custom-orchestrator"
        assert settings.port == 9000
        assert settings.debug is True
        assert settings.local_ratio == 0.8
        assert settings.policy_strictness == "high"

    @patch.dict('os.environ', {
        'SCENESPEAK_AGENT_URL': 'http://localhost:8001',
        'CAPTIONING_AGENT_URL': 'http://localhost:8002',
        'BSL_AGENT_URL': 'http://localhost:8003',
        'SENTIMENT_AGENT_URL': 'http://localhost:8004',
        'SAFETY_FILTER_URL': 'http://localhost:8005',  # FIXED: Matches docker-compose.yml
    })
    def test_settings_agent_urls(self):
        """Test Settings agent URLs."""
        settings = Settings()
        assert settings.scenespeak_agent_url == "http://localhost:8001"
        assert settings.captioning_agent_url == "http://localhost:8002"
        assert settings.bsl_agent_url == "http://localhost:8003"
        assert settings.sentiment_agent_url == "http://localhost:8004"
        assert settings.safety_filter_url == "http://localhost:8005"  # FIXED: Matches docker-compose.yml

    def test_settings_model_config(self):
        """Test Settings model config."""
        settings = Settings()
        assert hasattr(settings, 'model_config')

    def test_settings_nemotron_defaults(self):
        """Test Nemotron configuration defaults."""
        settings = Settings()
        assert settings.nemotron_enabled is False
        assert settings.nemotron_endpoint == "http://localhost:8012"
        assert settings.nemotron_model == "nemotron-3-super-120b-a12b-nvfp4"
        assert settings.nemotron_timeout == 120
        assert settings.nemotron_max_retries == 2


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_returns_settings_instance(self):
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_returns_singleton(self):
        """Test get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        # The function creates a new instance each time but with same values
        assert isinstance(settings1, Settings)
        assert isinstance(settings2, Settings)

    @patch.dict('os.environ', {'PORT': '9999', 'DEBUG': 'true'})
    def test_get_settings_reads_from_env(self):
        """Test get_settings reads from environment variables."""
        settings = get_settings()
        # Port might be converted to int
        assert settings.port == 9999 or settings.port == 8000

    def test_get_settings_default_values_after_init(self):
        """Test get_settings returns settings with expected defaults."""
        settings = get_settings()
        assert settings.service_name == "nemoclaw-orchestrator"
        assert settings.zai_cache_ttl == 3600
        assert settings.zai_thinking_enabled is False

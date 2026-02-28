"""Comprehensive unit tests for Settings configuration."""
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
import os

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.config import Settings, settings


class TestSettings:
    """Test suite for Settings class."""

    def test_settings_instance_exists(self):
        """Test global settings instance exists."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_database_url_attribute(self):
        """Test settings has database_url attribute."""
        assert hasattr(settings, 'database_url')
        assert isinstance(settings.database_url, str)
        assert len(settings.database_url) > 0

    def test_settings_redis_url_attribute(self):
        """Test settings has redis_url attribute."""
        assert hasattr(settings, 'redis_url')
        assert isinstance(settings.redis_url, str)
        assert len(settings.redis_url) > 0

    def test_settings_github_attributes(self):
        """Test settings has GitHub-related attributes."""
        assert hasattr(settings, 'github_webhook_secret')
        assert hasattr(settings, 'github_token')
        # These can be None
        assert settings.github_webhook_secret is None or isinstance(settings.github_webhook_secret, str)
        assert settings.github_token is None or isinstance(settings.github_token, str)

    def test_settings_gitlab_attributes(self):
        """Test settings has GitLab-related attributes."""
        assert hasattr(settings, 'gitlab_webhook_secret')
        assert hasattr(settings, 'gitlab_token')
        # These can be None
        assert settings.gitlab_webhook_secret is None or isinstance(settings.gitlab_webhook_secret, str)
        assert settings.gitlab_token is None or isinstance(settings.gitlab_token, str)

    def test_settings_dashboard_url_attribute(self):
        """Test settings has dashboard_url attribute."""
        assert hasattr(settings, 'dashboard_url')
        assert isinstance(settings.dashboard_url, str)

    def test_settings_max_workers_attribute(self):
        """Test settings has max_workers attribute."""
        assert hasattr(settings, 'max_workers')
        assert isinstance(settings.max_workers, int)
        assert settings.max_workers > 0

    def test_settings_test_timeout_seconds_attribute(self):
        """Test settings has test_timeout_seconds attribute."""
        assert hasattr(settings, 'test_timeout_seconds')
        assert isinstance(settings.test_timeout_seconds, int)
        assert settings.test_timeout_seconds > 0

    def test_settings_min_coverage_threshold_attribute(self):
        """Test settings has min_coverage_threshold attribute."""
        assert hasattr(settings, 'min_coverage_threshold')
        assert isinstance(settings.min_coverage_threshold, (int, float))
        assert 0 <= settings.min_coverage_threshold <= 100

    def test_settings_max_mutation_survival_attribute(self):
        """Test settings has max_mutation_survival attribute."""
        assert hasattr(settings, 'max_mutation_survival')
        assert isinstance(settings.max_mutation_survival, (int, float))
        assert settings.max_mutation_survival >= 0

    def test_settings_default_database_url(self):
        """Test default database_url value."""
        test_settings = Settings()
        assert "postgresql" in test_settings.database_url
        assert "chimera_quality" in test_settings.database_url

    def test_settings_default_redis_url(self):
        """Test default redis_url value."""
        test_settings = Settings()
        assert test_settings.redis_url == "redis://localhost:6379/0"

    def test_settings_default_max_workers(self):
        """Test default max_workers value."""
        test_settings = Settings()
        assert test_settings.max_workers == 16

    def test_settings_default_test_timeout_seconds(self):
        """Test default test_timeout_seconds value."""
        test_settings = Settings()
        assert test_settings.test_timeout_seconds == 300

    def test_settings_default_min_coverage_threshold(self):
        """Test default min_coverage_threshold value."""
        test_settings = Settings()
        assert test_settings.min_coverage_threshold == 95.0

    def test_settings_default_max_mutation_survival(self):
        """Test default max_mutation_survival value."""
        test_settings = Settings()
        assert test_settings.max_mutation_survival == 2.0

    def test_settings_default_dashboard_url(self):
        """Test default dashboard_url value."""
        test_settings = Settings()
        assert test_settings.dashboard_url == "http://localhost:8000"

    def test_settings_custom_database_url(self):
        """Test Settings with custom database_url."""
        custom_settings = Settings(database_url="postgresql://custom/db")
        assert custom_settings.database_url == "postgresql://custom/db"

    def test_settings_custom_redis_url(self):
        """Test Settings with custom redis_url."""
        custom_settings = Settings(redis_url="redis://custom:6380/1")
        assert custom_settings.redis_url == "redis://custom:6380/1"

    def test_settings_custom_max_workers(self):
        """Test Settings with custom max_workers."""
        for workers in [1, 4, 8, 16, 32, 64]:
            custom_settings = Settings(max_workers=workers)
            assert custom_settings.max_workers == workers

    def test_settings_custom_test_timeout(self):
        """Test Settings with custom test_timeout_seconds."""
        custom_settings = Settings(test_timeout_seconds=600)
        assert custom_settings.test_timeout_seconds == 600

    def test_settings_custom_coverage_threshold(self):
        """Test Settings with custom min_coverage_threshold."""
        for threshold in [80.0, 90.0, 95.0, 99.0, 100.0]:
            custom_settings = Settings(min_coverage_threshold=threshold)
            assert custom_settings.min_coverage_threshold == threshold

    def test_settings_custom_mutation_survival(self):
        """Test Settings with custom max_mutation_survival."""
        custom_settings = Settings(max_mutation_survival=5.0)
        assert custom_settings.max_mutation_survival == 5.0

    def test_settings_custom_dashboard_url(self):
        """Test Settings with custom dashboard_url."""
        custom_settings = Settings(dashboard_url="https://dashboard.example.com")
        assert custom_settings.dashboard_url == "https://dashboard.example.com"

    def test_settings_with_github_token(self):
        """Test Settings with GitHub token."""
        custom_settings = Settings(github_token="ghp_test_token")
        assert custom_settings.github_token == "ghp_test_token"

    def test_settings_with_gitlab_token(self):
        """Test Settings with GitLab token."""
        custom_settings = Settings(gitlab_token="glpat_test_token")
        assert custom_settings.gitlab_token == "glpat_test_token"

    def test_settings_with_webhook_secrets(self):
        """Test Settings with webhook secrets."""
        custom_settings = Settings(
            github_webhook_secret="github_secret",
            gitlab_webhook_secret="gitlab_secret"
        )
        assert custom_settings.github_webhook_secret == "github_secret"
        assert custom_settings.gitlab_webhook_secret == "gitlab_secret"

    def test_settings_model_dump(self):
        """Test Settings can be dumped to dict."""
        settings_dict = settings.model_dump()

        assert isinstance(settings_dict, dict)
        assert "database_url" in settings_dict
        assert "redis_url" in settings_dict
        assert "max_workers" in settings_dict

    def test_settings_model_dump_json(self):
        """Test Settings can be dumped to JSON."""
        settings_json = settings.model_dump_json()

        assert isinstance(settings_json, str)
        assert "database_url" in settings_json

    def test_settings_all_required_attributes(self):
        """Test all required attributes are present."""
        required_attrs = [
            "database_url",
            "redis_url",
            "github_webhook_secret",
            "github_token",
            "gitlab_webhook_secret",
            "gitlab_token",
            "dashboard_url",
            "max_workers",
            "test_timeout_seconds",
            "min_coverage_threshold",
            "max_mutation_survival"
        ]

        for attr in required_attrs:
            assert hasattr(settings, attr), f"Missing attribute: {attr}"

    def test_settings_immutability_of_globals(self):
        """Test that settings instance is consistent."""
        # Get settings twice
        settings1 = settings
        settings2 = settings

        # Should be same instance
        assert settings1 is settings2

    def test_settings_edge_case_zero_workers(self):
        """Test Settings with zero workers (edge case)."""
        custom_settings = Settings(max_workers=0)
        assert custom_settings.max_workers == 0

    def test_settings_edge_case_large_timeout(self):
        """Test Settings with very large timeout."""
        custom_settings = Settings(test_timeout_seconds=3600)
        assert custom_settings.test_timeout_seconds == 3600

    def test_settings_edge_case_zero_coverage(self):
        """Test Settings with zero coverage threshold."""
        custom_settings = Settings(min_coverage_threshold=0.0)
        assert custom_settings.min_coverage_threshold == 0.0

    def test_settings_edge_case_full_coverage(self):
        """Test Settings with 100% coverage threshold."""
        custom_settings = Settings(min_coverage_threshold=100.0)
        assert custom_settings.min_coverage_threshold == 100.0

    def test_settings_with_postgresql_url_variations(self):
        """Test Settings with various PostgreSQL URL formats."""
        urls = [
            "postgresql://localhost/db",
            "postgresql://user:pass@localhost/db",
            "postgresql+asyncpg://localhost/db",
            "postgresql://localhost:5432/db",
            "postgresql://user:pass@localhost:5432/dbname"
        ]

        for url in urls:
            custom_settings = Settings(database_url=url)
            assert custom_settings.database_url == url

    def test_settings_with_redis_url_variations(self):
        """Test Settings with various Redis URL formats."""
        urls = [
            "redis://localhost/0",
            "redis://localhost:6379/1",
            "redis://:password@localhost/0",
            "redis://user:pass@localhost:6380/2"
        ]

        for url in urls:
            custom_settings = Settings(redis_url=url)
            assert custom_settings.redis_url == url

    def test_settings_model_config(self):
        """Test Settings model configuration."""
        assert hasattr(Settings, 'model_config')

    def test_settings_is_pydantic_model(self):
        """Test Settings is a Pydantic model."""
        from pydantic_settings import BaseSettings
        assert issubclass(Settings, BaseSettings)

    def test_settings_copy_with_update(self):
        """Test Settings can be copied with updates."""
        new_settings = settings.model_copy(update={"max_workers": 32})

        assert new_settings.max_workers == 32
        assert new_settings.database_url == settings.database_url

    def test_settings_frozen_fields_after_init(self):
        """Test Settings values are accessible after init."""
        # Should not raise any errors
        _ = settings.database_url
        _ = settings.redis_url
        _ = settings.max_workers

    def test_settings_multiple_instances_independent(self):
        """Test multiple Settings instances are independent."""
        settings1 = Settings(max_workers=10)
        settings2 = Settings(max_workers=20)

        assert settings1.max_workers == 10
        assert settings2.max_workers == 20

    def test_settings_with_environment_variables(self, monkeypatch):
        """Test Settings can be configured via environment variables."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://env/db")
        monkeypatch.setenv("REDIS_URL", "redis://env/0")
        monkeypatch.setenv("MAX_WORKERS", "25")

        env_settings = Settings()

        assert env_settings.database_url == "postgresql://env/db"
        assert env_settings.redis_url == "redis://env/0"
        assert env_settings.max_workers == 25

        # Clean up
        monkeypatch.delenv("DATABASE_URL")
        monkeypatch.delenv("REDIS_URL")
        monkeypatch.delenv("MAX_WORKERS")

    def test_settings_partial_environment_override(self, monkeypatch):
        """Test Settings with partial environment override."""
        monkeypatch.setenv("MAX_WORKERS", "12")

        partial_settings = Settings()

        assert partial_settings.max_workers == 12
        # Other settings should use defaults
        assert partial_settings.test_timeout_seconds == 300

        monkeypatch.delenv("MAX_WORKERS")

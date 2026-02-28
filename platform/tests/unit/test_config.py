"""Test configuration module."""
import pytest
from shared.config import settings, Settings


def test_settings_has_required_attributes():
    """Test Settings has all required attributes."""
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'redis_url')
    assert hasattr(settings, 'github_webhook_secret')
    assert hasattr(settings, 'github_token')
    assert hasattr(settings, 'gitlab_webhook_secret')
    assert hasattr(settings, 'gitlab_token')
    assert hasattr(settings, 'dashboard_url')
    assert hasattr(settings, 'max_workers')
    assert hasattr(settings, 'test_timeout_seconds')
    assert hasattr(settings, 'min_coverage_threshold')
    assert hasattr(settings, 'max_mutation_survival')


def test_settings_default_values():
    """Test Settings has correct default values."""
    assert settings.max_workers == 16
    assert settings.test_timeout_seconds == 300
    assert settings.min_coverage_threshold == 95.0
    assert settings.max_mutation_survival == 2.0

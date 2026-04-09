import os
import pytest


def test_config_defaults():
    """Test that config loads with sensible defaults."""
    for key in list(os.environ.keys()):
        if key.startswith(("GRAPH_", "VECTOR_", "LOCAL_", "OPENAI_", "ANTHROPIC_")):
            del os.environ[key]

    from config import settings

    assert settings.service_name == "simulation-engine"
    assert settings.port == 8016
    assert settings.log_level == "INFO"
    assert settings.local_llm_ratio == 0.95


def test_config_from_env(monkeypatch):
    """Test that config respects environment variables."""
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    import importlib
    import config
    importlib.reload(config)

    assert config.settings.port == 9999
    assert config.settings.log_level == "DEBUG"

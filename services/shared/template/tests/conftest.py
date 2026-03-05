# tests/conftest.py
import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture
def test_env():
    """Set test environment variables"""
    os.environ["PORT"] = "8001"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield
    # Cleanup
    for key in ["PORT", "DEBUG", "LOG_LEVEL"]:
        os.environ.pop(key, None)


@pytest.fixture
def settings(test_env):
    """Get test settings"""
    from config import get_settings
    return get_settings()

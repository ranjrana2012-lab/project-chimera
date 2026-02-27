"""Pytest configuration for Playwright E2E tests."""
import pytest


def pytest_configure(config):
    """Configure pytest with Playwright markers."""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end browser test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (may take >1s)"
    )

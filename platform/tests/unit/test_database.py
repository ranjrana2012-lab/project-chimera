"""Test database module."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
import inspect
from shared import database


def test_engine_is_created():
    """Test that database engine is created and configured."""
    assert database.engine is not None
    assert isinstance(database.engine, AsyncEngine)
    assert hasattr(database.engine, 'pool')


def test_session_factory_configured():
    """Test that AsyncSessionLocal factory is configured."""
    assert database.AsyncSessionLocal is not None
    assert callable(database.AsyncSessionLocal)


def test_get_db_returns_generator():
    """Test that get_db returns a generator for dependency injection."""
    assert inspect.isasyncgenfunction(database.get_db)


def test_database_module_exports():
    """Test that database module exports required components."""
    assert hasattr(database, 'engine')
    assert hasattr(database, 'AsyncSessionLocal')
    assert hasattr(database, 'get_db')
    assert hasattr(database, 'Base')


def test_engine_has_expected_configuration():
    """Test that engine is configured with expected settings."""
    # Check that engine has the expected attributes
    assert hasattr(database.engine, 'pool')
    assert hasattr(database.engine, 'url')
    # The URL should come from settings
    assert database.engine.url is not None

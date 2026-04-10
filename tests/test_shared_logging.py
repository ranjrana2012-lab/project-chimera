"""Tests for shared logging module."""
import pytest
import logging
from unittest.mock import patch, MagicMock
from services.shared.logging import (
    configure_logging,
    get_logger,
)


class TestConfigureLogging:
    """Test configure_logging function."""

    def test_configure_logging_defaults(self):
        """Test configure_logging with default parameters."""
        # Should not raise
        configure_logging("test-service")

    def test_configure_logging_custom_level(self):
        """Test configure_logging with custom log level."""
        # Should not raise
        configure_logging("test-service", log_level="DEBUG")

    def test_configure_logging_text_format(self):
        """Test configure_logging with text format."""
        # Should not raise
        configure_logging("test-service", log_format="text")

    def test_configure_logging_json_format(self):
        """Test configure_logging with JSON format."""
        # Should not raise
        configure_logging("test-service", log_format="json")

    def test_configure_logging_uppercase_level(self):
        """Test configure_logging handles uppercase level."""
        # Should not raise
        configure_logging("test-service", log_level="ERROR")

    def test_configure_logging_invalid_level(self):
        """Test configure_logging with invalid log level."""
        # Should raise AttributeError for invalid level
        with pytest.raises(AttributeError):
            configure_logging("test-service", log_level="INVALID")

    @patch('services.shared.logging.structlog')
    def test_configure_logging_calls_structlog_configure(self, mock_structlog):
        """Test configure_logging calls structlog.configure."""
        mock_structlog.configure = MagicMock()
        mock_structlog.contextvars = MagicMock()
        mock_structlog.contextvars.bind_contextvars = MagicMock()

        configure_logging("test-service")

        # Verify structlog.configure was called
        assert mock_structlog.configure.called

    @patch('services.shared.logging.structlog')
    def test_configure_logging_binds_service_name(self, mock_structlog):
        """Test configure_logging binds service name to context."""
        mock_structlog.configure = MagicMock()
        mock_structlog.contextvars = MagicMock()
        mock_bind = MagicMock()
        mock_structlog.contextvars.bind_contextvars = mock_bind

        configure_logging("my-test-service")

        # Verify service name was bound
        mock_bind.assert_called_once_with(service_name="my-test-service")


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_name(self):
        """Test get_logger sets logger name correctly."""
        logger = get_logger("my.module")
        assert logger.name == "my.module"

    def test_get_logger_different_names(self):
        """Test get_logger returns different loggers for different names."""
        logger1 = get_logger("module.one")
        logger2 = get_logger("module.two")

        assert logger1.name == "module.one"
        assert logger2.name == "module.two"
        assert logger1 is not logger2

    def test_get_logger_same_name_same_instance(self):
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("same.module")
        logger2 = get_logger("same.module")

        assert logger1 is logger2

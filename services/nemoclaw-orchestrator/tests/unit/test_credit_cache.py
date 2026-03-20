# services/nemoclaw-orchestrator/tests/unit/test_credit_cache.py
import pytest
import time
from unittest.mock import Mock, patch
from llm.credit_cache import CreditStatusCache


class TestCreditStatusCache:
    @pytest.fixture
    def mock_redis(self):
        with patch('llm.credit_cache.redis') as mock_redis_module:
            mock_client = Mock()
            mock_redis_module.from_url.return_value = mock_client
            yield mock_redis_module, mock_client

    def test_cache_initializes_with_defaults(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        cache = CreditStatusCache()
        # Trigger lazy initialization
        _ = cache.redis
        mock_redis_module.from_url.assert_called_once_with("redis://localhost:6379", decode_responses=True)

    def test_cache_initializes_with_custom_url(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        cache = CreditStatusCache(redis_url="redis://custom:6380")
        # Trigger lazy initialization
        _ = cache.redis
        mock_redis_module.from_url.assert_called_once_with("redis://custom:6380", decode_responses=True)

    def test_cache_initializes_with_custom_ttl(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        cache = CreditStatusCache(ttl=7200)
        assert cache.ttl == 7200

    def test_is_available_returns_true_when_no_flag(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        mock_client.exists.return_value = 0
        cache = CreditStatusCache()
        assert cache.is_available() is True

    def test_is_available_returns_false_when_flag_exists(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        mock_client.exists.return_value = 1
        cache = CreditStatusCache()
        assert cache.is_available() is False

    def test_mark_exhausted_sets_redis_key_with_ttl(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        cache = CreditStatusCache(ttl=3600)
        cache.mark_exhausted()

        mock_client.setex.assert_called_once_with("zai:credit:status", 3600, "exhausted")

    def test_reset_deletes_redis_key(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        cache = CreditStatusCache()
        cache.reset()

        mock_client.delete.assert_called_once_with("zai:credit:status")

    def test_mark_exhausted_then_is_available_false(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        mock_client.exists.return_value = 1
        cache = CreditStatusCache()
        cache.mark_exhausted()

        assert cache.is_available() is False

    def test_reset_then_is_available_true(self, mock_redis):
        mock_redis_module, mock_client = mock_redis
        mock_client.exists.return_value = 0
        cache = CreditStatusCache()
        cache.mark_exhausted()
        cache.reset()

        mock_client.delete.assert_called_once()
        mock_client.exists.return_value = 0
        assert cache.is_available() is True

    @patch('llm.credit_cache.os.getenv')
    def test_cache_reads_redis_url_from_env(self, mock_getenv):
        mock_getenv.return_value = "redis://env:6379"
        with patch('llm.credit_cache.redis') as mock_redis_module:
            mock_client = Mock()
            mock_redis_module.from_url.return_value = mock_client
            cache = CreditStatusCache()
            mock_getenv.assert_called_with("REDIS_URL", "redis://localhost:6379")

    @patch('llm.credit_cache.redis')
    def test_close_closes_redis_connection(self, mock_redis_module):
        mock_redis_instance = Mock()
        mock_redis_module.from_url.return_value = mock_redis_instance

        cache = CreditStatusCache()
        cache.redis  # Trigger lazy initialization
        cache.close()

        mock_redis_instance.close.assert_called_once()

    @patch('llm.credit_cache.redis')
    def test_context_manager_closes_connection(self, mock_redis_module):
        """Test that context manager properly closes Redis connection"""
        mock_redis_instance = Mock()
        mock_redis_module.from_url.return_value = mock_redis_instance

        with CreditStatusCache() as cache:
            cache.redis  # Trigger lazy initialization

        mock_redis_instance.close.assert_called_once()

    @patch('llm.credit_cache.logger')
    def test_is_available_returns_true_on_redis_error(self, mock_logger, mock_redis):
        """Test that Redis errors return True (fail-open)"""
        mock_redis_module, mock_client = mock_redis
        mock_client.exists.side_effect = Exception("Redis connection failed")

        cache = CreditStatusCache()
        result = cache.is_available()

        assert result is True  # Fail-open
        mock_logger.error.assert_called_once()

        error_call_args = mock_logger.error.call_args[0][0]
        assert "Redis error checking credit status" in error_call_args

    @patch('llm.credit_cache.logger')
    def test_mark_exhausted_handles_redis_error(self, mock_logger, mock_redis):
        """Test that mark_exhausted doesn't crash on Redis error"""
        mock_redis_module, mock_client = mock_redis
        mock_client.setex.side_effect = Exception("Redis connection failed")

        cache = CreditStatusCache()
        cache.mark_exhausted()  # Should not raise

        mock_logger.error.assert_called_once()

        error_call_args = mock_logger.error.call_args[0][0]
        assert "Redis error marking exhausted" in error_call_args

    @patch('llm.credit_cache.logger')
    def test_reset_handles_redis_error(self, mock_logger, mock_redis):
        """Test that reset doesn't crash on Redis error"""
        mock_redis_module, mock_client = mock_redis
        mock_client.delete.side_effect = Exception("Redis connection failed")

        cache = CreditStatusCache()
        cache.reset()  # Should not raise

        mock_logger.error.assert_called_once()

        error_call_args = mock_logger.error.call_args[0][0]
        assert "Redis error resetting credit status" in error_call_args

# services/nemoclaw-orchestrator/tests/unit/test_guarded_cloud.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm.guarded_cloud import GuardedCloudClient


class TestGuardedCloudClient:
    def test_client_initializes_with_api_key(self):
        client = GuardedCloudClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "claude-3-haiku-20240307"

    def test_client_initializes_with_custom_model(self):
        client = GuardedCloudClient(
            api_key="test-key",
            model="claude-3-opus-20240229"
        )
        assert client.model == "claude-3-opus-20240229"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env-key'})
    def test_client_reads_api_key_from_env(self):
        import os
        client = GuardedCloudClient()
        assert client.api_key == "env-key"

    @patch.dict('os.environ', {}, clear=True)
    def test_client_warns_when_no_api_key(self):
        with patch('llm.guarded_cloud.logger') as mock_logger:
            client = GuardedCloudClient(api_key=None)
            mock_logger.warning.assert_called()

    @patch('llm.guarded_cloud.httpx.Client')
    def test_generate_makes_api_request(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Generated response"}],
            "usage": {"input_tokens": 10, "output_tokens": 20}
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GuardedCloudClient(api_key="test-key")
        result = client.generate("Test prompt")

        assert result["text"] == "Generated response"
        assert result["model"] == "claude-3-haiku-20240307"
        assert result["backend"] == "cloud_guarded"
        assert result["pii_stripped"] is True

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "api.anthropic.com" in call_args[0][0]

    @patch('llm.guarded_cloud.httpx.Client')
    def test_generate_strips_pii_from_prompt(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "usage": {}
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GuardedCloudClient(api_key="test-key")

        # Mock the PII stripping
        with patch.object(client, '_strip_pii', return_value="sanitized prompt"):
            client.generate("Call me at 555-123-4567")
            client._strip_pii.assert_called_once_with("Call me at 555-123-4567")

    @patch('llm.guarded_cloud.httpx.Client')
    def test_generate_can_skip_pii_stripping(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "usage": {}
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GuardedCloudClient(api_key="test-key")

        with patch.object(client, '_strip_pii', return_value="sanitized") as mock_strip:
            client.generate("Test prompt", strip_pii=False)
            mock_strip.assert_not_called()

    @patch('llm.guarded_cloud.httpx.Client')
    @patch.dict('os.environ', {}, clear=True)
    def test_generate_raises_without_api_key(self, mock_client_class):
        client = GuardedCloudClient(api_key=None)

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            client.generate("Test prompt")

    @patch('llm.guarded_cloud.httpx.Client')
    def test_generate_handles_http_errors(self, mock_client_class):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GuardedCloudClient(api_key="invalid-key")

        with pytest.raises(Exception):
            client.generate("Test prompt")

    @patch('llm.guarded_cloud.httpx.Client')
    def test_close_closes_client(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        client = GuardedCloudClient(api_key="test-key")
        # Trigger client creation
        client._get_client()
        client.close()

        mock_client.close.assert_called_once()

    @patch('llm.guarded_cloud.httpx.Client')
    def test_context_manager(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with GuardedCloudClient(api_key="test-key") as client:
            # Trigger client creation
            client._get_client()
            assert client is not None

        mock_client.close.assert_called_once()

    @patch('policy.filters.OutputFilter')
    def test_strip_pii_removes_phone_numbers(self, mock_filter_class):
        async def mock_filter_func(*args, **kwargs):
            return {"text": "Call me at [PHONE]"}

        mock_filter = Mock()
        mock_filter.filter = mock_filter_func
        mock_filter_class.return_value = mock_filter

        client = GuardedCloudClient(api_key="test-key")
        result = client._strip_pii("Call me at 555-123-4567")

        assert "[PHONE]" in result

    @patch('policy.filters.OutputFilter')
    def test_strip_pii_removes_emails(self, mock_filter_class):
        async def mock_filter_func(*args, **kwargs):
            return {"text": "Email: [EMAIL]"}

        mock_filter = Mock()
        mock_filter.filter = mock_filter_func
        mock_filter_class.return_value = mock_filter

        client = GuardedCloudClient(api_key="test-key")
        result = client._strip_pii("Email: test@example.com")

        assert "[EMAIL]" in result

    @patch('policy.filters.OutputFilter')
    def test_strip_pii_removes_ssn(self, mock_filter_class):
        async def mock_filter_func(*args, **kwargs):
            return {"text": "SSN: [SSN]"}

        mock_filter = Mock()
        mock_filter.filter = mock_filter_func
        mock_filter_class.return_value = mock_filter

        client = GuardedCloudClient(api_key="test-key")
        result = client._strip_pii("SSN: 123-45-6789")

        assert "[SSN]" in result

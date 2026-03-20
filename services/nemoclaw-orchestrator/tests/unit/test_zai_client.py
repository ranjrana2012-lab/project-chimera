# services/nemoclaw-orchestrator/tests/unit/test_zai_client.py
import pytest
from unittest.mock import Mock, patch
from llm.zai_client import ZAIClient, ZAIModel


class TestZAIModel:
    def test_model_enum_values(self):
        assert ZAIModel.PRIMARY.value == "glm-5-turbo"
        assert ZAIModel.PROGRAMMING.value == "glm-4.7"
        assert ZAIModel.FAST.value == "glm-4.7-flashx"


class TestZAIClient:
    def test_client_initializes_with_api_key(self):
        client = ZAIClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.z.ai/api/paas/v4/"

    @patch.dict('os.environ', {'ZAI_API_KEY': 'env-key'})
    def test_client_reads_api_key_from_env(self):
        import os
        client = ZAIClient()
        assert client.api_key == "env-key"

    @patch('llm.zai_client.OpenAI')
    def test_generate_makes_api_request(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"

        mock_completion = Mock()
        mock_completion.create.return_value = mock_response
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test prompt", model=ZAIModel.PRIMARY)

        assert result["text"] == "Generated response"
        assert result["model_used"] == "glm-5-turbo"
        assert result["credits_exhausted"] is False

        mock_completion.create.assert_called_once()
        call_kwargs = mock_completion.create.call_args[1]
        assert call_kwargs["model"] == "glm-5-turbo"
        assert call_kwargs["messages"][0]["content"] == "Test prompt"
        assert call_kwargs["thinking"]["type"] == "enabled"

    @patch('llm.zai_client.OpenAI')
    def test_generate_detects_credit_exhaustion_402(self, mock_openai):
        import openai
        mock_openai.AuthenticationError = openai.AuthenticationError
        mock_openai.RateLimitError = openai.RateLimitError

        # Mock 402 error
        error = Exception("Insufficient credits")
        error.status_code = 402
        mock_completion = Mock()
        mock_completion.create.side_effect = error
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test prompt", model=ZAIModel.PRIMARY)

        assert result["error"] == "credit_exhausted"
        assert "Insufficient credits" in result["details"]

    @patch('llm.zai_client.OpenAI')
    def test_generate_detects_credit_exhaustion_403(self, mock_openai):
        # Mock 403 error with "insufficient credits" message
        error = Exception("Error: insufficient credits quota exceeded")
        error.status_code = 403
        mock_completion = Mock()
        mock_completion.create.side_effect = error
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test prompt", model=ZAIModel.PRIMARY)

        assert result["error"] == "credit_exhausted"

    @patch('llm.zai_client.OpenAI')
    def test_generate_with_thinking_disabled(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"

        mock_completion = Mock()
        mock_completion.create.return_value = mock_response
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test", model=ZAIModel.PRIMARY, thinking=False)

        call_kwargs = mock_completion.create.call_args[1]
        assert call_kwargs.get("thinking") is None

    @patch('llm.zai_client.OpenAI')
    def test_close_closes_client(self, mock_openai):
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance

        client = ZAIClient(api_key="test-key")
        # Trigger client creation
        client._get_client()
        client.close()

        mock_client_instance.close.assert_called_once()

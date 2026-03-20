# services/nemoclaw-orchestrator/tests/integration/test_zai_live.py
import pytest
import os
from llm.zai_client import ZAIClient, ZAIModel


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    not os.getenv("ZAI_API_KEY"),
    reason="ZAI_API_KEY not set"
)
class TestZAILiveAPI:
    """Live tests against real Z.AI API (requires API key)"""

    @pytest.fixture
    def client(self):
        return ZAIClient()

    def test_generate_with_primary_model(self, client):
        """Test actual API call with GLM-5-Turbo"""
        result = client.generate(
            prompt="Say 'Hello, World!' in exactly those words.",
            model=ZAIModel.PRIMARY,
            max_tokens=50
        )

        assert "text" in result
        assert result["model_used"] == "glm-5-turbo"
        assert "Hello, World!" in result["text"] or len(result["text"]) > 0

    def test_generate_with_programming_model(self, client):
        """Test actual API call with GLM-4.7"""
        result = client.generate(
            prompt="Write a Python function that adds two numbers.",
            model=ZAIModel.PROGRAMMING,
            max_tokens=100
        )

        assert "text" in result
        assert result["model_used"] == "glm-4.7"
        assert "def " in result["text"] or len(result["text"]) > 0

    def test_generate_with_fast_model(self, client):
        """Test actual API call with GLM-4.7-FlashX"""
        result = client.generate(
            prompt="What is 2+2?",
            model=ZAIModel.FAST,
            max_tokens=20
        )

        assert "text" in result
        assert result["model_used"] == "glm-4.7-flashx"

    def test_thinking_parameter(self, client):
        """Test thinking parameter is accepted"""
        result = client.generate(
            prompt="Count to 5.",
            model=ZAIModel.PRIMARY,
            thinking=True
        )

        assert "text" in result
        assert result["credits_exhausted"] is False

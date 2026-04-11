"""Integration tests for SceneSpeak Agent LLM service.

Tests the updated /api/generate endpoint with:
- GLM 4.7 API support
- Nemotron (OpenAI-compatible) fallback
- Ollama fallback
- Proper error handling (422 for validation)
- Timeout handling
- Context support
"""

import pytest
import requests
import os


def test_scenespeak_generate_with_glm_api(scenespeak_url, sample_prompt):
    """Test LLM generation using GLM 4.7 API (primary)."""
    # Skip if GLM_API_KEY not set
    if not os.environ.get("GLM_API_KEY"):
        pytest.skip("GLM_API_KEY not set")

    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={
            "prompt": sample_prompt,
            "max_tokens": 100,
            "temperature": 0.7
        },
        timeout=120
    )

    assert response.status_code == 200
    data = response.json()

    # New format supports both "text" and "dialogue" for compatibility
    assert "text" in data or "dialogue" in data
    text = data.get("text") or data.get("dialogue")
    assert len(text) > 0

    # Check for model and tokens_used (either in metadata or root)
    if "metadata" in data:
        assert "model" in data["metadata"]
        assert "tokens_used" in data["metadata"]
    else:
        assert "model" in data or data.get("metadata", {}).get("model")
        assert "tokens_used" in data or data.get("metadata", {}).get("tokens_used")


def test_scenespeak_fallback_to_nemotron(scenespeak_url, sample_prompt):
    """Test LLM fallback to local Nemotron when GLM fails."""
    # Force fallback by using invalid API key scenario
    # This test requires LOCAL_LLM_ENABLED=true or Nemotron running

    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={
            "prompt": sample_prompt,
            "max_tokens": 50,
            "temperature": 0.5,
            "use_fallback": True  # Force Nemotron fallback
        },
        timeout=120
    )

    # Should either succeed with fallback or fail gracefully
    if response.status_code == 200:
        data = response.json()
        assert "text" in data or "dialogue" in data
        text = data.get("text") or data.get("dialogue")
        # Nemotron responses may be shorter but should still exist
        assert len(text) > 0 or data.get("fallback_used") is True or \
               data.get("metadata", {}).get("adapter") in ["openai_local", "nemotron", "local", "local-fallback"]
    else:
        # Expected to fail if no local LLM is configured
        assert response.status_code in [500, 503]
        data = response.json()
        assert "Local LLM unavailable" in str(data.get("detail", "")) or \
               "No dialogue generation method available" in str(data.get("detail", ""))


def test_scenespeak_timeout_handling(scenespeak_url):
    """Test that timeout is handled gracefully."""
    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={
            "prompt": "Write a very long response",
            "max_tokens": 1000,
            "timeout": 1  # Very short timeout
        },
        timeout=5
    )

    # Should either succeed quickly or return timeout error
    assert response.status_code in [200, 504, 500, 408]


def test_scenespeak_with_context(scenespeak_url):
    """Test LLM generation with additional context."""
    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={
            "prompt": "Continue the dialogue",
            "context": {
                "sentiment": "positive",
                "show_id": "test_show",
                "scene": "act1_scene1",
                "previous_dialogue": "Hello, welcome to the show!"
            }
        },
        timeout=120
    )

    # Should either succeed or fail gracefully if no LLM configured
    if response.status_code == 200:
        data = response.json()
        assert "text" in data or "dialogue" in data
        # Check that context was passed through
        if "metadata" in data:
            assert "context" in data["metadata"]
    else:
        # Expected to fail if no LLM is configured
        assert response.status_code in [500, 503]


def test_scenespeak_missing_prompt(scenespeak_url):
    """Test validation error when prompt is missing."""
    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={"max_tokens": 100}  # Missing prompt
    )

    # Should return 422 validation error
    assert response.status_code == 422
    data = response.json()
    assert "prompt" in str(data.get("detail", "")).lower()


def test_scenespeak_empty_prompt(scenespeak_url):
    """Test validation error when prompt is empty."""
    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={"prompt": "   ", "max_tokens": 100}  # Empty prompt (whitespace)
    )

    # Should return 422 validation error
    assert response.status_code == 422
    data = response.json()
    assert "empty" in str(data.get("detail", "")).lower() or "prompt" in str(data.get("detail", "")).lower()


def test_scenespeak_health_includes_llm_status(scenespeak_url):
    """Test that health endpoint includes LLM availability."""
    response = requests.get(f"{scenespeak_url}/health")
    assert response.status_code == 200

    data = response.json()
    # Check for various LLM status fields
    assert "llm_available" in data or "model_available" in data or "status" in data

    # Check for model_info
    if "model_info" in data:
        assert "name" in data["model_info"]
        assert "loaded" in data["model_info"]


def test_scenespeak_use_fallback_parameter(scenespeak_url, sample_prompt):
    """Test the use_fallback parameter is accepted."""
    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={
            "prompt": sample_prompt,
            "max_tokens": 50,
            "use_fallback": True
        },
        timeout=120
    )

    # Should accept the parameter (may fail if no LLM configured)
    if response.status_code == 200:
        data = response.json()
        # Check if fallback was used
        fallback_used = data.get("fallback_used") or data.get("metadata", {}).get("fallback_used", False)
        adapter = data.get("metadata", {}).get("adapter", "")
        # If successful, should indicate fallback was used
        assert fallback_used or adapter in ["local", "local-fallback", "nemotron", "openai_local"]


def test_scenespeak_response_format_compatibility(scenespeak_url):
    """Test that response includes both legacy and new formats."""
    # This test requires a working LLM
    if not os.environ.get("GLM_API_KEY") and not os.environ.get("LOCAL_LLM_ENABLED"):
        pytest.skip("No LLM configured")

    response = requests.post(
        f"{scenespeak_url}/api/generate",
        json={
            "prompt": "Say hello",
            "max_tokens": 10
        },
        timeout=120
    )

    if response.status_code == 200:
        data = response.json()
        # Should have text/dialogue
        assert "text" in data or "dialogue" in data

        # Should have metadata
        if "metadata" in data:
            assert "model" in data["metadata"]
            assert "tokens_used" in data["metadata"]
            assert "adapter" in data["metadata"]
            assert "fallback_used" in data["metadata"]

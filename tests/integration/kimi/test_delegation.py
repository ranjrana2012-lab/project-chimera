import pytest
import sys
from pathlib import Path

# Add nemoclaw-orchestrator to path (hyphenated directory name)
# From tests/integration/kimi/, go up 3 levels to project root, then to services/nemoclaw-orchestrator
nemoclaw_dir = Path(__file__).parent.parent.parent.parent / "services" / "nemoclaw-orchestrator"
sys.path.insert(0, str(nemoclaw_dir))

from delegation import (
    KimiDelegator,
    NemoCapabilityChecker
)

@pytest.fixture
def delegator():
    return KimiDelegator()

@pytest.fixture
def checker():
    return NemoCapabilityChecker()

@pytest.mark.asyncio
async def test_delegates_long_context(delegator):
    """Test delegation of long context requests"""
    # Need 35000 chars to exceed 8192 token threshold (35000 / 4 = 8750 tokens)
    request = {
        "request_id": "test-1",
        "user_input": "A" * 35000,
        "multimodal_content": []
    }

    result = await delegator.delegate_if_needed(request)

    # Should delegate (returns response, not None)
    assert result is not None
    assert result.get("metadata", {}).get("delegated_to_kimi") is True

@pytest.mark.asyncio
async def test_skips_simple_requests(delegator):
    """Test that simple requests are not delegated"""
    request = {
        "request_id": "test-2",
        "user_input": "Hello",
        "multimodal_content": []
    }

    result = await delegator.delegate_if_needed(request)

    # Should NOT delegate (returns None)
    assert result is None

def test_detects_long_context(checker):
    """Test long context detection"""
    # Need 35000 chars to exceed 8192 token threshold (35000 / 4 = 8750 tokens)
    request = {
        "user_input": "A" * 35000,
        "multimodal_content": []
    }

    assert checker.should_delegate(request) is True

def test_detects_multimodal(checker):
    """Test multimodal detection"""
    request = {
        "user_input": "Describe this",
        "multimodal_content": [{"type": "IMAGE"}]
    }

    assert checker.should_delegate(request) is True

def test_detects_agentic_coding(checker):
    """Test agentic coding keyword detection"""
    request = {
        "user_input": "Create an agent to process data",
        "multimodal_content": []
    }

    assert checker.should_delegate(request) is True

def test_respects_delegation_disabled(checker, monkeypatch):
    """Test that delegation can be disabled"""
    monkeypatch.setenv("KIMI_DELEGATION_ENABLED", "false")

    # Create new checker with disabled delegation
    checker_disabled = NemoCapabilityChecker()

    request = {
        "user_input": "A" * 10000,
        "multimodal_content": []
    }

    assert checker_disabled.should_delegate(request) is False

def test_custom_threshold(checker, monkeypatch):
    """Test custom threshold configuration"""
    monkeypatch.setenv("KIMI_LONG_CONTEXT_THRESHOLD", "100")

    # Create new checker with custom threshold
    checker_custom = NemoCapabilityChecker()

    # Short request should delegate with low threshold
    request = {
        "user_input": "A" * 500,  # 125 tokens
        "multimodal_content": []
    }

    assert checker_custom.should_delegate(request) is True

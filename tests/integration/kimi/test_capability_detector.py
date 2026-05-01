import pytest
from services.kimi_super_agent.capability_detector import (
    CapabilityDetector,
    CapabilityHint,
    MultimodalContent
)

@pytest.fixture
def detector():
    return CapabilityDetector(long_context_threshold=8192)

def test_detects_long_context(detector):
    """Test detection of long context requests"""
    request = {
        "user_input": "A" * 40000,  # 40K characters (~10K tokens)
        "multimodal_content": []
    }

    hint = detector.detect(request)

    assert hint == CapabilityHint.LONG_CONTEXT

def test_detects_multimodal(detector):
    """Test detection of multimodal content"""
    request = {
        "user_input": "Describe this image",
        "multimodal_content": [
            MultimodalContent(type="IMAGE", data=b"fake", mime_type="image/png")
        ]
    }

    hint = detector.detect(request)

    assert hint == CapabilityHint.MULTIMODAL

def test_detects_agentic_coding(detector):
    """Test detection of agentic coding requests"""
    request = {
        "user_input": "Create a new agent that handles customer support",
        "multimodal_content": []
    }

    hint = detector.detect(request)

    assert hint == CapabilityHint.AGENTIC_CODING

def test_returns_none_for_simple_request(detector):
    """Test returns NONE for simple requests"""
    request = {
        "user_input": "Hello",
        "multimodal_content": []
    }

    hint = detector.detect(request)

    assert hint == CapabilityHint.NONE

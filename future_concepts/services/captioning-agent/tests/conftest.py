# tests/conftest.py
"""Pytest configuration and fixtures"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_audio_data():
    """Mock audio data for testing"""
    return b"RIFF" + b"\x00" * 100  # Minimal WAV header


@pytest.fixture
def sample_transcription():
    """Sample transcription result"""
    return {
        "text": "Hello, this is a test of the captioning system.",
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "Hello, this is a test"},
            {"start": 1.5, "end": 3.0, "text": "of the captioning system."}
        ],
        "duration": 3.0
    }

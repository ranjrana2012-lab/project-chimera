"""Pytest configuration for OpenClaw Orchestrator tests"""

import pytest
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_skill_request():
    """Sample skill invocation request."""
    return {
        "skill_name": "scenespeak",
        "input": {
            "current_scene": {
                "scene_id": "scene-001",
                "title": "Test Scene",
            },
            "dialogue_context": [],
            "sentiment_vector": {"overall": "neutral"},
        },
        "timeout_ms": 3000,
    }


@pytest.fixture
def sample_pipeline_request():
    """Sample pipeline execution request."""
    return {
        "steps": [
            {
                "skill_name": "sentiment",
                "input_mapping": {},
            },
            {
                "skill_name": "scenespeak",
                "input_mapping": {
                    "sentiment": "sentiment_output",
                },
            },
        ],
        "input": {
            "social_posts": ["This is amazing!", "Great performance!"],
        },
        "parallel": False,
        "timeout_ms": 10000,
    }

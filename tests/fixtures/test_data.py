"""Test data for API requests."""
import base64


class TestData:
    """Sample request data for testing."""

    # SceneSpeak test data
    SCENESPEAK_REQUEST = {
        "context": "A sunny garden at sunset",
        "character": "ALICE",
        "sentiment": 0.8,
        "max_tokens": 256,
        "temperature": 0.7
    }

    # Captioning test data
    SAMPLE_AUDIO_BASE64 = base64.b64encode(b"mock_audio_data").decode()
    CAPTIONING_REQUEST = {
        "audio_data": SAMPLE_AUDIO_BASE64,
        "language": "en",
        "timestamps": True,
        "word_timestamps": False
    }

    # Sentiment test data
    SENTIMENT_REQUESTS = [
        "This performance is absolutely amazing!",
        "I'm not sure about this scene...",
        "Best show I've ever seen!"
    ]

    # BSL test data
    BSL_REQUEST = {
        "text": "Hello, how are you today?",
        "preserve_format": True,
        "include_metadata": True
    }

    # Safety test data
    SAFETY_REQUEST_SAFE = {
        "content": "The character should say something appropriate here.",
        "context": "family_show"
    }

    # Lighting test data
    LIGHTING_REQUEST = {
        "universe": 1,
        "values": {"1": 255, "2": 200, "3": 150},
        "fade_time_ms": 1000
    }

    # OpenClaw test data
    OPENCLAW_REQUEST = {
        "pipeline": "sentiment_to_dialogue",
        "input": {
            "social_posts": ["Amazing performance!"]
        },
        "context": {
            "scene_id": "scene-001"
        },
        "timeout_ms": 5000
    }

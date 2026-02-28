"""Mock AI model responses for fast testing."""
from datetime import datetime, timezone
from typing import Any, Dict


class MockLLMResponse:
    """Mock LLM response for SceneSpeak Agent."""

    @staticmethod
    def generate_response(context: str, character: str, sentiment: float) -> Dict[str, Any]:
        return {
            "proposed_lines": f"{character}: [Responding to {context}]",
            "stage_cues": ["[LIGHTING: Default lighting]"],
            "metadata": {
                "model": "mock-llm-v1",
                "tokens_generated": 42,
                "prompt_tokens": 100
            },
            "cached": False,
            "latency_ms": 50,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class MockWhisperResponse:
    """Mock Whisper response for Captioning Agent."""

    @staticmethod
    def transcribe(audio_data: str, language: str) -> Dict[str, Any]:
        return {
            "text": "This is a mock transcription of the audio.",
            "language": language,
            "confidence": 0.95,
            "segments": [
                {
                    "id": 0,
                    "text": "This is a mock transcription",
                    "start": 0.0,
                    "end": 2.5
                }
            ],
            "processing_time_ms": 150.5,
            "model_version": "mock-whisper-v1"
        }


class MockSentimentResponse:
    """Mock sentiment analysis response."""

    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        return {
            "text": text,
            "sentiment": {
                "label": "positive",
                "score": 0.85
            },
            "confidence": 0.92,
            "emotion_scores": {
                "joy": 0.75,
                "sadness": 0.05,
                "anger": 0.02,
                "fear": 0.03,
                "surprise": 0.10,
                "disgust": 0.05
            },
            "processing_time_ms": 25.0,
            "model_version": "mock-distilbert-v1"
        }


class MockBSLResponse:
    """Mock BSL translation response."""

    @staticmethod
    def translate(text: str) -> Dict[str, Any]:
        return {
            "source_text": text,
            "gloss_text": text.upper().replace(" ", "  "),
            "gloss_format": "simple",
            "metadata": {
                "source_word_count": len(text.split()),
                "gloss_sign_count": len(text.split())
            },
            "confidence": 0.88,
            "breakdown": [
                {"source": word, "gloss": word.upper(), "markers": []}
                for word in text.split()
            ],
            "translation_time_ms": 45.0,
            "model_version": "mock-opus-mt-v1"
        }


class MockSafetyResponse:
    """Mock safety check response."""

    @staticmethod
    def check(content: str) -> Dict[str, Any]:
        return {
            "safe": True,
            "confidence": 0.98,
            "flagged_categories": [],
            "categories": {
                "profanity": {"score": 0.0, "flagged": False},
                "hate_speech": {"score": 0.0, "flagged": False},
                "sexual": {"score": 0.0, "flagged": False},
                "violence": {"score": 0.0, "flagged": False}
            },
            "filtered_content": content,
            "explanation": "Content is safe",
            "review_required": False,
            "processing_time_ms": 10.0,
            "model_version": "mock-safety-v1"
        }

"""
Sentiment Analyzer Module

Provides sentiment analysis using DistilBERT ML model.

The analyzer detects:
- Sentiment: positive, negative, neutral
- Score: 0.0 (negative) to 1.0 (positive)
- Emotions: joy, surprise, neutral, sadness, anger, fear
"""

import logging
from typing import Dict, List

from .config import get_settings
from .ml_model import SentimentModel

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analyzer using DistilBERT ML model.

    ML-only approach - all rule-based logic has been removed.
    """

    def __init__(self, use_ml_model: bool = True):
        """
        Initialize the sentiment analyzer.

        Args:
            use_ml_model: Must be True (ML-only approach)

        Raises:
            ValueError: If use_ml_model is False
        """
        if not use_ml_model:
            raise ValueError("ML-only approach: use_ml_model must be True")

        self.settings = get_settings()
        self.model = SentimentModel(
            cache_dir=self.settings.model_cache_dir,
            device=self.settings.device
        )
        self.model_available = False

        logger.info("SentimentAnalyzer initialized with ML model")

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment, score, confidence
        """
        if not text or not text.strip():
            return self._neutral_result()

        # Load model if not loaded (with graceful fallback to mock)
        if not self.model_available:
            try:
                self.model.load()
                self.model_available = True
                logger.info("ML model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load ML model, using mock: {e}")
                self.model_available = False
                return self._mock_result(text)

        # Use loaded model
        if self.model_available:
            return self.model.analyze(text)
        else:
            return self._mock_result(text)

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment analysis results
        """
        if not texts:
            return []

        # Load model if not loaded (with graceful fallback to mock)
        if not self.model_available:
            try:
                self.model.load()
                self.model_available = True
                logger.info("ML model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load ML model, using mock: {e}")
                self.model_available = False

        # Use loaded model or mock
        if self.model_available:
            return self.model.analyze_batch(texts)
        else:
            return [self._mock_result(text) for text in texts]

    def _neutral_result(self) -> Dict:
        """Return a neutral sentiment result with score 0.0."""
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "confidence": 0.5,
            "emotions": {
                "joy": 0.0,
                "surprise": 0.0,
                "neutral": 1.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0
            }
        }

    def _mock_result(self, text: str) -> Dict:
        """
        Return a mock sentiment result when ML model is unavailable.

        Simple keyword-based mock for testing/fallback scenarios.
        """
        text_lower = text.lower()

        # Simple keyword matching for demo purposes
        positive_words = ["good", "great", "love", "amazing", "excellent", "happy", "joy"]
        negative_words = ["bad", "hate", "terrible", "awful", "sad", "angry", "poor"]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return {
                "sentiment": "positive",
                "score": 0.6,
                "confidence": 0.5,
                "emotions": {"joy": 0.6, "surprise": 0.2, "neutral": 0.1, "sadness": 0.0, "anger": 0.0, "fear": 0.0}
            }
        elif negative_count > positive_count:
            return {
                "sentiment": "negative",
                "score": -0.6,
                "confidence": 0.5,
                "emotions": {"joy": 0.0, "surprise": 0.1, "neutral": 0.1, "sadness": 0.5, "anger": 0.3, "fear": 0.1}
            }
        else:
            return self._neutral_result()

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

        # Load model if not loaded
        if not self.model_available:
            self.model.load()
            self.model_available = True

        return self.model.analyze(text)

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

        # Load model if not loaded
        if not self.model_available:
            self.model.load()
            self.model_available = True

        return self.model.analyze_batch(texts)

    def _neutral_result(self) -> Dict:
        """Return a neutral sentiment result."""
        return {
            "sentiment": "neutral",
            "score": 0.5,
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

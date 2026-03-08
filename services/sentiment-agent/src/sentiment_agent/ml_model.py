"""ML Model Wrapper for Sentiment Analysis."""

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import logging

logger = logging.getLogger(__name__)


class SentimentModel:
    """DistilBERT SST-2 model wrapper for sentiment analysis."""

    MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

    def __init__(self, cache_dir: str = "./models_cache", device: str = "auto"):
        """Initialize model with lazy loading."""
        self.cache_dir = cache_dir
        self.device = self._detect_device() if device == "auto" else device
        self.model = None
        self.tokenizer = None

    def _detect_device(self) -> str:
        """Auto-detect available device."""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def load(self):
        """Load model and tokenizer."""
        logger.info(f"Loading {self.MODEL_NAME} on {self.device}")
        self.tokenizer = DistilBertTokenizer.from_pretrained(
            self.MODEL_NAME, cache_dir=self.cache_dir
        )
        self.model = DistilBertForSequenceClassification.from_pretrained(
            self.MODEL_NAME, cache_dir=self.cache_dir
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model loaded successfully")

    def analyze(self, text: str) -> dict:
        """Analyze sentiment of text."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # Convert to sentiment
        negative_prob = predictions[0][0].item()
        positive_prob = predictions[0][1].item()

        if positive_prob > 0.6:
            sentiment = "positive"
            score = positive_prob
        elif negative_prob > 0.6:
            sentiment = "negative"
            score = 1.0 - negative_prob
        else:
            sentiment = "neutral"
            score = 0.5

        confidence = max(positive_prob, negative_prob)

        # Infer emotions from sentiment (SST-2 is binary sentiment classification)
        emotions = {
            "joy": 0.0,
            "surprise": 0.0,
            "neutral": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0
        }

        if sentiment == "positive":
            emotions["joy"] = 0.7 + (confidence * 0.3)  # 0.7-1.0 based on confidence
            emotions["surprise"] = 0.3 + (confidence * 0.2)  # 0.3-0.5
            emotions["neutral"] = max(0.0, 0.1 - confidence * 0.1)
        elif sentiment == "negative":
            emotions["sadness"] = 0.6 + (confidence * 0.3)  # 0.6-0.9
            emotions["anger"] = 0.4 + (confidence * 0.3)  # 0.4-0.7
            emotions["fear"] = 0.1 + (confidence * 0.2)  # 0.1-0.3
            emotions["neutral"] = max(0.0, 0.1 - confidence * 0.1)
        else:  # neutral
            emotions["neutral"] = 0.8 + (confidence * 0.2)  # 0.8-1.0
            emotions["joy"] = 0.1
            emotions["surprise"] = 0.1

        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "emotions": emotions
        }

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        """Analyze multiple texts."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)
        return results

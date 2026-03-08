"""Unit tests for ML model wrapper."""

import pytest
from unittest.mock import Mock, patch
import torch

from src.sentiment_agent.ml_model import SentimentModel


class TestSentimentModel:
    """Test SentimentModel class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache_dir = "./test_cache"

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_init_creates_instance(self, mock_model_class, mock_tokenizer_class):
        """Test initialization creates instance."""
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.return_value = Mock()

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")

        assert model.cache_dir == self.cache_dir
        assert model.device == "cpu"
        assert model.model is None

    def test_detect_device_cuda_available(self):
        """Test CUDA device detection when available."""
        with patch('torch.cuda.is_available', return_value=True):
            model = SentimentModel(device="auto")
            assert model.device == "cuda"

    def test_detect_device_cpu_fallback(self):
        """Test CPU fallback when CUDA unavailable."""
        with patch('torch.cuda.is_available', return_value=False):
            model = SentimentModel(device="auto")
            assert model.device == "cpu"

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_load_model(self, mock_model_class, mock_tokenizer_class):
        """Test model loading."""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")
        model.load()

        assert model.model is not None
        assert model.tokenizer is not None

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_analyze_returns_sentiment(self, mock_model_class, mock_tokenizer_class):
        """Test analyze returns sentiment dict."""
        # Setup mock model
        mock_model = Mock()
        mock_tokenizer = Mock()

        # Mock model output (positive sentiment)
        mock_output = Mock()
        mock_output.logits = torch.tensor([[1.0, 5.0]])  # High positive logit
        mock_model.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model

        # Mock tokenizer - return dict-like object with .to() method
        mock_inputs = {"input_ids": torch.tensor([[1, 2, 3]])}

        # Create a mock that behaves like a dict and has .to() method
        class MockTokenizerOutput(dict):
            def to(self, device):
                return self

        mock_tokenizer_result = MockTokenizerOutput(mock_inputs)
        mock_tokenizer.return_value = mock_tokenizer_result
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")
        model.model = mock_model
        model.tokenizer = mock_tokenizer

        result = model.analyze("This is amazing!")

        assert "sentiment" in result
        assert "score" in result
        assert "confidence" in result
        assert "emotions" in result

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_analyze_returns_emotions_for_positive(self, mock_model_class, mock_tokenizer_class):
        """Test analyze returns emotions dict with high joy for positive sentiment."""
        mock_model = Mock()
        mock_tokenizer = Mock()

        # Mock model output (positive sentiment)
        mock_output = Mock()
        mock_output.logits = torch.tensor([[1.0, 5.0]])  # High positive logit
        mock_model.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model

        class MockTokenizerOutput(dict):
            def to(self, device):
                return self

        mock_tokenizer_result = MockTokenizerOutput({"input_ids": torch.tensor([[1, 2, 3]])})
        mock_tokenizer.return_value = mock_tokenizer_result
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")
        model.model = mock_model
        model.tokenizer = mock_tokenizer

        result = model.analyze("This is amazing!")

        assert "emotions" in result
        assert "joy" in result["emotions"]
        assert "surprise" in result["emotions"]
        assert "neutral" in result["emotions"]
        assert "sadness" in result["emotions"]
        assert "anger" in result["emotions"]
        assert "fear" in result["emotions"]
        # Positive text should have high joy
        assert result["emotions"]["joy"] > 0.5

    @patch('src.sentiment_agent.ml_model.DistilBertTokenizer')
    @patch('src.sentiment_agent.ml_model.DistilBertForSequenceClassification')
    def test_analyze_returns_emotions_for_negative(self, mock_model_class, mock_tokenizer_class):
        """Test analyze returns emotions dict with high sadness/anger for negative sentiment."""
        mock_model = Mock()
        mock_tokenizer = Mock()

        # Mock model output (negative sentiment)
        mock_output = Mock()
        mock_output.logits = torch.tensor([[5.0, 1.0]])  # High negative logit
        mock_model.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model

        class MockTokenizerOutput(dict):
            def to(self, device):
                return self

        mock_tokenizer_result = MockTokenizerOutput({"input_ids": torch.tensor([[1, 2, 3]])})
        mock_tokenizer.return_value = mock_tokenizer_result
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        model = SentimentModel(cache_dir=self.cache_dir, device="cpu")
        model.model = mock_model
        model.tokenizer = mock_tokenizer

        result = model.analyze("This was terrible!")

        assert "emotions" in result
        # Negative text should have high sadness or anger
        assert result["emotions"]["sadness"] > 0.3 or result["emotions"]["anger"] > 0.3

"""
Unit tests for Sentiment Agent models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from services.sentiment_agent.src.models.request import (
    SentimentRequest,
    SentimentBatchRequest,
    SentimentAnalysisOptions
)
from services.sentiment_agent.src.models.response import (
    SentimentResponse,
    SentimentBatchResponse,
    SentimentScore,
    EmotionScores,
    SentimentTrend,
    TrendDataPoint,
    SentimentLabel
)


@pytest.mark.unit
class TestSentimentAnalysisOptions:
    """Test cases for SentimentAnalysisOptions."""

    def test_default_options(self):
        """Test default options values."""
        options = SentimentAnalysisOptions()

        assert options.include_emotions is True
        assert options.include_trend is False
        assert options.aggregation_window == 60
        assert options.min_confidence == 0.5

    def test_custom_options(self):
        """Test custom options values."""
        options = SentimentAnalysisOptions(
            include_emotions=False,
            include_trend=True,
            aggregation_window=300,
            min_confidence=0.8
        )

        assert options.include_emotions is False
        assert options.include_trend is True
        assert options.aggregation_window == 300
        assert options.min_confidence == 0.8

    def test_aggregation_window_validation(self):
        """Test aggregation window validation."""
        with pytest.raises(ValidationError):
            SentimentAnalysisOptions(aggregation_window=0)

        with pytest.raises(ValidationError):
            SentimentAnalysisOptions(aggregation_window=4000)

    def test_min_confidence_validation(self):
        """Test min confidence validation."""
        with pytest.raises(ValidationError):
            SentimentAnalysisOptions(min_confidence=-0.1)

        with pytest.raises(ValidationError):
            SentimentAnalysisOptions(min_confidence=1.1)


@pytest.mark.unit
class TestSentimentRequest:
    """Test cases for SentimentRequest."""

    def test_valid_request(self):
        """Test valid sentiment request."""
        request = SentimentRequest(
            text="This is amazing!",
            options=SentimentAnalysisOptions(include_emotions=True),
            request_id="req-123"
        )

        assert request.text == "This is amazing!"
        assert request.options.include_emotions is True
        assert request.request_id == "req-123"

    def test_request_without_options(self):
        """Test request without options uses defaults."""
        request = SentimentRequest(text="Great show!")

        assert request.text == "Great show!"
        assert request.options is not None
        assert request.options.include_emotions is True

    def test_text_length_validation(self):
        """Test text length validation."""
        # Empty text
        with pytest.raises(ValidationError):
            SentimentRequest(text="")

        # Text too long (> 5000 characters)
        with pytest.raises(ValidationError):
            SentimentRequest(text="a" * 5001)

    def test_request_without_request_id(self):
        """Test request without request_id (should be optional)."""
        request = SentimentRequest(text="Good performance!")

        assert request.request_id is None


@pytest.mark.unit
class TestSentimentBatchRequest:
    """Test cases for SentimentBatchRequest."""

    def test_valid_batch_request(self):
        """Test valid batch request."""
        request = SentimentBatchRequest(
            texts=["Great!", "Amazing!", "Love it!"],
            request_id="batch-123"
        )

        assert len(request.texts) == 3
        assert request.request_id == "batch-123"

    def test_batch_size_validation(self):
        """Test batch size validation."""
        # Empty batch
        with pytest.raises(ValidationError):
            SentimentBatchRequest(texts=[])

        # Batch too large (> 100 texts)
        with pytest.raises(ValidationError):
            SentimentBatchRequest(texts=["text"] * 101)


@pytest.mark.unit
class TestEmotionScores:
    """Test cases for EmotionScores."""

    def test_valid_emotion_scores(self):
        """Test valid emotion scores."""
        emotions = EmotionScores(
            joy=0.85,
            sadness=0.05,
            anger=0.02,
            fear=0.03,
            surprise=0.30,
            disgust=0.01
        )

        assert emotions.joy == 0.85
        assert emotions.sadness == 0.05

    def test_emotion_score_validation(self):
        """Test emotion score bounds validation."""
        with pytest.raises(ValidationError):
            EmotionScores(
                joy=1.5,  # Invalid: > 1.0
                sadness=0.5,
                anger=0.5,
                fear=0.5,
                surprise=0.5,
                disgust=0.5
            )

        with pytest.raises(ValidationError):
            EmotionScores(
                joy=-0.1,  # Invalid: < 0.0
                sadness=0.5,
                anger=0.5,
                fear=0.5,
                surprise=0.5,
                disgust=0.5
            )


@pytest.mark.unit
class TestSentimentScore:
    """Test cases for SentimentScore."""

    def test_positive_sentiment(self):
        """Test positive sentiment score."""
        score = SentimentScore(
            label=SentimentLabel.POSITIVE,
            confidence=0.95,
            positive_score=0.98,
            negative_score=0.02
        )

        assert score.label == SentimentLabel.POSITIVE
        assert score.confidence == 0.95

    def test_sentiment_score_validation(self):
        """Test sentiment score bounds validation."""
        with pytest.raises(ValidationError):
            SentimentScore(
                label=SentimentLabel.POSITIVE,
                confidence=1.5,  # Invalid: > 1.0
                positive_score=0.9,
                negative_score=0.1
            )


@pytest.mark.unit
class TestTrendDataPoint:
    """Test cases for TrendDataPoint."""

    def test_valid_trend_data_point(self):
        """Test valid trend data point."""
        point = TrendDataPoint(
            timestamp=datetime.now(),
            score=0.75,
            count=15
        )

        assert point.score == 0.75
        assert point.count == 15


@pytest.mark.unit
class TestSentimentTrend:
    """Test cases for SentimentTrend."""

    def test_valid_sentiment_trend(self):
        """Test valid sentiment trend."""
        trend = SentimentTrend(
            current_score=0.65,
            direction="rising",
            change_percent=12.5,
            data_points=[]
        )

        assert trend.current_score == 0.65
        assert trend.direction == "rising"
        assert trend.change_percent == 12.5


@pytest.mark.unit
class TestSentimentResponse:
    """Test cases for SentimentResponse."""

    def test_valid_response(self):
        """Test valid sentiment response."""
        sentiment = SentimentScore(
            label=SentimentLabel.POSITIVE,
            confidence=0.95,
            positive_score=0.98,
            negative_score=0.02
        )

        emotions = EmotionScores(
            joy=0.85,
            sadness=0.05,
            anger=0.02,
            fear=0.03,
            surprise=0.30,
            disgust=0.01
        )

        response = SentimentResponse(
            request_id="req-123",
            text="This is amazing!",
            sentiment=sentiment,
            emotions=emotions,
            processing_time_ms=45.2,
            model_version="distilbert-sst-2-v0.1.0"
        )

        assert response.request_id == "req-123"
        assert response.text == "This is amazing!"
        assert response.sentiment.label == SentimentLabel.POSITIVE
        assert response.emotions.joy == 0.85


@pytest.mark.unit
class TestSentimentBatchResponse:
    """Test cases for SentimentBatchResponse."""

    def test_valid_batch_response(self):
        """Test valid batch response."""
        sentiment1 = SentimentScore(
            label=SentimentLabel.POSITIVE,
            confidence=0.95,
            positive_score=0.98,
            negative_score=0.02
        )

        emotions1 = EmotionScores(
            joy=0.85, sadness=0.05, anger=0.02,
            fear=0.03, surprise=0.30, disgust=0.01
        )

        result1 = SentimentResponse(
            request_id="batch-123-0",
            text="Great!",
            sentiment=sentiment1,
            emotions=emotions1,
            processing_time_ms=20.0,
            model_version="distilbert-sst-2-v0.1.0"
        )

        batch_response = SentimentBatchResponse(
            request_id="batch-123",
            results=[result1],
            aggregate={
                'overall_label': 'positive',
                'average_confidence': 0.95,
                'positive_count': 1,
                'negative_count': 0,
                'neutral_count': 0,
                'average_score': 0.95
            },
            total_processing_time_ms=50.0,
            model_version="distilbert-sst-2-v0.1.0"
        )

        assert batch_response.request_id == "batch-123"
        assert len(batch_response.results) == 1
        assert batch_response.aggregate['overall_label'] == 'positive'

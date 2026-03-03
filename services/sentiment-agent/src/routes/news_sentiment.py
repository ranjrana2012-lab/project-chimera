"""News sentiment routes for WorldMonitor integration."""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from ..models.context import NewsSentimentRequest, NewsSentimentResponse
from ..core.news_sentiment_analyzer import NewsSentimentAnalyzer


def get_news_sentiment_analyzer() -> NewsSentimentAnalyzer:
    """Dependency to get the news sentiment analyzer instance."""
    from ..main import handler
    if not handler or not handler.news_sentiment_analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="News sentiment analyzer not available"
        )
    return handler.news_sentiment_analyzer


router = APIRouter()


@router.post("/news/sentiment", response_model=NewsSentimentResponse)
async def analyze_news_sentiment(
    request: NewsSentimentRequest,
    analyzer: NewsSentimentAnalyzer = Depends(get_news_sentiment_analyzer)
) -> NewsSentimentResponse:
    """Analyze sentiment of news articles from WorldMonitor.

    This endpoint fetches news articles from the WorldMonitor sidecar
    and analyzes their sentiment using the sentiment analyzer.

    Args:
        request: News sentiment analysis request with filtering options
        analyzer: News sentiment analyzer instance

    Returns:
        NewsSentimentResponse with analyzed articles and sentiment statistics

    Raises:
        HTTPException: If the analyzer is not available
    """
    try:
        return await analyzer.analyze_news(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze news sentiment: {str(e)}"
        )


@router.get("/news/sentiment/health")
async def news_sentiment_health(
    analyzer: NewsSentimentAnalyzer = Depends(get_news_sentiment_analyzer)
) -> Dict[str, Any]:
    """Check the health of the news sentiment analyzer.

    Args:
        analyzer: News sentiment analyzer instance

    Returns:
        Health status dictionary
    """
    return {
        "status": "healthy",
        "analyzer_available": analyzer is not None,
        "sidecar_url": analyzer.sidecar_url if analyzer else None
    }

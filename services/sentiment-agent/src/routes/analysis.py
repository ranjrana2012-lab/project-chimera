"""
Sentiment analysis routes for Sentiment Agent.

This module provides the main API endpoints for sentiment analysis,
including single text analysis, batch analysis, and trend tracking.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status

from ..models.request import SentimentRequest, SentimentBatchRequest
from ..models.response import SentimentResponse, SentimentBatchResponse
from ..models.context import ContextEnrichmentOptions

router = APIRouter()


@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest) -> SentimentResponse:
    """Analyze sentiment of a single text.

    This endpoint processes a single text input and returns:
    - Sentiment classification (positive/negative/neutral)
    - Confidence scores
    - Optional emotion detection
    - Optional trend analysis

    Args:
        request: Sentiment analysis request

    Returns:
        SentimentResponse with analysis results

    Raises:
        HTTPException: If handler is not initialized
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        # Convert options to dict
        options = request.options.model_dump() if request.options else {}

        # Extract context options if provided
        context_options = None
        if hasattr(request, 'context_options') and request.context_options:
            context_options = request.context_options

        result = await handler.analyze(
            text=request.text,
            options=options,
            context_options=context_options,
            request_id=request.request_id
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze-batch", response_model=SentimentBatchResponse)
async def analyze_batch_sentiment(request: SentimentBatchRequest) -> SentimentBatchResponse:
    """Analyze sentiment of multiple texts.

    This endpoint processes multiple text inputs and returns:
    - Individual sentiment results for each text
    - Aggregated statistics across all texts
    - Average confidence and sentiment distribution

    Args:
        request: Batch sentiment analysis request

    Returns:
        SentimentBatchResponse with batch analysis results

    Raises:
        HTTPException: If handler is not initialized or batch is empty
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    if not request.texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch request must contain at least one text"
        )

    try:
        # Convert options to dict
        options = request.options.model_dump() if request.options else {}

        result = await handler.analyze_batch(
            texts=request.texts,
            options=options,
            request_id=request.request_id
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/aggregate")
async def get_aggregate_sentiment(
    window_seconds: Optional[int] = None
) -> dict:
    """Get aggregated sentiment statistics.

    Returns aggregated sentiment data for a time window,
    including:
    - Overall sentiment label
    - Average score and confidence
    - Count of positive/negative/neutral samples
    - Sentiment ratios and intensity

    Args:
        window_seconds: Time window in seconds (default: from config)

    Returns:
        Aggregated sentiment statistics

    Raises:
        HTTPException: If handler is not initialized
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        result = await handler.get_aggregate(window_seconds=window_seconds)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get aggregate: {str(e)}"
        )


@router.get("/trend")
async def get_sentiment_trend(
    window_seconds: int = 300,
    interval_seconds: int = 30
) -> dict:
    """Get sentiment trend over time.

    Returns time-series sentiment data for visualization,
    showing how sentiment has changed over the specified window.

    Args:
        window_seconds: Total time window to analyze (default: 5 minutes)
        interval_seconds: Size of each interval in seconds (default: 30 seconds)

    Returns:
        List of time-series data points with timestamps

    Raises:
        HTTPException: If handler is not initialized
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    if window_seconds <= 0 or interval_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Window and interval must be positive"
        )

    try:
        result = await handler.get_time_series(
            window_seconds=window_seconds,
            interval_seconds=interval_seconds
        )
        return {"data_points": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trend: {str(e)}"
        )


@router.get("/emotions")
async def get_emotion_aggregate(
    window_seconds: Optional[int] = None
) -> dict:
    """Get aggregated emotion scores.

    Returns average emotion scores for a time window,
    including:
    - joy
    - sadness
    - anger
    - fear
    - surprise
    - disgust

    Args:
        window_seconds: Time window in seconds (default: from config)

    Returns:
        Dictionary with average emotion scores

    Raises:
        HTTPException: If handler is not initialized
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        result = await handler.get_emotion_aggregate(window_seconds=window_seconds)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emotion aggregate: {str(e)}"
        )


@router.post("/invoke")
async def invoke_skill(request: dict) -> dict:
    """Standard skill invocation endpoint.

    This endpoint follows the OpenClaw skill invocation pattern,
    accepting a standard input format and returning output in the
    expected structure.

    Args:
        request: Standard skill invocation request with 'input' key

    Returns:
        Standard skill response with 'output' key

    Raises:
        HTTPException: If handler is not initialized or request is invalid
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    input_data = request.get("input", {})

    # Check for batch analysis
    texts = input_data.get("texts")

    if texts and isinstance(texts, list):
        # Batch analysis
        options = input_data.get("options", {})
        request_id = input_data.get("request_id")

        result = await handler.analyze_batch(
            texts=texts,
            options=options,
            request_id=request_id
        )

        return {
            "output": {
                "aggregate": result["aggregate"],
                "individual_results": [
                    {
                        "text": r["text"],
                        "sentiment": r["sentiment"].model_dump(),
                        "emotions": r["emotions"].model_dump() if r["emotions"] else None
                    }
                    for r in result["results"]
                ]
            },
            "metadata": {
                "request_id": result["request_id"],
                "total_samples": len(result["results"]),
                "processing_time_ms": result["total_processing_time_ms"],
                "model_version": result["model_version"]
            }
        }

    # Single text analysis
    text = input_data.get("text", "")
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request must contain 'text' or 'texts' in input"
        )

    options = input_data.get("options", {})
    request_id = input_data.get("request_id")

    result = await handler.analyze(
        text=text,
        options=options,
        request_id=request_id
    )

    return {
        "output": {
            "text": result["text"],
            "sentiment": result["sentiment"].model_dump(),
            "emotions": result["emotions"].model_dump() if result["emotions"] else None,
            "trend": result["trend"]
        },
        "metadata": {
            "request_id": result["request_id"],
            "processing_time_ms": result["processing_time_ms"],
            "model_version": result["model_version"]
        }
    }

"""
Sentiment Agent - Main Application

Provides sentiment analysis services for understanding audience reactions.
Features:
- Rule-based sentiment analysis (current)
- DistilBERT ML model integration (placeholder for future)
- Batch analysis support
- Business metrics and distributed tracing
- Webhook integration to orchestrator for real-time updates
"""

import time
import logging
import httpx
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from sentiment_agent.config import get_settings
from sentiment_agent.models import (
    AnalyzeRequest,
    BatchRequest,
    SentimentResponse,
    BatchResponse,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse
)
from sentiment_agent.sentiment_analyzer import SentimentAnalyzer
from sentiment_agent.tracing import get_tracer
from sentiment_agent.metrics import record_analysis

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = get_tracer()
analyzer = SentimentAnalyzer(use_ml_model=settings.use_ml_model)

# Orchestrator webhook URL
ORCHESTRATOR_WEBHOOK = "http://openclaw-orchestrator:8000/api/sentiment/webhook"


async def send_sentiment_webhook(text: str, sentiment: str, score: float, confidence: float):
    """Send sentiment analysis result to orchestrator webhook.

    Args:
        text: Original text analyzed
        sentiment: Sentiment classification
        score: Sentiment score
        confidence: Confidence score
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            payload = {
                "text": text,
                "sentiment": sentiment,
                "score": score,
                "confidence": confidence
            }
            response = await client.post(ORCHESTRATOR_WEBHOOK, json=payload)
            if response.status_code == 200:
                logger.debug(f"Sent sentiment webhook: {sentiment}")
            else:
                logger.warning(f"Webhook failed: {response.status_code}")
    except Exception as e:
        # Don't fail analysis if webhook fails
        logger.warning(f"Failed to send sentiment webhook: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("Sentiment Agent starting up")
    logger.info(f"ML model enabled: {settings.use_ml_model}")
    logger.info(f"Tracing enabled: {settings.enable_tracing}")

    # Load ML model on startup
    try:
        analyzer.model.load()
        analyzer.model_available = True
        logger.info("Sentiment ML model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
        raise  # Fail startup if model unavailable

    logger.info(f"Model available: {analyzer.model_available}")

    yield
    logger.info("Sentiment Agent shutting down")


# Create FastAPI app
app = FastAPI(
    title="Sentiment Agent",
    description="Sentiment analysis service for understanding audience reactions",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health/live", response_model=LivenessResponse)
async def liveness():
    """Liveness probe for Kubernetes."""
    return LivenessResponse(status="alive")


@app.get("/health/ready", response_model=ReadinessResponse)
async def readiness():
    """Readiness probe for Kubernetes with model availability check."""
    return ReadinessResponse(
        status="ready",
        service="sentiment-agent",
        model_available=analyzer.model_available
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with detailed status."""
    return HealthResponse(
        status="healthy",
        service="sentiment-agent",
        model_available=analyzer.model_available
    )


@app.post("/v1/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: AnalyzeRequest) -> SentimentResponse:
    """
    Analyze sentiment of a single text.

    Args:
        request: Analysis request with text to analyze

    Returns:
        SentimentResponse with sentiment classification, score, and emotions
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("sentiment_analysis") as span:
            text_length = len(request.text)
            span.set_attribute("analysis.text_length", text_length)
            span.set_attribute("audience.size", 1)  # Single text analysis

            # Validate text length
            if text_length > settings.max_text_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Text length exceeds maximum of {settings.max_text_length}"
                )

            # Analyze sentiment
            result = analyzer.analyze(request.text)

            # Calculate duration
            duration = time.time() - start_time

            # Record span attributes
            span.set_attribute("sentiment.score", result["score"])
            span.set_attribute("sentiment.label", result["sentiment"])
            span.set_attribute("analysis.duration_ms", int(duration * 1000))

            # Record business metrics (use default show_id for individual analysis)
            record_analysis(
                show_id="default",
                sentiment=result["score"],
                emotions=result["emotions"],
                duration=duration
            )

            logger.info(
                f"Analyzed sentiment: {result['sentiment']} "
                f"(score={result['score']:.2f}, confidence={result['confidence']:.2f})"
            )

            # Send webhook to orchestrator (fire and forget)
            await send_sentiment_webhook(
                text=request.text,
                sentiment=result["sentiment"],
                score=result["score"],
                confidence=result["confidence"]
            )

            return SentimentResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        duration = time.time() - start_time
        # Record failed analysis
        record_analysis("default", 0.5, {
            "joy": 0.0, "surprise": 0.0, "neutral": 1.0,
            "sadness": 0.0, "anger": 0.0, "fear": 0.0
        }, duration)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/batch", response_model=BatchResponse)
async def analyze_batch(request: BatchRequest) -> BatchResponse:
    """
    Analyze sentiment of multiple texts in batch.

    Args:
        request: Batch analysis request with list of texts

    Returns:
        BatchResponse with list of sentiment analysis results
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("batch_sentiment_analysis") as span:
            text_count = len(request.texts)
            span.set_attribute("batch.text_count", text_count)
            span.set_attribute("audience.size", text_count)

            # Validate batch size
            if text_count > settings.batch_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Batch size exceeds maximum of {settings.batch_size}"
                )

            # Analyze batch
            results = analyzer.analyze_batch(request.texts)

            # Calculate duration
            duration = time.time() - start_time

            # Record span attributes
            span.set_attribute("analysis.duration_ms", int(duration * 1000))

            # Aggregate metrics for batch
            avg_sentiment = sum(r["score"] for r in results) / len(results) if results else 0.5

            # Aggregate emotions
            emotion_totals = {
                "joy": 0.0, "surprise": 0.0, "neutral": 0.0,
                "sadness": 0.0, "anger": 0.0, "fear": 0.0
            }
            for result in results:
                for emotion, score in result["emotions"].items():
                    emotion_totals[emotion] += score

            if results:
                avg_emotions = {k: v / len(results) for k, v in emotion_totals.items()}
            else:
                avg_emotions = emotion_totals

            # Record business metrics
            record_analysis(
                show_id="batch",
                sentiment=avg_sentiment,
                emotions=avg_emotions,
                duration=duration
            )

            logger.info(
                f"Analyzed batch of {text_count} texts "
                f"(avg_sentiment={avg_sentiment:.2f}, duration={duration:.3f}s)"
            )

            return BatchResponse(results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics in the standard format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start server
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )

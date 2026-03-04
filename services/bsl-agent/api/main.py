"""
BSL Text2Gloss Agent - FastAPI Application

Main API with translation and batch endpoints.
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

from core.translation import (
    BSLTranslator,
    TranslationRequest,
    TranslationResponse,
    GlossFormat,
    translate_and_enrich
)

# Import business metrics to register them with Prometheus
import core.business_metrics


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Metrics
translation_requests = Counter(
    'bsl_api_requests_total',
    'Total BSL API requests',
    ['endpoint', 'status']
)


# Global service instance
translator: Optional[BSLTranslator] = None


def get_translator() -> BSLTranslator:
    """Get global translator instance."""
    global translator
    if translator is None:
        translator = BSLTranslator(redis_client=None)
    return translator


# Create FastAPI app
app = FastAPI(
    title="BSL Text2Gloss Agent",
    description="British Sign Language gloss notation translation service",
    version="0.5.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "bsl-agent",
        "version": "0.5.0"
    }


@app.post("/api/v1/translate")
async def translate(request_data: dict):
    """
    Translate text to BSL gloss notation.

    Request body:
    {
        "text": "Hello, how are you?",
        "language": "en" (optional),
        "gloss_format": "singspell" (optional),
        "region": "northern" (optional)
    }

    Response:
    {
        "request_id": "...",
        "source_text": "Hello, how are you?",
        "gloss": "HELLO[right] HOW YOU ?q",
        "gloss_format": "singspell",
        "duration": 2.5,
        "confidence": 0.85,
        "translation_time_ms": 150,
        "breakdown": ["HELLO[right]", "HOW", "YOU", "?q"],
        "from_cache": false,
        "error": null
    }
    """
    try:
        translator_instance = get_translator()

        request = TranslationRequest(
            text=request_data.get("text", ""),
            language=request_data.get("language", "en"),
            gloss_format=GlossFormat(request_data.get("gloss_format", "singspell")),
            region=request_data.get("region")
        )

        result = translator_instance.translate(request)

        translation_requests.labels(endpoint="translate", status="success").inc()

        return {
            "request_id": result.request_id,
            "source_text": result.source_text,
            "gloss": result.gloss,
            "gloss_format": result.gloss_format,
            "duration": result.duration,
            "confidence": result.confidence,
            "translation_time_ms": result.translation_time_ms,
            "breakdown": result.breakdown,
            "non_manual_markers": result.non_manual_markers,
            "region": result.region,
            "from_cache": result.from_cache,
            "error": result.error,
            "degraded": result.degraded
        }

    except Exception as e:
        logger.error(f"Translation error: {e}")
        translation_requests.labels(endpoint="translate", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/translate/batch")
async def translate_batch(requests_data: dict):
    """
    Translate multiple texts in batch.

    Request body:
    {
        "texts": [
            {"text": "Hello", "gloss_format": "singspell"},
            {"text": "Thank you"}
        ]
    }

    Response:
    {
        "translations": [...],
        "total": 2,
        "processing_time_ms": 200
    }
    """
    try:
        translator_instance = get_translator()

        texts = requests_data.get("texts", [])
        translation_requests = []

        for item in texts:
            request = TranslationRequest(
                text=item.get("text", ""),
                language=item.get("language", "en"),
                gloss_format=GlossFormat(item.get("gloss_format", "singspell")),
                region=item.get("region")
            )
            translation_requests.append(request)

        start_time = asyncio.get_event_loop().time()

        results = translator_instance.translate_batch(translation_requests)

        duration = asyncio.get_event_loop().time() - start_time

        translation_requests.labels(endpoint="batch", status="success").inc()

        return {
            "translations": [
                {
                    "request_id": r.request_id,
                    "source_text": r.source_text,
                    "gloss": r.gloss,
                    "gloss_format": r.gloss_format,
                    "duration": r.duration,
                    "confidence": r.confidence
                }
                for r in results
            ],
            "total": len(results),
            "processing_time_ms": duration * 1000
        }

    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        translation_requests.labels(endpoint="batch", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

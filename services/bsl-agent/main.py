"""
BSL Agent - Main Application

Provides text-to-BSL-gloss translation and avatar rendering services with
OpenTelemetry tracing, Prometheus metrics, and health checks.
"""

import time
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from opentelemetry import trace
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config import get_settings
from translator import BSLTranslator
from avatar_renderer import AvatarRenderer
from models import (
    TranslateRequest,
    TranslateResponse,
    RenderRequest,
    RenderResponse,
    HealthResponse
)
from tracing import setup_telemetry, instrument_fastapi, add_span_attributes, record_error
from metrics import record_translation, record_render

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = setup_telemetry("bsl-agent")
translator = BSLTranslator()
avatar_renderer = AvatarRenderer(
    model_path=settings.avatar_model_path,
    resolution=tuple(map(int, settings.avatar_resolution.split('x'))),
    fps=settings.avatar_fps,
    enable_facial_expressions=settings.enable_facial_expressions,
    enable_body_language=settings.enable_body_language
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("BSL Agent starting up")
    logger.info(f"Avatar rendering enabled: {settings.enable_facial_expressions}")
    logger.info(f"Avatar resolution: {settings.avatar_resolution} @ {settings.avatar_fps}fps")
    yield
    logger.info("BSL Agent shutting down")


# Create FastAPI app
app = FastAPI(
    title="BSL Agent",
    description="British Sign Language gloss notation translation and avatar rendering service",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    return HealthResponse(
        status="ready",
        service="bsl-agent",
        translator_ready=True,
        avatar_ready=True
    )


@app.post("/v1/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest) -> TranslateResponse:
    """
    Translate English text to BSL gloss notation.

    Args:
        request: Translation request with text and options

    Returns:
        TranslateResponse with gloss notation and metadata

    Example:
        POST /v1/translate
        {
            "text": "Hello, how are you?",
            "include_nmm": true,
            "context": {"show_id": "bards-tale"}
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("translate_text") as span:
            # Extract context
            context = request.context or {}
            show_id = context.get("show_id", "unknown")

            # Perform translation
            result = translator.translate_with_nmm(request.text)

            # Extract NMM markers if requested
            nmm_markers = result["non_manual_markers"] if request.include_nmm else None

            # Calculate duration
            duration_sec = time.time() - start_time

            # Record metrics
            record_translation(
                show_id=show_id,
                words=len(request.text.split()),
                duration=duration_sec,
                quality=result["confidence"],
                gloss_words=len(result["breakdown"])
            )

            # Add span attributes for tracing
            add_span_attributes(span, {
                "show.id": show_id,
                "translation.text_length": len(request.text),
                "translation.word_count": len(request.text.split()),
                "translation.gloss_word_count": len(result["breakdown"]),
                "translation.gloss_format": "singspell",
                "translation.confidence": result["confidence"],
                "translation.include_nmm": request.include_nmm,
                "translation.nmm_count": len(nmm_markers) if nmm_markers else 0
            })

            logger.info(
                f"Translation completed for show={show_id}, "
                f"words={len(request.text.split())}, "
                f"duration={duration_sec:.3f}s"
            )

            return TranslateResponse(
                gloss=result["gloss"],
                breakdown=result["breakdown"],
                duration_estimate=result["duration_estimate"],
                confidence=result["confidence"],
                non_manual_markers=nmm_markers,
                translation_time_ms=result["translation_time_ms"]
            )

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        duration_sec = time.time() - start_time

        # Record error on current span
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "translation",
            "error.text_length": len(request.text)
        })

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/render", response_model=RenderResponse)
async def render_avatar(request: RenderRequest) -> RenderResponse:
    """
    Render BSL signs using avatar system.

    Args:
        request: Render request with gloss and session info

    Returns:
        RenderResponse with animation data and status

    Example:
        POST /v1/render
        {
            "gloss": "HELLO HOW YOU",
            "session_id": "user-123",
            "include_nmm": true
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("render_avatar") as span:
            # Generate animation data
            animation_data = avatar_renderer.render_gloss(
                gloss=request.gloss,
                non_manual_markers=[] if not request.include_nmm else None
            )

            # Calculate metrics
            gesture_count = len(animation_data["gestures"])
            duration_sec = time.time() - start_time

            # Record metrics
            session_id = request.session_id or "unknown"
            record_render(
                show_id="unknown",  # Could be extracted from context in future
                gesture_count=gesture_count,
                duration=duration_sec,
                session_id=session_id
            )

            # Add span attributes for tracing
            add_span_attributes(span, {
                "render.gloss_word_count": len(request.gloss.split()),
                "render.gesture_count": gesture_count,
                "render.duration_total": animation_data["total_duration"],
                "render.session_id": session_id,
                "render.include_nmm": request.include_nmm
            })

            logger.info(
                f"Avatar render completed: gestures={gesture_count}, "
                f"duration={duration_sec:.3f}s, session={session_id}"
            )

            return RenderResponse(
                success=True,
                animation_data=animation_data,
                gestures_queued=gesture_count,
                session_id=request.session_id,
                message=f"Successfully queued {gesture_count} gestures for rendering"
            )

    except Exception as e:
        logger.error(f"Avatar rendering failed: {e}")

        # Record error on current span
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "render",
            "error.gloss_length": len(request.gloss)
        })

        # Return error response
        return RenderResponse(
            success=False,
            animation_data={},
            gestures_queued=0,
            session_id=request.session_id,
            message=f"Rendering failed: {str(e)}"
        )


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
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower()
    )

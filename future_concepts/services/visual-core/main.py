"""Visual Core Service - Main FastAPI Application.

LTX-2 video generation integration hub for Project Chimera.
Serves as the central service for AI-powered video generation.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import List, Optional

from config import settings
from tracing import setup_tracing, instrument_fastapi, shutdown_tracing
from metrics import request_latency
from models import VideoGenerationRequest, VideoGenerationResponse, BatchGenerationRequest
from ltx_client import get_ltx_client
from prompt_factory import PromptFactory, VisualStyle, CameraMotion
from video_pipeline import VideoPipeline
import uuid
import os


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Video pipeline for FFmpeg processing
video_pipeline = VideoPipeline(ffmpeg_path=settings.ffmpeg_path)


# Initialize OpenTelemetry tracing
try:
    tracer = setup_tracing(
        service_name=settings.service_name,
        service_version="1.0.0",
        otlp_endpoint=settings.otlp_endpoint,
        environment="production"
    )
    logger.info("Tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize tracing: {e}")
    tracer = None


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Visual Core Service...")
    try:
        # Instrument FastAPI with OpenTelemetry
        instrument_fastapi(app)

        logger.info("Visual Core Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Visual Core Service...")
    shutdown_tracing()
    logger.info("Visual Core Service stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Visual Core Service",
    description="LTX-2 video generation integration hub for Project Chimera",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================================
# Security Middleware (Environment-based CORS, Security Headers, Rate Limiting)
# ============================================================================
import sys
import os

# Add shared module to path for security middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

# Add CORS middleware - replaced with security middleware
from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    setup_rate_limit_error_handler,
)


# ============================================================================
# Health & Metrics Endpoints
# ============================================================================

@app.get("/health/live", response_model=Dict[str, str])
async def liveness_probe():
    """Liveness probe endpoint."""
    return {"status": "alive"}


@app.get("/health/ready", response_model=Dict[str, object])
async def readiness_probe():
    """Readiness probe endpoint."""
    dependencies = {}
    all_ready = True

    # Check LTX API connectivity
    try:
        client = get_ltx_client()
        # Initialize client if needed for health check
        if not client._client:
            import httpx
            client._client = httpx.AsyncClient(
                base_url=client.api_base,
                headers={"Authorization": f"Bearer {client.api_key}"},
                timeout=10.0
            )

        # Simple health check - try to reach API
        response = await client._client.get("/")
        dependencies["ltx_api"] = response.status_code < 500
    except Exception as e:
        logger.warning(f"LTX API health check failed: {e}")
        dependencies["ltx_api"] = False
        all_ready = False

    return {
        "status": "ready" if all_ready else "not_ready",
        "service": settings.service_name,
        "dependencies": dependencies
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Video Generation Endpoints
# ============================================================================

@app.post("/api/v1/generate/text", response_model=VideoGenerationResponse)
async def generate_video_from_text(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate video from text prompt using LTX-2 API.
    """
    request_id = str(uuid.uuid4())

    try:
        client = get_ltx_client()

        result = await client.text_to_video(
            prompt=request.prompt,
            duration=request.duration,
            resolution=request.resolution,
            fps=request.fps,
            model=request.model,
            generate_audio=request.generate_audio,
            camera_motion=request.camera_motion,
            lora_path=request.lora_id
        )

        return VideoGenerationResponse(
            request_id=request_id,
            video_id=result.video_id,
            status="complete",
            url=result.url
        )

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return VideoGenerationResponse(
            request_id=request_id,
            video_id="",
            status="error",
            error=str(e)
        )


@app.post("/api/v1/generate/prompt", response_model=VideoGenerationResponse)
async def generate_from_prompt(
    prompt: str,
    style: str = "corporate_briefing",
    duration: int = 10,
    resolution: str = "1920x1080"
):
    """Generate video from enhanced prompt"""

    request_id = str(uuid.uuid4())

    try:
        # Build prompt using factory
        visual_style = VisualStyle(style)
        camera_motion = CameraMotion.STATIC

        enhanced_prompt = PromptFactory.build_prompt(
            narrative=prompt,
            style=visual_style,
            camera_motion=camera_motion,
            duration=duration
        )

        # Add technical enhancements
        enhanced_prompt = PromptFactory.enhance_prompt_for_video(
            enhanced_prompt,
            {
                "resolution": resolution,
                "generate_audio": True
            }
        )

        # Generate video
        client = get_ltx_client()
        result = await client.text_to_video(
            prompt=enhanced_prompt,
            duration=duration,
            resolution=resolution
        )

        return VideoGenerationResponse(
            request_id=request_id,
            video_id=result.video_id,
            status="complete",
            url=result.url
        )

    except Exception as e:
        logger.error(f"Prompt-based video generation failed: {e}")
        return VideoGenerationResponse(
            request_id=request_id,
            video_id="",
            status="error",
            error=str(e)
        )


# ============================================================================
# Video Pipeline Endpoints
# ============================================================================

@app.post("/api/v1/video/stitch")
async def stitch_videos(
    video_urls: List[str],
    transitions: bool = True,
    output_filename: Optional[str] = None
):
    """Stitch multiple videos together"""

    try:
        if output_filename is None:
            output_filename = f"stitched_{uuid.uuid4().hex}.mp4"

        output_path = os.path.join(settings.cache_path, output_filename)

        result_path = await video_pipeline.stitch_videos(
            video_urls=video_urls,
            output_path=output_path,
            transitions=transitions
        )

        return {"status": "success", "url": result_path}

    except Exception as e:
        logger.error(f"Video stitching failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )

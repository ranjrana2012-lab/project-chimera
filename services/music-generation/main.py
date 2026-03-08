"""
Music Generation Service - Main FastAPI Application
Project Chimera v0.5.0
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config import settings
from .model_pool import ModelPool, get_model_pool
from .metrics import (
    request_counter,
    model_load_time,
    active_generations
)
from .tracing import (
    setup_tracing,
    instrument_fastapi,
    get_tracer,
    trace_model_loading,
    shutdown_tracing
)
from .models import (
    HealthResponse,
    ModelInfo,
    GenerateRequest,
    GenerateResponse,
    GenerationMetadata,
    ContinueRequest,
    ContinueResponse,
    BatchGenerateRequest,
    BatchGenerateResponse,
    BatchGenerateItem,
    GenresResponse,
    MoodsResponse,
    HistoryResponse,
    VALID_GENRES,
    VALID_MOODS
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize OpenTelemetry tracing
try:
    tracer = setup_tracing(
        service_name=settings.service_name,
        service_version="0.5.0",
        otlp_endpoint=settings.otlp_endpoint,
        environment=settings.environment
    )
    logger.info("Tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize tracing: {e}")
    tracer = None


# Global model pool
model_pool: ModelPool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Music Generation Service...")
    global model_pool

    try:
        # Instrument FastAPI with OpenTelemetry
        instrument_fastapi(app)

        # Initialize model pool (models loaded lazily)
        model_pool = get_model_pool()

        logger.info("Model pool initialized (models will load on demand)")
        logger.info("Music Generation Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model pool: {e}")
        model_load_time.labels(model="model_pool", status="error").set(0)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Music Generation Service...")
    if model_pool:
        # Cleanup any loaded models
        if hasattr(model_pool, 'models'):
            for model_name in list(model_pool.models.keys()):
                if model_pool.models[model_name] is not None:
                    try:
                        # Unload model to free memory
                        del model_pool.models[model_name]
                        del model_pool.processors[model_name]
                        model_pool.models[model_name] = None
                        model_pool.processors[model_name] = None
                    except Exception as e:
                        logger.warning(f"Error unloading model {model_name}: {e}")
    shutdown_tracing()
    logger.info("Music Generation Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Music Generation Service",
    description="AI-powered music generation service for Project Chimera",
    version="0.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# Include routers (when they are created, they will be included here)
# app.include_router(models_router, prefix="/api/v1", tags=["models"])
# app.include_router(generate_router, prefix="/api/v1", tags=["generate"])


@app.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe endpoint.
    Returns service status indicating if the service is running.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe() -> Dict[str, str]:
    """
    Readiness probe endpoint.
    Returns service status indicating if the service is ready to handle requests.
    """
    if model_pool is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint with model information for E2E tests.
    Returns overall health status including model loaded state.
    """
    # Check if any model is loaded
    model_loaded = False
    if model_pool is not None:
        for model_name in model_pool.models:
            if model_pool.models[model_name] is not None:
                model_loaded = True
                break

    model_info = None
    if model_loaded:
        # Create model info dict (not a ModelInfo object to avoid .dict() issues)
        model_info = {
            "name": "musicgen",
            "loaded": True,
            "version": "0.5.0"
        }

    return HealthResponse(
        status="healthy",
        service="music-generation",
        model_loaded=model_loaded,
        model_info=model_info
    )


# ============================================================================
# E2E-Compatible Music Generation API Endpoints
# ============================================================================

# In-memory generation history for E2E tests
generation_history: List[Dict] = []
generation_counter = 0


@app.post("/generate", response_model=GenerateResponse)
async def generate_music(request: GenerateRequest):
    """
    Generate music from a text prompt.

    Args:
        request: Generation request with prompt, duration, and optional parameters

    Returns:
        GenerateResponse with audio data and metadata
    """
    global generation_counter, generation_history

    start_time = time.time()

    # Validate optional parameters against valid values
    if request.mood and request.mood not in VALID_MOODS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid mood. Valid moods: {', '.join(sorted(VALID_MOODS))}"
        )

    if request.genre and request.genre not in VALID_GENRES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid genre. Valid genres: {', '.join(sorted(VALID_GENRES))}"
        )

    # Simulate music generation (placeholder)
    # In a real implementation, this would call the actual model
    audio_data = {
        "url": f"/api/audio/generated/{generation_counter}.wav",
        "format": "wav"
    }

    generation_time = time.time() - start_time
    generation_counter += 1

    # Create generation record for history
    generation_record = {
        "id": generation_counter,
        "prompt": request.prompt,
        "duration": request.duration,
        "mood": request.mood,
        "genre": request.genre,
        "tempo": request.tempo,
        "timestamp": datetime.utcnow().isoformat(),
        "generation_time_ms": generation_time * 1000
    }
    generation_history.append(generation_record)

    # Keep only last 100 generations
    if len(generation_history) > 100:
        generation_history.pop(0)

    metadata = GenerationMetadata(
        model="musicgen",
        generation_time_ms=generation_time * 1000,
        timestamp=datetime.utcnow().isoformat()
    )

    logger.info(
        f"Music generated: prompt='{request.prompt}', "
        f"duration={request.duration}s, mood={request.mood}, genre={request.genre}"
    )

    return GenerateResponse(
        audio_data=audio_data,
        duration=request.duration,
        format="wav",
        prompt=request.prompt,
        mood=request.mood,
        genre=request.genre,
        tempo=request.tempo,
        metadata=metadata
    )


@app.get("/api/genres", response_model=GenresResponse)
async def get_genres():
    """
    Get available music genres.

    Returns:
        GenresResponse with list of available genres
    """
    return GenresResponse(genres=sorted(list(VALID_GENRES)))


@app.get("/api/moods", response_model=MoodsResponse)
async def get_moods():
    """
    Get available music moods.

    Returns:
        MoodsResponse with list of available moods
    """
    return MoodsResponse(moods=sorted(list(VALID_MOODS)))


@app.post("/generate/continue", response_model=ContinueResponse)
async def continue_generation(request: ContinueRequest):
    """
    Continue generating from existing music.

    Args:
        request: Continue request with seed_music_id and additional duration

    Returns:
        ContinueResponse with extended audio data
    """
    start_time = time.time()

    # Simulate continuation (placeholder)
    audio_data = {
        "url": f"/api/audio/continued/{request.seed_music_id}.wav",
        "format": "wav"
    }

    generation_time = time.time() - start_time

    logger.info(
        f"Music continued: seed={request.seed_music_id}, "
        f"additional_duration={request.duration}s"
    )

    return ContinueResponse(
        audio_data=audio_data,
        seed_music_id=request.seed_music_id,
        duration=request.duration,
        format="wav"
    )


@app.post("/generate/batch", response_model=BatchGenerateResponse)
async def batch_generate(request: BatchGenerateRequest):
    """
    Generate multiple music tracks in one request.

    Args:
        request: Batch request with list of prompts

    Returns:
        BatchGenerateResponse with list of generated tracks
    """
    tracks = []
    total_duration = 0

    for item in request.prompts:
        start_time = time.time()

        # Simulate generation for each track
        audio_data = {
            "url": f"/api/audio/batch/{generation_counter + len(tracks)}.wav",
            "format": "wav"
        }

        generation_time = time.time() - start_time

        track_response = GenerateResponse(
            audio_data=audio_data,
            duration=item.duration,
            format="wav",
            prompt=item.prompt,
            mood=item.mood,
            genre=item.genre,
            metadata=GenerationMetadata(
                model="musicgen",
                generation_time_ms=generation_time * 1000,
                timestamp=datetime.utcnow().isoformat()
            )
        )

        tracks.append(track_response)
        total_duration += item.duration

    logger.info(f"Batch generation completed: {len(tracks)} tracks, {total_duration}s total")

    return BatchGenerateResponse(
        tracks=tracks,
        total_duration=total_duration,
        count=len(tracks)
    )


@app.get("/api/history", response_model=HistoryResponse)
async def get_history(limit: int = 10):
    """
    Get generation history.

    Args:
        limit: Maximum number of history entries to return (default: 10)

    Returns:
        HistoryResponse with list of past generations
    """
    # Limit to requested amount, max 100
    actual_limit = min(max(1, limit), 100)
    history_slice = generation_history[-actual_limit:] if generation_history else []

    return HistoryResponse(
        generations=history_slice,
        count=len(history_slice),
        limit=actual_limit
    )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )

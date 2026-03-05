"""
SceneSpeak Agent - Main Application

Provides dialogue generation services with GLM 4.7 API integration,
local LLM fallback, business metrics, and distributed tracing.
"""

import time
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from fastapi.responses import Response
from pydantic import BaseModel

from config import get_settings
from glm_client import GLMClient
from models import GenerateRequest, DialogueResponse, HealthResponse
from tracing import setup_telemetry, instrument_fastapi, add_dialogue_span_attributes, record_error
from metrics import record_generation

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = setup_telemetry("scenespeak-agent")
glm_client = GLMClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("SceneSpeak Agent starting up")
    logger.info(f"GLM API configured: {bool(settings.glm_api_key)}")
    logger.info(f"Local model configured: {bool(settings.local_model_path)}")
    yield
    logger.info("SceneSpeak Agent shutting down")


# Create FastAPI app
app = FastAPI(
    title="SceneSpeak Agent",
    description="Dialogue generation service with GLM 4.7 API and local LLM fallback",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)


# Legacy Request/Response Models (for backward compatibility)
class GenerateResponse(BaseModel):
    """Response from dialogue generation (legacy format)."""
    dialogue: str
    adapter: str
    metadata: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint (legacy)."""
    return HealthResponse(
        status="healthy",
        service="scenespeak-agent",
        model_available=bool(settings.glm_api_key or settings.local_model_path)
    )


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    model_available = bool(settings.glm_api_key or settings.local_model_path)
    return {
        "status": "ready",
        "service": "scenespeak-agent",
        "model_available": model_available
    }


@app.post("/v1/generate", response_model=DialogueResponse)
async def generate_dialogue_v1(request: GenerateRequest) -> DialogueResponse:
    """
    Generate dialogue using GLM 4.7 API with local LLM fallback.

    Args:
        request: Generation request with prompt and parameters

    Returns:
        DialogueResponse with generated text and metadata
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("generate_dialogue") as span:
            span.set_attribute("prompt_length", len(request.prompt))
            span.set_attribute("max_tokens", request.max_tokens)
            span.set_attribute("temperature", request.temperature)

            # Extract context for tracing
            context = request.context or {}
            show_id = context.get("show_id", "unknown")
            scene_number = context.get("scene_number")
            adapter_name = context.get("adapter", "default")

            # Generate dialogue
            response = await glm_client.generate(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            duration_sec = duration_ms / 1000

            # Add span attributes for tracing
            add_dialogue_span_attributes(
                span,
                show_id=show_id,
                scene_number=scene_number,
                adapter_name=response.source,
                tokens_input=int(len(request.prompt.split()) * 1.3),
                tokens_output=response.tokens_used,
                dialogue_lines_count=len(response.text.split('.'))
            )

            # Record business metrics
            record_generation(
                show_id=show_id,
                adapter=response.source,
                tokens=response.tokens_used,
                duration=duration_sec,
                quality=0.85,  # Will be calculated based on actual metrics
                cache_hit=False
            )

            logger.info(
                f"Generated dialogue for show={show_id}, source={response.source}, "
                f"tokens={response.tokens_used}, duration={duration_sec:.3f}s"
            )

            return response

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        duration_sec = (time.time() - start_time)
        record_generation("unknown", "api", 0, duration_sec, 0.0, False)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/generate/legacy", response_model=GenerateResponse)
async def generate_dialogue_legacy(request: GenerateRequest) -> GenerateResponse:
    """
    Legacy endpoint for dialogue generation.

    Maintains backward compatibility with existing integrations.
    """
    start_time = time.time()

    try:
        # Extract context
        context = request.context or {}
        show_id = context.get("show_id", "unknown")
        adapter = context.get("adapter", "default")

        # Generate dialogue
        response = await glm_client.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        # Calculate duration
        duration_sec = (time.time() - start_time)

        # Record business metrics
        record_generation(
            show_id=show_id,
            adapter=response.source,
            tokens=response.tokens_used,
            duration=duration_sec,
            quality=0.85,
            cache_hit=False
        )

        # Return legacy format
        return GenerateResponse(
            dialogue=response.text,
            adapter=response.source,
            metadata={
                "model": response.model,
                "tokens_used": response.tokens_used,
                "duration_ms": response.duration_ms,
                "generation_time": duration_sec,
                "source": response.source
            }
        )

    except Exception as e:
        logger.error(f"Dialogue generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics in the standard format.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
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

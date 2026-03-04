"""
SceneSpeak Agent - Main Application

Provides dialogue generation services with business metrics integration.
"""

import time
import logging
from typing import Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from metrics import record_generation

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SceneSpeak Agent",
    description="Dialogue generation service with quality metrics",
    version="1.0.0"
)


# Request/Response Models
@dataclass
class DialogueMetadata:
    """Metadata for dialogue generation."""
    show_id: str
    quality_score: float = 0.8
    from_cache: bool = False


class GenerateRequest(BaseModel):
    """Request for dialogue generation."""
    prompt: str = Field(..., description="The prompt for dialogue generation")
    adapter: Optional[str] = Field("default", description="The adapter to use")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class GenerateResponse(BaseModel):
    """Response from dialogue generation."""
    dialogue: str = Field(..., description="Generated dialogue text")
    adapter: str = Field(..., description="Adapter used for generation")
    metadata: dict = Field(default_factory=dict, description="Generation metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="scenespeak-agent")


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate dialogue based on a prompt.

    This endpoint demonstrates integration with business metrics.
    In production, this would call an actual LLM service.
    """
    start = time.time()

    try:
        # Simulate dialogue generation
        # In production, this would call the actual LLM adapter
        await time.sleep(0.1)  # Simulate processing

        result_dialogue = f"Generated dialogue for: {request.prompt}"

        # Calculate generation time
        duration = time.time() - start

        # Extract metadata
        metadata = request.metadata or {}
        show_id = metadata.get("show_id", "unknown")
        adapter = request.adapter or "default"

        # Estimate tokens (rough approximation: words = tokens/1.3)
        estimated_tokens = int(len(result_dialogue.split()) * 1.3)

        # Create response with metadata
        response_metadata = {
            "quality_score": 0.85,  # In production, calculate actual quality
            "from_cache": False,    # In production, check actual cache
            "generation_time": duration,
            "adapter": adapter
        }

        # Record business metrics
        record_generation(
            show_id=show_id,
            adapter=adapter,
            tokens=estimated_tokens,
            duration=duration,
            quality=response_metadata["quality_score"],
            cache_hit=response_metadata["from_cache"]
        )

        logger.info(
            f"Generated dialogue for show={show_id}, adapter={adapter}, "
            f"tokens={estimated_tokens}, duration={duration:.3f}s"
        )

        return GenerateResponse(
            dialogue=result_dialogue,
            adapter=adapter,
            metadata=response_metadata
        )

    except Exception as e:
        logger.error(f"Dialogue generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    In production, this would be served by prometheus_client's start_http_server.
    For now, we return a simple status.
    """
    return {"status": "metrics available at /metrics via prometheus_client"}


@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info("SceneSpeak Agent starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("SceneSpeak Agent shutting down...")


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start server
    # Note: In production, use start_http_server for Prometheus metrics
    uvicorn.run(app, host="0.0.0.0", port=8000)

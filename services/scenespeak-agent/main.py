"""
SceneSpeak Agent - Main Application

Provides dialogue generation services with business metrics integration
and distributed tracing.
"""

import time
import logging
from typing import Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from metrics import record_generation
from tracing import setup_telemetry, instrument_fastapi, add_dialogue_span_attributes, record_error

logger = logging.getLogger(__name__)

# Set up distributed tracing
tracer = setup_telemetry("scenespeak-agent")

# Create FastAPI app
app = FastAPI(
    title="SceneSpeak Agent",
    description="Dialogue generation service with quality metrics and distributed tracing",
    version="1.0.0"
)

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)


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

    This endpoint demonstrates integration with business metrics
    and distributed tracing. In production, this would call an actual LLM service.
    """
    start = time.time()

    # Start tracing span if telemetry is available
    if tracer is not None:
        generate_span = tracer.start_as_current_span("generate_dialogue")
        span = generate_span.__enter__()
    else:
        span = None
        generate_span = None

    try:
        # Extract metadata for tracing
        metadata = request.metadata or {}
        show_id = metadata.get("show_id", "unknown")
        scene_number = metadata.get("scene_number")
        adapter = request.adapter or "default"

        # Simulate dialogue generation
        # In production, this would call the actual LLM adapter
        await time.sleep(0.1)  # Simulate processing

        result_dialogue = f"Generated dialogue for: {request.prompt}"

        # Calculate generation time
        duration = time.time() - start

        # Estimate tokens (rough approximation: words = tokens/1.3)
        estimated_tokens_input = int(len(request.prompt.split()) * 1.3)
        estimated_tokens_output = int(len(result_dialogue.split()) * 1.3)
        dialogue_lines_count = len(result_dialogue.split('.'))

        # Add span attributes for tracing
        if span is not None:
            add_dialogue_span_attributes(
                span,
                show_id=show_id,
                scene_number=scene_number,
                adapter_name=adapter,
                tokens_input=estimated_tokens_input,
                tokens_output=estimated_tokens_output,
                dialogue_lines_count=dialogue_lines_count
            )

        # Create response with metadata
        response_metadata = {
            "quality_score": 0.85,  # In production, calculate actual quality
            "from_cache": False,    # In production, check actual cache
            "generation_time": duration,
            "adapter": adapter,
            "tokens_input": estimated_tokens_input,
            "tokens_output": estimated_tokens_output
        }

        # Record business metrics
        record_generation(
            show_id=show_id,
            adapter=adapter,
            tokens=estimated_tokens_output,
            duration=duration,
            quality=response_metadata["quality_score"],
            cache_hit=response_metadata["from_cache"]
        )

        logger.info(
            f"Generated dialogue for show={show_id}, adapter={adapter}, "
            f"tokens_input={estimated_tokens_input}, tokens_output={estimated_tokens_output}, "
            f"duration={duration:.3f}s"
        )

        return GenerateResponse(
            dialogue=result_dialogue,
            adapter=adapter,
            metadata=response_metadata
        )

    except Exception as e:
        logger.error(f"Dialogue generation failed: {e}")

        # Record error on span
        if span is not None:
            record_error(span, e, {"error.endpoint": "/v1/generate"})

        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Close the span
        if generate_span is not None:
            generate_span.__exit__(None, None, None)


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

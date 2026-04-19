"""SceneSpeak Agent - Main Application

Provides dialogue generation services with GLM 4.7 API integration,
local LLM fallback, business metrics, and distributed tracing.
"""

import time
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

import sys
import os

# Get the directory containing this file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# Add service directory to path FIRST for local modules
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Add shared module path (after local so local takes precedence)
shared_path = os.path.join(project_root, "shared")
if shared_path not in sys.path:
    sys.path.append(shared_path)

# Import local modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from shared.kafka_bus import KafkaEventBus
except ImportError:
    KafkaEventBus = None

import config
import glm_client
import local_llm
import openai_llm  # New OpenAI-compatible client
import models
import metrics
import tracing

get_settings = config.get_settings
GLMClient = glm_client.GLMClient
GLMDialogueResponse = glm_client.DialogueResponse  # Dataclass from glm_client
LocalLLMClient = local_llm.LocalLLMClient
OpenAILLMClient = openai_llm.OpenAILLMClient  # New client
GenerateRequest = models.GenerateRequest
DialogueResponse = models.DialogueResponse
HealthResponse = models.HealthResponse
record_generation = metrics.record_generation

# Setup tracing - use local module (setup_telemetry)
setup_tracing = tracing.setup_telemetry
instrument_fastapi = tracing.instrument_fastapi
add_dialogue_span_attributes = tracing.add_dialogue_span_attributes

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = setup_tracing(
    service_name="scenespeak-agent"
)
glm_client = GLMClient()
local_llm_client: Optional[LocalLLMClient] = None
openai_llm_client: Optional[OpenAILLMClient] = None  # New client
kafka_bus = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    global local_llm_client, openai_llm_client, kafka_bus

    logger.info("SceneSpeak Agent starting up")
    logger.info(f"GLM API configured: {bool(settings.glm_api_key)}")
    logger.info(f"Local LLM enabled: {settings.local_llm_enabled}")
    logger.info(f"Local LLM type: {settings.local_llm_type}")

    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    if KafkaEventBus:
        kafka_bus = KafkaEventBus(bootstrap_servers, "scenespeak-agent")
        try:
            await kafka_bus.start()
            
            async def handle_dialogue_request(msg: dict):
                prompt = msg.get("prompt", "")
                task_id = msg.get("task_id", "")
                context = msg.get("context", {})
                if prompt and task_id:
                    # Prefer GLM or fallback internally
                    try:
                        response = await glm_client.generate(
                            prompt=prompt,
                            max_tokens=500,
                            temperature=0.7,
                            prefer_local=False
                        )
                        await kafka_bus.publish("chimera.dialogue.completed", {
                            "task_id": task_id,
                            "dialogue": response.text,
                            "status": "success",
                            "model": response.model
                        })
                    except Exception as e:
                        logger.error(f"Failed to generate dialogue for {task_id}: {e}")
                        await kafka_bus.publish("chimera.dialogue.completed", {
                            "task_id": task_id,
                            "dialogue": "",
                            "status": "error",
                            "error": str(e)
                        })
                    
            await kafka_bus.subscribe("chimera.dialogue.request", handle_dialogue_request)
        except Exception as e:
            logger.error(f"Failed to start Kafka bus: {e}")

    # Initialize local LLM if enabled
    if settings.local_llm_enabled:
        try:
            # Use OpenAI-compatible client (Nemotron) if configured
            if getattr(settings, 'local_llm_type', 'ollama') == 'openai':
                openai_llm_client = OpenAILLMClient(
                    base_url=settings.local_llm_url,
                    model=settings.local_llm_model,
                    timeout=getattr(settings, 'llm_timeout', 120)
                )
                connected = await openai_llm_client.connect()
                if connected:
                    logger.info(
                        f"OpenAI-compatible LLM connected: {settings.local_llm_url} "
                        f"with model {settings.local_llm_model}"
                    )
                else:
                    logger.warning(
                        f"OpenAI-compatible LLM unavailable at {settings.local_llm_url}, "
                        "will use GLM API or fallback"
                    )
            else:
                # Use Ollama client
                local_llm_client = LocalLLMClient(
                    base_url=settings.local_llm_url,
                    model=settings.local_llm_model
                )
                connected = await local_llm_client.connect()
                if connected:
                    logger.info(
                        f"Ollama LLM connected: {settings.local_llm_url} "
                        f"with model {settings.local_llm_model}"
                    )
                else:
                    logger.warning(
                        f"Ollama LLM unavailable at {settings.local_llm_url}, "
                        "will use GLM API or fallback"
                    )
        except Exception as e:
            logger.warning(f"Failed to initialize local LLM: {e}")

    yield

    # Cleanup
    if local_llm_client:
        await local_llm_client.disconnect()
    if openai_llm_client:
        await openai_llm_client.disconnect()
    if kafka_bus:
        await kafka_bus.stop()
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

# ============================================================================
# Security Middleware (Environment-based CORS, Security Headers, Rate Limiting)
# ============================================================================
try:
    from shared.middleware import (
        SecurityHeadersMiddleware,
        configure_cors,
        setup_rate_limit_error_handler,
    )
    # Apply security configurations
    configure_cors(app)
    app.add_middleware(SecurityHeadersMiddleware)
    setup_rate_limit_error_handler(app)
except ImportError:
    logger.warning("Shared middleware not available")


# Legacy Request/Response Models (for backward compatibility)
class GenerateResponse(BaseModel):
    """Response from dialogue generation (legacy format)."""
    dialogue: str
    adapter: str
    metadata: dict


@app.get("/health")
async def health_check():
    """Health check endpoint with model_info for E2E tests."""
    local_available = (local_llm_client and await local_llm_client.is_available()) or \
                      (openai_llm_client and await openai_llm_client.is_available())
    return {
        "status": "healthy",
        "service": "scenespeak-agent",
        "model_available": bool(settings.glm_api_key or local_available),
        "local_llm_available": local_available,
        "openai_llm_available": bool(openai_llm_client and await openai_llm_client.is_available()) if openai_llm_client else False,
        "glm_api_available": bool(settings.glm_api_key),
        "model_info": {
            "name": settings.local_llm_model if local_available else "glm-4.7",
            "loaded": bool(settings.glm_api_key or local_available),
            "version": "1.0.0",
            "type": getattr(settings, 'local_llm_type', 'ollama')
        }
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    local_available = (local_llm_client and await local_llm_client.is_available()) or \
                      (openai_llm_client and await openai_llm_client.is_available())
    model_available = bool(settings.glm_api_key or local_available)
    return {
        "status": "ready",
        "service": "scenespeak-agent",
        "model_available": model_available,
        "local_llm_available": local_available,
        "openai_llm_available": bool(openai_llm_client and await openai_llm_client.is_available()) if openai_llm_client else False,
        "glm_api_available": bool(settings.glm_api_key)
    }


@app.get("/health/local-llm")
async def local_llm_health():
    """Detailed health check for local LLM."""
    if not local_llm_client:
        return {
            "status": "not_configured",
            "message": "Local LLM client not initialized"
        }

    return await local_llm_client.health_check()


@app.get("/health/model_info")
async def health_with_model_info():
    """Health check with model information for E2E tests."""
    local_available = local_llm_client and await local_llm_client.is_available()

    return {
        "status": "healthy",
        "service": "scenespeak-agent",
        "model_info": {
            "name": "glm-4.7",
            "loaded": bool(settings.glm_api_key or local_available),
            "version": "1.0.0",
            "local_llm_available": local_available
        }
    }


@app.post("/api/generate")
async def generate_dialogue_api(request: dict):
    """
    Generate dialogue using /api/generate endpoint (E2E test compatible).

    Simplified API for dialogue generation that matches E2E test expectations.
    Supports GLM 4.7 API, Nemotron (OpenAI-compatible), and Ollama fallback.

    Args:
        request: Generation request with prompt and optional parameters

    Returns:
        Response with dialogue and metadata

    Example:
        POST /api/generate
        {
            "prompt": "The hero enters the room",
            "context": { "scene": "act1_scene1" },
            "use_fallback": true  # Force local LLM
        }
    """
    start_time = time.time()

    # Validate prompt parameter FIRST (before any processing)
    if "prompt" not in request:
        raise HTTPException(status_code=422, detail="prompt is required")

    prompt = request.get("prompt", "")
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=422, detail="prompt cannot be empty")

    # Extract parameters from request
    context = request.get("context", {})
    style = request.get("style")  # Optional style parameter
    max_tokens = request.get("max_tokens", 500)
    temperature = request.get("temperature", 0.7)
    use_fallback = request.get("use_fallback", False)  # Force local LLM
    timeout = request.get("timeout", 120)  # Optional timeout override

    try:
        # Determine which client to use
        response = None
        fallback_used = False

        # If use_fallback is True, try local LLM first (Nemotron or Ollama)
        if use_fallback:
            # Try OpenAI-compatible client (Nemotron) first
            if openai_llm_client and await openai_llm_client.is_available():
                try:
                    openai_response = await openai_llm_client.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    # Convert to DialogueResponse format
                    from local_llm import LocalLLMResponse
                    llm_resp = LocalLLMResponse(
                        text=openai_response.text,
                        tokens_used=openai_response.tokens_used,
                        model=openai_response.model,
                        duration_ms=openai_response.duration_ms
                    )
                    response = GLMDialogueResponse(
                        text=llm_resp.text,
                        tokens_used=llm_resp.tokens_used,
                        model=llm_resp.model,
                        source="nemotron",
                        duration_ms=llm_resp.duration_ms
                    )
                    fallback_used = True
                    logger.info(f"Using Nemotron (fallback) for generation")
                except Exception as e:
                    logger.warning(f"Nemotron generation failed: {e}")

            # Try Ollama if Nemotron unavailable or failed
            if response is None and local_llm_client and await local_llm_client.is_available():
                try:
                    local_response = await local_llm_client.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    response = GLMDialogueResponse(
                        text=local_response.text,
                        tokens_used=local_response.tokens_used,
                        model=local_response.model,
                        source="local",
                        duration_ms=local_response.duration_ms
                    )
                    fallback_used = True
                    logger.info(f"Using Ollama (fallback) for generation")
                except Exception as e:
                    logger.warning(f"Ollama generation failed: {e}")

        # Use GLM client (with built-in fallback) if not using forced fallback
        # or if forced fallback failed
        if response is None:
            response = await glm_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                prefer_local=use_fallback
            )
            # Check if fallback was actually used
            fallback_used = response.source in ["local", "local-fallback", "nemotron"]

        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000

        # Build metadata with expected fields
        metadata = {
            "model": response.model or "glm-4.7",
            "latency_ms": round(duration_ms, 2),
            "tokens_used": response.tokens_used,
            "adapter": response.source,
            "generation_time": duration_ms / 1000,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "fallback_used": fallback_used
        }

        # Add context to metadata if provided
        if context:
            metadata["context"] = context

        # Add style to metadata if provided
        if style:
            metadata["style"] = style

        # Record metrics
        show_id = context.get("show_id", "unknown")
        record_generation(
            show_id=show_id,
            adapter=response.source,
            tokens=response.tokens_used,
            duration=duration_ms / 1000,
            quality=0.85,
            cache_hit=False
        )

        # Return response in both legacy and new formats for compatibility
        return {
            "dialogue": response.text,
            "text": response.text,  # New format
            "metadata": metadata,
            # Direct fields for new format
            "model": metadata["model"],
            "tokens_used": metadata["tokens_used"],
            "fallback_used": fallback_used
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is (including 422 validation errors)
        raise
    except Exception as e:
        logger.error(f"API generation failed: {e}")
        duration_ms = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=str(e))


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

"""
BSL Agent - Main Application

Provides text-to-BSL-gloss translation and avatar rendering services with
OpenTelemetry tracing, Prometheus metrics, and health checks.
"""

import time
import logging
import json
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, UTC

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response, HTMLResponse, FileResponse
from opentelemetry import trace
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config import get_settings
from translator import BSLTranslator
from avatar_renderer import AvatarRenderer
from avatar_webgl import (
    AvatarWebGLRenderer,
    LipSyncEngine,
    FacialExpressionController,
    BodyPoseController,
    GestureQueueManager,
    BSLAnimationLibrary,
    AnimationWorkerPool,
    GLBCompressor,
    LRUCache,
    AnimationStreamer,
    GPUInstancer
)
from models import (
    TranslateRequest,
    TranslateResponse,
    RenderRequest,
    RenderResponse,
    HealthResponse,
    APITranslateRequest,
    APITranslateResponse,
    SignMetadata,
    APIAvatarGenerateRequest,
    APIAvatarGenerateResponse,
    APIAvatarExpressionRequest,
    APIAvatarExpressionResponse,
    APIAvatarHandshapeRequest,
    APIAvatarHandshapeResponse,
    AnimationMetadata,
    VALID_EXPRESSIONS,
    VALID_HANDSHAPES
)
from tracing import setup_telemetry, instrument_fastapi, add_span_attributes, record_error
from metrics import record_translation, record_render
import sys
import os
# Add shared module to path for health models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.models.health import ReadinessResponse, ModelInfo, HealthMetrics

logger = logging.getLogger(__name__)
settings = get_settings()

# Track startup time for enhanced health endpoints
startup_time = time.time()

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
avatar_webgl = AvatarWebGLRenderer(
    model_path=settings.avatar_model_path,
    resolution=tuple(map(int, settings.avatar_resolution.split('x'))),
    fps=settings.avatar_fps,
    enable_facial_expressions=settings.enable_facial_expressions,
    enable_body_language=settings.enable_body_language
)

# Advanced feature components
lip_sync_engine = LipSyncEngine(fps=settings.avatar_fps)
expression_controller = FacialExpressionController(fps=settings.avatar_fps)
body_pose_controller = BodyPoseController(fps=settings.avatar_fps)
gesture_queue_manager = GestureQueueManager(fps=settings.avatar_fps)
animation_library = BSLAnimationLibrary(fps=settings.avatar_fps)

# Performance optimization components
animation_worker_pool = AnimationWorkerPool(max_workers=4)
glb_compressor = GLBCompressor()
animation_cache = LRUCache(max_size=100, max_memory_mb=500)
animation_streamer = AnimationStreamer(chunk_size=4096, fps=settings.avatar_fps)
gpu_instancer = GPUInstancer(max_instances=100)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Get static files directory
STATIC_DIR = Path(__file__).parent / "static"


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

# Add validation exception handler to return standardized error responses
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.models.errors import StandardErrorResponse, ErrorCode

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standardized error response."""
    errors = exc.errors()
    # Get the first error message and return as string
    error_msg = errors[0]["msg"] if errors else "Validation error"
    # If it's a missing field error, return a helpful message
    for error in errors:
        if error["type"] == "missing":
            field = error["loc"][-1] if error["loc"] else "field"
            error_msg = f"{field} is required"
            break
        elif error["type"] == "value_error.missing":
            error_msg = "This field is required"
            break

    return JSONResponse(
        status_code=422,
        content=StandardErrorResponse(
            error=error_msg,
            code=ErrorCode.VALIDATION_ERROR,
            detail=str(exc.errors()),
            retryable=False
        ).model_dump()
    )

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)


@app.get("/health")
async def health():
    """Health check endpoint with renderer information for E2E tests."""
    return {
        "status": "healthy",
        "service": "bsl-agent",
        "translator_ready": True,
        "avatar_ready": True,
        "renderer_info": avatar_webgl.get_renderer_info(),
        "advanced_features": {
            "lip_sync": True,
            "expression_control": True,
            "body_pose_control": True,
            "gesture_queue": True
        }
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready", response_model=ReadinessResponse)
async def readiness():
    """Enhanced readiness endpoint with model and dependency info."""
    uptime = int(time.time() - startup_time)

    return ReadinessResponse(
        status="ready",
        version="1.0.0",
        uptime=uptime,
        model_info=ModelInfo(
            loaded=True,
            name="bsl-avatar-v1",
            last_loaded=datetime.now(UTC)
        ),
        metrics=None  # Will be implemented with full metrics tracking
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


@app.post("/api/translate", response_model=APITranslateResponse)
async def translate_text_api(request: APITranslateRequest) -> APITranslateResponse:
    """
    Translate English text to BSL gloss notation (E2E test compatible).

    This endpoint is designed for E2E testing and provides sign metadata
    including handshapes and locations.

    Args:
        request: Translation request with text and optional context

    Returns:
        APITranslateResponse with gloss, duration, and sign metadata

    Example:
        POST /api/translate
        {
            "text": "Hello, how are you?",
            "context": {"formal": true}
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("translate_text_api") as span:
            # Perform translation
            gloss, breakdown, duration = translator.text_to_gloss(request.text)

            # Generate sign metadata with handshapes and locations
            signs = _generate_sign_metadata(breakdown)

            # Extract context if provided
            context = request.context or {}
            formal_mode = context.get("formal", False)

            # Adjust duration for formal mode (slower signing)
            if formal_mode:
                duration *= 1.2

            # Calculate metrics
            duration_sec = time.time() - start_time

            # Add span attributes
            add_span_attributes(span, {
                "translation.text_length": len(request.text),
                "translation.word_count": len(request.text.split()),
                "translation.gloss_word_count": len(breakdown),
                "translation.formal_mode": formal_mode
            })

            logger.info(
                f"API translation completed: '{request.text}' -> '{gloss}' "
                f"({len(breakdown)} signs, {duration_sec:.3f}s)"
            )

            return APITranslateResponse(
                gloss=gloss,
                duration=duration,
                signs=signs
            )

    except Exception as e:
        logger.error(f"API translation failed: {e}")

        # Record error
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "api_translation",
            "error.text_length": len(request.text)
        })

        raise HTTPException(status_code=500, detail=str(e))


def _generate_sign_metadata(breakdown: list[str]) -> list[SignMetadata]:
    """
    Generate sign metadata including handshapes and locations.

    Args:
        breakdown: List of BSL gloss words

    Returns:
        List of SignMetadata objects with handshape and location info
    """
    # Common handshapes for BSL
    handshapes = {
        "HELLO": "flat_hand_wave",
        "GOOD": "flat_hand",
        "MORNING": "flat_hand_chest",
        "PLEASE": "flat_hand_circular",
        "THANK": "flat_hand_chest",
        "YOU": "pointing_finger",
        "HOW": "flat_hand",
        "WHAT": "flat_hand",
        "WHERE": "index_finger",
        "WHEN": "flat_hand",
        "WHY": "flat_hand",
        "WHO": "index_finger",
        "WHICH": "index_finger",
        "THIS": "index_finger",
        "THAT": "index_finger",
        "HERE": "flat_hand",
        "THERE": "pointing_finger",
        "YES": "fist_nod",
        "NO": "flat_hand_wave",
        "UNDERSTAND": "flat_hand_head",
        "LOOK": "v_hand_eyes",
        "LISTEN": "cupped_hand_ear",
        "WELCOME": "flat_hand_sweep",
        "GOODBYE": "flat_hand_wave",
        "NAME": "index_finger_chest",
        "MY": "flat_hand_chest",
        "YOUR": "pointing_finger",
        "STOP": "flat_hand_palm",
        "WAIT": "flat_hand_up",
    }

    # Common locations for BSL
    locations = {
        "HELLO": "forehead",
        "GOOD": "chest",
        "MORNING": "chest",
        "PLEASE": "chest_circular",
        "THANK": "chest",
        "YOU": "forward",
        "HOW": "chest",
        "WHAT": "chest",
        "WHERE": "side",
        "WHEN": "chest",
        "WHY": "chest",
        "WHO": "side",
        "WHICH": "side",
        "THIS": "forward",
        "THAT": "forward",
        "HERE": "down",
        "THERE": "forward_point",
        "YES": "head_nod",
        "NO": "head_shake",
        "UNDERSTAND": "head",
        "LOOK": "eyes",
        "LISTEN": "ear",
        "WELCOME": "outward_sweep",
        "GOODBYE": "outward",
        "NAME": "chest",
        "MY": "chest",
        "YOUR": "forward",
        "STOP": "palm_out",
        "WAIT": "palm_up",
    }

    signs = []

    for gloss_word in breakdown:
        # Get handshape and location, with defaults
        handshape = handshapes.get(gloss_word, "flat_hand")
        location = locations.get(gloss_word, "neutral_space")

        # Handle finger-spelling
        if gloss_word.startswith("FS-"):
            handshape = "finger_spelling"
            location = "neutral_space"

        signs.append(SignMetadata(
            gloss=gloss_word,
            handshape=handshape,
            location=location
        ))

    return signs


# ============================================================================
# E2E Avatar Endpoints
# ============================================================================

@app.post("/api/avatar/generate", response_model=APIAvatarGenerateResponse)
async def api_avatar_generate(request: APIAvatarGenerateRequest) -> APIAvatarGenerateResponse:
    """
    Generate avatar animation data for text (E2E test compatible).

    Args:
        request: Avatar generation request with text and optional expression

    Returns:
        APIAvatarGenerateResponse with animation data and metadata

    Example:
        POST /api/avatar/generate
        {
            "text": "Welcome to the show",
            "expression": "happy"  // optional
        }
    """
    start_time = time.time()

    try:
        # Translate text to gloss
        gloss, breakdown, duration = translator.text_to_gloss(request.text)

        # Generate animation frames using WebGL renderer
        animation_data = avatar_webgl.generate_animation(
            gloss=breakdown,
            expression=request.expression or "neutral"
        )

        # Create metadata
        processing_time = time.time() - start_time
        metadata = AnimationMetadata(
            duration_ms=processing_time * 1000,
            fps=settings.avatar_fps
        )

        # Record render metric
        # Note: record_render requires show_id, gesture_count, duration - using defaults for E2E
        try:
            record_render(
                show_id="e2e_test",
                gesture_count=len(breakdown),
                duration=processing_time
            )
        except Exception as e:
            logger.warning(f"Failed to record render metrics: {e}")

        logger.info(
            f"API avatar generation completed: '{request.text}' -> {len(animation_data.get('frames', []))} frames"
        )

        return APIAvatarGenerateResponse(
            animation_data=animation_data,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"API avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/expression", response_model=APIAvatarExpressionResponse)
async def api_avatar_expression(request: APIAvatarExpressionRequest) -> APIAvatarExpressionResponse:
    """
    Apply expression to avatar (E2E test compatible).

    Args:
        request: Expression request with expression name

    Returns:
        APIAvatarExpressionResponse with expression and applied status

    Example:
        POST /api/avatar/expression
        {
            "expression": "happy"
        }
    """
    try:
        # Validate expression
        if request.expression not in VALID_EXPRESSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid expression: '{request.expression}'. Valid expressions: {VALID_EXPRESSIONS}"
            )

        # Apply expression using avatar renderer
        applied = avatar_webgl.set_expression(request.expression)

        logger.info(f"Expression '{request.expression}' applied: {applied}")

        return APIAvatarExpressionResponse(
            expression=request.expression,
            applied=applied
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Expression application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/handshape", response_model=APIAvatarHandshapeResponse)
async def api_avatar_handshape(request: APIAvatarHandshapeRequest) -> APIAvatarHandshapeResponse:
    """
    Apply handshape to avatar (E2E test compatible).

    Args:
        request: Handshape request with handshape and hand

    Returns:
        APIAvatarHandshapeResponse with handshape, hand, and applied status

    Example:
        POST /api/avatar/handshape
        {
            "handshape": "wave",
            "hand": "right"
        }
    """
    try:
        # Validate hand parameter
        if request.hand not in ("left", "right"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid hand: '{request.hand}'. Must be 'left' or 'right'"
            )

        # Validate handshape
        if request.handshape not in VALID_HANDSHAPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid handshape: '{request.handshape}'. Valid handshapes: {VALID_HANDSHAPES}"
            )

        # Apply handshape using avatar renderer
        applied = avatar_webgl.set_handshape(request.handshape, request.hand)

        logger.info(f"Handshape '{request.handshape}' applied to {request.hand} hand: {applied}")

        return APIAvatarHandshapeResponse(
            handshape=request.handshape,
            hand=request.hand,
            applied=applied
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Handshape application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Internal API Endpoints
# ============================================================================

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


@app.get("/avatar", response_class=HTMLResponse)
async def get_avatar_viewer():
    """
    Serve the 3D avatar viewer HTML page.

    Returns:
        HTML page with Three.js-based avatar viewer
    """
    avatar_html_path = STATIC_DIR / "avatar.html"
    if avatar_html_path.exists():
        return FileResponse(avatar_html_path)
    return HTMLResponse("<h1>Avatar viewer not found</h1>", status_code=404)


@app.get("/static/{file_path:path}")
async def serve_static_files(file_path: str):
    """
    Serve static files for the avatar viewer.

    Args:
        file_path: Path to the static file

    Returns:
        File response
    """
    file_path = STATIC_DIR / file_path
    if file_path.exists():
        return FileResponse(file_path)
    return Response(content="File not found", status_code=404)


@app.post("/api/avatar/generate")
async def generate_avatar_animation(request: RenderRequest) -> Dict[str, Any]:
    """
    Generate NMM animation for BSL gloss.

    Creates WebGL/Three.js compatible animation data for the 3D avatar.

    Args:
        request: Render request with gloss and session info

    Returns:
        NMM animation data for client-side rendering

    Example:
        POST /api/avatar/generate
        {
            "gloss": "HELLO HOW YOU",
            "session_id": "user-123",
            "include_nmm": true
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("generate_avatar_animation") as span:
            # Determine NMM markers
            nmm_markers = None if request.include_nmm else []

            # Generate NMM animation
            animation_data = avatar_webgl.render_gloss_to_nmm(
                gloss=request.gloss,
                non_manual_markers=nmm_markers
            )

            # Calculate metrics
            duration_sec = time.time() - start_time

            # Record metrics
            session_id = request.session_id or "unknown"
            record_render(
                show_id="unknown",
                gesture_count=len(request.gloss.split()),
                duration=duration_sec,
                session_id=session_id
            )

            # Add span attributes
            add_span_attributes(span, {
                "avatar.gloss_word_count": len(request.gloss.split()),
                "avatar.animation_duration": animation_data["metadata"]["duration"],
                "avatar.session_id": session_id,
                "avatar.format": "nmm-animation-v1"
            })

            logger.info(
                f"NMM animation generated: gloss='{request.gloss}', "
                f"duration={duration_sec:.3f}s, session={session_id}"
            )

            return {
                "success": True,
                "animation_data": animation_data,
                "session_id": request.session_id,
                "message": f"Successfully generated animation for {len(request.gloss.split())} signs"
            }

    except Exception as e:
        logger.error(f"Avatar animation generation failed: {e}")

        # Record error
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "avatar_animation",
            "error.gloss_length": len(request.gloss)
        })

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avatar/info")
async def get_avatar_info() -> Dict[str, Any]:
    """
    Get avatar renderer information.

    Returns:
        Avatar renderer configuration and status
    """
    return avatar_webgl.get_renderer_info()


@app.post("/api/avatar/expression")
async def set_avatar_expression(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set facial expression for the avatar.

    Args:
        data: Expression data with 'expression' and optional 'intensity'

    Returns:
        Expression morph target values

    Example:
        POST /api/avatar/expression
        {
            "expression": "happy",
            "intensity": 0.8
        }
    """
    try:
        expression = data.get("expression", "neutral")
        intensity = data.get("intensity", 1.0)

        result = avatar_webgl.set_expression(expression, intensity)

        # Broadcast to all connected WebSocket clients
        await manager.broadcast({
            "type": "expression",
            "data": result
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/avatar/handshape")
async def set_avatar_handshape(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set hand shape for BSL signing.

    Args:
        data: Handshape data with 'hand', 'handshape', and optional 'intensity'

    Returns:
        Hand configuration

    Example:
        POST /api/avatar/handshape
        {
            "hand": "right",
            "handshape": "fist",
            "intensity": 1.0
        }
    """
    try:
        hand = data.get("hand", "right")
        handshape = data.get("handshape", "fist")
        intensity = data.get("intensity", 1.0)

        result = avatar_webgl.set_handshape(hand, handshape, intensity)

        # Broadcast to all connected WebSocket clients
        await manager.broadcast({
            "type": "handshape",
            "data": result
        })

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.websocket("/ws/avatar")
async def avatar_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time avatar animation updates.

    Clients can connect to receive real-time animation updates,
    expression changes, and other avatar state changes.

    Example:
        const ws = new WebSocket('ws://localhost:8003/ws/avatar');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'animation') {
                // Update avatar animation
            }
        };
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "play_animation":
                # Play animation
                animation_name = data.get("animation")
                if animation_name:
                    result = avatar_webgl.play_animation(animation_name)
                    await websocket.send_json({
                        "type": "animation_started",
                        "data": result
                    })

            elif message_type == "set_expression":
                # Set expression
                expression = data.get("expression", "neutral")
                intensity = data.get("intensity", 1.0)
                try:
                    result = avatar_webgl.set_expression(expression, intensity)
                    await manager.broadcast({
                        "type": "expression",
                        "data": result
                    })
                except ValueError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message_type == "set_handshape":
                # Set handshape
                hand = data.get("hand", "right")
                handshape = data.get("handshape", "fist")
                intensity = data.get("intensity", 1.0)
                try:
                    result = avatar_webgl.set_handshape(hand, handshape, intensity)
                    await manager.broadcast({
                        "type": "handshape",
                        "data": result
                    })
                except ValueError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# ADVANCED FEATURES ENDPOINTS
# ============================================================================

@app.post("/api/avatar/lipsync")
async def generate_lip_sync(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate lip-sync animation for text or audio.

    Advanced lip-sync engine with coarticulation support for
    smooth mouth transitions during speech.

    Args:
        text: Text to generate lip-sync for
        duration: Duration in seconds
        fps: Optional FPS (defaults to avatar FPS)

    Returns:
        Lip-sync animation data with viseme sequence
    """
    try:
        text = request.get("text", "")
        duration = float(request.get("duration", len(text) * 0.1))
        fps = request.get("fps", settings.avatar_fps)

        if not text:
            raise HTTPException(status_code=422, detail="text is required")

        # Generate lip-sync keyframes
        keyframes = lip_sync_engine.generate_lip_sync_keyframes(text, duration, fps)

        # Convert to animation format
        animation_data = {
            "format": "nmm-animation-v1",
            "type": "lipsync",
            "fps": fps,
            "duration": duration,
            "keyframes": [kf.to_dict() for kf in keyframes],
            "metadata": {
                "text": text,
                "viseme_count": len(keyframes),
                "generated_at": datetime.now().isoformat()
            }
        }

        return {
            "success": True,
            "animation_data": animation_data,
            "metadata": {
                "duration_ms": duration * 1000,
                "fps": fps
            }
        }

    except Exception as e:
        logger.error(f"Lip-sync generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/expression/blend")
async def blend_expressions(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Blend multiple facial expressions together.

    Supports layered expressions for upper face, lower face, or full face.

    Args:
        expressions: List of (expression_name, layer, weight) tuples
            Example: [["happy", "lower_face", 0.7], ["surprised", "upper_face", 0.3]]

    Returns:
        Blended morph target values
    """
    try:
        expressions_data = request.get("expressions", [])

        if not expressions_data:
            raise HTTPException(status_code=422, detail="expressions is required")

        # Convert to tuples
        expressions = [
            (expr["expression"], expr.get("layer", "full_face"), expr.get("weight", 1.0))
            for expr in expressions_data
        ]

        # Blend expressions
        result = expression_controller.blend_expressions(expressions)

        return {
            "success": True,
            "morph_targets": result["morph_targets"],
            "layers_applied": result["expressions"]
        }

    except Exception as e:
        logger.error(f"Expression blend failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/expression/transition")
async def expression_transition(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate keyframes for smooth expression transition.

    Args:
        from_expression: Starting expression name
        to_expression: Target expression name
        duration: Transition duration in seconds

    Returns:
        Transition keyframes for smooth animation
    """
    try:
        from_expr = request.get("from_expression", "neutral")
        to_expr = request.get("to_expression", "neutral")
        duration = float(request.get("duration", 0.3))
        fps = request.get("fps", settings.avatar_fps)

        if from_expr not in expression_controller.get_available_expressions():
            raise HTTPException(
                status_code=422,
                detail=f"Unknown from_expression: {from_expr}"
            )

        if to_expr not in expression_controller.get_available_expressions():
            raise HTTPException(
                status_code=422,
                detail=f"Unknown to_expression: {to_expr}"
            )

        # Generate transition keyframes
        keyframes = expression_controller.generate_transition_keyframes(
            from_expr, to_expr, duration, fps
        )

        return {
            "success": True,
            "from_expression": from_expr,
            "to_expression": to_expr,
            "duration": duration,
            "keyframes": [kf.to_dict() for kf in keyframes],
            "keyframe_count": len(keyframes)
        }

    except Exception as e:
        logger.error(f"Expression transition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/pose")
async def set_avatar_pose(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set predefined body pose for avatar.

    Args:
        pose: Pose name (neutral, signing_space, one_handed_sign, two_handed_sign)
        duration: Optional transition duration

    Returns:
        Pose configuration and transition keyframes if duration provided
    """
    try:
        pose_name = request.get("pose", "neutral")
        duration = request.get("duration")

        # Set pose
        result = body_pose_controller.set_pose(pose_name)

        # Generate transition if duration provided
        if duration is not None:
            current_pose = body_pose_controller._current_pose or "neutral"
            duration = float(duration)

            keyframes = body_pose_controller.generate_pose_keyframes(
                current_pose, pose_name, duration
            )

            result["transition_keyframes"] = [kf.to_dict() for kf in keyframes]

        return result

    except Exception as e:
        logger.error(f"Set pose failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/joint")
async def set_joint_transform(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set transform for a specific joint.

    Args:
        joint: Joint name (e.g., "head", "left_hand", "right_arm")
        rotation: Optional [x, y, z] rotation in degrees
        position: Optional [x, y, z] position

    Returns:
        Updated joint configuration
    """
    try:
        joint = request.get("joint")
        rotation = request.get("rotation")
        position = request.get("position")

        if not joint:
            raise HTTPException(status_code=422, detail="joint is required")

        result = body_pose_controller.set_joint_transform(joint, rotation, position)
        return result

    except Exception as e:
        logger.error(f"Set joint transform failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/avatar/queue")
async def enqueue_gesture(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a gesture to the playback queue.

    Args:
        gesture_id: Unique gesture identifier
        animation: Animation data (NMM format)
        priority: Priority level (critical, high, normal, low, idle)
        blend_mode: Blend mode (smooth, cut, crossfade)
        interruptible: Whether gesture can be interrupted

    Returns:
        Queue status
    """
    try:
        gesture_id = request.get("gesture_id")
        animation_data = request.get("animation")
        priority = request.get("priority", "normal")
        blend_mode = request.get("blend_mode", "smooth")
        interruptible = request.get("interruptible", True)

        if not gesture_id or not animation_data:
            raise HTTPException(status_code=422, detail="gesture_id and animation are required")

        # Create NMM animation
        animation = avatar_webgl.NMMAnimation.from_dict(animation_data)

        # Enqueue
        result = gesture_queue_manager.enqueue(
            gesture_id, animation, priority, blend_mode, interruptible
        )

        return result

    except Exception as e:
        logger.error(f"Enqueue gesture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avatar/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """Get current gesture queue status."""
    return gesture_queue_manager.get_queue_status()


@app.post("/api/avatar/queue/interrupt")
async def interrupt_current_gesture(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interrupt current gesture with a new one.

    Args:
        gesture_id: New gesture to interrupt with

    Returns:
        Interrupt status
    """
    try:
        gesture_id = request.get("gesture_id")
        if not gesture_id:
            raise HTTPException(status_code=422, detail="gesture_id is required")

        success = gesture_queue_manager.interrupt_current(gesture_id)

        return {
            "success": success,
            "gesture_id": gesture_id,
            "message": "Gesture interrupted" if success else "Interrupt failed"
        }

    except Exception as e:
        logger.error(f"Interrupt gesture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/avatar/queue")
async def clear_gesture_queue(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clear gesture queue.

    Args:
        priority_threshold: Optional priority level to clear up to

    Returns:
        Number of gestures cleared
    """
    try:
        priority_threshold = request.get("priority_threshold")
        cleared = gesture_queue_manager.clear_queue(priority_threshold)

        return {
            "success": True,
            "cleared_count": cleared
        }

    except Exception as e:
        logger.error(f"Clear queue failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avatar/features")
async def get_advanced_features_info() -> Dict[str, Any]:
    """
    Get information about available advanced avatar features.

    Returns:
        Feature information and capabilities
    """
    return {
        "success": True,
        "advanced_features": {
            "lip_sync": {
                "enabled": True,
                "description": "Audio/text-driven mouth animation with coarticulation",
                "visemes": len(lip_sync_engine.VISEMES),
                "coarticulation": True
            },
            "facial_expressions": {
                "enabled": True,
                "description": "Advanced expression blending with transitions",
                "expressions": expression_controller.get_available_expressions(),
                "layers": expression_controller.get_expression_layers()
            },
            "body_poses": {
                "enabled": True,
                "description": "Predefined poses with IK support",
                "poses": body_pose_controller.get_available_poses(),
                "joint_hierarchy": list(body_pose_controller.JOINT_HIERARCHY.keys())
            },
            "gesture_queue": {
                "enabled": True,
                "description": "Priority queue with blending and interruption",
                "max_queue_size": gesture_queue_manager._max_queue_size,
                "blend_modes": ["smooth", "cut", "crossfade"],
                "priorities": list(gesture_queue_manager.PRIORITY.keys())
            }
        },
        "version": "1.0.0"
    }


# ============================================================================
# BSL Animation Library Endpoints
# ============================================================================

@app.get("/api/avatar/library")
async def get_animation_library() -> Dict[str, Any]:
    """
    Get the complete BSL animation library catalog.

    Returns:
        Animation library with categories and counts
    """
    categories = animation_library.get_categories()

    return {
        "success": True,
        "library": {
            "total_animations": len(animation_library._animations),
            "categories": categories,
            "available_categories": ["phrase", "letter", "number", "emotion"]
        },
        "version": "1.0.0"
    }


@app.get("/api/avatar/library/{category}")
async def get_animations_by_category(category: str) -> Dict[str, Any]:
    """
    Get all animations in a specific category.

    Args:
        category: Category name ('phrase', 'letter', 'number', 'emotion')

    Returns:
        List of animation IDs in the category
    """
    animations = animation_library.list_animations(category=category)

    if not animations:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found. Available: phrase, letter, number, emotion"
        )

    return {
        "success": True,
        "category": category,
        "count": len(animations),
        "animations": animations
    }


@app.get("/api/avatar/library/{category}/{item}")
async def get_animation(category: str, item: str) -> Dict[str, Any]:
    """
    Get a specific animation from the library.

    Args:
        category: Category name ('phrase', 'letter', 'number', 'emotion')
        item: Item name (e.g., 'hello', 'A', '0', 'happy')

    Returns:
        Animation data with NMM keyframes
    """
    animation_id = f"{category}_{item}"
    animation = animation_library.get_animation(animation_id)

    if not animation:
        raise HTTPException(
            status_code=404,
            detail=f"Animation '{animation_id}' not found"
        )

    return {
        "success": True,
        "animation": {
            "id": animation_id,
            "name": animation.name,
            "duration": animation.duration,
            "fps": animation.fps,
            "loop": animation.loop,
            "keyframe_count": len(animation.keyframes),
            "keyframes": [kf.to_dict() for kf in animation.keyframes]
        }
    }


@app.post("/api/avatar/library/{category}/{item}/play")
async def play_library_animation(
    category: str,
    item: str,
    blend: float = 0.3
) -> Dict[str, Any]:
    """
    Play an animation from the library on the avatar.

    Args:
        category: Category name ('phrase', 'letter', 'number', 'emotion')
        item: Item name (e.g., 'hello', 'A', '0', 'happy')
        blend: Blend duration in seconds for smooth transition

    Returns:
        Animation playback status
    """
    animation_id = f"{category}_{item}"
    animation = animation_library.get_animation(animation_id)

    if not animation:
        raise HTTPException(
            status_code=404,
            detail=f"Animation '{animation_id}' not found"
        )

    # Load and play the animation
    avatar_renderer.load_animation(animation)
    avatar_renderer.play_animation(animation.name, loop=animation.loop)

    return {
        "success": True,
        "message": f"Playing animation '{animation_id}'",
        "animation": {
            "id": animation_id,
            "name": animation.name,
            "duration": animation.duration,
            "blend_duration": blend
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/avatar/library/search")
async def search_animations(q: str = "") -> Dict[str, Any]:
    """
    Search animations by name or description.

    Args:
        q: Search query string

    Returns:
        Matching animations
    """
    if not q or len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters"
        )

    q_lower = q.lower()
    results = []

    for animation_id, animation in animation_library._animations.items():
        # Search in animation ID and name
        if q_lower in animation_id.lower() or q_lower in animation.name.lower():
            results.append({
                "id": animation_id,
                "name": animation.name,
                "duration": animation.duration,
                "category": animation_id.split("_")[0]
            })

    return {
        "success": True,
        "query": q,
        "count": len(results),
        "results": results[:20]  # Limit to 20 results
    }


# ============================================================================
# Performance Optimization Endpoints
# ============================================================================

@app.get("/api/avatar/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get animation cache statistics.

    Returns:
        Cache statistics including hit rate, memory usage, etc.
    """
    stats = animation_cache.get_stats()

    return {
        "success": True,
        "cache": stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/avatar/cache/clear")
async def clear_cache(category: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear animation cache.

    Args:
        category: Optional category to clear (phrases, letters, numbers, emotions)

    Returns:
        Cache clear status
    """
    if category:
        # Clear specific category
        prefix = f"phrase_{category}" if category in ['hello', 'goodbye', 'please', 'thank_you'] else f"{category}_"
        cleared = 0

        # Get all keys to iterate
        all_keys = list(animation_cache._cache.keys())
        for key in all_keys:
            if key.startswith(prefix):
                animation_cache.invalidate(key)
                cleared += 1

        return {
            "success": True,
            "cleared": cleared,
            "category": category,
            "message": f"Cleared {cleared} cached {category} animations"
        }
    else:
        # Clear all cache
        size_before = len(animation_cache._cache)
        animation_cache.clear()

        return {
            "success": True,
            "cleared": size_before,
            "message": f"Cleared all {size_before} cached animations"
        }


@app.post("/api/avatar/stream/start")
async def start_animation_stream(
    category: str,
    item: str
) -> Dict[str, Any]:
    """
    Start streaming an animation.

    Args:
        category: Animation category (phrase, letter, number, emotion)
        item: Animation item name

    Returns:
        Stream information with stream ID
    """
    animation_id = f"{category}_{item}"
    animation = animation_library.get_animation(animation_id)

    if not animation:
        raise HTTPException(
            status_code=404,
            detail=f"Animation '{animation_id}' not found"
        )

    stream_id = animation_streamer.start_stream(animation)

    return {
        "success": True,
        "stream_id": stream_id,
        "animation": {
            "id": animation_id,
            "name": animation.name,
            "duration": animation.duration
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/avatar/stream/{stream_id}/chunk")
async def get_stream_chunk(stream_id: str) -> Dict[str, Any]:
    """
    Get the next chunk of a streaming animation.

    Args:
        stream_id: Stream ID

    Returns:
        Chunk data with keyframes
    """
    chunk = animation_streamer.get_next_chunk(stream_id)

    if not chunk:
        raise HTTPException(
            status_code=404,
            detail=f"Stream '{stream_id}' not found or complete"
        )

    return {
        "success": True,
        "chunk": chunk,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/avatar/stream/{stream_id}/progress")
async def get_stream_progress(stream_id: str) -> Dict[str, Any]:
    """
    Get streaming animation progress.

    Args:
        stream_id: Stream ID

    Returns:
        Progress information
    """
    progress = animation_streamer.get_stream_progress(stream_id)

    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"Stream '{stream_id}' not found"
        )

    return {
        "success": True,
        "progress": progress,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.delete("/api/avatar/stream/{stream_id}")
async def cancel_stream(stream_id: str) -> Dict[str, Any]:
    """
    Cancel an active animation stream.

    Args:
        stream_id: Stream ID

    Returns:
        Cancellation status
    """
    cancelled = animation_streamer.cancel_stream(stream_id)

    if not cancelled:
        raise HTTPException(
            status_code=404,
            detail=f"Stream '{stream_id}' not found"
        )

    return {
        "success": True,
        "stream_id": stream_id,
        "message": "Stream cancelled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/avatar/performance")
async def get_performance_stats() -> Dict[str, Any]:
    """
    Get overall performance statistics.

    Returns:
        Performance metrics for all optimization systems
    """
    return {
        "success": True,
        "performance": {
            "cache": animation_cache.get_stats(),
            "worker_pool": {
                "max_workers": animation_worker_pool.max_workers,
                "active_tasks": len(animation_worker_pool._task_queue),
                "pending_results": len(animation_worker_pool._results)
            },
            "gpu_instancer": gpu_instancer.get_stats(),
            "active_streams": len(animation_streamer._active_streams)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


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

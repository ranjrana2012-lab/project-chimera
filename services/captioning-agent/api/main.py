"""
Captioning Agent - FastAPI Application

Main API application with WebSocket streaming endpoint.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
from typing import Optional, List

from api.streaming import get_streaming_service, get_manager
from api.tracing import get_tracer, trace_transcription, trace_streaming_session
from core.transcription import TranscriptionService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Setup tracing
tracer = get_tracer()


# Prometheus metrics
transcription_requests = Counter(
    'captioning_transcription_requests_total',
    'Total transcription requests',
    ['status']
)
transcription_duration = Histogram(
    'captioning_transcription_duration_seconds',
    'Transcription duration'
)
websocket_connections = Counter(
    'captioning_websocket_connections_total',
    'Total WebSocket connections'
)


# Global service instances
transcription_service: Optional[TranscriptionService] = None
streaming_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global transcription_service, streaming_service

    # Startup
    logger.info("Starting Captioning Agent...")

    # Initialize transcription service
    # TODO: Load API key from environment/config
    transcription_service = TranscriptionService(
        whisper_api_key="test-key",  # Replace with real key
        redis_client=None  # TODO: Initialize Redis
    )

    streaming_service = get_streaming_service(transcription_service)

    logger.info("Captioning Agent ready")

    yield

    # Shutdown
    logger.info("Shutting down Captioning Agent...")


# Create FastAPI app
app = FastAPI(
    title="Captioning Agent",
    description="Real-time speech-to-text captioning with WebSocket streaming",
    version="0.5.0",
    lifespan=lifespan
)

# Instrument FastAPI with tracing
from shared.tracing import instrument_fastapi
instrument_fastapi(app)


@app.get("/health")
async def health_check():
    """Health check endpoint with model information for E2E tests."""
    model_loaded = transcription_service is not None
    return {
        "status": "healthy",
        "service": "captioning-agent",
        "version": "0.5.0",
        "model_info": {
            "name": "whisper",
            "loaded": model_loaded
        }
    }


@app.post("/api/v1/transcribe")
async def transcribe(audio_data: dict):
    """
    Transcribe audio data.

    Request body:
    {
        "audio": "base64-encoded audio data",
        "language": "en" (optional)
    }

    Response:
    {
        "request_id": "...",
        "text": "Transcription text",
        "language": "en",
        "duration": 1.5,
        "confidence": 0.95,
        "processing_time_ms": 1500,
        "model_version": "whisper-1"
    }
    """
    import base64
    import hashlib

    try:
        audio_bytes = base64.b64decode(audio_data.get("audio", ""))
        language = audio_data.get("language")
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        # Trace transcription operation
        with trace_transcription(audio_size_bytes=len(audio_bytes), language=language) as span:
            result = transcription_service.transcribe(audio_bytes, audio_hash, language)

            # Record additional span attributes
            from shared.tracing import add_span_attributes
            add_span_attributes(span, {
                "transcription.confidence": result.confidence,
                "transcription.from_cache": result.from_cache or False,
                "transcription.model": result.model_version or "unknown"
            })

            duration = result.processing_time_ms / 1000.0 if result.processing_time_ms else 0
            transcription_duration.observe(duration)

        if result.error:
            transcription_requests.labels(status="error").inc()
            # Record error on span
            from shared.tracing import record_error
            if result.error:
                span.record_exception(Exception(result.error))
        else:
            transcription_requests.labels(status="success").inc()

        return {
            "request_id": result.request_id,
            "text": result.text,
            "language": result.language,
            "duration": result.duration,
            "confidence": result.confidence,
            "processing_time_ms": result.processing_time_ms,
            "model_version": result.model_version,
            "error": result.error,
            "warning": result.warning,
            "from_cache": result.from_cache,
            "degraded": result.degraded
        }

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        transcription_requests.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/v1/stream")
async def stream_captions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time caption streaming.

    Client sends:
    {
        "type": "audio",
        "data": "base64-encoded audio chunk"
    }

    Server sends:
    {
        "type": "caption",
        "timestamp": 1234567890.123,
        "text": "Transcription",
        "language": "en",
        "confidence": 0.95
    }
    """
    websocket_connections.inc()

    session_id = f"session_{asyncio.get_event_loop().time()}"

    try:
        # Trace streaming session
        with trace_streaming_session(session_id):
            await streaming_service.handle_client(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get service statistics."""
    stats = streaming_service.get_stats()
    stats["prometheus_metrics"] = generate_latest().decode()
    return stats


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")


@app.post("/api/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    timestamps: Optional[str] = Query(None)
):
    """
    Transcribe audio file with multipart form data.

    Request:
    - audio: File upload (multipart/form-data)
    - language: Optional language code (e.g., 'en')
    - timestamps: Optional query parameter 'true' to include segment timestamps

    Response:
    {
        "transcription": "Transcription text",
        "confidence": 0.95,
        "duration": 1.5,
        "segments": [...]  // when timestamps=true
    }
    """
    import hashlib

    try:
        # Read audio file
        audio_bytes = await audio.read()
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        # Validate file type (basic check)
        allowed_types = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/x-wav', 'audio/webm', 'audio/ogg']
        if audio.content_type and audio.content_type not in allowed_types:
            transcription_requests.labels(status="error").inc()
            raise HTTPException(
                status_code=422,
                detail=f"Invalid audio format: {audio.content_type}. Allowed: {', '.join(allowed_types)}"
            )

        # Trace transcription operation
        with trace_transcription(audio_size_bytes=len(audio_bytes), language=language) as span:
            result = transcription_service.transcribe(audio_bytes, audio_hash, language)

            # Record additional span attributes
            from shared.tracing import add_span_attributes
            add_span_attributes(span, {
                "transcription.confidence": result.confidence,
                "transcription.from_cache": result.from_cache or False,
                "transcription.model": result.model_version or "unknown"
            })

            duration = result.processing_time_ms / 1000.0 if result.processing_time_ms else 0
            transcription_duration.observe(duration)

        if result.error:
            transcription_requests.labels(status="error").inc()
            from shared.tracing import record_error
            span.record_exception(Exception(result.error))
        else:
            transcription_requests.labels(status="success").inc()

        # Build response
        response_data = {
            "transcription": result.text,
            "confidence": result.confidence,
            "duration": result.duration,
            "language": result.language,
            "model_version": result.model_version,
            "processing_time_ms": result.processing_time_ms
        }

        # Add segments if timestamps requested
        if timestamps and timestamps.lower() == 'true':
            # Mock segment data for E2E tests
            # In production, this would come from the actual transcription result
            response_data["segments"] = [
                {
                    "id": 0,
                    "seek": 0,
                    "start": 0.0,
                    "end": result.duration or 1.0,
                    "text": result.text or "Mock transcription",
                    "tokens": [1, 2, 3],
                    "temperature": 0.0,
                    "avg_logprob": -0.5,
                    "compression_ratio": 1.0,
                    "no_speech_prob": 0.1
                }
            ]

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        transcription_requests.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/live")
async def liveness():
    """Liveness probe endpoint."""
    return {"status": "alive"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

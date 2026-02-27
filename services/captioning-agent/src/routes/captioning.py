"""
Transcription routes for Captioning Agent
"""

import base64
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..models.request import TranscriptionRequest, StreamingTranscriptionRequest
from ..models.response import TranscriptionResponse, StreamingTranscriptionChunk

router = APIRouter()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(request: TranscriptionRequest):
    """
    Transcribe audio using Whisper.

    Accepts audio via URL or base64-encoded data and returns
    the transcribed text with timestamps and confidence scores.
    """
    from ....main import handler

    if not handler:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        # Get audio source
        source_type, source_value = request.get_audio_source()

        # Prepare audio data
        if source_type == "data":
            audio_data = base64.b64decode(source_value)
        else:  # url
            # In production, you'd download the URL
            # For now, return an error
            raise HTTPException(
                status_code=400,
                detail="Audio URL downloads not yet implemented. Use audio_data instead."
            )

        # Transcribe
        result = await handler.transcribe(
            audio=audio_data,
            language=request.language,
            task=request.task,
            timestamps=request.timestamps,
            vad_filter=request.vad_filter,
            word_timestamps=request.word_timestamps,
        )

        return TranscriptionResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


@router.post("/detect-language")
async def detect_language(request: TranscriptionRequest):
    """
    Detect the language of audio.

    Returns the detected language code and confidence score.
    Requires at least 1 second of audio.
    """
    from ....main import handler

    if not handler:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        # Get audio source
        source_type, source_value = request.get_audio_source()

        if source_type == "data":
            audio_data = base64.b64decode(source_value)
        else:
            raise HTTPException(
                status_code=400,
                detail="Audio URL not supported for language detection"
            )

        result = await handler.detect_language(audio_data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {e}")


@router.websocket("/stream")
async def transcribe_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transcription.

    Client should send audio chunks as binary messages.
    The server responds with transcription results as JSON.

    Protocol:
    1. Client sends JSON: StreamingTranscriptionRequest
    2. Server responds: {"status": "connected", "session_id": "..."}
    3. Client sends binary audio chunks
    4. Server responds: StreamingTranscriptionChunk JSON
    """
    from ....main import handler

    if not handler:
        await websocket.close(code=1011, reason="Service not ready")
        return

    await websocket.accept()

    session_id = None

    try:
        # Receive initial configuration
        config_json = await websocket.receive_json()
        config = StreamingTranscriptionRequest(**config_json)

        # Create streaming session
        session_info = await handler.create_stream_session(
            session_id=config.session_id,
            language=config.language,
            sample_rate=config.sample_rate,
            channels=config.channels,
        )
        session_id = session_info["session_id"]

        # Send confirmation
        await websocket.send_json({
            "status": "connected",
            "session_id": session_id,
        })

        # Process audio stream
        while True:
            # Receive audio chunk
            data = await websocket.receive()

            if "bytes" in data:
                audio_chunk = data["bytes"]

                # Process chunk
                async for result in handler.process_stream_audio(
                    session_id, audio_chunk
                ):
                    await websocket.send_json(result)

            elif "text" in data:
                # Handle text messages (e.g., "done" to end session)
                message = data["text"].lower()
                if message == "done":
                    break

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        # End session
        if session_id:
            await handler.end_stream_session(session_id)


@router.post("/invoke")
async def invoke(request: dict):
    """
    Standard skill invocation endpoint.

    Compatible with the Project Chimera skill system.
    """
    from ....main import handler

    if not handler:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        # Extract from standard skill format
        input_data = request.get("input", {})

        # Build transcription request
        transcribe_request = TranscriptionRequest(
            audio_url=input_data.get("audio_url"),
            audio_data=input_data.get("audio_data"),
            language=input_data.get("language", "en"),
            task=input_data.get("task", "transcribe"),
            timestamps=input_data.get("timestamps", True),
            vad_filter=input_data.get("vad_filter", False),
            word_timestamps=input_data.get("word_timestamps", False),
        )

        result = await transcribe(transcribe_request)

        return {
            "output": {
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
                "segments": [
                    {
                        "id": s.id,
                        "text": s.text,
                        "start": s.start,
                        "end": s.end,
                    }
                    for s in result.segments
                ],
            },
            "processing_time_ms": result.processing_time_ms,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

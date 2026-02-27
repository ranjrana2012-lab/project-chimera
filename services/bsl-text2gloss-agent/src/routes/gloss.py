"""Translation endpoints for BSL Text2Gloss Agent."""

import uuid
import time
from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from ...models.request import TranslationRequest, BatchTranslationRequest
from ...models.response import TranslationResponse, SignBreakdown

router = APIRouter()


@router.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest) -> TranslationResponse:
    """Translate English text to BSL gloss notation.

    Args:
        request: Translation request with English text

    Returns:
        Translation response with BSL gloss notation

    Raises:
        HTTPException: If translation fails
    """
    from ....main import handler

    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

    request_id = f"req-bsl-{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    try:
        # Normalize text if requested
        input_text = request.text
        if request.normalize:
            input_text = handler.translator.formatter.normalize_text(input_text)

        # Perform translation
        translation_result = await handler.translator.translate(input_text)

        # Create breakdown if requested
        breakdown = []
        if request.include_breakdown:
            breakdown = handler.translator.formatter.create_breakdown(
                translation_result["gloss"],
                input_text,
                translation_result["confidence"]
            )
            breakdown = [SignBreakdown(**b) for b in breakdown]

        # Format notations
        notations = {
            "simplified": handler.translator.formatter.format_gloss(
                translation_result["gloss"],
                handler.translator.formatter.__class__.__name__.lower()
            )
        }

        translation_time_ms = (time.time() - start_time) * 1000

        return TranslationResponse(
            request_id=request_id,
            gloss_text=translation_result["gloss"],
            source_text=request.text,
            breakdown=breakdown,
            notations=notations,
            language="bsl",
            gloss_format=request.gloss_format,
            confidence=translation_result["confidence"],
            translation_time_ms=translation_time_ms,
            model_version=translation_result.get("model_used", "unknown")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/translate/batch")
async def translate_batch(request: BatchTranslationRequest) -> dict:
    """Translate multiple English texts to BSL gloss notation.

    Args:
        request: Batch translation request

    Returns:
        Batch translation response with all translations

    Raises:
        HTTPException: If translation fails
    """
    from ....main import handler

    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

    request_id = f"req-bsl-batch-{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    translations = []
    successful = 0
    failed = 0

    for text in request.texts:
        try:
            # Create single translation request
            single_request = TranslationRequest(
                text=text,
                source_lang=request.source_lang,
                gloss_format=request.gloss_format,
                include_breakdown=request.include_breakdown,
                normalize=request.normalize
            )

            # Use the translate endpoint logic
            result = await _do_translation(single_request, handler, request_id)
            translations.append(result)
            successful += 1

        except Exception as e:
            failed += 1
            # Add error entry
            translations.append({
                "error": str(e),
                "source_text": text
            })

    total_time_ms = (time.time() - start_time) * 1000

    return {
        "request_id": request_id,
        "translations": translations,
        "total_count": len(request.texts),
        "successful_count": successful,
        "failed_count": failed,
        "total_time_ms": total_time_ms,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/invoke")
async def invoke(request: dict) -> dict:
    """OpenAI-compatible invoke endpoint for orchestrator integration.

    Args:
        request: Dictionary with 'input' containing translation parameters

    Returns:
        Dictionary with 'output' containing translation result
    """
    from ....main import handler

    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

    input_data = request.get("input", {})

    # Create translation request from input
    translate_request = TranslationRequest(
        text=input_data.get("text", ""),
        source_lang=input_data.get("source_lang", "en"),
        gloss_format=input_data.get("gloss_format", "hamnosys"),
        include_breakdown=input_data.get("include_breakdown", True),
        normalize=input_data.get("normalize", True)
    )

    result = await _do_translation(translate_request, handler)

    return {"output": result.model_dump()}


async def _do_translation(
    request: TranslationRequest,
    handler,
    request_id: str = None
) -> TranslationResponse:
    """Helper function to perform translation."""
    if request_id is None:
        request_id = f"req-bsl-{uuid.uuid4().hex[:12]}"

    start_time = time.time()

    # Normalize text if requested
    input_text = request.text
    if request.normalize:
        input_text = handler.translator.formatter.normalize_text(input_text)

    # Perform translation
    translation_result = await handler.translator.translate(input_text)

    # Create breakdown if requested
    breakdown = []
    if request.include_breakdown:
        breakdown = handler.translator.formatter.create_breakdown(
            translation_result["gloss"],
            input_text,
            translation_result["confidence"]
        )
        breakdown = [SignBreakdown(**b) for b in breakdown]

    # Format notations
    notations = {
        "simplified": handler.translator.formatter.format_gloss(
            translation_result["gloss"],
            handler.translator.formatter.__class__.__name__.lower()
        )
    }

    translation_time_ms = (time.time() - start_time) * 1000

    return TranslationResponse(
        request_id=request_id,
        gloss_text=translation_result["gloss"],
        source_text=request.text,
        breakdown=breakdown,
        notations=notations,
        language="bsl",
        gloss_format=request.gloss_format,
        confidence=translation_result["confidence"],
        translation_time_ms=translation_time_ms,
        model_version=translation_result.get("model_used", "unknown")
    )


@router.get("/formats")
async def list_formats() -> dict:
    """List available gloss notation formats.

    Returns:
        Dictionary with supported formats and descriptions
    """
    return {
        "formats": [
            {
                "name": "hamnosys",
                "description": "Hamburg Notation System - comprehensive sign language notation",
                "features": ["handshape", "location", "movement", "non_manual"]
            },
            {
                "name": "stokoe",
                "description": "Stokoe notation - original sign writing system",
                "features": ["handshape", "location", "movement"]
            },
            {
                "name": "simplified",
                "description": "Simple uppercase gloss notation",
                "features": ["basic_gloss"]
            }
        ]
    }


@router.get("/health")
async def translation_health() -> dict:
    """Health check specific to translation functionality.

    Returns:
        Health status of translation components
    """
    from ....main import handler

    model_loaded = False
    if handler and handler.translator:
        model_loaded = handler.translator._loaded

    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "service": "bsl-translation"
    }


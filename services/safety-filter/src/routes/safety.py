"""Safety check routes for Safety Filter service."""

from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any

from ..models.request import SafetyCheckRequest, SafetyBatchRequest
from ..models.response import SafetyCheckResponse, SafetyBatchResponse
from ....main import handler


router = APIRouter()


@router.post("/check", response_model=SafetyCheckResponse)
async def check_content(request: SafetyCheckRequest, http_request: Request) -> SafetyCheckResponse:
    """Check content for safety issues.

    This endpoint analyzes content for profanity, hate speech, sexual content,
    violence, harassment, self-harm, misinformation, and spam.

    Args:
        request: Safety check request with content and options
        http_request: HTTP request object

    Returns:
        Safety check response with decision, confidence, and details

    Raises:
        HTTPException: If the check fails
    """
    try:
        return await handler.check_content(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety check failed: {str(e)}"
        )


@router.post("/check/batch", response_model=SafetyBatchResponse)
async def check_batch(request: SafetyBatchRequest) -> SafetyBatchResponse:
    """Check multiple contents for safety issues.

    This endpoint analyzes multiple content items for safety issues
    and returns aggregated results.

    Args:
        request: Batch safety check request

    Returns:
        Batch safety check response with results and aggregates

    Raises:
        HTTPException: If the batch check fails
    """
    try:
        return await handler.check_batch(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch safety check failed: {str(e)}"
        )


@router.post("/filter")
async def filter_content(request: Dict[str, Any]) -> Dict[str, Any]:
    """Filter content by replacing flagged words.

    This endpoint filters profanity and other flagged content by
    replacing matched words with a filter character.

    Request body:
        content: Text content to filter
        filter_char: Character to replace with (default: "*")
        categories: Optional list of categories to filter

    Returns:
        Filtered content with original and filtered text
    """
    try:
        content = request.get("content", "")
        filter_char = request.get("filter_char", "*")
        categories = request.get("categories")

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is required"
            )

        filtered = await handler.filter_content(
            content,
            filter_char=filter_char,
            categories=categories
        )

        return {
            "original": content,
            "filtered": filtered,
            "filter_char": filter_char
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content filtering failed: {str(e)}"
        )


@router.post("/invoke")
async def invoke_skill(request: Dict[str, Any]) -> Dict[str, Any]:
    """OpenClaw skill invocation endpoint.

    This endpoint allows the Safety Filter to be invoked as an
    OpenClaw skill.

    Args:
        request: OpenClaw skill invocation request

    Returns:
        Skill response with safety check results
    """
    try:
        input_data = request.get("input", {})
        content = input_data.get("content", "")

        if not content:
            return {
                "error": "No content provided",
                "output": None
            }

        # Create safety check request
        safety_request = SafetyCheckRequest(
            content=content,
            options=input_data.get("options"),
            request_id=request.get("request_id"),
            user_id=request.get("user_id"),
            source=input_data.get("source", "openclaw")
        )

        # Perform check
        result = await handler.check_content(safety_request)

        # Return in OpenClaw format
        return {
            "output": {
                "decision": result.decision.value,
                "safe": result.safe,
                "confidence": result.confidence,
                "explanation": result.explanation
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "output": None
        }


# Alias for compatibility with existing code
filter_content_legacy = filter_content

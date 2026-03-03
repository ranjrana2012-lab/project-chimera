"""Context routes for Sentiment Agent WorldMonitor integration.

This module provides API endpoints for accessing global context
and country-specific context from the WorldMonitor sidecar service.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ..models.context import GlobalContext, CountryContext, ContextEnrichmentOptions

router = APIRouter()


@router.get("/global", response_model=GlobalContext)
async def get_global_context(
    include_threats: Optional[bool] = True,
    include_events: Optional[bool] = True,
    include_cii: Optional[bool] = True
) -> GlobalContext:
    """Get global context from WorldMonitor.

    Returns:
        GlobalContext with global geopolitical information including:
        - Global CII (Composite Instability Index)
        - Country-specific contexts
        - Active threats
        - Major global events

    Raises:
        HTTPException: If handler is not initialized or context fetch fails
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    if not handler.context_enricher:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Context enrichment not enabled"
        )

    try:
        options = ContextEnrichmentOptions(
            include_context=True,
            include_threats=include_threats,
            include_events=include_events,
            include_cii=include_cii
        )

        context = await handler.context_enricher.get_context(options)

        if not context:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to fetch context from WorldMonitor"
            )

        return context

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get global context: {str(e)}"
        )


@router.get("/country/{code}")
async def get_country_context(code: str) -> JSONResponse:
    """Get country-specific context from WorldMonitor.

    Args:
        code: ISO country code (e.g., 'US', 'GB', 'UA')

    Returns:
        CountryContext with country-specific information including:
        - Country CII score
        - Stability trend
        - Recent events
        - AI-generated news summary
        - Instability factors

    Raises:
        HTTPException: If handler is not initialized or country code is invalid
    """
    from ....main import handler

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    if not handler.context_enricher:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Context enrichment not enabled"
        )

    if not code or len(code) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid country code. Must be a 2-letter ISO code."
        )

    try:
        context = await handler.context_enricher.get_country_context(code.upper())

        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Country context not found for code: {code.upper()}"
            )

        return JSONResponse(content=context)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get country context: {str(e)}"
        )


@router.websocket("/stream")
async def context_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time context updates.

    This endpoint provides a WebSocket connection for receiving
    real-time updates when the global context changes.

    Clients will receive JSON messages with the following structure:
    {
        "type": "context_update",
        "data": {
            "global_cii": 65,
            "country_summary": {...},
            "active_threats": [...],
            "major_events": [...],
            "last_updated": "2026-03-03T10:30:00Z"
        }
    }

    Raises:
        WebSocketDisconnect: If client disconnects
    """
    from ....main import handler

    await websocket.accept()

    if not handler or not handler.context_enricher:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Create a queue for this connection
    import asyncio
    queue = asyncio.Queue()

    async def context_callback(context_data):
        """Callback to push context updates to the queue."""
        try:
            await queue.put({
                "type": "context_update",
                "data": context_data
            })
        except Exception as e:
            pass  # Queue might be closed

    # Register callback if we have a WebSocket client
    ws_client = getattr(handler.context_enricher, '_ws_client', None)
    if ws_client:
        ws_client.add_callback(context_callback)

    try:
        # Send initial context if available
        initial_context = handler.context_enricher.get_context()
        if initial_context:
            await websocket.send_json({
                "type": "context_update",
                "data": initial_context
            })

        # Keep connection alive and send updates
        while True:
            try:
                # Wait for updates with timeout
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass

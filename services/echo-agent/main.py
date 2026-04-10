"""Echo Agent Service.

Simplest agent that echoes back input text.
Tests the entire pipeline with minimal processing.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# Request/Response Models
class EchoRequest(BaseModel):
    """Request model for echo endpoint."""
    text: str
    delay_ms: int = 0
    metadata: Dict[str, Any] = None


class EchoResponse(BaseModel):
    """Response model for echo endpoint."""
    echoed_text: str
    original_text: str
    processed_at: str
    delay_ms: int
    metadata: Dict[str, Any] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    status: str
    checks: Dict[str, bool]


# FastAPI App
app = FastAPI(
    title="Echo Agent",
    description="Simplest agent that echoes back input - tests entire pipeline",
    version="1.0.0"
)


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "service": "echo-agent",
        "version": "1.0.0",
        "description": "Echo agent - echoes back input text",
        "endpoints": {
            "health": "/health",
            "readiness": "/readiness",
            "echo": "/echo"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="echo-agent",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


@app.get("/readiness", response_model=ReadinessResponse, tags=["health"])
async def readiness() -> ReadinessResponse:
    """Readiness check endpoint."""
    return ReadinessResponse(
        status="ready",
        checks={
            "api": True,
            "memory": True
        }
    )


@app.post("/echo", response_model=EchoResponse, tags=["echo"])
async def echo(request: EchoRequest) -> EchoResponse:
    """Echo back the input text.

    This is the simplest agent - it just echoes back what it receives.
    Useful for testing the entire pipeline without complex processing.
    """
    import asyncio

    # Simulate optional delay for testing async behavior
    if request.delay_ms > 0:
        await asyncio.sleep(request.delay_ms / 1000.0)

    return EchoResponse(
        echoed_text=request.text,
        original_text=request.text,
        processed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        delay_ms=request.delay_ms,
        metadata=request.metadata or {}
    )


@app.get("/echo", tags=["echo"])
async def echo_get(text: str, delay_ms: int = 0) -> EchoResponse:
    """Echo endpoint via GET request.

    Useful for quick testing without POST body.
    """
    import asyncio

    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000.0)

    return EchoResponse(
        echoed_text=text,
        original_text=text,
        processed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        delay_ms=delay_ms,
        metadata={}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)

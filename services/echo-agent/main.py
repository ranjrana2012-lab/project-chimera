"""Echo Agent Service.

Simplest agent that echoes back input text.
Tests the entire pipeline with minimal processing.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Literal, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


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


class DMXOutputRequest(BaseModel):
    """Request model for DMX hardware output."""
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        default="neutral",
        description="Sentiment value for DMX lighting control"
    )
    score: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Sentiment score between -1.0 and 1.0"
    )
    channels: Optional[Dict[str, int]] = Field(
        default=None,
        description="Optional custom DMX channel override values"
    )

    @field_validator('sentiment')
    @classmethod
    def validate_sentiment(cls, v: str) -> str:
        """Validate that sentiment is one of the allowed values."""
        if v not in ["positive", "negative", "neutral"]:
            raise ValueError(
                f"Invalid sentiment '{v}'. Must be one of: positive, negative, neutral"
            )
        return v


class DMXOutputResponse(BaseModel):
    """Response model for DMX hardware output."""
    status: str
    mode: str
    channels: Dict[str, int]
    timestamp: str
    hardware: str


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
    import os
    mode = os.environ.get("ECHO_MODE", "echo")

    # Indicate DMX/hardware mode when in dmx-sentiment mode
    service_name = "echo-agent" if mode == "echo" else "echo-hardware-bridge"

    return HealthResponse(
        status="healthy",
        service=service_name,
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


@app.post("/dmx/output", response_model=DMXOutputResponse, tags=["hardware"])
async def dmx_output(request: DMXOutputRequest) -> DMXOutputResponse:
    """
    Mock DMX hardware output based on sentiment.

    Simulates sending DMX commands to lighting hardware.
    In production, this would interface with actual DMX controllers.

    Args:
        request: DMX output request with sentiment, score, and optional channel overrides

    Returns:
        DMX channel values and confirmation

    Raises:
        HTTPException: If sentiment validation fails
    """
    try:
        # Calculate DMX values
        dmx_channels = _calculate_dmx_channels(request.sentiment, request.score)

        # Apply custom channel override if provided
        if request.channels:
            dmx_channels.update(request.channels)

        # Log DMX output using proper logging
        logger.info(
            "DMX output command",
            extra={
                "sentiment": request.sentiment,
                "score": request.score,
                "channels": dmx_channels,
                "mode": "dmx_sentiment"
            }
        )

        return DMXOutputResponse(
            status="sent",
            mode="dmx_sentiment",
            channels=dmx_channels,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            hardware="simulated"
        )

    except ValueError as e:
        # Handle Pydantic validation errors
        logger.error(f"DMX output validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"DMX output error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def _calculate_dmx_channels(sentiment: str, score: float) -> dict:
    """Calculate DMX channel values based on sentiment.

    Args:
        sentiment: positive, negative, or neutral
        score: sentiment score (-1 to 1)

    Returns:
        Dictionary with DMX channel values
    """
    # DMX channels: 1-3 are RGB, 4 is brightness, 5-10 are special effects
    dmx = {
        "1_red": 128,
        "2_green": 128,
        "3_blue": 128,
        "4_brightness": 200,
        "5_effect": 0,  # 0=none, 1=sparkle, 2=dim, 3=strobe
        "6_speed": 0,  # For effect speed
        "7_color_temp": 0,
        "8_pan": 0,
        "9_tilt": 0,
        "10_zoom": 0
    }

    if sentiment == "positive":
        # Warm colors - orange/yellow
        dmx["1_red"] = 255
        dmx["2_green"] = min(255, int(200 + score * 55))
        dmx["3_blue"] = 50
        dmx["4_brightness"] = 255
        dmx["5_effect"] = 1  # sparkle
        dmx["6_speed"] = int(abs(score) * 100)
    elif sentiment == "negative":
        # Cool colors - blue/purple
        dmx["1_red"] = 50
        dmx["2_green"] = 50
        dmx["3_blue"] = 255
        dmx["4_brightness"] = 180
        dmx["5_effect"] = 2  # dim
        dmx["6_speed"] = int(abs(score) * 50)
    else:
        # Neutral - white
        dmx["1_red"] = 200
        dmx["2_green"] = 200
        dmx["3_blue"] = 200
        dmx["4_brightness"] = 220
        dmx["5_effect"] = 0  # steady
        dmx["6_speed"] = 0

    return dmx


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", "8014"))
    mode = os.environ.get("ECHO_MODE", "echo")

    if mode == "dmx-sentiment":
        logger.info(f"DMX Hardware Bridge starting on port {port}")

    uvicorn.run(app, host="0.0.0.0", port=port)

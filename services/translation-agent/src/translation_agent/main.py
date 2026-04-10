"""Translation Agent FastAPI service."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from .config import get_settings, Settings
from .models import (
    TranslationRequest,
    TranslationResponse,
    SupportedLanguagesResponse,
    TranslationStatus,
)
from .translator import TranslationEngine

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add shared module to path
shared_path = os.path.join(os.path.dirname(__file__), "../../shared")
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Try to import shared modules (may not be available in all contexts)
try:
    from shared.tracing import setup_tracing, instrument_fastapi
    from shared.metrics import record_business_metric
    SHARED_AVAILABLE = True
except ImportError:
    logger.warning("Shared modules not available - running in standalone mode")
    SHARED_AVAILABLE = False

    # Stubs for when shared module is not available
    def setup_tracing(*args, **kwargs):
        """Stub for setup_tracing."""
        pass

    def instrument_fastapi(app):
        """Stub for instrument_fastapi."""
        pass

    def record_business_metric(*args, **kwargs):
        """Stub for record_business_metric."""
        pass

# Global engine instance
_engine: TranslationEngine | None = None


def get_engine() -> TranslationEngine:
    """Get global translation engine instance."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = TranslationEngine(settings)
    return _engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Lifespan context manager for startup/shutdown."""
    settings = get_settings()

    # Setup tracing
    setup_tracing(
        service_name=settings.service_name,
        otlp_endpoint=settings.otlp_endpoint,
    )

    # Initialize engine
    global _engine
    _engine = TranslationEngine(settings)
    logger.info(f"{settings.service_name} started on port {settings.port}")

    yield

    # Cleanup
    if _engine:
        await _engine.close()
    logger.info(f"{settings.service_name} shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Translation Agent",
    description="Multi-language translation service for Project Chimera",
    version="0.1.0",
    lifespan=lifespan,
)

# Instrument FastAPI with tracing
instrument_fastapi(app)

# Add shared middleware
if SHARED_AVAILABLE:
    try:
        from shared.middleware import (
            SecurityHeadersMiddleware,
            configure_cors,
            setup_rate_limit_error_handler,
        )

        app.add_middleware(SecurityHeadersMiddleware)
        configure_cors(app)
        setup_rate_limit_error_handler(app)
        logger.info("Shared middleware configured")
    except ImportError as e:
        logger.warning(f"Shared middleware not available: {e}")


# Request/Response models
class TranslateRequestModel(BaseModel):
    """API request model for translation."""

    text: str = Field(..., min_length=1, description="Text to translate")
    source_language: str = Field(..., min_length=2, description="Source language code")
    target_language: str = Field(..., min_length=2, description="Target language code")

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_codes(cls, v: str) -> str:
        """Validate language code format."""
        if not v or len(v) < 2:
            raise ValueError("Language code must be at least 2 characters")
        return v.lower()


class TranslateResponseModel(BaseModel):
    """API response model for translation."""

    translated_text: str
    source_language: str
    target_language: str
    status: str
    confidence: float
    cached: bool
    error: str | None = None


# Health endpoints
@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint."""
    settings = get_settings()
    engine = get_engine()
    engine_health = await engine.health_check()

    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "0.1.0",
        "engine": engine_health,
    }


@app.get("/readiness")
async def readiness() -> dict[str, Any]:
    """Readiness check endpoint."""
    engine = get_engine()
    engine_health = await engine.health_check()

    is_ready = engine_health.get("bsl_service") in ("healthy", "unreachable")

    return {
        "ready": is_ready,
        "engine": engine_health,
    }


@app.get("/liveness")
async def liveness() -> dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "alive"}


# Translation endpoints
@app.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages() -> SupportedLanguagesResponse:
    """Get list of supported languages."""
    settings = get_settings()
    return SupportedLanguagesResponse.from_list(settings.supported_languages)


@app.post("/translate", response_model=TranslateResponseModel)
async def translate(request: TranslateRequestModel) -> TranslateResponseModel:
    """Translate text between languages."""
    try:
        # Create translation request
        translation_request = TranslationRequest(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
        )

        # Perform translation
        engine = get_engine()
        response = await engine.translate(translation_request)

        # Record metric
        record_business_metric(
            metric_name="translation.request",
            value=1.0,
            tags={
                "source_lang": request.source_language,
                "target_lang": request.target_language,
                "cached": str(response.cached),
                "status": response.status.value,
            },
        )

        return TranslateResponseModel(**response.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}",
        )


@app.post("/translate/cache/clear")
async def clear_cache() -> dict[str, str]:
    """Clear translation cache."""
    engine = get_engine()
    engine.clear_cache()
    record_business_metric("translation.cache_cleared", 1.0)
    return {"status": "cache_cleared"}


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with service info."""
    settings = get_settings()
    return {
        "service": settings.service_name,
        "version": "0.1.0",
        "description": "Multi-language translation service for Project Chimera",
        "endpoints": {
            "health": "/health",
            "readiness": "/readiness",
            "languages": "/languages",
            "translate": "/translate",
        },
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


def main() -> None:
    """Run the translation agent service."""
    settings = get_settings()
    uvicorn.run(
        "translation_agent.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

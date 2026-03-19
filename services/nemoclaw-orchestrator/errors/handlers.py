# services/nemoclaw-orchestrator/errors/handlers.py
"""Global error handlers for FastAPI application"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from errors.exceptions import ChimeraError

logger = logging.getLogger(__name__)


async def chimera_error_handler(request: Request, exc: ChimeraError) -> JSONResponse:
    """
    Handle ChimeraError exceptions

    Maps error codes to appropriate HTTP status codes and returns
    structured error response.
    """
    logger.error(
        f"ChimeraError: {exc.code} - {exc.message}",
        extra={
            "error_code": exc.code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "details": {}
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    logger.warning(
        f"Validation Error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {
                "errors": exc.errors()
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions"""
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {} if not logger.isEnabledFor(logging.DEBUG) else {
                "exception_type": type(exc).__name__,
                "message": str(exc)
            }
        }
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application

    Args:
        app: FastAPI application instance
    """
    from fastapi import status

    # Register custom Chimera error handler
    app.add_exception_handler(ChimeraError, chimera_error_handler)

    # Register standard HTTP exception handler
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Register validation error handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Register generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers registered successfully")

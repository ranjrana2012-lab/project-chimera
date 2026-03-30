"""
Shared security middleware for Project Chimera services.
Provides security headers, CORS, and rate limiting.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (only in production with HTTPS)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (basic, tighten per-service)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response


def get_cors_origins() -> list[str]:
    """Get allowed CORS origins from environment."""
    cors_origins = os.getenv("CORS_ORIGINS", "")

    if cors_origins:
        return [origin.strip() for origin in cors_origins.split(",")]

    # Default for development
    return ["http://localhost:3000", "http://localhost:8000"]


def configure_cors(app) -> None:
    """Configure CORS with environment-based origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class RateLimitExceededHTTPException(Exception):
    """Custom exception for rate limit errors."""
    pass


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "error": "rate_limit_exceeded"
        }
    )


def setup_rate_limit_error_handler(app) -> None:
    """Register rate limit exception handler."""
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)


__all__ = [
    "SecurityHeadersMiddleware",
    "get_cors_origins",
    "configure_cors",
    "limiter",
    "RateLimitExceededHTTPException",
    "rate_limit_exception_handler",
    "setup_rate_limit_error_handler",
]
"""
Rate limiting utilities for Project Chimera services.
Provides configurable rate limiting with slowapi.
"""

from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimitExceededHTTPException(RateLimitExceeded):
    """Custom exception for rate limit errors with HTTP response."""
    pass


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors with proper HTTP response.

    Args:
        request: The FastAPI request object
        exc: The rate limit exception

    Returns:
        JSONResponse with 429 status code
    """
    logger.warning(f"Rate limit exceeded for {request.client.host}: {exc.detail}")

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "error": "rate_limit_exceeded",
            "retry_after": 60  # Suggest retry after 60 seconds
        }
    )


def get_rate_limit_per_minute():
    """Get rate limit per minute from environment."""
    import os
    return int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))


def get_rate_limit_per_hour():
    """Get rate limit per hour from environment."""
    import os
    return int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))


__all__ = [
    "RateLimitExceededHTTPException",
    "rate_limit_exception_handler",
    "get_rate_limit_per_minute",
    "get_rate_limit_per_hour",
]
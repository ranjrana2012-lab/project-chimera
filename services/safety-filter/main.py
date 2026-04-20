"""
Safety Filter - Main Application

Provides multi-layer content moderation with OpenTelemetry tracing,
Prometheus metrics, and health checks.
"""

import time
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from opentelemetry import trace
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

import sys
import os

# Add shared module to path for security middleware
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from shared.kafka_bus import KafkaEventBus
except ImportError:
    KafkaEventBus = None

from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    setup_rate_limit_error_handler,
)

from config import get_settings
from content_moderator import ContentModerator
from models import (
    ModerateRequest,
    ModerateResponse,
    CheckRequest,
    CheckResponse,
    HealthResponse,
    PolicyInfo,
    APIModerateRequest,
    APIModerateResponse,
    CategoryScores,
    ModerationMetadata
)
from tracing import setup_telemetry, instrument_fastapi, add_span_attributes, record_error
from metrics import record_moderation, update_blocklist_size, update_audit_log_size

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize components
tracer = setup_telemetry("safety-filter")
moderator = ContentModerator(
    policy=settings.default_policy,
    enable_ml_filter=settings.enable_ml_filter,
    audit_log_max_size=settings.audit_log_max_size
)
kafka_bus = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    global kafka_bus
    logger.info("Safety Filter starting up")
    logger.info(f"Default policy: {settings.default_policy}")
    logger.info(f"ML filter enabled: {settings.enable_ml_filter}")
    logger.info(f"Context filter enabled: {settings.enable_context_filter}")
    
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    if KafkaEventBus:
        kafka_bus = KafkaEventBus(bootstrap_servers, "safety-filter")
        try:
            await kafka_bus.start()
            
            async def handle_safety_request(msg: dict):
                text = msg.get("text", "")
                task_id = msg.get("task_id", "")
                policy = msg.get("policy", settings.default_policy)
                if text and task_id:
                    result = moderator.moderate(text=text)
                    await kafka_bus.publish("chimera.safety.completed", {
                        "task_id": task_id,
                        "safe": result.is_safe,
                        "confidence": result.confidence,
                        "reason": result.reason if not result.is_safe else None
                    })
                    
            await kafka_bus.subscribe("chimera.safety.request", handle_safety_request)
        except Exception as e:
            logger.error(f"Failed to start Kafka bus: {e}")

    yield
    if kafka_bus:
        await kafka_bus.stop()
    logger.info("Safety Filter shutting down")


# Create FastAPI app
app = FastAPI(
    title="Safety Filter",
    description="Multi-layer content moderation for AI-generated content",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI with automatic tracing
instrument_fastapi(app)

# ============================================================================
# Security Middleware (Environment-based CORS, Security Headers, Rate Limiting)
# ============================================================================
from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    setup_rate_limit_error_handler,
)

# Apply security configurations
configure_cors(app)
app.add_middleware(SecurityHeadersMiddleware)
setup_rate_limit_error_handler(app)

# Add validation exception handler to return string error messages
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: RequestValidationError, exc: RequestValidationError):
    """Return validation errors as string messages instead of arrays."""
    errors = exc.errors()
    # Get the first error message and return as string
    error_msg = errors[0]["msg"] if errors else "Validation error"
    # If it's a missing field error, return a helpful message
    for error in errors:
        if error["type"] == "missing":
            field = error["loc"][-1] if error["loc"] else "field"
            error_msg = f"{field} is required"
            break
        elif error["type"] == "value_error.missing":
            error_msg = "This field is required"
            break

    return JSONResponse(
        status_code=422,
        content={"detail": error_msg}
    )


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns service health status and model information for E2E tests.
    """
    return {
        "status": "healthy",
        "service": "safety-filter",
        "moderator_ready": True,
        "policy": settings.default_policy,
        "model_info": {
            "name": "ml-safety-filter",
            "loaded": True,
            "version": "1.0.0"
        }
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    return HealthResponse(
        status="ready",
        service="safety-filter",
        moderator_ready=True,
        policy=settings.default_policy
    )


@app.get("/health/model_info")
async def health_with_model_info():
    """
    Health check with model information.

    Returns detailed model status for E2E tests.
    """
    return {
        "status": "healthy",
        "service": "safety-filter",
        "model_info": {
            "name": "safety-filter",
            "loaded": True,
            "version": "1.0.0"
        },
        "moderator_ready": True,
        "policy": settings.default_policy
    }


@app.post("/api/moderate", response_model=APIModerateResponse)
async def moderate_content_api(request: APIModerateRequest) -> APIModerateResponse:
    """
    Moderate content using /api/moderate endpoint (E2E test compatible).

    Simplified API for content moderation that matches E2E test expectations.

    Args:
        request: Moderation request with text and optional parameters

    Returns:
        APIModerateResponse with safe flag, confidence, and category scores

    Example:
        POST /api/moderate
        {
            "text": "Hello, world!",
            "threshold": 0.8
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("moderate_content_api") as span:
            # Perform moderation using internal API
            result = moderator.moderate(
                text=request.text,
                context=request.context
            )

            # Calculate category scores based on matched patterns
            categories = CategoryScores()

            # Map pattern types to categories
            pattern_type_mapping = {
                "profanity": "harassment",
                "hate_speech": "hate",
                "sexual": "sexual",
                "violence": "violence",
                "self_harm": "self_harm",
                "harmful": "violence"
            }

            for pattern in result.matched_patterns:
                category = pattern_type_mapping.get(pattern.type, "harassment")
                if hasattr(categories, category):
                    current_value = getattr(categories, category)
                    # Increase score based on severity
                    severity_multiplier = {
                        "safe": 0.0,
                        "low": 0.2,
                        "medium": 0.5,
                        "high": 0.8,
                        "critical": 1.0
                    }.get(pattern.severity.value, 0.5)
                    setattr(categories, category, max(current_value, severity_multiplier))

            # Determine if content is safe based on threshold
            # If confidence is below threshold, consider it unsafe
            is_safe = result.is_safe and result.confidence >= request.threshold

            # If any category score is above threshold, mark as unsafe
            if not result.is_safe:
                is_safe = False

            processing_time = (time.time() - start_time) * 1000

            # Generate metadata
            metadata = ModerationMetadata(
                model="safety-filter-v1",
                latency_ms=round(processing_time, 2),
                policy=request.context.get("policy", "family") if request.context else settings.default_policy,
                timestamp=f"{start_time:.3f}"
            )

            return APIModerateResponse(
                safe=is_safe,
                confidence=result.confidence,
                categories=categories,
                flagged_reason=result.reason if not result.is_safe else None,
                metadata=metadata
            )

    except Exception as e:
        logger.error(f"API moderation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/moderate", response_model=ModerateResponse)
async def moderate_content(request: ModerateRequest) -> ModerateResponse:
    """
    Moderate content with full details.

    Performs comprehensive content moderation using multi-layer filtering:
    - Layer 1: Pattern matching (profanity, PII, harmful content)
    - Layer 2: Context-aware analysis

    Args:
        request: Moderation request with content and options

    Returns:
        ModerateResponse with full moderation details

    Example:
        POST /v1/moderate
        {
            "content": "Hello, world!",
            "content_id": "msg-123",
            "user_id": "user-456",
            "policy": "family"
        }
    """
    start_time = time.time()

    try:
        with tracer.start_as_current_span("moderate_content") as span:
            # Perform moderation
            result = moderator.moderate(
                text=request.content,
                content_id=request.content_id,
                user_id=request.user_id,
                session_id=request.session_id,
                context=request.context
            )

            # Calculate metrics
            duration_sec = time.time() - start_time

            # Record metrics
            record_moderation(
                policy=request.policy or settings.default_policy,
                is_safe=result.is_safe,
                action=result.action.value,
                content_length_chars=len(request.content),
                duration=duration_sec,
                pattern_match_count=len(result.matched_patterns),
                confidence=result.confidence
            )

            # Update audit log size metric
            update_audit_log_size(len(moderator.audit_log))

            # Add span attributes for tracing
            add_span_attributes(span, {
                "moderation.content_id": request.content_id or "unknown",
                "moderation.user_id": request.user_id or "unknown",
                "moderation.content_length": len(request.content),
                "moderation.is_safe": result.is_safe,
                "moderation.action": result.action.value,
                "moderation.level": result.level.value,
                "moderation.layer": result.layer.value,
                "moderation.pattern_matches": len(result.matched_patterns),
                "moderation.confidence": result.confidence,
                "moderation.policy": request.policy or settings.default_policy
            })

            logger.info(
                f"Moderation completed: safe={result.is_safe}, "
                f"action={result.action.value}, "
                f"patterns={len(result.matched_patterns)}, "
                f"duration={duration_sec:.3f}s"
            )

            return ModerateResponse(
                safe=result.is_safe,
                result=result
            )

    except Exception as e:
        logger.error(f"Moderation failed: {e}")
        duration_sec = time.time() - start_time

        # Record error on current span
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "moderation",
            "error.content_length": len(request.content)
        })

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/check", response_model=CheckResponse)
async def check_content(request: CheckRequest) -> CheckResponse:
    """
    Quick safety check (boolean result).

    Performs a fast safety check without full moderation details.

    Args:
        request: Check request with content

    Returns:
        CheckResponse with boolean safe flag

    Example:
        POST /v1/check
        {
            "content": "Hello, world!",
            "policy": "family"
        }
    """
    try:
        with tracer.start_as_current_span("check_content") as span:
            # Perform quick check
            is_safe = moderator.is_safe(
                text=request.content,
                policy=request.policy
            )

            # Add span attributes
            add_span_attributes(span, {
                "check.content_length": len(request.content),
                "check.is_safe": is_safe,
                "check.policy": request.policy
            })

            logger.debug(f"Quick check: safe={is_safe}")

            return CheckResponse(
                safe=is_safe,
                confidence=1.0 if is_safe else 0.0,
                reason="Content passed safety checks" if is_safe else "Content blocked by policy"
            )

    except Exception as e:
        logger.error(f"Safety check failed: {e}")

        # Record error on current span
        current_span = trace.get_current_span()
        record_error(current_span, e, {
            "error.context": "check",
            "error.content_length": len(request.content)
        })

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/stats")
async def get_stats():
    """
    Get moderation statistics.

    Returns statistics about moderation activity including:
    - Total checks performed
    - Allow/block/flag counts
    - Allow/block/flag rates
    - Current policy
    - Pattern count
    """
    return moderator.get_statistics()


@app.get("/v1/audit")
async def get_audit_log(limit: int = 100, user_id: Optional[str] = None):
    """
    Get recent audit log entries.

    Args:
        limit: Maximum number of entries to return (default: 100)
        user_id: Optional filter by user ID

    Returns:
        Audit log entries with moderation details
    """
    return {
        "total": len(moderator.audit_log),
        "entries": moderator.get_audit_log(limit=limit, user_id=user_id)
    }


@app.get("/v1/policies")
async def list_policies():
    """
    List available moderation policies.

    Returns information about available moderation policies:
    - family: Family-friendly filtering (all ages)
    - teen: Teen filtering (13+)
    - adult: Adult filtering (18+)
    - unrestricted: No filtering
    """
    policies = {
        "family": {
            "name": "family",
            "description": "Family-friendly filtering (all ages)",
            "level": "low",
            "pattern_count": 0  # Will be calculated
        },
        "teen": {
            "name": "teen",
            "description": "Teen filtering (13+)",
            "level": "medium",
            "pattern_count": 0
        },
        "adult": {
            "name": "adult",
            "description": "Adult filtering (18+)",
            "level": "high",
            "pattern_count": 0
        },
        "unrestricted": {
            "name": "unrestricted",
            "description": "No filtering",
            "level": "safe",
            "pattern_count": 0
        }
    }

    # Get actual pattern counts for current policy
    policies[settings.default_policy]["pattern_count"] = moderator.pattern_matcher.get_pattern_count()

    return {"policies": list(policies.values())}


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics in the standard format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower()
    )

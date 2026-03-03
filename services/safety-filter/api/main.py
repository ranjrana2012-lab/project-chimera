"""
Safety Filter Agent - FastAPI Application

Content safety filtering API with policy templates.
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

from core.safety import (
    SafetyFilterService,
    check_content_safety,
    POLICY_TEMPLATES,
    ContentSeverity
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Metrics
safety_checks = Counter(
    'safety_api_checks_total',
    'Total safety API checks',
    ['endpoint', 'result']
)


# Global service instance
service: Optional[SafetyFilterService] = None


def get_service() -> SafetyFilterService:
    """Get global safety filter service."""
    global service
    if service is None:
        service = SafetyFilterService(policy_name="family")
    return service


# Create FastAPI app
app = FastAPI(
    title="Safety Filter Agent",
    description="Multi-layer content safety filtering with policy templates",
    version="0.5.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "safety-filter",
        "version": "0.5.0",
        "policies": list(POLICY_TEMPLATES.keys())
    }


@app.post("/api/v1/check")
async def check_content(request_data: dict):
    """
    Check content for safety policy violations.

    Request body:
    {
        "content": "Text to check",
        "content_id": "optional-identifier",
        "policy": "family" (optional)
    }

    Response:
    {
        "is_safe": true,
        "severity": "safe",
        "matched_terms": [],
        "layer": "contextual",
        "confidence": 1.0,
        "policy": "family",
        "reasoning": "Content passed all safety checks",
        "processing_time_ms": 15
    }
    """
    try:
        service_instance = get_service()

        content = request_data.get("content", "")
        content_id = request_data.get("content_id")
        policy = request_data.get("policy", "family")

        # Use requested policy
        original_policy = service_instance.policy.name
        if policy != original_policy:
            from core.safety import POLICY_TEMPLATES
            service_instance.policy = POLICY_TEMPLATES.get(policy, POLICY_TEMPLATES["family"])

        result = service_instance.check_content(content, content_id)

        # Restore original policy
        from core.safety import POLICY_TEMPLATES
        service_instance.policy = POLICY_TEMPLATES.get(original_policy, POLICY_TEMPLATES["family"])

        if result.is_safe:
            safety_checks.labels(endpoint="check", result="safe").inc()
        else:
            safety_checks.labels(endpoint="check", result="blocked").inc()

        return {
            "is_safe": result.is_safe,
            "severity": result.severity.value,
            "matched_terms": result.matched_terms,
            "layer": result.layer.value,
            "confidence": result.confidence,
            "policy": result.policy_violated,
            "reasoning": result.reasoning,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        logger.error(f"Safety check error: {e}")
        safety_checks.labels(endpoint="check", result="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/filter")
async def filter_content(request_data: dict):
    """
    Filter content and return only if safe.

    This endpoint blocks unsafe content from proceeding.

    Request body:
    {
        "content": "Text to filter",
        "policy": "family"
    }

    Response:
    {
        "allowed": true,
        "content": "Original safe content",
        "filter_result": {...}
    }
    OR

    Response:
    {
        "allowed": false,
        "content": null,
        "filter_result": {
            "severity": "medium",
            "reasoning": "Blocked terms: hell"
        }
    }
    """
    service_instance = get_service()

    content = request_data.get("content", "")
    policy = request_data.get("policy", "family")

    # Check content
    result = check_content_safety(content, policy)

    allowed = result["is_safe"]

    if allowed:
        safety_checks.labels(endpoint="filter", result="allowed").inc()
        return {
            "allowed": True,
            "content": content,
            "filter_result": result
        }
    else:
        safety_checks.labels(endpoint="filter", result="blocked").inc()
        return {
            "allowed": False,
            "content": None,  # Don't return unsafe content
            "filter_result": result,
            "suggestion": f"Content blocked due to: {result['reasoning']}"
        }


@app.get("/api/v1/policies")
async def list_policies():
    """List available policy templates."""
    return {
        "policies": [
            {
                "name": name,
                "description": template.description,
                "severity": template.severity_threshold.value,
                "requires_ml": template.require_ml_confirmation
            }
            for name, template in POLICY_TEMPLATES.items()
        ]
    }


@app.get("/api/v1/stats")
async def get_stats():
    """Get safety filter statistics."""
    service_instance = get_service()

    stats = service_instance.get_stats()
    stats["audit_log_size"] = len(service_instance.audit_log)

    return stats


@app.get("/api/v1/audit")
async def get_audit_log(limit: int = 100):
    """Get recent audit log entries."""
    service_instance = get_service()

    log_entries = service_instance.get_audit_log(limit)

    return {
        "total": len(service_instance.audit_log),
        "entries": log_entries
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

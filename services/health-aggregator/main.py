"""Health Aggregator Service.

Polls all services and provides unified health status endpoint.
"""
import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Service Configuration
ACTIVE_SERVICES: Dict[str, str] = {
    "nemo-claw-orchestrator": os.getenv(
        "NEMO_CLAW_ORCHESTRATOR_URL", "http://localhost:8001"
    ),
    "scenespeak-agent": os.getenv("SCENESPEAK_AGENT_URL", "http://localhost:8002"),
    "sentiment-agent": os.getenv("SENTIMENT_AGENT_URL", "http://localhost:8003"),
    "safety-filter": os.getenv("SAFETY_FILTER_URL", "http://localhost:8004"),
    "captioning-agent": os.getenv("CAPTIONING_AGENT_URL", "http://localhost:8005"),
    "audio-controller": os.getenv("AUDIO_CONTROLLER_URL", "http://localhost:8006"),
}

FROZEN_SERVICES: Dict[str, str] = {
    "openclaw-orchestrator": os.getenv(
        "OPENCLAW_ORCHESTRATOR_URL", "http://localhost:8010"
    ),
    "bsl-agent": os.getenv("BSL_AGENT_URL", "http://localhost:8011"),
}

# Pydantic Models
class ServiceHealth(BaseModel):
    """Health status for a single service."""

    name: str
    status: str  # "healthy" or "unhealthy"
    response_time_ms: Optional[float] = None
    last_check: str
    error: Optional[str] = None


class HealthAggregate(BaseModel):
    """Aggregated health status for all services."""

    timestamp: str
    active_services: Dict[str, Dict]
    frozen_services: Dict[str, Dict]
    summary: Dict[str, int]


# FastAPI App
app = FastAPI(title="Health Aggregator", version="1.0.0")


async def check_service_health(service_name: str, service_url: str) -> Dict:
    """Check health of a single service.

    Args:
        service_name: Name of the service
        service_url: URL of the service's health endpoint

    Returns:
        Dictionary with health status
    """
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "name": service_name,
                    "status": "healthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "last_check": timestamp,
                    "error": None,
                }
            else:
                return {
                    "name": service_name,
                    "status": "unhealthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "last_check": timestamp,
                    "error": f"HTTP {response.status_code}",
                }

    except httpx.TimeoutException as e:
        return {
            "name": service_name,
            "status": "unhealthy",
            "response_time_ms": None,
            "last_check": timestamp,
            "error": f"Request timed out: {str(e)}",
        }

    except httpx.ConnectError as e:
        return {
            "name": service_name,
            "status": "unhealthy",
            "response_time_ms": None,
            "last_check": timestamp,
            "error": f"Connection error: {str(e)}",
        }

    except Exception as e:
        return {
            "name": service_name,
            "status": "unhealthy",
            "response_time_ms": None,
            "last_check": timestamp,
            "error": str(e),
        }


@app.get("/health", response_model=HealthAggregate)
async def get_aggregated_health():
    """Get aggregated health status for all services.

    Returns:
        HealthAggregate with status of all services and summary
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Check active services
    active_results = {}
    for service_name, service_url in ACTIVE_SERVICES.items():
        active_results[service_name] = await check_service_health(
            service_name, service_url
        )

    # Check frozen services
    frozen_results = {}
    for service_name, service_url in FROZEN_SERVICES.items():
        frozen_results[service_name] = await check_service_health(
            service_name, service_url
        )

    # Calculate summary
    healthy_active = sum(
        1 for s in active_results.values() if s["status"] == "healthy"
    )
    unhealthy_active = len(active_results) - healthy_active

    healthy_frozen = sum(
        1 for s in frozen_results.values() if s["status"] == "healthy"
    )
    unhealthy_frozen = len(frozen_results) - healthy_frozen

    summary = {
        "total_active": len(ACTIVE_SERVICES),
        "total_frozen": len(FROZEN_SERVICES),
        "healthy_active": healthy_active,
        "unhealthy_active": unhealthy_active,
        "healthy_frozen": healthy_frozen,
        "unhealthy_frozen": unhealthy_frozen,
    }

    return HealthAggregate(
        timestamp=timestamp,
        active_services=active_results,
        frozen_services=frozen_results,
        summary=summary,
    )


@app.get("/")
async def root():
    """Get service information.

    Returns:
        Service info and available endpoints
    """
    return {
        "service": "Health Aggregator",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Get aggregated health status for all services",
            "/": "Service information",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8012)

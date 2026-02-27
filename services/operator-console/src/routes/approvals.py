"""Approval workflow endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.core.approval_handler import ApprovalHandler
from src.models.request import ApprovalRequest, ApprovalResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])

# Module-level dependency
_approval_handler: ApprovalHandler | None = None


def init_approvals(approval_handler: ApprovalHandler) -> None:
    """Initialize approvals routes with dependencies.

    Args:
        approval_handler: Approval handler instance
    """
    global _approval_handler
    _approval_handler = approval_handler


@router.get("/pending")
async def get_pending_approvals(
    limit: int = Query(100, ge=1, le=1000),
    source_service: Optional[str] = Query(None, description="Filter by service"),
) -> dict:
    """Get all pending approval requests.

    Args:
        limit: Maximum results
        source_service: Optional service filter

    Returns:
        List of pending approval requests
    """
    if not _approval_handler:
        return {"requests": [], "total": 0}

    requests = _approval_handler.get_pending_requests()

    if source_service:
        requests = [r for r in requests if r.source_service == source_service]

    return {
        "requests": [
            {
                "request_id": r.request_id,
                "source_service": r.source_service,
                "content_type": r.content_type,
                "content_preview": r.content_preview,
                "metadata": r.metadata,
                "priority": r.priority,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            }
            for r in requests[:limit]
        ],
        "total": len(requests),
    }


@router.get("/request/{request_id}")
async def get_approval_request(request_id: str) -> dict:
    """Get a specific approval request.

    Args:
        request_id: Request ID

    Returns:
        Approval request details
    """
    if not _approval_handler:
        raise HTTPException(status_code=503, detail="Approval handler not available")

    request = _approval_handler.get_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail=f"Request not found: {request_id}")

    return {
        "request_id": request.request_id,
        "source_service": request.source_service,
        "content_type": request.content_type,
        "content_preview": request.content_preview,
        "metadata": request.metadata,
        "priority": r.priority,
        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
    }


@router.post("/approve")
async def approve_request(
    request_id: str,
    approved_by: str = Query(..., description="Operator making approval"),
    reason: Optional[str] = Query(None, description="Reason for approval"),
    modifications: Optional[dict] = None,
) -> dict:
    """Approve a pending request.

    Args:
        request_id: Request to approve
        approved_by: Operator making approval
        reason: Optional reason
        modifications: Optional approved modifications

    Returns:
        Approval response
    """
    if not _approval_handler:
        raise HTTPException(status_code=503, detail="Approval handler not available")

    try:
        response = await _approval_handler.approve(
            request_id=request_id,
            approved_by=approved_by,
            reason=reason,
            modifications=modifications,
        )

        return {
            "status": "approved",
            "request_id": response.request_id,
            "approved_by": response.approved_by,
            "reason": response.reason,
            "modifications": response.modifications,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error approving request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject_request(
    request_id: str,
    rejected_by: str = Query(..., description="Operator making rejection"),
    reason: str = Query(..., description="Reason for rejection"),
) -> dict:
    """Reject a pending request.

    Args:
        request_id: Request to reject
        rejected_by: Operator making rejection
        reason: Reason for rejection

    Returns:
        Approval response
    """
    if not _approval_handler:
        raise HTTPException(status_code=503, detail="Approval handler not available")

    try:
        response = await _approval_handler.reject(
            request_id=request_id,
            rejected_by=rejected_by,
            reason=reason,
        )

        return {
            "status": "rejected",
            "request_id": response.request_id,
            "rejected_by": response.approved_by,
            "reason": response.reason,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error rejecting request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_approval_history(
    limit: int = Query(100, ge=1, le=1000),
    source_service: Optional[str] = Query(None, description="Filter by service"),
) -> dict:
    """Get approval decision history.

    Args:
        limit: Maximum results
        source_service: Optional service filter

    Returns:
        List of approval responses
    """
    if not _approval_handler:
        return {"decisions": [], "total": 0}

    history = _approval_handler.get_history(limit=limit, source_service=source_service)

    return {
        "decisions": [
            {
                "request_id": r.request_id,
                "status": r.status.value,
                "approved_by": r.approved_by,
                "reason": r.reason,
                "modifications": r.modifications,
            }
            for r in history
        ],
        "total": len(history),
    }


@router.get("/stats")
async def get_approval_stats() -> dict:
    """Get approval statistics.

    Returns:
        Approval statistics
    """
    if not _approval_handler:
        return {}

    return _approval_handler.get_stats()


@router.post("/submit")
async def submit_approval_request(request: ApprovalRequest) -> dict:
    """Submit a new approval request (typically called by other services).

    Args:
        request: Approval request to submit

    Returns:
        Request ID
    """
    if not _approval_handler:
        raise HTTPException(status_code=503, detail="Approval handler not available")

    try:
        request_id = await _approval_handler.submit_request(request)

        return {
            "status": "submitted",
            "request_id": request_id,
            "message": "Approval request submitted",
        }

    except Exception as e:
        logger.error(f"Error submitting request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

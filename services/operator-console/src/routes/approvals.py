from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ApprovalRequest(BaseModel):
    type: str
    description: str
    timeout_seconds: int = 30
    metadata: dict = None


class DecisionRequest(BaseModel):
    decision: str  # approve, deny


@router.post("/approvals")
async def request_approval(request: ApprovalRequest):
    from ....main import handler
    approval = await handler.request_approval(
        request.type,
        request.description,
        request.timeout_seconds,
        request.metadata
    )
    return approval


@router.get("/approvals")
async def get_pending_approvals():
    from ....main import handler
    return await handler.get_pending_approvals()


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(approval_id: str, request: DecisionRequest):
    from ....main import handler
    return await handler.decide_approval(approval_id, request.decision)


@router.post("/invoke")
async def invoke(request: dict):
    from ....main import handler
    input_data = request.get("input", {})
    action = input_data.get("action", "")

    if action == "request_approval":
        approval = await handler.request_approval(
            input_data.get("type", "generic"),
            input_data.get("description", ""),
            input_data.get("timeout_seconds", 30),
            input_data.get("metadata")
        )
        return {"output": approval}
    elif action == "get_dashboard":
        dashboard = await handler.get_dashboard_data()
        return {"output": dashboard}

    return {"output": {"error": f"Unknown action: {action}"}}

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class CreateAlertRequest(BaseModel):
    level: str  # info, warning, critical
    message: str
    source: str
    metadata: dict = None


@router.post("/alerts")
async def create_alert(request: CreateAlertRequest):
    from ....main import handler
    alert = await handler.create_alert(
        request.level,
        request.message,
        request.source,
        request.metadata
    )
    return alert


@router.get("/alerts")
async def get_alerts(unacknowledged_only: bool = Query(False)):
    from ....main import handler
    return await handler.get_alerts(unacknowledged_only)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    from ....main import handler
    return {"success": await handler.acknowledge_alert(alert_id)}


@router.get("/dashboard")
async def get_dashboard():
    from ....main import handler
    return await handler.get_dashboard_data()

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SetSceneRequest(BaseModel):
    name: str
    channels: dict
    osc_address: str = "/lighting/scene"


@router.post("/scene")
async def set_scene(request: SetSceneRequest):
    from ....main import handler
    result = await handler.set_scene(request.model_dump())
    return result


@router.post("/blackout")
async def blackout():
    from ....main import handler
    result = await handler.blackout()
    return result


@router.get("/status")
async def get_status():
    from ....main import handler
    return await handler.get_status()


@router.post("/invoke")
async def invoke(request: dict):
    from ....main import handler
    input_data = request.get("input", {})
    action = input_data.get("action", "set_scene")

    if action == "blackout":
        result = await handler.blackout()
    elif action == "set_scene":
        result = await handler.set_scene(input_data)
    else:
        result = {"error": f"Unknown action: {action}"}

    return {"output": result}

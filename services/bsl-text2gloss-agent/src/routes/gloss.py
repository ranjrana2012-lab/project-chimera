from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str


@router.post("/translate")
async def translate(request: TranslateRequest):
    from ....main import handler
    result = await handler.translate(request.text)
    return result


@router.post("/invoke")
async def invoke(request: dict):
    from ....main import handler
    input_data = request.get("input", {})
    result = await handler.translate(input_data.get("text", ""))
    return {"output": result}

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class FilterRequest(BaseModel):
    content: str


@router.post("/filter")
async def filter_content(request: FilterRequest):
    from ....main import handler
    result = await handler.filter(request.content)
    return result


@router.get("/review-queue")
async def get_review_queue():
    from ....main import handler
    return await handler.get_review_queue()


@router.post("/review/{item_id}")
async def review_decision(item_id: str, decision: str):
    from ....main import handler
    return await handler.review_decision(item_id, decision)


@router.post("/invoke")
async def invoke(request: dict):
    from ....main import handler
    input_data = request.get("input", {})
    result = await handler.filter(input_data.get("content", ""))
    return {"output": result}

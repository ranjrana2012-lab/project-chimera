from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TranscribeRequest(BaseModel):
    audio_data: str  # base64 encoded
    language: str = None


@router.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    from ....main import handler
    import base64

    audio = base64.b64decode(request.audio_data)
    result = await handler.transcribe(audio, request.language)
    return result


@router.post("/invoke")
async def invoke(request: dict):
    from ....main import handler
    import base64

    input_data = request.get("input", {})
    audio = base64.b64decode(input_data.get("audio_data", ""))
    result = await handler.transcribe(audio, input_data.get("language"))
    return {"output": result}

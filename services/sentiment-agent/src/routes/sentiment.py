from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AnalyzeRequest(BaseModel):
    text: str


class BatchAnalyzeRequest(BaseModel):
    texts: list


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    from ....main import handler
    result = await handler.analyze(request.text)
    return result


@router.post("/analyze-batch")
async def analyze_batch(request: BatchAnalyzeRequest):
    from ....main import handler
    result = await handler.analyze_batch(request.texts)
    return result


@router.post("/invoke")
async def invoke(request: dict):
    from ....main import handler
    input_data = request.get("input", {})

    if "texts" in input_data:
        result = await handler.analyze_batch(input_data["texts"])
        # Aggregate results
        return {"output": _aggregate_sentiment(result["results"])}
    else:
        result = await handler.analyze(input_data.get("text", ""))
        return {"output": result}


def _aggregate_sentiment(results: list) -> dict:
    """Aggregate batch sentiment results."""
    total = len(results)
    if total == 0:
        return {"overall": "neutral", "intensity": 0.5}

    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0

    for r in results:
        sentiment_counts[r["sentiment"]] += 1
        total_confidence += r["confidence"]

    dominant = max(sentiment_counts, key=sentiment_counts.get)
    intensity = sentiment_counts[dominant] / total

    return {
        "overall": dominant,
        "intensity": intensity,
        "confidence": total_confidence / total,
        "sample_size": total,
    }

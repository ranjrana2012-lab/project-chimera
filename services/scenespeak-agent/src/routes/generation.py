"""Generation API routes."""
from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram

from ..models.request import GenerationRequest
from ..models.response import GenerationResponse
from ..core.llm_engine import LLMEngine
from ..core.caches import ResponseCache
import redis.asyncio as redis

router = APIRouter(prefix="/v1", tags=["generation"])

# Metrics
generation_counter = Counter('scenespeak_generations_total', 'Total generations', ['status'])
generation_duration = Histogram('scenespeak_generation_duration_seconds', 'Generation duration')

# Dependencies
_engine = None
_cache = None


def set_engine(engine: LLMEngine) -> None:
    """Set the global LLM engine instance."""
    global _engine
    _engine = engine


def set_cache(cache: ResponseCache) -> None:
    """Set the global ResponseCache instance."""
    global _cache
    _cache = cache


async def get_engine() -> LLMEngine:
    """Get the LLM engine dependency."""
    global _engine
    return _engine


async def get_cache() -> ResponseCache:
    """Get the ResponseCache dependency."""
    global _cache
    return _cache


@router.post("/generate", response_model=GenerationResponse)
async def generate(
    request: GenerationRequest,
    engine: LLMEngine = Depends(get_engine),
    cache: ResponseCache = Depends(get_cache)
):
    """Generate dialogue."""
    with generation_duration.time():
        try:
            # Check cache first
            if request.use_cache:
                prompt = engine._build_prompt(request)
                params = {
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p
                }
                cached = await cache.get(prompt, params)
                if cached:
                    generation_counter.labels(status="cache_hit").inc()
                    return GenerationResponse(**cached)

            # Generate
            response = await engine.generate(request)
            generation_counter.labels(status="success").inc()

            # Cache result
            if request.use_cache:
                await cache.set(prompt, params, response.model_dump())

            return response

        except Exception as e:
            generation_counter.labels(status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))

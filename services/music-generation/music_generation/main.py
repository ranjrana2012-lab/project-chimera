from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog

from music_generation.models import ModelPoolManager
from music_generation.inference import InferenceEngine
from music_generation.audio import AudioProcessor
from music_generation.schemas import GenerationParams


logger = structlog.get_logger()


class GenerateRequest(BaseModel):
    model_name: str
    prompt: str
    duration_seconds: int = 30
    format: str = "wav"
    sample_rate: int = 44100


class GenerateResponse(BaseModel):
    request_id: str
    status: str
    audio_url: str | None = None
    duration_seconds: int


# Global instances
model_pool: ModelPoolManager | None = None
inference_engine: InferenceEngine | None = None
audio_processor: AudioProcessor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global model_pool, inference_engine, audio_processor

    # Initialize
    model_pool = ModelPoolManager()
    inference_engine = InferenceEngine(model_pool)
    audio_processor = AudioProcessor()

    logger.info("music_generation_service_started")

    yield

    # Cleanup
    logger.info("music_generation_service_stopped")


app = FastAPI(
    title="Music Generation Service",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "music-generation",
        "models_loaded": len(model_pool.loaded_models) if model_pool else 0
    }


@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_music(request: GenerateRequest):
    """Generate music with specified model"""
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        result = await inference_engine.generate(
            model_name=request.model_name,
            prompt=request.prompt,
            params=request
        )

        return GenerateResponse(
            request_id="placeholder",
            status="completed",
            audio_url=None,  # Will be implemented with MinIO
            duration_seconds=int(result.duration_seconds)
        )
    except Exception as e:
        logger.error("generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)

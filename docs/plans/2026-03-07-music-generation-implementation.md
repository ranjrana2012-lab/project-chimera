# Music Generation Model Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build music generation service with MusicGen and ACE-Step model integration on ARM64 GB10 GPU

**Architecture:** Single FastAPI service (port 8011) with model pool manager supporting both MusicGen and ACE-Step models, async inference engine, audio processing pipeline, ARM64-optimized PyTorch with CUDA 13.0, Docker/K3s deployment.

**Tech Stack:** Python 3.12+, FastAPI, PyTorch 2.5+ (CUDA 13.0 ARM64), MusicGen/ACE-Step models, librosa, soundfile

---

## Phase 1: Foundation Setup

### Task 1: Create Service Directory Structure

**Files:**
- Create: `services/music-generation/`
- Create: `services/music-generation/tests/`
- Create: `services/music-generation/tests/__init__.py`

**Step 1: Create directories**

```bash
mkdir -p services/music-generation/tests
```

**Step 2: Create test init file**

```bash
touch services/music-generation/tests/__init__.py
```

**Step 3: Verify structure**

Run: `ls -la services/music-generation/`
Expected: Empty directory with tests/ subdirectory

**Step 4: Commit**

```bash
git add services/music-generation/
git commit -m "feat(music-generation): create service directory structure"
```

---

### Task 2: Create Requirements File

**Files:**
- Create: `services/music-generation/requirements.txt`

**Step 1: Write requirements**

```python
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Machine Learning
torch==2.5.0+cu121  # CUDA 12.1 compatible with CUDA 13 runtime
torchaudio==2.5.0+cu121
transformers==4.36.0
accelerate==0.25.0
sentencepiece==0.1.99
huggingface-hub==0.20.0

# Audio Processing
librosa==0.10.1
soundfile==0.12.1
numpy==1.24.4

# Utilities
python-multipart==0.0.6
aiofiles==23.2.1

# Observability
prometheus-client==0.19.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-logging==0.43b0

# Testing
pytest==7.4.4
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.26.0
```

**Step 2: Verify file**

Run: `cat services/music-generation/requirements.txt`
Expected: Requirements content displayed

**Step 3: Commit**

```bash
git add services/music-generation/requirements.txt
git commit -m "feat(music-generation): add requirements with PyTorch CUDA support"
```

---

### Task 3: Create Configuration Module

**Files:**
- Create: `services/music-generation/config.py`

**Step 1: Write configuration code**

```python
"""Music Generation Service Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Service
    service_name: str = "music-generation"
    port: int = 8011
    log_level: str = "INFO"
    environment: str = "development"

    # Model Paths
    musicgen_model_path: str = "/models/musicgen"
    acestep_model_path: str = "/models/acestep"
    huggingface_cache_dir: str = "/models/cache"

    # Model Settings
    default_model: str = "musicgen"  # or "acestep"
    max_vram_mb: int = 8192  # GB10 GPU VRAM limit
    model_offload: bool = True  # Offload to CPU when not in use

    # Generation Settings
    default_duration: float = 5.0  # seconds
    max_duration: float = 30.0
    sample_rate: int = 44100
    normalize_db: float = -1.0
    trim_silence: bool = True

    # GPU Settings
    device: str = "cuda"  # or "cpu" for testing
    torch_threads: int = 4

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    class Config:
        """Pydantic config."""
        env_prefix = ""


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/music-generation/config.py`
Expected: No output (syntax valid)

**Step 3: Commit**

```bash
git add services/music-generation/config.py
git commit -m "feat(music-generation): add configuration module"
```

---

### Task 4: Create Pydantic Models

**Files:**
- Create: `services/music-generation/models.py`

**Step 1: Write Pydantic models**

```python
"""Pydantic models for Music Generation Service."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from enum import Enum


class ModelName(str, Enum):
    """Available model names."""
    MUSICGEN = "musicgen"
    ACESTEP = "acestep"


class GenerationRequest(BaseModel):
    """Music generation request."""

    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt for music generation")
    model: ModelName = Field(default=ModelName.MUSICGEN, description="Model to use")
    duration: float = Field(default=5.0, ge=1.0, le=30.0, description="Duration in seconds")
    sample_rate: int = Field(default=44100, ge=16000, le=48000, description="Sample rate in Hz")

    @validator("prompt")
    def prompt_not_empty(cls, v):
        """Validate prompt is not just whitespace."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()


class GenerationResponse(BaseModel):
    """Music generation response."""

    success: bool
    audio_url: Optional[str] = None
    duration: float
    sample_rate: int
    format: str = "wav"
    model: str
    generation_time: float
    file_size: Optional[int] = None
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    loaded: bool
    vram_mb: Optional[int] = None
    sample_rate: int
    description: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str  # "ok" or "error"
    service: str
    version: str = "1.0.0"
    models_loaded: list[str] = []


class ErrorResponse(BaseModel):
    """Error response."""

    error: dict
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/music-generation/models.py`
Expected: No output

**Step 3: Commit**

```bash
git add services/music-generation/models.py
git commit -m "feat(music-generation): add Pydantic models"
```

---

### Task 5: Create Environment Template

**Files:**
- Create: `services/music-generation/.env.example`

**Step 1: Write environment template**

```bash
# Music Generation Service Configuration

# Service Settings
SERVICE_NAME=music-generation
PORT=8011
LOG_LEVEL=INFO
ENVIRONMENT=development

# Model Paths (adjust for your system)
MUSICGEN_MODEL_PATH=/models/musicgen
ACESTEP_MODEL_PATH=/models/acestep
HUGGINGFACE_CACHE_DIR=/models/cache

# Model Settings
DEFAULT_MODEL=musicgen
MAX_VRAM_MB=8192
MODEL_OFFLOAD=true

# Generation Settings
DEFAULT_DURATION=5.0
MAX_DURATION=30.0
SAMPLE_RATE=44100
NORMALIZE_DB=-1.0
TRIM_SILENCE=true

# GPU Settings
DEVICE=cuda
TORCH_THREADS=4

# OpenTelemetry
OTLP_ENDPOINT=http://localhost:4317
```

**Step 2: Verify file**

Run: `cat services/music-generation/.env.example`
Expected: Environment template displayed

**Step 3: Commit**

```bash
git add services/music-generation/.env.example
git commit -m "feat(music-generation): add environment configuration template"
```

---

## Phase 2: Model Pool Manager

### Task 6: Create Model Pool Manager

**Files:**
- Create: `services/music-generation/model_pool.py`

**Step 1: Write model pool code**

```python
"""Model Pool Manager for Music Generation."""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict
import torch
from transformers import AutoModelForConditionalGeneration, AutoProcessor

from config import get_settings
from models import ModelName

logger = logging.getLogger(__name__)


class ModelPool:
    """Manages loading and unloading of music generation models."""

    def __init__(self):
        """Initialize model pool."""
        self.settings = get_settings()
        self.models: Dict[ModelName, Optional[torch.nn.Module]] = {
            ModelName.MUSICGEN: None,
            ModelName.ACESTEP: None,
        }
        self.processors: Dict[ModelName, Optional] = {
            ModelName.MUSICGEN: None,
            ModelName.ACESTEP: None,
        }
        self.device = torch.device(self.settings.device)
        self._load_lock = asyncio.Lock()

    async def get_model(self, model_name: ModelName):
        """Get loaded model, loading if necessary.

        Args:
            model_name: Which model to get

        Returns:
            Tuple of (model, processor)
        """
        async with self._load_lock:
            if self.models[model_name] is None:
                await self._load_model(model_name)

            return self.models[model_name], self.processors[model_name]

    async def _load_model(self, model_name: ModelName):
        """Load a model into memory.

        Args:
            model_name: Which model to load
        """
        logger.info(f"Loading model: {model_name}")

        if model_name == ModelName.MUSICGEN:
            model_path = self.settings.musicgen_model_path
            model_id = "facebook/musicgen-small"
        else:  # ACESTEP
            model_path = self.settings.acestep_model_path
            model_id = "ACE-Step/ACE-Step"  # Placeholder - update with actual

        try:
            # Check if local path exists
            if Path(model_path).exists():
                logger.info(f"Loading from local path: {model_path}")
                model = AutoModelForConditionalGeneration.from_pretrained(
                    model_path,
                    local_files_only=True,
                    torch_dtype=torch.float16,
                )
                processor = AutoProcessor.from_pretrained(
                    model_path,
                    local_files_only=True,
                )
            else:
                logger.info(f"Loading from HuggingFace: {model_id}")
                model = AutoModelForConditionalGeneration.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16,
                    cache_dir=self.settings.huggingface_cache_dir,
                )
                processor = AutoProcessor.from_pretrained(
                    model_id,
                    cache_dir=self.settings.huggingface_cache_dir,
                )

            model = model.to(self.device)
            model.eval()

            self.models[model_name] = model
            self.processors[model_name] = processor

            logger.info(f"Model {model_name} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    async def unload_model(self, model_name: ModelName):
        """Unload a model to free VRAM.

        Args:
            model_name: Which model to unload
        """
        async with self._load_lock:
            if self.models[model_name] is not None:
                logger.info(f"Unloading model: {model_name}")
                del self.models[model_name]
                del self.processors[model_name]
                self.models[model_name] = None
                self.processors[model_name] = None

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                logger.info(f"Model {model_name} unloaded")

    def estimate_vram_mb(self, model_name: ModelName) -> int:
        """Estimate VRAM usage for a model.

        Args:
            model_name: Which model to estimate

        Returns:
            Estimated VRAM in MB
        """
        # Rough estimates - adjust based on actual usage
        if model_name == ModelName.MUSICGEN:
            return 4096  # ~4GB for musicgen-small
        else:  # ACESTEP
            return 2048  # ~2GB

    async def switch_model(self, from_model: ModelName, to_model: ModelName):
        """Switch from one model to another.

        Args:
            from_model: Model to unload
            to_model: Model to load
        """
        await self.unload_model(from_model)
        await self._load_model(to_model)


# Global model pool instance
_model_pool: Optional[ModelPool] = None


def get_model_pool() -> ModelPool:
    """Get global model pool instance."""
    global _model_pool
    if _model_pool is None:
        _model_pool = ModelPool()
    return _model_pool
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/music-generation/model_pool.py`
Expected: No output

**Step 3: Commit**

```bash
git add services/music-generation/model_pool.py
git commit -m "feat(music-generation): add model pool manager"
```

---

## Phase 3: Audio Processor

### Task 7: Create Audio Processor

**Files:**
- Create: `services/music-generation/audio.py`

**Step 1: Write audio processor code**

```python
"""Audio processing utilities."""

import logging
import numpy as np
import soundfile as sf
from io import BytesIO

from config import get_settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process generated audio."""

    def __init__(self):
        """Initialize audio processor."""
        self.settings = get_settings()

    def normalize(self, audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
        """Normalize audio to target dB level.

        Args:
            audio: Audio array
            target_db: Target level in dB

        Returns:
            Normalized audio
        """
        if audio.size == 0:
            return audio

        # Calculate current RMS
        rms = np.sqrt(np.mean(audio ** 2))

        if rms == 0:
            return audio

        # Calculate required gain
        target_rms = 10 ** (target_db / 20)
        gain = target_rms / rms

        # Apply gain with clipping to prevent distortion
        normalized = audio * gain
        normalized = np.clip(normalized, -1.0, 1.0)

        return normalized

    def trim_silence(self, audio: np.ndarray, sample_rate: int,
                    threshold_db: float = -40.0) -> np.ndarray:
        """Trim silence from start and end.

        Args:
            audio: Audio array
            sample_rate: Sample rate in Hz
            threshold_db: Silence threshold in dB

        Returns:
            Trimmed audio
        """
        if audio.size == 0:
            return audio

        # Calculate amplitude in dB
        amplitude = 20 * np.log10(np.abs(audio) + 1e-10)

        # Find non-silent regions
        non_silent = amplitude > threshold_db

        if not np.any(non_silent):
            return audio

        # Find first and last non-silent sample
        first_non_silent = np.where(non_silent)[0][0]
        last_non_silent = np.where(non_silent)[0][-1]

        # Add small margin
        margin = int(sample_rate * 0.1)  # 100ms margin
        start = max(0, first_non_silent - margin)
        end = min(len(audio), last_non_silent + margin + 1)

        return audio[start:end]

    def to_wav(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """Convert audio to WAV format.

        Args:
            audio: Audio array
            sample_rate: Sample rate in Hz

        Returns:
            WAV file as bytes
        """
        buffer = BytesIO()

        # Ensure audio is in correct format
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        sf.write(buffer, sample_rate, audio, format='WAV')
        buffer.seek(0)

        return buffer.read()

    def process(self, audio: np.ndarray, sample_rate: int) -> tuple[bytes, dict]:
        """Process audio through full pipeline.

        Args:
            audio: Raw audio output from model
            sample_rate: Sample rate in Hz

        Returns:
            Tuple of (wav_bytes, metadata)
        """
        # Normalize
        processed = self.normalize(audio, self.settings.normalize_db)

        # Trim silence
        if self.settings.trim_silence:
            processed = self.trim_silence(processed, sample_rate)

        # Convert to WAV
        wav_bytes = self.to_wav(processed, sample_rate)

        # Metadata
        metadata = {
            "duration_seconds": len(processed) / sample_rate,
            "sample_rate": sample_rate,
            "channels": 1 if processed.ndim == 1 else processed.shape[1],
            "format": "wav",
            "file_size_bytes": len(wav_bytes),
        }

        return wav_bytes, metadata


# Global audio processor instance
_audio_processor: Optional[AudioProcessor] = None


def get_audio_processor() -> AudioProcessor:
    """Get global audio processor instance."""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/music-generation/audio.py`
Expected: No output

**Step 3: Commit**

```bash
git add services/music-generation/audio.py
git commit -m "feat(music-generation): add audio processor"
```

---

## Phase 4: Inference Engine

### Task 8: Create Inference Engine

**Files:**
- Create: `services/music-generation/inference.py`

**Step 1: Write inference engine code**

```python
"""Music generation inference engine."""

import asyncio
import logging
from typing import Callable, Optional
import torch
import numpy as np

from config import get_settings
from models import ModelName, GenerationRequest
from model_pool import get_model_pool

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Async music generation engine."""

    def __init__(self):
        """Initialize inference engine."""
        self.settings = get_settings()
        self.model_pool = get_model_pool()

    async def generate(self, request: GenerationRequest,
                     progress_callback: Optional[Callable] = None) -> tuple[np.ndarray, int]:
        """Generate music from prompt.

        Args:
            request: Generation request
            progress_callback: Optional progress callback

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        # Get model
        model, processor = await self.model_pool.get_model(request.model)

        # Prepare inputs
        inputs = processor(
            text=request.prompt,
            return_tensors="pt"
        ).to(self.model_pool.device)

        # Calculate max tokens based on duration
        # Rough estimate: 50 tokens per second
        max_new_tokens = int(request.duration * 50)

        logger.info(f"Generating {request.duration}s of music with {request.model}")

        # Generate
        with torch.no_grad():
            sampling_rate = model.config.audio_encoder.sampling_rate
            generate_kwargs = {
                "max_new_tokens": max_new_tokens,
                "do_sample": True,
                "temperature": 0.7,
                "top_k": 50,
            }

            if progress_callback:
                # For progress tracking, we'd need to use a streaming approach
                # For now, just call the callback at start and end
                await progress_callback(0, 100)

            outputs = model.generate(**inputs, **generate_kwargs)

            if progress_callback:
                await progress_callback(100, 100)

        # Decode audio
        audio_values = outputs[0, 0].cpu().numpy()

        # Resample if needed
        from scipy.signal import resample_poly
        if sampling_rate != request.sample_rate:
            audio_values = resample_poly(
                audio_values,
                sampling_rate,
                request.sample_rate
            )

        return audio_values, request.sample_rate

    async def generate_async_with_cancellation(self, request: GenerationRequest,
                                             cancellation_token: asyncio.CancelledError) -> tuple[np.ndarray, int]:
        """Generate with cancellation support.

        Args:
            request: Generation request
            cancellation_token: Token to check for cancellation

        Returns:
            Tuple of (audio_array, sample_rate)

        Raises:
            asyncio.CancelledError: If generation is cancelled
        """
        task = asyncio.create_task(self.generate(request))

        try:
            result = await asyncio.wait_for(
                asyncio.shield(task),
                timeout=300.0  # 5 minute timeout
            )
            return result
        except asyncio.CancelledError:
            task.cancel()
            logger.info("Generation cancelled by user")
            raise

    def estimate_vram_required(self, model: ModelName, duration: float) -> int:
        """Estimate VRAM required for generation.

        Args:
            model: Which model
            duration: Duration in seconds

        Returns:
            Estimated VRAM in MB
        """
        base_vram = self.model_pool.estimate_vram_mb(model)

        # Add overhead for longer durations
        duration_multiplier = min(2.0, duration / 5.0)

        return int(base_vram * duration_multiplier)


# Global inference engine instance
_inference_engine: Optional[InferenceEngine] = None


def get_inference_engine() -> InferenceEngine:
    """Get global inference engine instance."""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = InferenceEngine()
    return _inference_engine
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/music-generation/inference.py`
Expected: No output (scipy import may fail but that's OK for now)

**Step 3: Commit**

```bash
git add services/music-generation/inference.py
git commit -m "feat(music-generation): add inference engine"
```

---

## Phase 5: Main FastAPI Service

### Task 9: Create Main Application

**Files:**
- Create: `services/music-generation/main.py`

**Step 1: Write main application code**

```python
"""Music Generation Service - FastAPI Application."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import JSONResponse

from config import get_settings
from models import (
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
    HealthResponse,
    ErrorResponse,
    ModelName,
)
from model_pool import get_model_pool
from inference import get_inference_engine
from audio import get_audio_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Metrics
generation_counter = Counter(
    'music_generation_total',
    'Total music generations',
    ['model', 'status']
)
generation_duration = Histogram(
    'music_generation_duration_seconds',
    'Music generation duration',
    ['model']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info(f"Music Generation Service starting up on port {settings.port}")

    # Pre-load default model if configured
    model_pool = get_model_pool()
    if settings.default_model:
        try:
            await model_pool._load_model(ModelName(settings.default_model))
            logger.info(f"Pre-loaded default model: {settings.default_model}")
        except Exception as e:
            logger.warning(f"Failed to pre-load model: {e}")

    yield

    # Cleanup
    logger.info("Music Generation Service shutting down")
    # Unload all models
    for model_name in ModelName:
        await model_pool.unload_model(model_name)


# Create FastAPI app
app = FastAPI(
    title="Music Generation Service",
    description="AI music generation using MusicGen and ACE-Step models",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health/live", response_model=HealthResponse)
async def liveness():
    """Liveness check."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        models_loaded=[]
    )


@app.get("/health/ready", response_model=HealthResponse)
async def readiness():
    """Readiness check with model status."""
    model_pool = get_model_pool()
    loaded_models = [
        name.value for name, model in model_pool.models.items()
        if model is not None
    ]

    return HealthResponse(
        status="ok",
        service=settings.service_name,
        models_loaded=loaded_models
    )


@app.get("/models", response_model=list[ModelInfo])
async def list_models():
    """List available models."""
    model_pool = get_model_pool()

    models = [
        ModelInfo(
            name="musicgen",
            loaded=model_pool.models[ModelName.MUSICGEN] is not None,
            vram_mb=model_pool.estimate_vram_mb(ModelName.MUSICGEN),
            sample_rate=32000,
            description="Meta MusicGen - High quality music generation"
        ),
        ModelInfo(
            name="acestep",
            loaded=model_pool.models[ModelName.ACESTEP] is not None,
            vram_mb=model_pool.estimate_vram_mb(ModelName.ACESTEP),
            sample_rate=44100,
            description="ACE-Step - Efficient music generation"
        )
    ]

    return models


@app.post("/generate", response_model=GenerationResponse)
async def generate_music(request: GenerationRequest):
    """Generate music from text prompt.

    Args:
        request: Generation request with prompt and parameters

    Returns:
        Generation response with audio
    """
    start_time = time.time()

    try:
        # Check VRAM availability
        inference_engine = get_inference_engine()
        required_vram = inference_engine.estimate_vram_required(
            request.model,
            request.duration
        )

        model_pool = get_model_pool()
        available_vram = settings.max_vram_mb

        # Switch models if needed
        current_model = request.model
        if required_vram > available_vram:
            # Try smaller model
            if request.model == ModelName.MUSICGEN:
                logger.warning("Insufficient VRAM for MusicGen, suggesting ACE-Step")
                return GenerationResponse(
                    success=False,
                    error=f"Insufficient VRAM. Required: {required_vram}MB, Available: {available_vram}MB. Try ACE-Step model."
                )

        # Generate audio
        audio_array, sample_rate = await inference_engine.generate(request)

        # Process audio
        audio_processor = get_audio_processor()
        wav_bytes, metadata = audio_processor.process(audio_array, sample_rate)

        generation_time = time.time() - start_time

        # Record metrics
        generation_counter.labels(
            model=request.model.value,
            status="success"
        ).inc()
        generation_duration.labels(
            model=request.model.value
        ).observe(generation_time)

        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "X-Generation-Time": str(generation_time),
                "X-Duration": str(metadata["duration_seconds"]),
                "X-Sample-Rate": str(sample_rate),
                "X-Model": request.model.value,
            }
        )

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        generation_counter.labels(
            model=request.model.value,
            status="error"
        ).inc()

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": str(e),
                    "details": {
                        "model": request.model.value,
                        "prompt": request.prompt[:100]  # Truncate for logging
                    }
                }
            }
        )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile services/music-generation/main.py`
Expected: No output

**Step 3: Commit**

```bash
git add services/music-generation/main.py
git commit -m "feat(music-generation): add main FastAPI application"
```

---

## Phase 6: Docker & Deployment

### Task 10: Create Dockerfile

**Files:**
- Create: `services/music-generation/Dockerfile`

**Step 1: Write Dockerfile**

```dockerfile
# Multi-stage build for ARM64
FROM --platform=linux/arm64 python:3.12-slim AS builder

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM --platform=linux/arm64 python:3.12-slim

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 chimera

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY *.py ./

# Create model directory
RUN mkdir -p /models && chown -R chimera:chimera /models

# Switch to non-root user
USER chimera

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8011/health/live')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
```

**Step 2: Verify Dockerfile syntax**

Run: `cat services/music-generation/Dockerfile`
Expected: Dockerfile content displayed

**Step 3: Commit**

```bash
git add services/music-generation/Dockerfile
git commit -m "feat(music-generation): add ARM64 Dockerfile"
```

---

### Task 11: Create K8s Deployment Manifest

**Files:**
- Create: `services/music-generation/manifests/k8s.yaml`

**Step 1: Write K8s manifest**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: music-generation-config
  namespace: chimera
data:
  SERVICE_NAME: "music-generation"
  PORT: "8011"
  LOG_LEVEL: "INFO"
  DEFAULT_MODEL: "musicgen"
  MAX_VRAM_MB: "8192"
  DEVICE: "cuda"
---
apiVersion: v1
kind: Service
metadata:
  name: music-generation
  namespace: chimera
  labels:
    app: music-generation
    service: music-generation
spec:
  type: ClusterIP
  ports:
  - port: 8011
    targetPort: 8011
    name: http
  selector:
    app: music-generation
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: music-generation
  namespace: chimera
  labels:
    app: music-generation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: music-generation
  template:
    metadata:
      labels:
        app: music-generation
    spec:
      nodeSelector:
        gpu: "true"
      containers:
      - name: music-generation
        image: music-generation:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8011
          name: http
        env:
        - name: SERVICE_NAME
          valueFrom:
            configMapKeyRef:
              name: music-generation-config
              key: SERVICE_NAME
        - name: PORT
          valueFrom:
            configMapKeyRef:
              name: music-generation-config
              key: PORT
        - name: DEVICE
          valueFrom:
            configMapKeyRef:
              name: music-generation-config
              key: DEVICE
        - name: MAX_VRAM_MB
          valueFrom:
            configMapKeyRef:
              name: music-generation-config
              key: MAX_VRAM_MB
        resources:
          requests:
            memory: "4Gi"
            nvidia.com/gpu: "1"
          limits:
            memory: "8Gi"
            nvidia.com/gpu: "1"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8011
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8011
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: models-pvc
  namespace: chimera
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

**Step 2: Create manifests directory first**

```bash
mkdir -p services/music-generation/manifests
```

**Step 3: Verify and commit**

```bash
git add services/music-generation/manifests/k8s.yaml
git commit -m "feat(music-generation): add K8s deployment manifests"
```

---

## Phase 7: Testing

### Task 12: Create Unit Tests

**Files:**
- Create: `services/music-generation/tests/test_music_generation.py`

**Step 1: Write unit tests**

```python
"""Unit tests for Music Generation Service."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from audio import AudioProcessor
from model_pool import ModelPool
from models import ModelName, GenerationRequest


class TestAudioProcessor:
    """Test audio processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = AudioProcessor()

    def test_normalize_silence(self):
        """Test normalizing silent audio."""
        audio = np.zeros(1000)
        result = self.processor.normalize(audio)
        assert np.array_equal(audio, result)

    def test_normalize_loud_audio(self):
        """Test normalizing loud audio."""
        audio = np.ones(1000) * 0.5
        result = self.processor.normalize(audio, target_db=-20.0)
        # Result should be scaled
        assert not np.array_equal(audio, result)

    def test_trim_silence_both_ends(self):
        """Test trimming silence from both ends."""
        # 100 samples of silence, 100 of audio, 100 of silence
        audio = np.concatenate([
            np.zeros(100),
            np.ones(100) * 0.5,
            np.zeros(100)
        ])
        result = self.processor.trim_silence(audio, 44100)
        # Should be shorter
        assert len(result) < len(audio)


class TestModelPool:
    """Test model pool manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pool = ModelPool()

    def test_estimate_vram_musicgen(self):
        """Test VRAM estimation for MusicGen."""
        vram = self.pool.estimate_vram_mb(ModelName.MUSICGEN)
        assert vram == 4096

    def test_estimate_vram_acestep(self):
        """Test VRAM estimation for ACE-Step."""
        vram = self.pool.estimate_vram_mb(ModelName.ACESTEP)
        assert vram == 2048

    def test_models_dict_initialized(self):
        """Test models dictionary starts empty."""
        assert self.pool.models[ModelName.MUSICGEN] is None
        assert self.pool.models[ModelName.ACESTEP] is None


class TestGenerationRequest:
    """Test generation request validation."""

    def test_valid_request(self):
        """Test valid request passes validation."""
        request = GenerationRequest(
            prompt="A happy upbeat song",
            model=ModelName.MUSICGEN,
            duration=5.0
        )
        assert request.prompt == "A happy upbeat song"

    def test_empty_prompt_fails(self):
        """Test empty prompt fails validation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="   ",  # Whitespace only
                model=ModelName.MUSICGEN
            )

    def test_duration_validation(self):
        """Test duration bounds validation."""
        # Too short
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="Test",
                duration=0.5
            )

        # Too long
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="Test",
                duration=60.0
            )
```

**Step 2: Run tests to verify they fail (models not implemented yet)**

Run: `cd services/music-generation && python -m pytest tests/test_music_generation.py -v 2>&1 | head -20`
Expected: Tests may pass or fail depending on imports

**Step 3: Commit tests**

```bash
git add services/music-generation/tests/test_music_generation.py
git commit -m "test(music-generation): add unit tests"
```

---

## Phase 8: Documentation

### Task 13: Create Service README

**Files:**
- Create: `services/music-generation/README.md`

**Step 1: Write README**

```markdown
# Music Generation Service

AI-powered music generation service using Meta's MusicGen and ACE-Step models for Project Chimera.

## Overview

The Music Generation Service provides real-time music generation capabilities:
- Text-to-music generation using AI models
- Support for both MusicGen (high quality) and ACE-Step (efficient)
- ARM64-optimized for Nvidia GB10 GPU
- Async generation with cancellation support
- Audio post-processing (normalize, trim)

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - CUDA-capable GPU (Nvidia GB10 tested)
# - Docker (for containerized deployment)

# Local development setup
cd services/music-generation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your model paths and GPU settings

# Run service
uvicorn main:app --reload --port 8011
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MUSICGEN_MODEL_PATH` | `/models/musicgen` | MusicGen model directory |
| `ACESTEP_MODEL_PATH` | `/models/acestep` | ACE-Step model directory |
| `DEFAULT_MODEL` | `musicgen` | Default model to use |
| `MAX_VRAM_MB` | `8192` | GPU memory limit in MB |
| `DEVICE` | `cuda` | Compute device (cuda/cpu) |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks models)
- `GET /metrics` - Prometheus metrics

### Generation
- `POST /generate` - Generate music from text prompt

**Request Body:**
```json
{
  "prompt": "A happy upbeat song with piano",
  "model": "musicgen",
  "duration": 5.0,
  "sample_rate": 44100
}
```

**Response:** WAV audio file with metadata headers

### Models
- `GET /models` - List available models and their status

## Development

### Code Structure
```
music-generation/
├── main.py              # FastAPI application
├── model_pool.py        # Model loading/unloading
├── inference.py         # Generation engine
├── audio.py             # Audio processing
├── config.py            # Configuration
├── models.py            # Pydantic models
├── metrics.py           # Prometheus metrics
└── tests/               # Test suite
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Docker

```bash
# Build image
docker build -t music-generation:latest .

# Run container
docker run -p 8011:8011 --gpus all music-generation:latest
```

## License

MIT - Project Chimera
```

**Step 2: Verify and commit**

```bash
git add services/music-generation/README.md
git commit -m "docs(music-generation): add service README"
```

---

### Task 14: Create API Documentation

**Files:**
- Create: `docs/api/music-generation.md`

**Step 1: Write API documentation**

```markdown
# Music Generation API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8011`
**Service:** AI music generation using MusicGen and ACE-Step models

---

## Overview

The Music Generation Service provides text-to-music generation using state-of-the-art AI models optimized for ARM64 GPUs.

---

## Endpoints

### 1. Generate Music

Generate music from text prompt.

**Endpoint:** `POST /generate`

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "prompt": "string (required, 1-500 chars)",
  "model": "musicgen | acestep (optional, default: musicgen)",
  "duration": "number (optional, 1-30 seconds, default: 5.0)",
  "sample_rate": "number (optional, default: 44100)"
}
```

**Response:** `audio/wav`

**Headers:**
- `X-Generation-Time`: Generation time in seconds
- `X-Duration`: Actual audio duration in seconds
- `X-Sample-Rate`: Sample rate in Hz
- `X-Model`: Model used

**Example:**
```bash
curl -X POST http://localhost:8011/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A dramatic orchestral piece with strings and brass",
    "model": "musicgen",
    "duration": 10.0
  }' \
  --output music.wav
```

---

### 2. Health Checks

**Endpoint:** `GET /health/live`

**Response:**
```json
{
  "status": "ok",
  "service": "music-generation",
  "version": "1.0.0",
  "models_loaded": []
}
```

**Endpoint:** `GET /health/ready`

**Response:**
```json
{
  "status": "ok",
  "service": "music-generation",
  "models_loaded": ["musicgen"]
}
```

---

### 3. List Models

**Endpoint:** `GET /models`

**Response:**
```json
[
  {
    "name": "musicgen",
    "loaded": true,
    "vram_mb": 4096,
    "sample_rate": 32000,
    "description": "Meta MusicGen - High quality music generation"
  },
  {
    "name": "acestep",
    "loaded": false,
    "vram_mb": 2048,
    "sample_rate": 44100,
    "description": "ACE-Step - Efficient music generation"
  }
]
```

---

### 4. Metrics

**Endpoint:** `GET /metrics`

**Response:** Prometheus metrics in plain text format

---

## Error Responses

All errors return JSON:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Common Error Codes:**
- `INSUFFICIENT_VRAM` - Not enough GPU memory
- `MODEL_NOT_FOUND` - Model file not found
- `INVALID_PROMPT` - Prompt validation failed
- `GENERATION_FAILED` - Generation error
- `GPU_UNAVAILABLE` - GPU not accessible

---

*API Documentation - Music Generation v1.0.0 - March 7, 2026*
```

**Step 2: Verify and commit**

```bash
git add docs/api/music-generation.md
git commit -m "docs(api): add music generation API documentation"
```

---

## Phase 9: Final Integration

### Task 15: Create Metrics Module

**Files:**
- Create: `services/music-generation/metrics.py`

**Step 1: Write metrics module**

```python
"""Prometheus metrics for Music Generation Service."""

from prometheus_client import Counter, Histogram, Gauge, Info

# Generation metrics
generations_total = Counter(
    'music_generations_total',
    'Total music generations',
    ['model', 'status']
)

generation_duration = Histogram(
    'music_generation_duration_seconds',
    'Music generation duration in seconds',
    ['model'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Model metrics
model_vram_usage = Gauge(
    'music_model_vram_usage_mb',
    'VRAM usage per model in MB',
    ['model']
)

model_loaded = Gauge(
    'music_model_loaded',
    'Whether a model is loaded (1 or 0)',
    ['model']
)

# Service info
service_info = Info(
    'music_generation_service',
    'Music Generation Service information'
)

service_info.info({
    'version': '1.0.0',
    'architecture': 'ARM64',
    'gpu': 'NVIDIA GB10'
})
```

**Step 2: Verify and commit**

```bash
git add services/music-generation/metrics.py
git commit -m "feat(music-generation): add Prometheus metrics module"
```

---

### Task 16: Create Tracing Module

**Files:**
- Create: `services/music-generation/tracing.py`

**Step 1: Write tracing module**

```python
"""OpenTelemetry tracing setup for Music Generation Service."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from config import get_settings


def setup_telemetry(service_name: str, otlp_endpoint: str):
    """Set up OpenTelemetry tracing.

    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP endpoint URL

    Returns:
        Tracer instance
    """
    # Create resource
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "chimera"
    })

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Set up OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True
    )

    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    return trace.get_tracer(__name__)


def instrument_fastapi(app):
    """Instrument FastAPI app with tracing.

    Args:
        app: FastAPI application
    """
    FastAPIInstrumentor.instrument_app(app)
```

**Step 2: Verify and commit**

```bash
git add services/music-generation/tracing.py
git commit -m "feat(music-generation): add OpenTelemetry tracing module"
```

---

### Task 17: Update Main with Metrics and Tracing

**Files:**
- Modify: `services/music-generation/main.py:1-50`

**Step 1: Add imports**

Find the imports section and add:
```python
from metrics import generations_total, generation_duration
from tracing import setup_telemetry, instrument_fastapi
```

**Step 2: Add telemetry to lifespan**

Find the `lifespan` function and add after `logger.info`:
```python
# Initialize telemetry
tracer = setup_telemetry(settings.service_name, settings.otlp_endpoint)
```

**Step 3: Add instrumentation after app creation**

Find `app = FastAPI(...)` and add after:
```python
# Instrument FastAPI
instrument_fastapi(app)
```

**Step 4: Update metrics in generate endpoint**

Find the generate function and update metrics recording:
```python
# Record metrics
generations_total.labels(
    model=request.model.value,
    status="success"
).inc()
generation_duration.labels(
    model=request.model.value
).observe(generation_time)
```

**Step 5: Verify and commit**

```bash
git add services/music-generation/main.py
git commit -m "feat(music-generation): integrate metrics and tracing"
```

---

### Task 18: Final Verification and Push

**Step 1: Verify all files created**

```bash
# Check service structure
ls -la services/music-generation/
```

Expected: All Python files, Dockerfile, manifests, tests present

**Step 2: Count files**

```bash
find services/music-generation -type f | wc -l
```

Expected: 17+ files

**Step 3: Final commit with summary**

```bash
git add services/music-generation/ docs/api/music-generation.md
git commit -m "feat(music-generation): complete model integration service

Implementation complete:
- Model pool manager with MusicGen and ACE-Step support
- Async inference engine with cancellation
- Audio processing pipeline (normalize, trim, WAV conversion)
- FastAPI service with health, generate, models, metrics endpoints
- ARM64-optimized for Nvidia GB10 GPU
- Docker multi-stage build
- K8s deployment manifests
- Comprehensive testing suite
- Full documentation

This completes Phase C (Music Generation) of the feature completion plan.
Next: Phase D (Sentiment Agent ML Model)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Step 4: Push to GitHub**

```bash
git push origin main
```

---

## Success Criteria Verification

Run this final checklist:

```bash
echo "=== Music Generation Service Checklist ==="
echo ""
echo "1. Service Structure:"
ls services/music-generation/*.py 2>/dev/null | wc -l
echo "   Expected: 9 Python files"
echo ""
echo "2. Documentation:"
[ -f "services/music-generation/README.md" ] && echo "   ✓ Service README" || echo "   ✗ Missing"
[ -f "docs/api/music-generation.md" ] && echo "   ✓ API docs" || echo "   ✗ Missing"
echo ""
echo "3. Configuration:"
[ -f "services/music-generation/.env.example" ] && echo "   ✓ Env template" || echo "   ✗ Missing"
echo ""
echo "4. Deployment:"
[ -f "services/music-generation/Dockerfile" ] && echo "   ✓ Dockerfile" || echo "   ✗ Missing"
[ -f "services/music-generation/manifests/k8s.yaml" ] && echo "   ✓ K8s manifest" || echo "   ✗ Missing"
echo ""
echo "5. Testing:"
[ -f "services/music-generation/tests/test_music_generation.py" ] && echo "   ✓ Tests exist" || echo "   ✗ Missing"
echo ""
echo "=== Verification Complete ==="
```

---

*Implementation Plan - Music Generation Model Integration - March 7, 2026*

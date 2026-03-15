# LTX-2 + MiroFish Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Visual Services Layer for Project Chimera with LTX-2 video generation and MiroFish agent swarm simulation

**Architecture:** Hybrid Visual Services Layer (Visual Core + Simulation Engine + Content Orchestrator + Socials Agent) with local orchestration on DGX Spark and LTX-2 API video generation

**Tech Stack:** FastAPI, LTX-2 API, httpx, GraphRAG, Zep Cloud, FFmpeg, Kubernetes (K3s), Prometheus, OpenTelemetry

---

## Table of Contents

1. [Phase 1: Foundation - Visual Core Service](#phase-1-foundation---visual-core-service)
2. [Phase 2: Foundation - Sentiment Agent Enhancement](#phase-2-foundation---sentiment-agent-enhancement)
3. [Phase 3: Foundation - First Demo](#phase-3-foundation---first-demo)

---

## Phase 1: Foundation - Visual Core Service

### Task 1: Create Visual Core Service Structure

**Files:**
- Create: `services/visual-core/`
- Create: `services/visual-core/main.py`
- Create: `services/visual-core/config.py`
- Create: `services/visual-core/requirements.txt`
- Create: `services/visual-core/Dockerfile`
- Create: `services/visual-core/k8s-deployment.yaml`

**Step 1: Create directory structure**

Run:
```bash
mkdir -p services/visual-core/{tests,integration}
```

**Step 2: Create requirements.txt**

Create `services/visual-core/requirements.txt`:

```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
aiofiles==23.2.1
pillow==10.1.0
numpy==1.26.2
python-multipart==0.0.6
```

**Step 3: Create config.py**

Create `services/visual-core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Visual Core service configuration"""

    # Service
    service_name: str = "visual-core"
    log_level: str = "INFO"
    port: int = 8014

    # LTX-2 API
    ltx_api_key: str
    ltx_api_base: str = "https://api.ltx.video/v1"
    ltx_model_default: str = "ltx-2-3-pro"
    ltx_model_fast: str = "ltx-2-fast"

    # Processing
    max_concurrent_requests: int = 5
    cache_path: str = "/app/cache/videos"
    lora_storage_path: str = "/app/models/lora"

    # FFmpeg
    ffmpeg_path: str = "ffmpeg"

    # Integration
    sentiment_agent_url: str = "http://sentiment-agent:8004"
    simulation_engine_url: str = "http://simulation-engine:8016"

    # Observability
    otlp_endpoint: str = "http://jaeger:4317"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Step 4: Create main.py (FastAPI application)**

Create `services/visual-core/main.py`:

```python
"""Visual Core Service - LTX-2 Integration Hub"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel

from config import settings
from tracing import setup_tracing, instrument_fastapi
from metrics import (
    video_generation_duration,
    video_generation_total,
    cache_hits_total,
    cache_requests_total
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("Starting Visual Core Service...")
    setup_tracing(
        service_name=settings.service_name,
        service_version="1.0.0",
        otlp_endpoint=settings.otlp_endpoint
    )
    yield
    logger.info("Visual Core Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Visual Core Service",
    description="LTX-2 video generation integration hub",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Metrics Endpoints
# ============================================================================

@app.get("/health/live", response_model=dict)
async def liveness_probe():
    """Liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/ready", response_model=dict)
async def readiness_probe():
    """Readiness probe endpoint"""
    return {
        "status": "ready",
        "service": settings.service_name,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


# ============================================================================
# API Routes (to be implemented in subsequent tasks)
# ============================================================================

@app.post("/api/v1/generate/text")
async def text_to_video():
    """Generate video from text prompt"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower()
    )
```

**Step 5: Create tracing.py**

Create `services/visual-core/tracing.py`:

```python
"""OpenTelemetry tracing setup for Visual Core"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_tracing(
    service_name: str,
    service_version: str,
    otlp_endpoint: str
) -> trace.Tracer:
    """Setup OpenTelemetry tracing"""

    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version
    })

    exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True
    )

    provider = TracerProvider(
        resource=resource,
        span_processor=BatchSpanProcessor([exporter])
    )

    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)


def instrument_fastapi(app):
    """Instrument FastAPI with OpenTelemetry"""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument httpx (will be used when ltx_client.py is created)
    HTTPXClientInstrumentor.instrument()
```

**Step 6: Create metrics.py**

Create `services/visual-core/metrics.py`:

```python
"""Prometheus metrics for Visual Core"""

from prometheus_client import Counter, Histogram, Gauge

# Video generation metrics
video_generation_total = Counter(
    'visual_core_video_generation_total',
    'Total video generation requests',
    ['model', 'status', 'resolution']
)

video_generation_duration = Histogram(
    'visual_core_video_generation_duration_seconds',
    'Video generation duration',
    ['model', 'resolution'],
    buckets=[10, 30, 60, 120, 300, 600]
)

# Cache metrics
cache_hits_total = Counter(
    'visual_core_cache_hits_total',
    'Total cache hits'
)

cache_requests_total = Counter(
    'visual_core_cache_requests_total',
    'Total cache requests'
)

# Active generations gauge
active_generations = Gauge(
    'visual_core_active_generations',
    'Currently active video generations'
)
```

**Step 7: Create Dockerfile**

Create `services/visual-core/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/cache/videos /app/models/lora

# Set environment
ENV PYTHONPATH=/app
ENV PORT=8014

# Expose port
EXPOSE 8014

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8014/health/live || exit 1

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

CMD ["python", "main.py"]
```

**Step 8: Create Kubernetes deployment**

Create `services/visual-core/k8s-deployment.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: visual-core-config
  namespace: project-chimera
data:
  LOG_LEVEL: "INFO"
  PORT: "8014"
  LTX_API_BASE: "https://api.ltx.video/v1"
  LTX_MODEL_DEFAULT: "ltx-2-3-pro"
  MAX_CONCURRENT_REQUESTS: "5"
  CACHE_PATH: "/app/cache/videos"
  LORA_STORAGE_PATH: "/app/models/lora"
  OTLP_ENDPOINT: "http://jaeger:4317"
---
apiVersion: v1
kind: Secret
metadata:
  name: visual-core-secrets
  namespace: project-chimera
type: Opaque
stringData:
  LTX_API_KEY: "your-api-key-here"
---
apiVersion: v1
kind: Service
metadata:
  name: visual-core
  namespace: project-chimera
  labels:
    app: visual-core
spec:
  type: ClusterIP
  ports:
  - port: 8014
    targetPort: 8014
  selector:
    app: visual-core
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: visual-core
  namespace: project-chimera
  labels:
    app: visual-core
spec:
  replicas: 2
  selector:
    matchLabels:
      app: visual-core
  template:
    metadata:
      labels:
        app: visual-core
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: visual-core
        image: visual-core:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8014
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: visual-core-config
              key: LOG_LEVEL
        - name: PORT
          valueFrom:
            configMapKeyRef:
              name: visual-core-config
              key: PORT
        - name: LTX_API_KEY
          valueFrom:
            secretKeyRef:
              name: visual-core-secrets
              key: LTX_API_KEY
        - name: LTX_API_BASE
          valueFrom:
            configMapKeyRef:
              name: visual-core-config
              key: LTX_API_BASE
        - name: OTLP_ENDPOINT
          valueFrom:
            configMapKeyRef:
              name: visual-core-config
              key: OTLP_ENDPOINT
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8014
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8014
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: video-cache-pvc
  namespace: project-chimera
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: local-path
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: visual-core-hpa
  namespace: project-chimera
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: visual-core
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Step 9: Commit Visual Core structure**

Run:
```bash
cd services/visual-core
git add .
git commit -m "feat(scaffold): create Visual Core service structure

- Create FastAPI application skeleton
- Add configuration management with pydantic-settings
- Setup OpenTelemetry tracing
- Add Prometheus metrics
- Create Kubernetes deployment manifests
- Add Dockerfile with FFmpeg support

Relates to: Phase 1 Task 1 of LTX-2 integration plan"
```

Expected: Git commit successful

---

### Task 2: Implement LTX Client

**Files:**
- Create: `services/visual-core/ltx_client.py`
- Create: `services/visual-core/models.py`

**Step 1: Create models.py with data models**

Create `services/visual-core/models.py`:

```python
"""Pydantic models for Visual Core service"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Resolution(str, Enum):
    """Video resolution options"""
    HD = "1920x1080"
    FHD = "1920x1080"
    UHD = "3840x2160"
    FOUR_K = "3840x2160"


class LTXModel(str, Enum):
    """LTX-2 model options"""
    PRO = "ltx-2-3-pro"
    FAST = "ltx-2-fast"


class CameraMotion(str, Enum):
    """Camera motion options"""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACK_LEFT = "track_left"
    TRACK_RIGHT = "track_right"


class LTXVideoRequest(BaseModel):
    """Request for LTX-2 video generation"""

    prompt: str = Field(..., description="Text prompt for video generation")
    duration: int = Field(default=10, ge=6, le=20, description="Video duration in seconds")
    resolution: Resolution = Field(default=Resolution.HD, description="Video resolution")
    fps: int = Field(default=24, ge=24, le=50, description="Frames per second")
    model: LTXModel = Field(default=LTXModel.PRO, description="LTX-2 model to use")
    generate_audio: bool = Field(default=True, description="Generate synchronized audio")
    camera_motion: Optional[CameraMotion] = Field(None, description="Camera movement")
    lora_id: Optional[str] = Field(None, description="LoRA model to apply")


class LTXVideoResult(BaseModel):
    """Result from LTX-2 video generation"""

    video_id: str
    url: str
    duration: float
    resolution: str
    fps: int
    has_audio: bool
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoGenerationRequest(BaseModel):
    """API request for video generation"""

    prompt: str
    duration: int = 10
    resolution: str = "1920x1080"
    fps: int = 24
    model: str = "ltx-2-3-pro"
    generate_audio: bool = True
    camera_motion: Optional[str] = None
    lora_id: Optional[str] = None


class VideoGenerationResponse(BaseModel):
    """API response for video generation"""

    request_id: str
    video_id: str
    status: str
    url: Optional[str] = None
    error: Optional[str] = None


class BatchGenerationRequest(BaseModel):
    """Request for batch video generation"""

    requests: List[VideoGenerationRequest]


class BatchGenerationResponse(BaseModel):
    """Response for batch video generation"""

    batch_id: str
    requests: List[VideoGenerationResponse]
```

**Step 2: Create ltx_client.py**

Create `services/visual-core/ltx_client.py`:

```python
"""LTX-2 API client for video generation"""

import httpx
import asyncio
from typing import List, Optional
from datetime import datetime

from models import (
    LTXVideoRequest, LTXVideoResult, LTXModel, Resolution, CameraMotion
)
from metrics import video_generation_duration, active_generations


class LTXAPIClient:
    """Async client for LTX-2 API"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.ltx.video/v1",
        timeout: int = 300
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def text_to_video(
        self,
        prompt: str,
        duration: int = 10,
        resolution: str = "1920x1080",
        fps: int = 24,
        model: str = "ltx-2-3-pro",
        generate_audio: bool = True,
        camera_motion: Optional[str] = None,
        lora_path: Optional[str] = None
    ) -> LTXVideoResult:
        """Generate video from text prompt"""

        start_time = datetime.utcnow()
        active_generations.inc()

        try:
            payload = {
                "prompt": prompt,
                "duration": duration,
                "resolution": resolution,
                "fps": fps,
                "model": model
            }

            if generate_audio:
                payload["generate_audio"] = True

            if camera_motion:
                payload["camera_motion"] = camera_motion

            if lora_path:
                payload["lora_path"] = lora_path

            response = await self._client.post(
                "/text-to-video",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            duration_sec = (datetime.utcnow() - start_time).total_seconds()
            video_generation_duration.labels(
                model=model,
                resolution=resolution
            ).observe(duration_sec)

            return LTXVideoResult(
                video_id=data.get("id", ""),
                url=data.get("url", ""),
                duration=data.get("duration", 0.0),
                resolution=data.get("resolution", resolution),
                fps=data.get("fps", fps),
                has_audio=data.get("has_audio", False),
                status=data.get("status", "processing")
            )

        finally:
            active_generations.dec()

    async def batch_generate(
        self,
        requests: List[LTXVideoRequest],
        max_concurrent: int = 3
    ) -> List[LTXVideoResult]:
        """Generate multiple videos in parallel batches"""

        results = []

        # Process in batches
        for i in range(0, len(requests), max_concurrent):
            batch = requests[i:i + max_concurrent]

            # Parallel generation within batch
            tasks = [
                self.text_to_video(
                    prompt=req.prompt,
                    duration=req.duration,
                    resolution=req.resolution.value,
                    fps=req.fps,
                    model=req.model.value,
                    generate_audio=req.generate_audio,
                    camera_motion=req.camera_motion.value if req.camera_motion else None,
                    lora_path=req.lora_id
                )
                for req in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    # Log error but continue
                    print(f"Error in batch generation: {result}")
                elif result is not None:
                    results.append(result)

        return results


# Global client instance
_client: Optional[LTXAPIClient] = None


def get_ltx_client() -> LTXAPIClient:
    """Get or create global LTX client instance"""
    global _client
    if _client is None:
        from config import settings
        _client = LTXAPIClient(
            api_key=settings.ltx_api_key,
            api_base=settings.ltx_api_base
        )
    return _client
```

**Step 3: Update main.py to use LTX client**

Modify `services/visual-core/main.py`, add after imports:

```python
from models import VideoGenerationRequest, VideoGenerationResponse, BatchGenerationRequest
from ltx_client import get_ltx_client
import uuid
```

Add endpoint implementation in main.py:

```python
@app.post("/api/v1/generate/text", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """Generate video from text prompt"""

    request_id = str(uuid.uuid4())

    try:
        client = get_ltx_client()

        result = await client.text_to_video(
            prompt=request.prompt,
            duration=request.duration,
            resolution=request.resolution,
            fps=request.fps,
            model=request.model,
            generate_audio=request.generate_audio,
            camera_motion=request.camera_motion,
            lora_path=request.lora_id
        )

        return VideoGenerationResponse(
            request_id=request_id,
            video_id=result.video_id,
            status="complete",
            url=result.url
        )

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return VideoGenerationResponse(
            request_id=request_id,
            video_id="",
            status="error",
            error=str(e)
        )
```

**Step 4: Create tests directory and basic test**

Create `services/visual-core/tests/__init__.py`:

```python
"""Tests for Visual Core service"""
```

Create `services/visual-core/tests/test_ltx_client.py`:

```python
"""Tests for LTX client"""

import pytest
from unittest.mock import AsyncMock, patch
from ltx_client import LTXAPIClient
from models import LTXVideoRequest


@pytest.mark.asyncio
async def test_ltx_client_initialization():
    """Test LTX client initialization"""

    client = LTXAPIClient(
        api_key="test-key",
        api_base="https://api.test.com/v1"
    )

    assert client.api_key == "test-key"
    assert client.api_base == "https://api.test.com/v1"


@pytest.mark.asyncio
async def test_text_to_video_request_format():
    """Test that video generation request is formatted correctly"""

    request = LTXVideoRequest(
        prompt="Test video",
        duration=10,
        resolution=Resolution.HD,
        fps=24,
        model=LTXModel.PRO,
        generate_audio=True
    )

    assert request.prompt == "Test video"
    assert request.duration == 10
    assert request.resolution == Resolution.HD
    assert request.fps == 24
    assert request.model == LTXModel.PRO
```

**Step 5: Run tests to verify structure**

Run:
```bash
cd services/visual-core
python -m pytest tests/ -v
```

Expected: Tests pass (some may be mocked until LTX API is configured)

**Step 6: Commit LTX client implementation**

Run:
```bash
cd services/visual-core
git add ltx_client.py models.py main.py tests/
git commit -m "feat: implement LTX-2 API client

- Add LTXAPIClient with text-to-video generation
- Implement batch generation with concurrency control
- Add Pydantic models for requests/responses
- Update main.py with /api/v1/generate/text endpoint
- Add basic unit tests for LTX client
- Add Prometheus metrics for video generation

Relates to: Phase 1 Task 2 of LTX-2 integration plan"
```

Expected: Git commit successful

---

### Task 3: Implement Prompt Factory

**Files:**
- Create: `services/visual-core/prompt_factory.py`

**Step 1: Create prompt factory**

Create `services/visual-core/prompt_factory.py`:

```python
"""Prompt engineering templates and factory for LTX-2 video generation"""

from enum import Enum
from typing import Dict, Any, Optional


class VisualStyle(str, Enum):
    """Visual style templates for video generation"""
    CORPORATE_BRIEFING = "corporate_briefing"
    DOCUMENTARY = "documentary"
    SOCIAL_MEDIA = "social_media"
    NEWS_REPORT = "news_report"
    ANALYTICAL = "analytical"


class CameraMotion(str, Enum):
    """Camera motion options"""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACK_LEFT = "track_left"
    TRACK_RIGHT = "track_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"


PROMPT_TEMPLATES = {
    VisualStyle.CORPORATE_BRIEFING: """
Professional corporate video briefing. Clean, modern aesthetic.
Setting: Well-lit modern office or executive boardroom.
Style: Business professional, calm, authoritative.
Camera: Steady, controlled movements. Mostly static with slow dollies.
Colors: Blue, gray, white corporate palette.
Text overlays: Clean sans-serif fonts, minimal.
Mood: Confident, trustworthy, professional.
Audio: Clear, measured narration with subtle ambient music.
""",

    VisualStyle.DOCUMENTARY: """
Documentary-style visual storytelling.
Setting: Dynamic environments, real-world locations.
Style: Cinematic, observational, authentic.
Camera: Handheld feel, natural movement, environmental shots.
Colors: Naturalistic, slightly desaturated.
Text overlays: Documentary-style lower thirds.
Mood: Informative, engaging, human.
Audio: Narrator with environmental ambience.
""",

    VisualStyle.SOCIAL_MEDIA: """
Social media content visualization.
Setting: Digital interfaces, social feeds, comment threads.
Style: Fast-paced, energetic, modern.
Camera: Quick cuts, zooms, dynamic transitions.
Colors: Vibrant, platform-appropriate branding.
Text overlays: Social media UI elements, emojis.
Mood: Engaging, shareable, viral.
Audio: Upbeat, contemporary, social-friendly.
""",

    VisualStyle.NEWS_REPORT: """
Breaking news report style.
Setting: News studio, on-location reporting.
Style: Journalistic, urgent, credible.
Camera: Professional broadcast quality, static to slow movement.
Colors: News network branding (red, blue, white).
Text overlays: Breaking news banners, tickers.
Mood: Urgent, informative, authoritative.
Audio: News anchor delivery with urgency.
""",

    VisualStyle.ANALYTICAL: """
Data visualization and analysis presentation.
Setting: Abstract data environments, clean backgrounds.
Style: Precise, technical, informative.
Camera: Smooth pans across data visualizations.
Colors: Analytical palette with data-driven accent colors.
Text overlays: Charts, graphs, key metrics.
Mood: Objective, analytical, insightful.
Audio: Clear explanation with ambient underscore.
"""
}


class PromptFactory:
    """Factory for creating LTX-2 video prompts"""

    @staticmethod
    def build_prompt(
        narrative: str,
        style: VisualStyle,
        camera_motion: CameraMotion,
        duration: int,
        custom_elements: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build complete LTX-2 prompt from components"""

        # Get base style template
        style_template = PROMPT_TEMPLATES.get(style, "")

        # Build scene-specific prompt
        scene_prompt = f"""{style_template}

SCENE: {narrative}

DURATION: {duration} seconds
CAMERA: {camera_motion.value}
"""

        # Add custom elements if provided
        if custom_elements:
            for key, value in custom_elements.items():
                scene_prompt += f"{key.upper()}: {value}\n"

        return scene_prompt.strip()

    @staticmethod
    def enhance_prompt_for_video(
        base_prompt: str,
        video_context: Dict[str, Any]
    ) -> str:
        """Enhance prompt with video-specific context"""

        enhancements = []

        # Add resolution context
        if video_context.get("resolution") == "3840x2160":
            enhancements.append("4K ultra-high definition, maximum detail")

        # Add audio context
        if video_context.get("generate_audio"):
            enhancements.append("Synchronized audio included - visuals and audio must match perfectly")

        # Add motion context
        if video_context.get("camera_motion"):
            enhancements.append(f"Camera movement: {video_context['camera_motion']}")

        # Add continuity context
        if video_context.get("previous_scene"):
            enhancements.append(f"Continuity from previous scene: {video_context['previous_scene']}")

        if enhancements:
            return f"{base_prompt}\n\nTECHNICAL: {'; '.join(enhancements)}."

        return base_prompt

    @staticmethod
    def create_briefing_prompt(
        topic: str,
        sentiment_summary: str,
        key_insights: List[str],
        duration: int
    ) -> str:
        """Create prompt for executive briefing video"""

        insights_text = "\n".join([f"- {insight}" for insight in key_insights])

        prompt = f"""{PROMPT_TEMPLATES[VisualStyle.CORPORATE_BRIEFING]}

EXECUTIVE BRIEFING: {topic}

SENTIMENT ANALYSIS:
{sentiment_summary}

KEY INSIGHTS:
{insights_text}

DURATION: {duration} seconds

This is an executive briefing video. Maintain professional, authoritative tone throughout.
Focus on clarity, data-driven insights, and actionable recommendations.
"""

        return prompt.strip()
```

**Step 2: Add prompt factory to main.py imports**

Modify `services/visual-core/main.py`, add to imports:

```python
from prompt_factory import PromptFactory, VisualStyle, CameraMotion
```

**Step 3: Add prompt-based endpoint**

Add to `services/visual-core/main.py`:

```python
@app.post("/api/v1/generate/prompt", response_model=VideoGenerationResponse)
async def generate_from_prompt(
    prompt: str,
    style: str = "corporate_briefing",
    duration: int = 10,
    resolution: str = "1920x1080"
):
    """Generate video from enhanced prompt"""

    request_id = str(uuid.uuid4())

    try:
        # Build prompt using factory
        visual_style = VisualStyle(style)
        camera_motion = CameraMotion.STATIC

        enhanced_prompt = PromptFactory.build_prompt(
            narrative=prompt,
            style=visual_style,
            camera_motion=camera_motion,
            duration=duration
        )

        # Add technical enhancements
        enhanced_prompt = PromptFactory.enhance_prompt_for_video(
            enhanced_prompt,
            {
                "resolution": resolution,
                "generate_audio": True
            }
        )

        # Generate video
        client = get_ltx_client()
        result = await client.text_to_video(
            prompt=enhanced_prompt,
            duration=duration,
            resolution=resolution
        )

        return VideoGenerationResponse(
            request_id=request_id,
            video_id=result.video_id,
            status="complete",
            url=result.url
        )

    except Exception as e:
        logger.error(f"Prompt-based video generation failed: {e}")
        return VideoGenerationResponse(
            request_id=request_id,
            video_id="",
            status="error",
            error=str(e)
        )
```

**Step 4: Create tests for prompt factory**

Create `services/visual-core/tests/test_prompt_factory.py`:

```python
"""Tests for prompt factory"""

from prompt_factory import PromptFactory, VisualStyle, CameraMotion
import pytest


def test_build_prompt_corporate():
    """Test building corporate briefing prompt"""

    prompt = PromptFactory.build_prompt(
        narrative="Market analysis showing growth",
        style=VisualStyle.CORPORATE_BRIEFING,
        camera_motion=CameraMotion.DOLLY_IN,
        duration=15
    )

    assert "corporate" in prompt.lower()
    assert "dolly_in" in prompt.lower()
    assert "15 seconds" in prompt


def test_enhance_prompt_with_resolution():
    """Test prompt enhancement for 4K resolution"""

    base = "Test prompt"
    enhanced = PromptFactory.enhance_prompt_for_video(
        base,
        {"resolution": "3840x2160", "generate_audio": True}
    )

    assert "4K" in enhanced
    assert "ultra-high definition" in enhanced


def test_create_briefing_prompt():
    """Test creating executive briefing prompt"""

    prompt = PromptFactory.create_briefing_prompt(
        topic="Acme Corp Q3 Performance",
        sentiment_summary="Overall sentiment is positive with 75% favorable mentions",
        key_insights=["Revenue up 15%", "Market share expanded"],
        duration=90
    )

    assert "ACME CORP Q3 PERFORMANCE" in prompt
    assert "Revenue up 15%" in prompt
    assert "90 seconds" in prompt
```

**Step 5: Run prompt factory tests**

Run:
```bash
cd services/visual-core
python -m pytest tests/test_prompt_factory.py -v
```

Expected: All tests pass

**Step 6: Commit prompt factory**

Run:
```bash
cd services/visual-core
git add prompt_factory.py main.py tests/test_prompt_factory.py
git commit -m "feat: implement prompt factory for LTX-2 video generation

- Add PromptFactory with style templates (corporate, documentary, social media, news, analytical)
- Implement build_prompt() for narrative-to-video prompt conversion
- Implement enhance_prompt_for_video() for technical enhancements
- Add create_briefing_prompt() for executive briefing videos
- Add /api/v1/generate/prompt endpoint for enhanced prompt generation
- Add comprehensive unit tests for all prompt factory methods
- Update main.py imports and endpoints

Relates to: Phase 1 Task 3 of LTX-2 integration plan"
```

Expected: Git commit successful

---

### Task 4: Create Video Pipeline Module

**Files:**
- Create: `services/visual-core/video_pipeline.py`

**Step 1: Create video pipeline module**

Create `services/visual-core/video_pipeline.py`:

```python
"""Video processing pipeline with FFmpeg on ARM64"""

import asyncio
import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
import aiofiles


class VideoPipeline:
    """Video processing pipeline using FFmpeg"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    async def stitch_videos(
        self,
        video_urls: List[str],
        output_path: str,
        transitions: bool = True,
        transition_duration: float = 1.0
    ) -> str:
        """Stitch multiple videos together"""

        # Download videos locally
        local_paths = await self._download_videos(video_urls)

        # Create concat file
        concat_file = await self._create_concat_file(local_paths)

        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]

        # Execute
        await self._run_ffmpeg(cmd)

        # Cleanup
        await self._cleanup_files(local_paths + [concat_file])

        return output_path

    async def add_overlays(
        self,
        video_path: str,
        output_path: str,
        overlays: Dict[str, Any]
    ) -> str:
        """Add overlays to video (logos, captions, etc.)"""

        filter_complex = []

        # Logo overlay
        if overlays.get("logo"):
            filter_complex.append(
                f"[1:v]scale=100:-1[logo];[0:v][logo]overlay=10:10[video]"
            )

        # Captions
        if overlays.get("captions"):
            caption_text = overlays["captions"]
            filter_complex.append(
                f"[video]drawtext=text='{caption_text}':"
                f"fontsize=24:fontcolor=white:x=(w-tw)/2:y=h-50:text_align=center"
            )

        # Build command
        cmd = [
            self.ffmpeg_path,
            "-i", video_path
        ]

        # Add logo input if provided
        if overlays.get("logo"):
            cmd.extend(["-i", overlays["logo"]])

        cmd.extend([
            "-filter_complex", ",".join(filter_complex),
            "-c:a", "copy",
            output_path
        ])

        await self._run_ffmpeg(cmd)
        return output_path

    async def generate_thumbnail(
        self,
        video_path: str,
        timestamp: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """Generate thumbnail from video"""

        if output_path is None:
            output_path = video_path.replace(".mp4", "_thumb.jpg")

        cmd = [
            self.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-q:v", "2",
            output_path
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def _run_ffmpeg(self, cmd: List[str]) -> None:
        """Execute FFmpeg command asynchronously"""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

    async def _download_videos(self, urls: List[str]) -> List[str]:
        """Download videos from URLs to local temp storage"""

        paths = []
        async with httpx.AsyncClient() as client:
            for url in urls:
                response = await client.get(url)
                response.raise_for_status()

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
                    await aiofiles.os.write(f.fileno(), response.content)
                    paths.append(f.name)

        return paths

    async def _create_concat_file(self, paths: List[str]) -> str:
        """Create FFmpeg concat file"""

        concat_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".txt"
        )

        for path in paths:
            concat_file.write(f"file '{path}'\n")

        concat_file.close()
        return concat_file.name

    async def _cleanup_files(self, paths: List[str]) -> None:
        """Clean up temporary files"""
        for path in paths:
            try:
                os.unlink(path)
            except OSError:
                pass
```

**Step 2: Add video pipeline to main.py**

Update `services/visual-core/main.py`, add to imports:

```python
from video_pipeline import VideoPipeline
```

Initialize pipeline:

```python
# At module level, after settings
video_pipeline = VideoPipeline(ffmpeg_path=settings.ffmpeg_path)
```

Add stitching endpoint:

```python
@app.post("/api/v1/video/stitch")
async def stitch_videos(
    video_urls: List[str],
    transitions: bool = True,
    output_filename: Optional[str] = None
):
    """Stitch multiple videos together"""

    try:
        if output_filename is None:
            output_filename = f"stitched_{uuid.uuid4().hex}.mp4"

        output_path = os.path.join(settings.cache_path, output_filename)

        result_path = await video_pipeline.stitch_videos(
            video_urls=video_urls,
            output_path=output_path,
            transitions=transitions
        )

        return {"status": "success", "url": result_path}

    except Exception as e:
        logger.error(f"Video stitching failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3: Test video pipeline**

Create `services/visual-core/tests/test_video_pipeline.py`:

```python
"""Tests for video pipeline"""

import pytest
from video_pipeline import VideoPipeline
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_download_videos():
    """Test video downloading"""

    pipeline = VideoPipeline()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.content = b"fake video content"

        mock_get.return_value = mock_response

        urls = ["http://example.com/video1.mp4"]
        paths = await pipeline._download_videos(urls)

        assert len(paths) == 1
        assert paths[0].endswith(".mp4")
```

**Step 4: Commit video pipeline**

Run:
```bash
cd services/visual-core
git add video_pipeline.py main.py tests/test_video_pipeline.py
git commit -m "feat: implement FFmpeg video processing pipeline

- Create VideoPipeline class for video operations
- Implement stitch_videos() for combining multiple clips
- Implement add_overlays() for logos and captions
- Implement generate_thumbnail() for preview images
- Add /api/v1/video/stitch endpoint to main.py
- Use ARM64-compatible FFmpeg commands
- Add comprehensive unit tests
- Handle temporary file cleanup

Relates to: Phase 1 Task 4 of LTX-2 integration plan"
```

---

### Task 5: Deploy Visual Core Service

**Files:**
- Modify: `services/visual-core/k8s-deployment.yaml`

**Step 1: Set LTX API key**

Run:
```bash
# Create secret for LTX API key
kubectl create secret generic visual-core-secrets \
  --from-literal=LTX_API_KEY='your-api-key-here' \
  -n project-chimera
```

Expected: Secret created

**Step 2: Build Docker image**

Run:
```bash
cd services/visual-core
docker build -t visual-core:latest .
```

Expected: Docker image builds successfully

**Step 3: Deploy to Kubernetes**

Run:
```bash
kubectl apply -f services/visual-core/k8s-deployment.yaml
```

Expected:
- ConfigMap created
- Secret created
- Service created
- Deployment created
- PVCs created
- HPA created

**Step 4: Verify deployment**

Run:
```bash
kubectl get pods -n project-chimera -l app=visual-core
kubectl get svc -n project-chimera -l app=visual-core
```

Expected: Pods are Running, Service is created

**Step 5: Test health endpoints**

Run:
```bash
kubectl exec -n project-chimera deployment/visual-core -- curl -s http://localhost:8014/health/live
kubectl exec -n project-chimera deployment/visual-core -- curl -s http://localhost:8014/health/ready
```

Expected: Both return 200 OK with status "alive"/"ready"

**Step 6: Commit deployment configuration**

Run:
```bash
cd services/visual-core
git add k8s-deployment.yaml
git commit -m "chore(deploy): add Kubernetes deployment manifests for Visual Core

- Add ConfigMap for environment configuration
- Add Secret for LTX API key
- Add Service for cluster access
- Add Deployment with security contexts (runAsNonRoot, seccomp)
- Add PersistentVolumeClaims for cache and LoRA storage
- Add HorizontalPodAutoscaler (2-8 replicas)
- Configure resource limits and requests
- Add health and readiness probes
- Add documentation in deployment file

Relates to: Phase 1 Task 5 of LTX-2 integration plan"
```

---

## Phase 2: Foundation - Sentiment Agent Enhancement

### Task 6: Add Video Module to Sentiment Agent

**Files:**
- Create: `services/sentiment-agent/src/sentiment_agent/video/`
- Create: `services/sentiment-agent/src/sentiment_agent/video/__init__.py`
- Create: `services/sentiment-agent/src/sentiment_agent/video/briefing.py`
- Create: `services/sentiment-agent/src/sentiment_agent/video/integration.py`
- Modify: `services/sentiment-agent/src/sentiment_agent/main.py`
- Modify: `services/sentiment-agent/k8s-deployment.yaml`
- Create: `services/sentiment-agent/tests/test_video.py`

**Step 1: Create video module structure**

Run:
```bash
mkdir -p services/sentiment-agent/src/sentiment_agent/video
```

**Step 2: Create video __init__.py**

Create `services/sentiment-agent/src/sentiment_agent/video/__init__.py`:

```python
"""Video briefing capabilities for Sentiment Agent"""
```

**Step 3: Create briefing.py**

Create `services/sentiment-agent/src/sentiment_agent/video/briefing.py`:

```python
"""Video briefing generation from sentiment analysis"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import httpx
import asyncio

logger = logging.getLogger(__name__)


class SentimentBriefingGenerator:
    """Generate video briefings from sentiment analysis"""

    def __init__(self, visual_core_url: str):
        self.visual_core_url = visual_core_url

    async def create_briefing(
        self,
        topic: str,
        timeframe: str,
        style: str = "corporate_briefing",
        duration: int = 90
    ) -> Dict[str, Any]:
        """Create sentiment briefing video"""

        # 1. Get sentiment data
        sentiment_data = await self._get_sentiment_data(topic, timeframe)

        # 2. Analyze sentiment trends
        trend_analysis = await self._analyze_trends(sentiment_data)

        # 3. Extract key insights
        key_insights = await self._extract_insights(sentiment_data, trend_analysis)

        # 4. Generate narrative
        narrative = await self._generate_narrative(
            topic=topic,
            sentiment_data=sentiment_data,
            insights=key_insights
        )

        # 5. Generate video via Visual Core
        video_url = await self._generate_video(
            narrative=narrative,
            style=style,
            duration=duration
        )

        # 6. Generate summary
        summary = await self._generate_summary(sentiment_data, key_insights)

        return {
            "briefing_id": str(datetime.utcnow().timestamp()),
            "topic": topic,
            "video_url": video_url,
            "summary": summary,
            "sentiment_data": sentiment_data,
            "trend_analysis": trend_analysis,
            "created_at": datetime.utcnow().isoformat()
        }

    async def _get_sentiment_data(
        self,
        topic: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """Get sentiment analysis data"""
        # Call existing sentiment analysis endpoints
        # This is a placeholder - actual implementation would call existing agent methods

        return {
            "topic": topic,
            "timeframe": timeframe,
            "overall_sentiment": 0.65,
            "sentiment_trend": "positive",
            "mention_count": 1250,
            "sentiment_distribution": {
                "positive": 0.45,
                "neutral": 0.35,
                "negative": 0.20
            }
        }

    async def _analyze_trends(
        self,
        sentiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze sentiment trends over time"""

        return {
            "direction": "improving",
            "velocity": 0.05,
            "inflection_points": []
        }

    async def _extract_insights(
        self,
        sentiment_data: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract key insights from sentiment data"""

        return [
            "Overall positive sentiment of 65%",
            "12% improvement over previous period",
            "Peak positive sentiment on weekends"
        ]

    async def _generate_narrative(
        self,
        topic: str,
        sentiment_data: Dict[str, Any],
        insights: List[str]
    ) -> str:
        """Generate narrative script for video"""

        return f"""
Sentiment analysis for {topic} shows positive momentum.
With an overall sentiment score of {sentiment_data['overall_sentiment']:.0%},
the brand is receiving favorable engagement across monitored platforms.

Key insights include:
{chr(10).join(insights)}

This positive trend suggests effective brand communication and audience engagement.
        """.strip()

    async def _generate_video(
        self,
        narrative: str,
        style: str,
        duration: int
    ) -> str:
        """Generate video via Visual Core"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.visual_core_url}/api/v1/generate/prompt",
                json={
                    "prompt": narrative,
                    "duration": duration,
                    "style": style,
                    "resolution": "1920x1080",
                    "generate_audio": True
                },
                timeout=600  # 10 minutes
            )
            response.raise_for_status()

            result = response.json()
            return result["url"]

    async def _generate_summary(
        self,
        sentiment_data: Dict[str, Any],
        insights: List[str]
    ) -> str:
        """Generate text summary"""

        return f"""
Sentiment Analysis Summary

Topic: {sentiment_data['topic']}
Timeframe: {sentiment_data['timeframe']}
Overall Sentiment: {sentiment_data['overall_sentiment']:.0%} ({sentiment_data['sentiment_trend']})

Key Insights:
{chr(10).join(f"- {insight}" for insight in insights)}

Recommendation: Continue current engagement strategy.
        """.strip()
```

**Step 4: Create integration.py**

Create `services/sentiment-agent/src/sentiment_agent/video/integration.py`:

```python
"""Integration with Visual Core service"""

import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VisualCoreClient:
    """Client for Visual Core service integration"""

    def __init__(self, base_url: str = "http://visual-core:8014"):
        self.base_url = base_url
        self.timeout = 600

    async def generate_video(
        self,
        narrative: str,
        style: str = "corporate_briefing",
        duration: int = 90
    ) -> str:
        """Generate video using Visual Core"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/generate/prompt",
                json={
                    "prompt": narrative,
                    "duration": duration,
                    "style": style
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result["url"]
```

**Step 5: Update main.py with video endpoints**

Modify `services/sentiment-agent/src/sentiment_agent/main.py`, add imports:

```python
from video.briefing import SentimentBriefingGenerator
from video.integration import VisualCoreClient
```

Initialize at module level:

```python
# After existing initialization
try:
    visual_core_client = VisualCoreClient(
        base_url=os.getenv("VISUAL_CORE_URL", "http://visual-core:8014")
    )
    briefing_generator = SentimentBriefingGenerator(
        visual_core_url=os.getenv("VISUAL_CORE_URL", "http://visual-core:8014")
    )
    logger.info("Video capabilities initialized")
except Exception as e:
    logger.warning(f"Video capabilities not available: {e}")
    visual_core_client = None
    briefing_generator = None
```

Add endpoints in main.py:

```python
@app.post("/api/v1/video/briefing")
async def create_sentiment_briefing(
    topic: str,
    timeframe: str = "7d",
    style: str = "corporate_briefing",
    duration: int = 90
):
    """Create sentiment briefing video"""

    if briefing_generator is None:
        raise HTTPException(
            status_code=503,
            detail="Video capabilities not available"
        )

    try:
        result = await briefing_generator.create_briefing(
            topic=topic,
            timeframe=timeframe,
            style=style,
            duration=duration
        )
        return result

    except Exception as e:
        logger.error(f"Failed to create sentiment briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/video/{briefing_id}")
async def get_briefing_status(briefing_id: str):
    """Get briefing generation status"""
    # Placeholder - would check actual status
    return {
        "briefing_id": briefing_id,
        "status": "processing",
        "progress": 50
    }
```

**Step 6: Update deployment configuration**

Modify `services/sentiment-agent/k8s-deployment.yaml`, add to ConfigMap data:

```yaml
  VISUAL_CORE_URL: "http://visual-core:8014"
  ENABLE_VIDEO_BRIEFING: "true"
  ENABLE_VIDEO_TRENDS: "true"
  DEFAULT_BRIEFING_DURATION: "90"
  DEFAULT_BRIEFING_STYLE: "corporate-briefing"
```

**Step 7: Create tests**

Create `services/sentiment-agent/tests/test_video.py`:

```python
"""Tests for sentiment agent video capabilities"""

import pytest
from unittest.mock import AsyncMock, patch
from video.briefing import SentimentBriefingGenerator


@pytest.mark.asyncio
async def test_sentiment_briefing_generation():
    """Test sentiment briefing generation"""

    generator = SentimentBriefingGenerator(
        visual_core_url="http://visual-core:8014"
    )

    with patch.object(generator, "_generate_video", return_value="http://example.com/video.mp4"):
        result = await generator.create_briefing(
            topic="Test Brand",
            timeframe="7d",
            style="corporate_briefing",
            duration=60
        )

        assert "briefing_id" in result
        assert result["video_url"] == "http://example.com/video.mp4"
        assert result["topic"] == "Test Brand"
```

**Step 8: Commit sentiment agent video enhancement**

Run:
```bash
cd services/sentiment-agent
git add src/sentiment_agent/video/ tests/test_video.py src/sentiment_agent/main.py k8s-deployment.yaml
git commit -m "feat: add video briefing capabilities to Sentiment Agent

- Create video module for briefing generation
- Add SentimentBriefingGenerator class
- Add VisualCoreClient for service integration
- Implement /api/v1/video/briefing endpoint
- Implement /api/v1/video/{briefing_id} status endpoint
- Update k8s deployment with VISUAL_CORE_URL config
- Add comprehensive unit tests
- Integrate with PromptFactory via Visual Core

Relates to: Phase 2 Task 6 of LTX-2 integration plan"
```

---

## Phase 3: Foundation - First Demo

### Task 7: Create End-to-End Demo

**Files:**
- Create: `demos/visual-intelligence-demo.py`
- Create: `demos/demo-data.py`

**Step 1: Create demos directory**

Run:
```bash
mkdir -p demos
```

**Step 2: Create demo data module**

Create `demos/demo-data.py`:

```python
"""Demo data for Visual Intelligence Reports"""

DEMO_SCENARIOS = {
    "tech_brand_sentiment": {
        "topic": "TechGiant Inc. Q1 Brand Sentiment Analysis",
        "timeframe": "30d",
        "style": "corporate_briefing",
        "duration": 90,
        "description": "Executive briefing on TechGiant brand sentiment"
    },
    "market_trend_analysis": {
        "topic": "AI Chip Market Trends - Q1 2026",
        "timeframe": "90d",
        "style": "analytical",
        "duration": 120,
        "description": "Comprehensive market trend analysis video"
    }
}


DEMO_SENTIMENT_DATA = {
    "tech_brand_sentiment": {
        "overall_sentiment": 0.72,
        "sentiment_trend": "improving",
        "mention_count": 5420,
        "sentiment_distribution": {
            "positive": 0.58,
            "neutral": 0.31,
            "negative": 0.11
        },
        "key_insights": [
            "22% increase in positive sentiment YoY",
            "Strong engagement on product announcement posts",
            "Influencer mentions driving positive sentiment",
            "Low negative sentiment compared to competitors"
        ],
        "trend_analysis": {
            "direction": "improving",
            "velocity": 0.08,
            "inflection_points": [
                "Product launch - March 15",
                "CEO interview - March 22"
            ]
        }
    }
}
```

**Step 3: Create demo script**

Create `demos/visual-intelligence-demo.py`:

```python
#!/usr/bin/env python3
"""Demo script for Visual Intelligence Report generation"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Service endpoints
SENTIMENT_AGENT_URL = "http://localhost:8004"
VISUAL_CORE_URL = "http://localhost:8014"


async def create_visual_intelligence_report(
    scenario: dict
) -> dict:
    """Create complete visual intelligence report"""

    print(f"Creating Visual Intelligence Report: {scenario['topic']}")
    print(f"Timeframe: {scenario['timeframe']}")
    print(f"Style: {scenario['style']}")
    print(f"Duration: {scenario['duration']}s")
    print()

    # Step 1: Create sentiment briefing
    print("Step 1: Generating sentiment briefing video...")
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SENTIMENT_AGENT_URL}/api/v1/video/briefing",
            json={
                "topic": scenario["topic"],
                "timeframe": scenario["timeframe"],
                "style": scenario["style"],
                "duration": scenario["duration"]
            },
            timeout=600
        )
        response.raise_for_status()
        briefing = response.json()

    briefing_time = time.time() - start_time
    print(f"✓ Briefing generated in {briefing_time:.1f}s")
    print(f"  Briefing ID: {briefing['briefing_id']}")
    print(f"  Video URL: {briefing['video_url']}")
    print()

    # Step 2: Generate PDF summary
    print("Step 2: Generating PDF summary...")
    # Placeholder - would generate actual PDF
    pdf_url = briefing["video_url"].replace(".mp4", "_summary.pdf")
    print(f"✓ PDF summary available")
    print()

    return {
        "report_id": briefing["briefing_id"],
        "scenario": scenario,
        "video_url": briefing["video_url"],
        "pdf_url": pdf_url,
        "generation_time": briefing_time,
        "created_at": datetime.utcnow().isoformat()
    }


async def run_demo():
    """Run the visual intelligence demo"""

    print("="*60)
    print("Visual Intelligence Report Demo")
    print("="*60)
    print()

    # Check service availability
    print("Checking service availability...")

    try:
        async with httpx.AsyncClient() as client:
            # Check sentiment agent
            sentiment_health = await client.get(f"{SENTIMENT_AGENT_URL}/health")
            print(f"✓ Sentiment Agent: {sentiment_health.status_code}")

            # Check visual core
            visual_health = await client.get(f"{VISUAL_CORE_URL}/health/live")
            print(f"✓ Visual Core: {visual_health.status_code}")

    except Exception as e:
        print(f"✗ Service check failed: {e}")
        return

    print()

    # Run demo scenarios
    from demo_data import DEMO_SCENARIOS, DEMO_SENTIMENT_DATA

    scenario = DEMO_SCENARIOS["tech_brand_sentiment"]

    result = await create_visual_intelligence_report(scenario)

    print()
    print("="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print()
    print(f"Report ID: {result['report_id']}")
    print(f"Video URL: {result['video_url']}")
    print(f"Generation Time: {result['generation_time']:.1f}s")
    print()
    print("To view the video:")
    print(f"  ffprobe {result['video_url']}")
    print()
    print("To redeploy:")
    print("  kubectl rollout restart deployment/sentiment-agent -n project-chimera")


if __name__ == "__main__":
    asyncio.run(run_demo())
```

**Step 4: Make demo script executable**

Run:
```bash
chmod +x demos/visual-intelligence-demo.py
```

**Step 5: Run demo to verify end-to-end flow**

Run:
```bash
# Ensure services are running
kubectl get pods -n project-chimera | grep -E "(sentiment|visual-core)"

# Run demo
cd demos
python3 visual-intelligence-demo.py
```

Expected: Complete demo runs successfully with video generated

**Step 6: Create demo documentation**

Create `demos/README.md`:

```markdown
# Visual Intelligence Report Demo

## Overview

This demo showcases the Visual Intelligence Report capability, generating executive video briefings from sentiment analysis.

## Prerequisites

1. All services running:
   ```bash
   kubectl get pods -n project-chimera
   ```

2. Services healthy:
   - sentiment-agent (port 8004)
   - visual-core (port 8014)

3. LTX-2 API key configured in visual-core-secrets

## Running the Demo

### Quick Start

```bash
cd demos
python3 visual-intelligence-demo.py
```

### What to Expect

The demo will:
1. Check service availability
2. Generate sentiment briefing video
3. Return video URL and report metadata

### Demo Scenario

**Topic:** "TechGiant Inc. Q1 Brand Sentiment Analysis"

**Output:**
- 90-second executive briefing video
- PDF summary report
- Generation metrics

### Verification

To verify the generated video:

```bash
# Download and play video
curl -O demo.mp4 {VIDEO_URL}
ffprobe demo.mp4
vlc demo.mp4  # or your preferred player
```

### Troubleshooting

**Services not responding:**
```bash
kubectl get pods -n project-chimera
kubectl logs -n project-chimera deployment/sentiment-agent
kubectl logs -n project-chimera deployment/visual-core
```

**Video generation failed:**
```bash
# Check Visual Core logs
kubectl logs -n project-chimera deployment/visual-core | grep ERROR
```

**API key issues:**
```bash
kubectl get secret visual-core-secrets -n project-chimera
```
```

**Step 7: Commit demo files**

Run:
```bash
cd demos
git add .
git commit -m "feat(demos): add Visual Intelligence Report demo

- Create visual-intelligence-demo.py script for end-to-end demo
- Add demo-data.py with sample scenarios
- Add README.md with demo documentation
- Include troubleshooting guide
- Showcase complete Visual Intelligence Report generation flow
- Demo uses TechGiant brand sentiment analysis scenario

Relates to: Phase 3 Task 7 of LTX-2 integration plan"
```

**Step 8: Update CHANGELOG.md**

Add to `CHANGELOG.md` under `[Unreleased]` section:

```yaml
## [Unreleased]

### Added
- **Visual Services Layer** - New video intelligence capability
  - Visual Core service (port 8014) - LTX-2 integration hub
  - Sentiment Agent enhanced with video briefing endpoints
  - First Visual Intelligence Report demo
  - End-to-end video generation pipeline from sentiment analysis
  - Prompt engineering templates for corporate, documentary, social media styles
  - FFmpeg video processing pipeline for ARM64 (DGX Spark optimized)
  - Kubernetes deployment with security contexts and autoscaling (2-8 replicas)
```

---

## Summary

This implementation plan covers **Phase 1: Foundation** of the LTX-2 + MiroFish integration:

- ✅ Visual Core Service structure and configuration
- ✅ LTX-2 API client implementation
- ✅ Prompt factory with style templates
- ✅ Video processing pipeline with FFmpeg
- ✅ Kubernetes deployment manifests
- ✅ Sentiment Agent video enhancement
- ✅ End-to-end demo with Visual Intelligence Report

**Next Phases** (in subsequent implementation plans):
- Phase 2: Social Intelligence (Socials Agent)
- Phase 3: Simulation Engine (MiroFish)
- Phase 4: Content Orchestration
- Phase 5: Revenue Launch

**Success Criteria for Phase 1:**
- [ ] Visual Core service deployed and healthy
- [ ] LTX-2 API integration working
- [ ] First video generated successfully
- [ ] Sentiment Agent video briefing working
- [ ] End-to-end demo runs successfully
- [ ] Demo video shows clear value proposition

---

**Implementation Notes:**

1. **LTX-2 API Key:** Must be obtained from https://console.ltx.video before deployment
2. **ARM64 FFmpeg:** Pre-built binary included or compile from source with NVENC support
3. **DGX Spark:** 128GB unified memory enables local agent orchestration, video generation via API
4. **First Video Generation:** Expect 2-5 minute latency for 60s video
5. **Scaling:** Visual Core scales to 8 replicas for concurrent generation

---

**Ready for Execution**

This plan is now ready for implementation using `superpowers:executing-plans`.

**Two execution options available:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task with code review
2. **Parallel Session (separate)** - Open new session with executing-plans for batch execution

**Which approach would you like?**

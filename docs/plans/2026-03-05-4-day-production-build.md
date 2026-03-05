# 4-Day Production Build Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build 10 fully functional AI/Platform services in 4 days using template-based factory approach, production-ready for Monday March 10 student demo.

**Architecture:** Create universal service template with FastAPI, OpenTelemetry tracing, Prometheus metrics, then instantiate 10 services (OpenClaw Orchestrator + 6 AI agents + Operator Console + 2 platform services) each with unique business logic, Docker support, and comprehensive tests.

**Tech Stack:** FastAPI, Python 3.12, OpenTelemetry, Prometheus, Docker (ARM64), Kubernetes, Kafka, Redis, GLM 4.7 API, Local LLMs (Whisper, DistilBERT), Nvidia DGX Spark GB10.

---

## Day 1: Thursday, March 6 - Foundation & Template

### Task 1: Create Shared Service Template

**Files:**
- Create: `services/shared/template/main.py`
- Create: `services/shared/template/config.py`
- Create: `services/shared/template/models.py`
- Create: `services/shared/template/metrics.py`
- Create: `services/shared/template/tracing.py`
- Create: `services/shared/template/tests/test_main.py`
- Create: `services/shared/template/tests/conftest.py`
- Create: `services/shared/template/Dockerfile`
- Create: `services/shared/template/requirements.txt`
- Create: `services/shared/template/README.md`

**Step 1: Write the health check tests**

```python
# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_live(client):
    """Test liveness endpoint returns 200"""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

def test_health_ready(client):
    """Test readiness endpoint returns 200"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert "status" in response.json()

def test_metrics_endpoint(client):
    """Test metrics endpoint returns prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
```

**Step 2: Run tests to verify they fail**

```bash
cd services/shared/template
pytest tests/test_main.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'main'"

**Step 3: Create main.py with FastAPI app and health endpoints**

```python
# main.py
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service Template",
    description="Production-ready service template for Project Chimera",
    version="1.0.0"
)

@app.get("/health/live")
async def liveness():
    """Basic liveness check - is the process running?"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Readiness check - can we handle requests?"""
    # Override in implementations to check dependencies
    return {"status": "ready", "checks": {}}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.on_event("startup")
async def startup_event():
    logger.info("Service starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Service shutting down")
```

**Step 4: Run tests to verify they pass**

```bash
cd services/shared/template
pytest tests/test_main.py -v
```
Expected: 3 PASS

**Step 5: Create tracing.py with OpenTelemetry setup**

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)

def setup_telemetry(service_name: str) -> trace.Tracer:
    """Set up OpenTelemetry tracing for the service"""

    # Create resource with service name
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "project-chimera"
    })

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Set up OTLP exporter (for Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )

    # Add exporter to provider
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(f"Telemetry initialized for {service_name}")

    return trace.get_tracer(__name__)

def instrument_fastapi(app, service_name: str):
    """Instrument FastAPI app with automatic tracing"""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
    logger.info(f"FastAPI instrumented for {service_name}")

def add_span_attributes(attributes: dict):
    """Add custom attributes to current span"""
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)

def record_error(exception: Exception):
    """Record exception in current span"""
    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception)
```

**Step 6: Create metrics.py with Prometheus metrics**

```python
# metrics.py
from prometheus_client import Counter, Histogram, Info
import time

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics (to be extended by services)
business_metrics = Counter(
    'business_operations_total',
    'Total business operations',
    ['operation', 'status']
)

# Service info
service_info = Info(
    'service',
    'Service information'
)

def init_service_info(service_name: str, version: str = "1.0.0"):
    """Initialize service info metric"""
    service_info.info({
        'name': service_name,
        'version': version
    })

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    request_count.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()
    request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

def record_business_operation(operation: str, status: str = "success"):
    """Record business operation metric"""
    business_metrics.labels(
        operation=operation,
        status=status
    ).inc()
```

**Step 7: Create config.py with environment-based configuration**

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Service configuration from environment variables"""

    # Service
    service_name: str = "service-template"
    service_version: str = "1.0.0"
    port: int = 8000
    debug: bool = False

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Kafka
    kafka_brokers: str = "localhost:9092"
    kafka_topic: str = "chimera-events"

    # AI Models
    glm_api_key: Optional[str] = None
    glm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"
    local_model_path: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    """Get service settings"""
    return Settings()
```

**Step 8: Create models.py with base Pydantic models**

```python
# models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    checks: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GenerateRequest(BaseModel):
    """Base generation request"""
    prompt: str = Field(..., min_length=1, description="Input prompt")
    max_tokens: Optional[int] = Field(500, ge=1, le=4096, description="Max tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")

class GenerateResponse(BaseModel):
    """Generation response"""
    text: str
    tokens_used: int
    model: str
    duration_ms: int
```

**Step 9: Create conftest.py for test fixtures**

```python
# tests/conftest.py
import pytest
import os
from fastapi.testclient import TestClient

@pytest.fixture
def test_env():
    """Set test environment variables"""
    os.environ["PORT"] = "8001"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield

@pytest.fixture
def settings(test_env):
    """Get test settings"""
    from config import get_settings
    return get_settings()
```

**Step 10: Create Dockerfile (ARM64)**

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for ARM64
RUN apt-get update && apt-get install -y \
    gcc \
    gcc-aarch64-linux-gnu \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 11: Create requirements.txt**

```text
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# OpenTelemetry
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-exporter-otlp>=1.21.0

# Prometheus
prometheus-client>=0.19.0

# Async
httpx>=0.25.2
aiohttp>=3.9.0

# Kafka
aiokafka>=0.9.0

# Redis
redis>=5.0.0

# AI/ML
transformers>=4.36.0
torch>=2.1.0
openai>=1.6.0

# Utilities
python-dotenv>=1.0.0
structlog>=2.4.0
```

**Step 12: Create README.md**

```markdown
# Service Template

Production-ready service template for Project Chimera.

## Features

- FastAPI with async support
- OpenTelemetry tracing (Jaeger)
- Prometheus metrics
- Health checks
- ARM64 Docker support
- Comprehensive tests

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Build Docker image
docker build -t service-template .

# Run in Docker
docker run -p 8000:8000 service-template
```

## Environment Variables

See `config.py` for full list.

## Endpoints

- `GET /health/live` - Liveness check
- `GET /health/ready` - Readiness check
- `GET /metrics` - Prometheus metrics
```

**Step 13: Commit template**

```bash
cd /home/ranj/Project_Chimera
git add services/shared/template/
git commit -m "feat(services): add production-ready service template

- FastAPI with health endpoints
- OpenTelemetry tracing setup
- Prometheus metrics
- Environment-based configuration
- ARM64 Dockerfile
- Test framework with fixtures
- Comprehensive README"
```

---

### Task 2: Build OpenClaw Orchestrator (Port 8000)

**Files:**
- Modify: `services/openclaw-orchestrator/main.py` (create new)
- Create: `services/openclaw-orchestrator/config.py`
- Create: `services/openclaw-orchestrator/models.py`
- Create: `services/openclaw-orchestrator/skill_router.py`
- Create: `services/openclaw-orchestrator/agent_coordinator.py`
- Create: `services/openclaw-orchestrator/event_manager.py`
- Create: `services/openclaw-orchestrator/tests/test_main.py`
- Create: `services/openclaw-orchestrator/tests/test_skill_router.py`
- Create: `services/openclaw-orchestrator/Dockerfile`
- Create: `services/openclaw-orchestrator/requirements.txt`

**Step 1: Write tests for orchestrator endpoints**

```python
# tests/test_main.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

def test_health_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

def test_health_ready_checks_dependencies(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "agents" in data["checks"]

def test_orchestrate_dialogue(client, mock_agent_response):
    response = client.post(
        "/v1/orchestrate",
        json={
            "skill": "dialogue_generator",
            "input": {"prompt": "Hello world"}
        }
    )
    assert response.status_code == 200
    assert "result" in response.json()
```

**Step 2: Run tests to verify they fail**

```bash
cd services/openclaw-orchestrator
pytest tests/test_main.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create main.py for OpenClaw Orchestrator**

```python
# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import logging
import httpx

from config import get_settings
from tracing import setup_telemetry, instrument_fastapi
from metrics import init_service_info, record_request
from models import OrchestrateRequest, OrchestrateResponse, HealthResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize tracing
tracer = setup_telemetry("openclaw-orchestrator")
init_service_info("openclaw-orchestrator", "1.0.0")

# Agent registry
AGENTS = {
    "scenespeak-agent": "http://scenespeak-agent:8001",
    "captioning-agent": "http://captioning-agent:8002",
    "bsl-agent": "http://bsl-agent:8003",
    "sentiment-agent": "http://sentiment-agent:8004",
    "lighting-sound-music": "http://lighting-sound-music:8005",
    "safety-filter": "http://safety-filter:8006",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("OpenClaw Orchestrator starting up")
    yield
    logger.info("OpenClaw Orchestrator shutting down")

app = FastAPI(
    title="OpenClaw Orchestrator",
    description="Central control plane for Project Chimera - routes skills to agents",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI
instrument_fastapi(app, "openclaw-orchestrator")

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Check if all agents are ready"""
    checks = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent_name, agent_url in AGENTS.items():
            try:
                response = await client.get(f"{agent_url}/health/live")
                checks[agent_name] = response.status_code == 200
            except Exception as e:
                logger.warning(f"Agent {agent_name} not ready: {e}")
                checks[agent_name] = False

    all_ready = all(checks.values())
    status = "ready" if all_ready else "not_ready"

    return HealthResponse(status=status, checks=checks)

@app.post("/v1/orchestrate")
async def orchestrate(request: OrchestrateRequest):
    """Route skill request to appropriate agent"""
    import time
    start_time = time.time()

    try:
        # Determine which agent handles this skill
        agent_url = get_agent_for_skill(request.skill)

        # Call the agent
        result = await call_agent(agent_url, request.skill, request.input)

        duration = (time.time() - start_time) * 1000

        # Record metrics
        record_request("POST", "/v1/orchestrate", 200, duration)

        return OrchestrateResponse(
            result=result,
            skill_used=request.skill,
            execution_time=duration / 1000,
            metadata={}
        )

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        record_request("POST", "/v1/orchestrate", 500, time.time() - start_time)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skills")
async def list_skills():
    """List available skills"""
    skills = [
        {
            "name": "dialogue_generator",
            "description": "Generate contextual dialogue",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "captioning",
            "description": "Speech-to-text transcription",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "bsl_translation",
            "description": "Text-to-BSL gloss translation",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "sentiment_analysis",
            "description": "Analyze audience sentiment",
            "version": "1.0.0",
            "enabled": True
        }
    ]

    return {"skills": skills, "total": len(skills), "enabled": len(skills)}

def get_agent_for_skill(skill: str) -> str:
    """Map skill to agent URL"""
    skill_to_agent = {
        "dialogue_generator": AGENTS["scenespeak-agent"],
        "captioning": AGENTS["captioning-agent"],
        "bsl_translation": AGENTS["bsl-agent"],
        "sentiment_analysis": AGENTS["sentiment-agent"],
    }

    if skill not in skill_to_agent:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill}")

    return skill_to_agent[skill]

async def call_agent(agent_url: str, skill: str, input_data: dict) -> dict:
    """Call agent endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{agent_url}/v1/{skill}",
            json=input_data
        )
        response.raise_for_status()
        return response.json()
```

**Step 4: Create config.py**

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    service_name: str = "openclaw-orchestrator"
    port: int = 8000

    # Agent URLs
    scenespeak_agent_url: str = "http://scenespeak-agent:8001"
    captioning_agent_url: str = "http://captioning-agent:8002"
    bsl_agent_url: str = "http://bsl-agent:8003"
    sentiment_agent_url: str = "http://sentiment-agent:8004"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
```

**Step 5: Create models.py**

```python
# models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class OrchestrateRequest(BaseModel):
    skill: str = Field(..., description="Name of skill to invoke")
    input: Dict[str, Any] = Field(..., description="Skill-specific input data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class OrchestrateResponse(BaseModel):
    result: Dict[str, Any]
    skill_used: str
    execution_time: float
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    checks: Optional[Dict[str, bool]] = None
```

**Step 6: Create tracing.py (copy from template)**

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)

def setup_telemetry(service_name: str) -> trace.Tracer:
    resource = Resource(attributes={
        "service.name": service_name,
        "service.namespace": "project-chimera"
    })

    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )

    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    logger.info(f"Telemetry initialized for {service_name}")
    return trace.get_tracer(__name__)

def instrument_fastapi(app, service_name: str):
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
    logger.info(f"FastAPI instrumented for {service_name}")
```

**Step 7: Create metrics.py**

```python
# metrics.py
from prometheus_client import Counter, Histogram, Info

request_count = Counter('orchestrator_requests_total', 'Total requests', ['skill', 'status'])
request_duration = Histogram('orchestrator_request_duration_seconds', 'Request duration', ['skill'])

def init_service_info(service_name: str, version: str = "1.0.0"):
    service_info = Info('orchestrator', 'Orchestrator info')
    service_info.info({'name': service_name, 'version': version})

def record_request(skill: str, status: int, duration: float):
    request_count.labels(skill=skill, status=status).inc()
    request_duration.labels(skill=skill).observe(duration)
```

**Step 8: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 9: Create requirements.txt**

```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
httpx>=0.25.2
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-exporter-otlp>=1.21.0
prometheus-client>=0.19.0
python-dotenv>=1.0.0
```

**Step 10: Run tests**

```bash
cd services/openclaw-orchestrator
pytest tests/test_main.py -v
```
Expected: All tests PASS

**Step 11: Commit OpenClaw Orchestrator**

```bash
cd /home/ranj/Project_Chimera
git add services/openclaw-orchestrator/
git commit -m "feat(orchestrator): implement OpenClaw Orchestrator

- FastAPI service with skill routing
- Agent coordinator with REST client
- Health checks for all downstream agents
- OpenTelemetry tracing
- Prometheus metrics
- ARM64 Dockerfile
- Comprehensive tests"
```

---

## Day 2: Friday, March 7 - AI Agents Part 1

### Task 3: Build SceneSpeak Agent (Port 8001)

**Files:**
- Modify: `services/scenespeak-agent/main.py` (update existing)
- Create: `services/scenespeak-agent/glm_client.py`
- Create: `services/scenespeak-agent/local_llm.py`
- Create: `services/scenespeak-agent/tests/test_glm_client.py`
- Create: `services/scenespeak-agent/Dockerfile`

**Step 1: Write tests for GLM client**

```python
# tests/test_glm_client.py
import pytest
from glm_client import GLMClient

@pytest.fixture
def client():
    return GLMClient(api_key="test-key")

def test_generate_dialogue(client, mock_glm_api):
    response = client.generate("Hello world", max_tokens=100)
    assert response.text is not None
    assert len(response.text) > 0
    assert response.model == "glm-4"

def test_fallback_to_local(client, mock_glm_failure):
    response = client.generate("Hello world", max_tokens=100)
    assert response.text is not None
    assert response.source == "local"
```

**Step 2: Run tests**

```bash
cd services/scenespeak-agent
pytest tests/test_glm_client.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create glm_client.py with fallback**

```python
# glm_client.py
import httpx
import logging
from typing import Optional
from dataclasses import dataclass
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class DialogueResponse:
    text: str
    tokens_used: int
    model: str
    source: str  # "api" or "local"
    duration_ms: int

class GLMClient:
    """GLM 4.7 API client with local fallback"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.glm_api_key
        self.api_base = settings.glm_api_base
        self.local_model_path = settings.local_model_path

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> DialogueResponse:
        """Generate dialogue with GLM 4.7, fallback to local"""

        # Try GLM 4.7 API first
        if self.api_key:
            try:
                return await self._call_glm_api(prompt, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"GLM API failed: {e}, falling back to local")

        # Fallback to local model
        return await self._call_local_model(prompt, max_tokens, temperature)

    async def _call_glm_api(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> DialogueResponse:
        """Call GLM 4.7 API"""
        import time

        payload = {
            "model": "glm-4",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        duration_ms = int((time.time() - start_time) * 1000)

        return DialogueResponse(
            text=data["choices"][0]["message"]["content"],
            tokens_used=data["usage"]["total_tokens"],
            model="glm-4",
            source="api",
            duration_ms=duration_ms
        )

    async def _call_local_model(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> DialogueResponse:
        """Call local LLM (you'll provide path tomorrow)"""
        import time

        if not self.local_model_path:
            raise ValueError("Local model path not configured")

        # TODO: Implement local model loading
        # Will be implemented when you provide model paths tomorrow

        logger.warning("Local model not yet implemented")

        # Placeholder
        return DialogueResponse(
            text=f"[Local model placeholder] {prompt}",
            tokens_used=0,
            model="local",
            source="local",
            duration_ms=0
        )
```

**Step 4: Update main.py to use GLM client**

```python
# main.py (update existing file)
from fastapi import FastAPI, HTTPException
from glm_client import GLMClient
from tracing import setup_telemetry
from metrics import init_service_info
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="SceneSpeak Agent", version="1.0.0")

# Initialize tracing
tracer = setup_telemetry("scenespeak-agent")
init_service_info("scenespeak-agent", "1.0.0")

# GLM client
glm_client = GLMClient()

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    # Check if GLM API or local model is available
    return {"status": "ready"}

@app.post("/v1/generate")
async def generate_dialogue(request: GenerateRequest):
    """Generate dialogue using GLM 4.7 with local fallback"""
    try:
        response = await glm_client.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return response
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Keep existing metrics and tracing code
```

**Step 5: Run tests**

```bash
cd services/scenespeak-agent
pytest tests/test_glm_client.py -v
pytest tests/test_main.py -v
```
Expected: All tests PASS

**Step 6: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ARM64 dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch for ARM64
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Step 7: Update requirements.txt**

```text
# Add to existing requirements.txt
httpx>=0.25.2
pydantic-settings>=2.1.0
```

**Step 8: Commit SceneSpeak Agent**

```bash
git add services/scenespeak-agent/
git commit -m "feat(scenespeak): add GLM 4.7 integration with local fallback

- GLM API client with retry logic
- Local LLM fallback (path to be configured)
- Generate dialogue endpoint
- Comprehensive tests
- ARM64 Dockerfile"
```

### Task 4: Build Captioning Agent (Port 8002)

**Files:**
- Create: `services/captioning-agent/main.py`
- Create: `services/captioning-agent/whisper_service.py`
- Create: `services/captioning-agent/websocket_handler.py`
- Create: `services/captioning-agent/tests/test_whisper.py`
- Create: `services/captioning-agent/Dockerfile`
- Create: `services/captioning-agent/requirements.txt`

**Step 1: Write tests for Whisper service**

```python
# tests/test_whisper.py
import pytest
from whisper_service import WhisperService

@pytest.fixture
def service():
    return WhisperService()

def test_transcribe_audio(service, mock_audio_file):
    result = service.transcribe(mock_audio_file)
    assert result.text is not None
    assert result.language is not None

def test_language_detection(service):
    result = service.detect_language("hello.wav")
    assert result in ["en", "es", "fr", "de"]
```

**Step 2: Run tests**

```bash
cd services/captioning-agent
pytest tests/test_whisper.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create whisper_service.py**

```python
# whisper_service.py
import torch
import whisper
import logging
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration: float
    words: list

class WhisperService:
    """Whisper speech-to-text service"""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model"""
        logger.info(f"Loading Whisper model: {self.model_size}")
        self.model = whisper.load_model(self.model_size)
        logger.info("Whisper model loaded")

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio file"""
        logger.info(f"Transcribing: {audio_path}")

        # Load audio
        audio = whisper.load_audio(audio_path)

        # Transcribe
        result = self.model.transcribe(
            audio,
            language=None,  # Auto-detect
            word_timestamps=True
        )

        return TranscriptionResult(
            text=result["text"].strip(),
            language=result["language"],
            duration=audio.shape[0] / whisper.audio.SAMPLE_RATE,
            words=result.get("segments", [])
        )

    def transcribe_stream(self, audio_chunk: bytes) -> str:
        """Transcribe audio chunk (for streaming)"""
        # TODO: Implement streaming transcription
        pass

    def detect_language(self, audio_path: str) -> str:
        """Detect language from audio"""
        audio = whisper.load_audio(audio_path)
        audio_tensor = torch.from_numpy(audio)
        audio_tensor = whisper.pad_or_trim(audio_tensor)
        mel = whisper.log_mel_spectrogram(audio_tensor).to(self.model.device)
        _, probs = self.model.detect_language(mel)
        return max(probs, key=probs.get)
```

**Step 4: Create main.py**

```python
# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from whisper_service import WhisperService
from tracing import setup_telemetry
from metrics import init_service_info, record_business_operation
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Captioning Agent",
    description="Real-time speech-to-text with Whisper model",
    version="1.0.0"
)

# Initialize
tracer = setup_telemetry("captioning-agent")
init_service_info("captioning-agent", "1.0.0")

# Whisper service
whisper_service = WhisperService(model_size="base")

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    return {"status": "ready"}

@app.post("/v1/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio file"""
    import tempfile

    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Transcribe
        result = whisper_service.transcribe(tmp_path)

        # Record metric
        record_business_operation("transcription", "success")

        return {
            "text": result.text,
            "language": result.language,
            "duration": result.duration
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        record_business_operation("transcription", "error")
        raise
    finally:
        # Cleanup
        import os
        if 'tmp_path' in locals():
            os.unlink(tmp_path)

@app.websocket("/v1/stream")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_bytes()

            # Process chunk
            # TODO: Implement streaming transcription

            # Send partial result
            await websocket.send_json({
                "text": "",
                "status": "processing"
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
```

**Step 5: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

**Step 6: Create requirements.txt**

```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
httpx>=0.25.2
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-exporter-otlp>=1.21.0
prometheus-client>=0.19.0
python-dotenv>=1.0.0

# Whisper
openai-whisper>=20231117
torch>=2.1.0
torchaudio>=2.1.0
```

**Step 7: Run tests**

```bash
cd services/captioning-agent
pytest tests/ -v
```

**Step 8: Commit Captioning Agent**

```bash
git add services/captioning-agent/
git commit -m "feat(captioning): add Whisper-based captioning service

- Whisper model integration
- File upload transcription endpoint
- WebSocket streaming endpoint (placeholder)
- Language detection
- Comprehensive tests
- ARM64 Dockerfile with ffmpeg"
```

### Task 5: Build BSL Agent (Port 8003)

**Files:**
- Create: `services/bsl-agent/main.py`
- Create: `services/bsl-agent/translator.py`
- Create: `services/bsl-agent/avatar_renderer.py`
- Create: `services/bsl-agent/tests/test_translator.py`
- Create: `services/bsl-agent/Dockerfile`
- Create: `services/bsl-agent/requirements.txt`

**Step 1: Write tests for translator**

```python
# tests/test_translator.py
import pytest
from translator import BSLTranslator

@pytest.fixture
def translator():
    return BSLTranslator()

def test_text_to_gloss(translator):
    result = translator.text_to_gloss("Hello world")
    assert result.gloss is not None
    assert len(result.gloss) > 0

def test_non_manual_markers(translator):
    result = translator.add_non_manual_markers("Hello")
    assert "nmm" in result.markers
```

**Step 2: Run tests**

```bash
cd services/bsl-agent
pytest tests/test_translator.py -v
```
Expected: FAIL

**Step 3: Create translator.py**

```python
# translator.py
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class GlossResult:
    gloss: List[str]
    language: str
    confidence: float

@dataclass
class AvatarPose:
    gloss: str
    pose_data: dict
    duration: float

class BSLTranslator:
    """Text-to-BSL gloss translator"""

    def __init__(self):
        self.gloss_dict = self._load_gloss_dictionary()

    def _load_gloss_dictionary(self):
        """Load BSL gloss dictionary"""
        # TODO: Load actual BSL dictionary
        logger.info("Loading BSL gloss dictionary")
        return {}

    def text_to_gloss(self, text: str) -> GlossResult:
        """Convert text to BSL gloss"""
        logger.info(f"Translating to BSL gloss: {text}")

        # Simple word-by-word translation (placeholder)
        words = text.lower().split()
        gloss = [f"BSL-{word}" for word in words]

        return GlossResult(
            gloss=gloss,
            language="bsl",
            confidence=0.8
        )

    def add_non_manual_markers(self, text: str) -> dict:
        """Add non-manual markers (facial expressions, body language)"""
        # TODO: Implement NMM detection
        markers = {
            "nmm": ["raised_eyebrows", "lean_forward"],
            "body": ["open_posture"]
        }
        return markers

    def format_gloss(self, gloss: List[str]) -> str:
        """Format gloss for display"""
        return " ".join(gloss)
```

**Step 4: Create avatar_renderer.py**

```python
# avatar_renderer.py
import logging
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class AvatarFrame:
    pose: Dict[str, Any]
    timestamp: float

class AvatarRenderer:
    """BSL avatar rendering service"""

    def __init__(self):
        self.avatar_library = self._load_avatar_library()

    def _load_avatar_library(self):
        """Load avatar pose library"""
        logger.info("Loading avatar library")
        # TODO: Load actual avatar library
        return {}

    def gloss_to_pose(self, gloss: str) -> AvatarFrame:
        """Convert gloss to avatar pose"""
        # TODO: Implement gloss-to-pose conversion
        return AvatarFrame(
            pose={"pose": "neutral"},
            timestamp=0.0
        )

    def render_frame(self, frame: AvatarFrame) -> bytes:
        """Render avatar frame to bytes"""
        # TODO: Implement actual rendering
        return b""
```

**Step 5: Create main.py**

```python
# main.py
from fastapi import FastAPI, HTTPException
from translator import BSLTranslator, GlossResult
from avatar_renderer import AvatarRenderer
from tracing import setup_telemetry
from metrics import init_service_info
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BSL Translation Agent",
    description="Text-to-BSL gloss translation with avatar rendering",
    version="1.0.0"
)

tracer = setup_telemetry("bsl-agent")
init_service_info("bsl-agent", "1.0.0")

translator = BSLTranslator()
renderer = AvatarRenderer()

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    return {"status": "ready"}

@app.post("/v1/translate")
async def translate_to_bsl(request: TranslateRequest):
    """Translate text to BSL gloss"""
    try:
        result = translator.text_to_gloss(request.text)
        nmm = translator.add_non_manual_markers(request.text)

        return {
            "gloss": result.gloss,
            "formatted": translator.format_gloss(result.gloss),
            "non_manual_markers": nmm,
            "confidence": result.confidence
        }
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/avatar")
async def generate_avatar(request: AvatarRequest):
    """Generate avatar from gloss"""
    try:
        frame = renderer.gloss_to_pose(request.gloss)
        # TODO: Return rendered frame
        return {"pose": frame.pose, "timestamp": frame.timestamp}
    except Exception as e:
        logger.error(f"Avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 6: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

**Step 7: Create requirements.txt**

```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-exporter-otlp>=1.21.0
prometheus-client>=0.19.0
python-dotenv>=1.0.0
```

**Step 8: Run tests**

```bash
cd services/bsl-agent
pytest tests/ -v
```

**Step 9: Commit BSL Agent**

```bash
git add services/bsl-agent/
git commit -m "feat(bsl): add text-to-BSL translation service

- Text-to-gloss translation
- Non-manual marker annotation
- Avatar rendering placeholder
- Translation endpoint
- Avatar generation endpoint
- Comprehensive tests
- ARM64 Dockerfile"
```

---

## Day 3: Saturday, March 8 - AI Agents Part 2 + Console

### Task 6: Build Sentiment Agent (Port 8004)

**Files:**
- Create: `services/sentiment-agent/main.py`
- Create: `services/sentiment-agent/sentiment_analyzer.py`
- Create: `services/sentiment-agent/worldmonitor_client.py`
- Create: `services/sentiment-agent/tests/test_analyzer.py`
- Create: `services/sentiment-agent/Dockerfile`
- Create: `services/sentiment-agent/requirements.txt`

**Step 1: Write tests**

```python
# tests/test_analyzer.py
import pytest
from sentiment_analyzer import SentimentAnalyzer

@pytest.fixture
def analyzer():
    return SentimentAnalyzer()

def test_analyze_sentiment(analyzer):
    result = analyzer.analyze("I love this!")
    assert result.sentiment > 0
    assert result.label == "POSITIVE"

def test_batch_analysis(analyzer):
    texts = ["Great!", "Terrible...", "Okay"]
    results = analyzer.analyze_batch(texts)
    assert len(results) == 3
```

**Step 2: Create sentiment_analyzer.py**

```python
# sentiment_analyzer.py
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    sentiment: float  # -1 to 1
    label: str  # POSITIVE, NEGATIVE, NEUTRAL
    confidence: float

class SentimentAnalyzer:
    """Sentiment analysis using DistilBERT"""

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        logger.info(f"Loading sentiment model: {model_name}")
        self.pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            return_all_scores=True
        )
        logger.info("Sentiment model loaded")

    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of single text"""
        results = self.pipeline(text)[0]

        # Convert to -1 to 1 scale
        pos_score = next(r for r in results if r["label"] == "POSITIVE")["score"]
        neg_score = next(r for r in results if r["label"] == "NEGATIVE")["score"]

        sentiment = pos_score - neg_score

        # Determine label
        if sentiment > 0.3:
            label = "POSITIVE"
        elif sentiment < -0.3:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        confidence = max(pos_score, neg_score)

        return SentimentResult(
            sentiment=sentiment,
            label=label,
            confidence=confidence
        )

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze sentiment of multiple texts"""
        return [self.analyze(text) for text in texts]

    def aggregate(self, results: List[SentimentResult]) -> dict:
        """Aggregate sentiment results"""
        if not results:
            return {"average": 0, "count": 0, "distribution": {}}

        avg_sentiment = sum(r.sentiment for r in results) / len(results)

        distribution = {}
        for r in results:
            distribution[r.label] = distribution.get(r.label, 0) + 1

        return {
            "average": avg_sentiment,
            "count": len(results),
            "distribution": distribution
        }
```

**Step 3: Create worldmonitor_client.py**

```python
# worldmonitor_client.py
import asyncio
import websockets
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class WorldMonitorClient:
    """WorldMonitor sidecar client for global context"""

    def __init__(self, url: str = "ws://localhost:8010/ws"):
        self.url = url
        self.connected = False
        self.context_cache = {}

    async def connect(self):
        """Connect to WorldMonitor WebSocket"""
        try:
            self.ws = await websockets.connect(self.url)
            self.connected = True
            logger.info(f"Connected to WorldMonitor: {self.url}")
        except Exception as e:
            logger.warning(f"WorldMonitor connection failed: {e}")
            self.connected = False

    async def subscribe_to_context(self, categories: list):
        """Subscribe to context updates"""
        if not self.connected:
            return

        subscribe_msg = {
            "action": "subscribe",
            "categories": categories
        }

        await self.ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to categories: {categories}")

    async def get_context(self, category: str) -> Optional[Dict]:
        """Get current context for category"""
        # Return cached context
        return self.context_cache.get(category)

    async def listen(self):
        """Listen for context updates"""
        if not self.connected:
            return

        try:
            async for message in self.ws:
                data = json.loads(message)
                self.context_cache[data["category"]] = data
                logger.debug(f"Context updated: {data['category']}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WorldMonitor connection closed")
            self.connected = False
```

**Step 4: Create main.py**

```python
# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from sentiment_analyzer import SentimentAnalyzer
from worldmonitor_client import WorldMonitorClient
from tracing import setup_telemetry
from metrics import init_service_info
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sentiment Agent",
    description="Audience sentiment analysis with WorldMonitor integration",
    version="1.0.0"
)

tracer = setup_telemetry("sentiment-agent")
init_service_info("sentiment-agent", "1.0.0")

analyzer = SentimentAnalyzer()
worldmonitor = WorldMonitorClient()

@app.on_event("startup")
async def startup():
    """Connect to WorldMonitor on startup"""
    await worldmonitor.connect()
    if worldmonitor.connected:
        asyncio.create_task(worldmonitor.listen())

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    return {"status": "ready"}

@app.post("/v1/analyze")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of text"""
    try:
        result = analyzer.analyze(request.text)
        return {
            "sentiment": result.sentiment,
            "label": result.label,
            "confidence": result.confidence
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/batch")
async def analyze_batch(request: BatchRequest):
    """Analyze sentiment of multiple texts"""
    try:
        results = analyzer.analyze_batch(request.texts)
        aggregated = analyzer.aggregate(results)
        return {
            "results": [
                {
                    "sentiment": r.sentiment,
                    "label": r.label,
                    "confidence": r.confidence
                }
                for r in results
            ],
            "aggregated": aggregated
        }
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/context/{category}")
async def get_context(category: str):
    """Get WorldMonitor context for category"""
    context = await worldmonitor.get_context(category)
    if context:
        return context
    return {"error": "Context not available"}
```

**Step 5: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

**Step 6: Create requirements.txt**

```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
transformers>=4.36.0
torch>=2.1.0
websockets>=12.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-exporter-otlp>=1.21.0
prometheus-client>=0.19.0
python-dotenv>=1.0.0
```

**Step 7: Run tests**

```bash
cd services/sentiment-agent
pytest tests/ -v
```

**Step 8: Commit**

```bash
git add services/sentiment-agent/
git commit -m "feat(sentiment): add DistilBERT sentiment analysis

- DistilBERT SST-2 model integration
- Single and batch text analysis
- Sentiment aggregation
- WorldMonitor sidecar client
- Context enrichment endpoints
- Comprehensive tests
- ARM64 Dockerfile"
```

### Task 7: Build Lighting-Sound-Music Service (Port 8005)

### Task 8: Build Safety Filter (Port 8006)

### Task 9: Build Operator Console (Port 8007)

---

## Day 4: Sunday, March 9 - Integration & Demo Prep

### Task 10: Create Docker Compose for Local Development

### Task 11: Integration Testing

### Task 12: Demo Preparation

---

## Implementation Notes

### When Local LLM Paths Are Provided Tomorrow

**For SceneSpeak Agent:**
1. Update `services/scenespeak-agent/glm_client.py`
2. Implement `_call_local_model()` method
3. Load model from provided path using transformers
4. Test with both API and local model

### ARM64 Considerations

All Dockerfiles use ARM64-compatible base images:
- `python:3.12-slim` is ARM64 compatible
- PyTorch wheels available for ARM64
- Test on Nvidia DGX Spark GB10 before commit

---

## Success Criteria

Each day ends with:
- All services built that day are running locally
- Docker images built successfully
- Tests passing (>80% coverage)
- Integration verified with OpenClaw
- Git commit with descriptive message

---

*Implementation Plan - Project Chimera v0.4.0 - March 5, 2026*

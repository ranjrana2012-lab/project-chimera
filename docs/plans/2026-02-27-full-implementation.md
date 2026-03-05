# Project Chimera - Full Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the complete Project Chimera AI-powered live theatre platform with all 8 services, real AI models, monitoring, and documentation for Monday student demonstration.

**Architecture:** k3s-based Kubernetes cluster with 8 FastAPI microservices (2 GPU, 6 CPU), Redis for state, Kafka for events, Prometheus/Grafana for monitoring.

**Tech Stack:** FastAPI, PyTorch, Redis, Kafka, Kubernetes (k3s), Docker, Prometheus, Grafana, Jaeger, Mistral-7B, Whisper, DistilBERT, OPUS-MT

**Estimated Time:** 42-55 hours

---

## Table of Contents

1. [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
2. [Phase 2: OpenClaw Orchestrator](#phase-2-openclaw-orchestrator)
3. [Phase 3: SceneSpeak Agent](#phase-3-SceneSpeak Agent)
4. [Phase 4: Captioning Agent](#phase-4-Captioning Agent)
5. [Phase 5: BSL-Text2Gloss Agent](#phase-5-bsl-text2gloss-agent)
6. [Phase 6: Sentiment Agent](#phase-6-Sentiment Agent)
7. [Phase 7: Lighting Control](#phase-7-lighting-control)
8. [Phase 8: Safety Filter](#phase-8-safety-filter)
9. [Phase 9: Operator Console](#phase-9-operator-console)
10. [Phase 10: Integration & Testing](#phase-10-integration--testing)
11. [Phase 11: Monitoring & Documentation](#phase-11-monitoring--documentation)
12. [Phase 12: Open Source Prep](#phase-12-open-source-preparation)

---

## Phase 1: Infrastructure Setup

**Estimated Time:** 4-6 hours

### Task 1.1: Fix Docker Permissions

**Step 1: Add user to docker group**

```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Step 2: Verify docker access**

```bash
docker ps
```

Expected: No permission error

**Step 3: Commit changes**

No files to commit

---

### Task 1.2: Configure k3s Registry

**Step 1: Create k3s registries configuration**

```bash
sudo mkdir -p /etc/rancher/k3s/
cat <<EOF | sudo tee /etc/rancher/k3s/registries.yaml
mirrors:
  "localhost:30500":
    endpoint:
      - "http://localhost:30500"
EOF
```

**Step 2: Restart k3s**

```bash
sudo systemctl restart k3s
```

**Step 3: Verify k3s is running**

```bash
kubectl get nodes
```

Expected: Node shows as Ready

---

### Task 1.3: Run Bootstrap

**Step 1: Run bootstrap command**

```bash
make bootstrap
```

Expected: All scripts complete successfully

**Step 2: Verify deployment**

```bash
make bootstrap-status
```

Expected: All pods Running

---

### Task 1.4: Create Documentation Standards

**Files:**
- Create: `docs/standards/python-style.md`
- Create: `docs/standards/documentation-style.md`
- Create: `docs/standards/testing-standards.md`

**Step 1: Write python-style.md**

```markdown
# Python Code Style Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-27

## Formatting

- Use `black` for code formatting
- Use `isort` for import sorting
- Line length: 100 characters

## Type Hints

All public functions MUST have type hints:

```python
def generate_dialogue(context: str, sentiment: float) -> dict:
    pass
```

## Docstrings

Use Google style docstrings:

```python
def generate_dialogue(context: str, sentiment: float) -> dict:
    """Generate dialogue for the given context.

    Args:
        context: Scene description
        sentiment: Sentiment value (-1.0 to 1.0)

    Returns:
        Dictionary with 'dialogue' and 'metadata' keys
    """
    pass
```

## Imports

Order: 1) stdlib, 2) third-party, 3) local

```python
import os
from datetime import datetime

import redis
import torch

from services.openclaw.src.core import skill_registry
```
```

**Step 2: Write documentation-style.md**

```markdown
# Documentation Style Guide

**Version:** 1.0.0

## File Header

Every .md file MUST start with:

```markdown
# Title

**Version:** 1.0.0
**Last Updated:** YYYY-MM-DD
**Audience:** [Beginner|Intermediate|Advanced]
**Estimated Reading Time:** X minutes

## Purpose
[Why this doc exists]

## Prerequisites
- [ ] Item 1
- [ ] Item 2
```

## Code Examples

All code examples MUST include:
- Language tag
- Brief description
- Expected output

## Links

Use descriptive link text:

- Good: [Setting up GPU](#gpu-setup)
- Bad: [click here](#gpu-setup)
```

**Step 3: Write testing-standards.md**

```markdown
# Testing Standards

**Version:** 1.0.0

## Test Naming

```python
def test_{function}_{scenario}_{expected_result}():
    pass
```

## AAA Pattern

Arrange-Act-Assert structure:

```python
def test_generate_dialogue_with_positive_sentiment():
    # Arrange
    context = "A sunny garden"
    sentiment = 0.8

    # Act
    result = generate_dialogue(context, sentiment)

    # Assert
    assert result["dialogue"] is not None
    assert len(result["dialogue"]) > 0
```

## Coverage

Minimum coverage by service:
- OpenClaw: 85%
- SceneSpeak: 80%
- Safety: 90%
- Others: 75%
```

**Step 4: Commit**

```bash
git add docs/standards/
git commit -m "docs: add code and documentation standards"
```

---

## Phase 2: OpenClaw Orchestrator

**Estimated Time:** 6 hours

**Port:** 8000
**GPU:** 1x NVIDIA GPU

### Task 2.1: Create OpenClaw Base Models

**Files:**
- Create: `services/openclaw-orchestrator/src/models/__init__.py`
- Create: `services/openclaw-orchestrator/src/models/skill.py`
- Create: `services/openclaw-orchestrator/src/models/request.py`
- Create: `services/openclaw-orchestrator/src/models/response.py`

**Step 1: Write __init__.py**

```python
"""OpenClaw Orchestrator data models."""
```

**Step 2: Write skill.py**

```python
"""Skill data models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Skill(BaseModel):
    """Represents a registered skill."""
    name: str
    version: str
    endpoint: str
    timeout: int = Field(default=5000, ge=100, le=60000)
    gpu_required: bool = False
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SkillHealth(BaseModel):
    """Skill health status."""
    name: str
    healthy: bool
    last_check: str
    error_message: Optional[str] = None
```

**Step 3: Write request.py**

```python
"""Request models."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class OrchestrationRequest(BaseModel):
    """Request for orchestration."""
    skills: List[str]
    input_data: Dict[str, Any]
    priority: Optional[int] = Field(default=100, ge=1, le=1000)
    timeout: Optional[int] = Field(default=30, ge=1, le=300)
    gpu_required: Optional[bool] = False
    request_id: Optional[str] = None

class SkillRequest(BaseModel):
    """Request to a single skill."""
    skill: str
    input_data: Dict[str, Any]
    timeout: int = 5000
```

**Step 4: Write response.py**

```python
"""Response models."""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class Status(str, Enum):
    """Execution status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

class OrchestrationResponse(BaseModel):
    """Response from orchestration."""
    request_id: str
    status: Status
    results: Dict[str, Any]
    execution_time_ms: float
    gpu_used: bool
    errors: Optional[Dict[str, str]] = None

class SkillResponse(BaseModel):
    """Response from a single skill."""
    skill: str
    status: Status
    output: Dict[str, Any]
    execution_time_ms: float
    error: Optional[str] = None
```

**Step 5: Write tests for models**

```python
# tests/unit/test_openclaw_models.py

import pytest
from services.openclaw.src.models.skill import Skill, SkillHealth
from services.openclaw.src.models.request import OrchestrationRequest
from services.openclaw.src.models.response import OrchestrationResponse, Status

class TestSkill:
    def test_skill_creation(self):
        skill = Skill(
            name="test-skill",
            version="1.0.0",
            endpoint="http://localhost:8001"
        )
        assert skill.name == "test-skill"
        assert skill.gpu_required is False

class TestOrchestrationRequest:
    def test_valid_request(self):
        request = OrchestrationRequest(
            skills=["scenespeak"],
            input_data={"context": "test"}
        )
        assert len(request.skills) == 1

    def test_priority_validation(self):
        with pytest.raises(ValueError):
            OrchestrationRequest(
                skills=["test"],
                input_data={},
                priority=2000  # Too high
            )
```

**Step 6: Run tests**

```bash
pytest tests/unit/test_openclaw_models.py -v
```

Expected: All pass

**Step 7: Commit**

```bash
git add services/openclaw-orchestrator/src/models/
git add tests/unit/test_openclaw_models.py
git commit -m "feat(openclaw): add base data models with validation"
```

---

### Task 2.2: Create Skill Registry

**Files:**
- Create: `services/openclaw-orchestrator/src/core/skill_registry.py`
- Modify: `services/openclaw-orchestrator/src/core/__init__.py`
- Create: `tests/unit/test_openclaw_skill_registry.py`

**Step 1: Write skill_registry.py**

```python
"""Skill registry for loading and managing skills."""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from ..models.skill import Skill, SkillHealth


class SkillRegistry:
    """Manages skill registration and health monitoring."""

    def __init__(self, config_path: str = "/app/configs/skills"):
        self.config_path = Path(config_path)
        self.skills: Dict[str, Skill] = {}
        self.health: Dict[str, SkillHealth] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load skill configurations from ConfigMaps."""
        try:
            config.load_kube_config()
            api = client.CoreV1Api()

            # Get ConfigMaps in current namespace
            namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read().strip()
            configmaps = api.list_namespaced_config_map(
                namespace=namespace,
                label_selector="project-chimera.io/component=skill"
            )

            for cm in configmaps.items:
                skill_name = cm.metadata.name.replace("-skill-config", "")
                skill_data = json.loads(cm.data["skill.json"])
                self.skills[skill_name] = Skill(**skill_data)

        except Exception as e:
            # Fallback to local files
            if self.config_path.exists():
                for skill_file in self.config_path.glob("*.json"):
                    with open(skill_file) as f:
                        skill_data = json.load(f)
                        skill = Skill(**skill_data)
                        self.skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        """List all registered skills."""
        return list(self.skills.values())

    def get_healthy_skills(self) -> List[Skill]:
        """Get all healthy skills."""
        return [
            skill for skill in self.skills.values()
            if self.health.get(skill.name, SkillHealth(name=skill.name, healthy=False)).healthy
        ]

    async def check_health(self, session: aiohttp.ClientSession) -> None:
        """Check health of all skills."""
        for skill in self.skills.values():
            try:
                async with session.get(
                    f"{skill.endpoint}/health/ready",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    is_healthy = response.status == 200
                    self.health[skill.name] = SkillHealth(
                        name=skill.name,
                        healthy=is_healthy,
                        last_check=datetime.utcnow().isoformat()
                    )
            except Exception as e:
                self.health[skill.name] = SkillHealth(
                    name=skill.name,
                    healthy=False,
                    last_check=datetime.utcnow().isoformat(),
                    error_message=str(e)
                )
```

**Step 2: Write tests**

```python
# tests/unit/test_openclaw_skill_registry.py

import pytest
from services.openclaw.src.core.skill_registry import SkillRegistry

class TestSkillRegistry:
    @pytest.fixture
    def registry(self, tmp_path):
        return SkillRegistry(config_path=str(tmp_path))

    def test_list_empty_skills(self, registry):
        assert registry.list_skills() == []

    def test_get_nonexistent_skill(self, registry):
        assert registry.get_skill("nonexistent") is None
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_openclaw_skill_registry.py -v
```

**Step 4: Commit**

```bash
git add services/openclaw-orchestrator/src/core/skill_registry.py
git add tests/unit/test_openclaw_skill_registry.py
git commit -m "feat(openclaw): add skill registry with health checking"
```

---

### Task 2.3: Create GPU Scheduler

**Files:**
- Create: `services/openclaw-orchestrator/src/core/gpu_scheduler.py`
- Create: `tests/unit/test_openclaw_gpu_scheduler.py`

**Step 1: Write gpu_scheduler.py**

```python
"""GPU allocation and scheduling."""
import asyncio
from typing import Dict, Optional
import pynvml

try:
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False


class GPUAllocation:
    """Represents a GPU allocation."""
    def __init__(self, gpu_id: int, memory_mb: int):
        self.gpu_id = gpu_id
        self.memory_mb = memory_mb
        self.allocated = False


class GPUScheduler:
    """Manages GPU resource allocation."""

    def __init__(self):
        self.allocations: Dict[str, GPUAllocation] = {}
        self.gpu_count = 0
        self.total_memory_mb = 0

        if GPU_AVAILABLE:
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            self.total_memory_mb = mem_info.total // (1024 * 1024)

    async def allocate_gpu(
        self,
        service: str,
        memory_mb: int,
        timeout: float = 30.0
    ) -> Optional[int]:
        """Allocate GPU for a service."""
        if not GPU_AVAILABLE:
            return None

        # Check if already allocated
        if service in self.allocations:
            return self.allocations[service].gpu_id

        # Try to allocate on GPU 0
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            free_mb = mem_info.free // (1024 * 1024)

            if free_mb >= memory_mb:
                self.allocations[service] = GPUAllocation(gpu_id=0, memory_mb=memory_mb)
                return 0
        except Exception as e:
            pass

        return None

    async def release_gpu(self, service: str) -> None:
        """Release GPU allocation."""
        if service in self.allocations:
            del self.allocations[service]

    def get_usage(self) -> Dict[str, int]:
        """Get current GPU usage in MB."""
        usage = {}
        for service, alloc in self.allocations.items():
            usage[service] = alloc.memory_mb
        return usage
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 2.4: Create Router

**Files:**
- Create: `services/openclaw-orchestrator/src/core/router.py`

**Step 1: Write router.py**

```python
"""Request routing to skills."""
import asyncio
import time
import uuid
from typing import Dict, Any, List
import aiohttp
import redis.asyncio as redis

from ..models.request import OrchestrationRequest, SkillRequest
from ..models.response import OrchestrationResponse, SkillResponse, Status
from .skill_registry import SkillRegistry
from .gpu_scheduler import GPUScheduler


class Router:
    """Routes requests to skills."""

    def __init__(
        self,
        registry: SkillRegistry,
        gpu_scheduler: GPUScheduler,
        redis_client: redis.Redis
    ):
        self.registry = registry
        self.gpu_scheduler = gpu_scheduler
        self.redis = redis_client
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """Orchestrate a request through multiple skills."""
        request_id = request.request_id or str(uuid.uuid4())
        start_time = time.time()

        results = {}
        errors = {}
        gpu_used = False

        # Allocate GPU if needed
        gpu_id = None
        if request.gpu_required:
            gpu_id = await self.gpu_scheduler.allocate_gpu(
                service="orchestrate",
                memory_mb=4000,
                timeout=request.timeout
            )
            if gpu_id is not None:
                gpu_used = True

        try:
            # Execute skills in sequence
            for skill_name in request.skills:
                skill = self.registry.get_skill(skill_name)
                if not skill:
                    errors[skill_name] = "Skill not found"
                    continue

                try:
                    skill_response = await self._invoke_skill(
                        skill,
                        request.input_data,
                        timeout=request.timeout
                    )
                    results[skill_name] = skill_response.output

                except asyncio.TimeoutError:
                    errors[skill_name] = "Timeout"
                except Exception as e:
                    errors[skill_name] = str(e)

        finally:
            if gpu_id is not None:
                await self.gpu_scheduler.release_gpu("orchestrate")

        execution_time = (time.time() - start_time) * 1000

        status = Status.SUCCESS if not errors else Status.ERROR

        return OrchestrationResponse(
            request_id=request_id,
            status=status,
            results=results,
            execution_time_ms=execution_time,
            gpu_used=gpu_used,
            errors=errors if errors else None
        )

    async def _invoke_skill(
        self,
        skill: 'Skill',
        input_data: Dict[str, Any],
        timeout: int
    ) -> SkillResponse:
        """Invoke a single skill."""
        start_time = time.time()

        async with self.session.post(
            f"{skill.endpoint}/v1/invoke",
            json={"input_data": input_data},
            timeout=aiohttp.ClientTimeout(total=timeout / 1000)
        ) as response:
            output = await response.json()
            execution_time = (time.time() - start_time) * 1000

            return SkillResponse(
                skill=skill.name,
                status=Status.SUCCESS,
                output=output,
                execution_time_ms=execution_time
            )
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 2.5: Create Policy Engine

**Files:**
- Create: `services/openclaw-orchestrator/src/core/policy_engine.py`

**Step 1: Write policy_engine.py**

```python
"""Content policy engine."""
import yaml
from pathlib import Path
from typing import Dict, Any, List

class PolicyEngine:
    """Evaluates content against policies."""

    def __init__(self, config_path: str = "/app/configs/policies.yaml"):
        self.config_path = Path(config_path)
        self.policies = self._load_policies()

    def _load_policies(self) -> Dict[str, Any]:
        """Load policies from config file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        return self._default_policies()

    def _default_policies(self) -> Dict[str, Any]:
        """Return default policies."""
        return {
            "profanity": {"enabled": True, "auto_block": True},
            "hate_speech": {"enabled": True, "auto_block": True},
            "violence": {"enabled": True, "auto_block": False}
        }

    def evaluate(self, content: str) -> Dict[str, Any]:
        """Evaluate content against policies."""
        # This is a placeholder - real implementation calls Safety Filter
        return {
            "decision": "approved",
            "confidence": 0.95,
            "categories": {
                "profanity": False,
                "hate_speech": False,
                "violence": False
            }
        }
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 2.6: Create Kafka Integration

**Files:**
- Create: `services/openclaw-orchestrator/src/core/kafka_producer.py`
- Create: `services/openclaw-orchestrator/src/core/kafka_consumer.py`

**Step 1: Write kafka_producer.py**

```python
"""Kafka event producer."""
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from aiokafka import AIOKafkaProducer
import asyncio

class KafkaProducer:
    """Produces events to Kafka."""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._loop = asyncio.get_event_loop()

    async def start(self):
        """Start the producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy'
        )
        await self.producer.start()

    async def stop(self):
        """Stop the producer."""
        if self.producer:
            await self.producer.stop()

    async def publish(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        source_service: str = "openclaw-orchestrator"
    ) -> None:
        """Publish an event to Kafka."""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_service": source_service,
            "data": data
        }

        await self.producer.send_and_wait(topic, value=event)
```

**Step 2: Write kafka_consumer.py**

```python
"""Kafka event consumer."""
import json
from typing import Callable, Dict, Any
from aiokafka import AIOKafkaConsumer
import asyncio

class KafkaConsumer:
    """Consumes events from Kafka."""

    def __init__(self, bootstrap_servers: str, topics: list[str]):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.consumer = None
        self.handlers: Dict[str, Callable] = {}

    def on(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        self.handlers[event_type] = handler

    async def start(self, group_id: str = "openclaw-orchestrator"):
        """Start the consumer."""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        await self.consumer.start()

    async def stop(self):
        """Stop the consumer."""
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        """Consume and process events."""
        async for msg in self.consumer:
            event = msg.value
            event_type = event.get("event_type")

            handler = self.handlers.get(event_type)
            if handler:
                await handler(event)
```

**Step 3: Write tests**

**Step 4: Run tests**

**Step 5: Commit**

---

### Task 2.7: Create FastAPI Routes

**Files:**
- Create: `services/openclaw-orchestrator/src/routes/orchestration.py`
- Create: `services/openclaw-orchestrator/src/routes/skills.py`
- Create: `services/openclaw-orchestrator/src/routes/health.py`

**Step 1: Write orchestration.py**

```python
"""Orchestration API routes."""
from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram

from ..models.request import OrchestrationRequest
from ..models.response import OrchestrationResponse
from ..core.router import Router
from ..core.skill_registry import SkillRegistry
from ..core.gpu_scheduler import GPUScheduler

router = APIRouter(prefix="/v1", tags=["orchestration"])

# Metrics
orchestration_counter = Counter(
    'orchestration_requests_total',
    'Total orchestration requests',
    ['status']
)
orchestration_duration = Histogram(
    'orchestration_duration_seconds',
    'Orchestration duration'
)

# Dependencies (simplified for now)
_router = None

async def get_router():
    global _router
    return _router

@router.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(
    request: OrchestrationRequest,
    router: Router = Depends(get_router)
):
    """Execute orchestration through specified skills."""
    with orchestration_duration.time():
        try:
            response = await router.orchestrate(request)

            if response.status.value == "success":
                orchestration_counter.labels(status="success").inc()
            else:
                orchestration_counter.labels(status="error").inc()

            return response

        except Exception as e:
            orchestration_counter.labels(status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Write skills.py**

```python
"""Skills API routes."""
from fastapi import APIRouter
from ..core.skill_registry import SkillRegistry
from ..models.skill import Skill

router = APIRouter(prefix="/v1/skills", tags=["skills"])

@router.get("", response_model=list[Skill])
async def list_skills():
    """List all registered skills."""
    # TODO: Implement
    return []

@router.get("/{skill_name}", response_model=Skill)
async def get_skill(skill_name: str):
    """Get a specific skill."""
    # TODO: Implement
    pass
```

**Step 3: Write health.py**

```python
"""Health check routes."""
from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter(tags=["health"])

_start_time = time.time()

@router.get("/health/live")
async def liveness():
    """Liveness probe."""
    return "OK"

@router.get("/health/ready")
async def readiness():
    """Readiness probe."""
    uptime = time.time() - _start_time
    return {
        "ready": True,
        "uptime": uptime,
        "dependencies": {
            "redis": "ok",  # TODO: Check Redis
            "kafka": "ok"   # TODO: Check Kafka
        }
    }
```

**Step 4: Update main.py**

```python
"""OpenClaw Orchestrator main application."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .routes import orchestration, skills, health
from .core.skill_registry import SkillRegistry
from .core.gpu_scheduler import GPUScheduler
from .core.router import Router
from .core.kafka_producer import KafkaProducer
import redis.asyncio as redis

# Global instances
registry = SkillRegistry()
gpu_scheduler = GPUScheduler()
kafka_producer = KafkaProducer("kafka.shared.svc.cluster.local:9092")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    await kafka_producer.start()

    # Initialize router with dependencies
    global _router
    _router = Router(
        registry=registry,
        gpu_scheduler=gpu_scheduler,
        redis_client=redis.Redis(host="redis.shared.svc.cluster.local", port=6379)
    )
    await _router.__aenter__()

    yield

    # Shutdown
    await _router.__aexit__()
    await kafka_producer.stop()

app = FastAPI(
    title="OpenClaw Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(orchestration.router)
app.include_router(skills.router)
app.include_router(health.router)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "openclaw-orchestrator",
        "version": "1.0.0",
        "status": "running"
    }
```

**Step 5: Write tests**

**Step 6: Run tests**

**Step 7: Commit**

---

### Task 2.8: Update Config and Requirements

**Files:**
- Modify: `services/openclaw-orchestrator/config.py`
- Modify: `services/openclaw-orchestrator/requirements.txt`

**Step 1: Update config.py**

```python
"""OpenClaw Orchestrator configuration."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Service
    app_name: str = "openclaw-orchestrator"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # GPU
    gpu_enabled: bool = True
    cuda_visible_devices: str = "0"

    # Redis
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # Kafka
    kafka_bootstrap_servers: str = "kafka.shared.svc.cluster.local:9092"
    kafka_consumer_group: str = "openclaw-orchestrator"

    # Vector DB
    vector_db_host: str = "vector-db.shared.svc.cluster.local"
    vector_db_port: int = 19530

    # Skills
    skills_config_path: str = "/app/configs/skills"

    # Monitoring
    jaeger_host: str = "jaeger.shared.svc.cluster.local"
    jaeger_port: int = 6831
    jaeger_sample_rate: float = 0.1

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

settings = Settings()
```

**Step 2: Update requirements.txt**

```
# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Redis
redis==5.0.1
hiredis==2.2.3

# Kafka
aiokafka==0.9.0

# Kubernetes
kubernetes==28.1.0

# GPU
pynvml==11.5.0

# Monitoring
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
opentelemetry-exporter-jaeger==1.21.0

# HTTP
aiohttp==3.9.1
httpx==0.25.2

# Utilities
python-multipart==0.0.6
pyyaml==6.0.1
```

**Step 3: Commit**

---

### Task 2.9: Update Deployment

**Files:**
- Modify: `infrastructure/kubernetes/base/openclaw/deployment.yaml`

**Step 1: Update deployment.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openclaw-orchestrator
  namespace: live
  labels:
    app: openclaw-orchestrator
    project: project-chimera
spec:
  replicas: 1
  selector:
    matchLabels:
      app: openclaw-orchestrator
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: openclaw-orchestrator
        project: project-chimera
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      priorityClassName: high-priority
      serviceAccountName: openclaw-orchestrator
      containers:
      - name: openclaw-orchestrator
        image: localhost:30500/project-chimera/openclaw-orchestrator:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: APP_NAME
          value: "openclaw-orchestrator"
        - name: APP_ENV
          value: "production"
        - name: APP_DEBUG
          value: "false"
        - name: REDIS_HOST
          value: "redis.shared.svc.cluster.local"
        - name: REDIS_PORT
          value: "6379"
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka.shared.svc.cluster.local:9092"
        - name: VECTOR_DB_HOST
          value: "vector-db.shared.svc.cluster.local"
        - name: VECTOR_DB_PORT
          value: "19530"
        - name: JAEGER_HOST
          value: "jaeger.shared.svc.cluster.local"
        - name: JAEGER_PORT
          value: "6831"
        - name: GPU_ENABLED
          value: "true"
        - name: K8S_NAMESPACE
          value: "live"
        - name: K8S_POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: K8S_POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        resources:
          requests:
            cpu: "2"
            memory: 8Gi
            nvidia.com/gpu: "1"
          limits:
            cpu: "4"
            memory: 16Gi
            nvidia.com/gpu: "1"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 30
        volumeMounts:
        - name: skills
          mountPath: /app/configs
          readOnly: true
        - name: models
          mountPath: /app/models
          readOnly: true
        - name: config
          mountPath: /app/configs
          readOnly: true
        - name: model-cache
          mountPath: /app/models/cache
      volumes:
      - name: skills
        configMap:
          name: skills-config
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
      - name: config
        configMap:
          name: openclaw-config
      - name: model-cache
        emptyDir:
          sizeLimit: 10Gi
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: openclaw-orchestrator
  namespace: live
---
apiVersion: v1
kind: Service
metadata:
  name: openclaw-orchestrator
  namespace: live
  labels:
    app: openclaw-orchestrator
    project: project-chimera
spec:
  selector:
    app: openclaw-orchestrator
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
```

**Step 2: Commit**

---

## Phase 3: SceneSpeak Agent

**Estimated Time:** 5 hours

**Port:** 8001
**GPU:** 1x NVIDIA GPU (8GB)

### Task 3.1: Create SceneSpeak Base Models

**Files:**
- Create: `services/SceneSpeak Agent/src/models/__init__.py`
- Create: `services/SceneSpeak Agent/src/models/request.py`
- Create: `services/SceneSpeak Agent/src/models/response.py`

**Step 1: Write models**

```python
# services/SceneSpeak Agent/src/models/request.py

from pydantic import BaseModel, Field
from typing import Optional

class GenerationRequest(BaseModel):
    """Request for dialogue generation."""
    context: str = Field(..., min_length=1, max_length=1000, description="Scene context")
    character: str = Field(..., description="Character name")
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0, description="Sentiment -1.0 to 1.0")
    max_tokens: Optional[int] = Field(default=256, ge=1, le=1024)
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    use_cache: Optional[bool] = True

# services/SceneSpeak Agent/src/models/response.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GenerationResponse(BaseModel):
    """Response from dialogue generation."""
    request_id: str
    dialogue: str
    character: str
    sentiment_used: float
    tokens: int
    confidence: float
    from_cache: bool
    generation_time_ms: float
    model_version: str
    timestamp: datetime
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 3.2: Create LLM Engine

**Files:**
- Create: `services/SceneSpeak Agent/src/core/llm_engine.py`

**Step 1: Write llm_engine.py**

```python
"""LLM engine for dialogue generation."""
import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from ..models.request import GenerationRequest
from ..models.response import GenerationResponse


class LLMEngine:
    """Manages LLM model loading and inference."""

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        device: str = "cuda",
        quantization: bool = True
    ):
        self.model_name = model_name
        self.device = device
        self.quantization = quantization
        self.model = None
        self.tokenizer = None
        self.loaded = False

    async def load(self) -> None:
        """Load the model."""
        if self.loaded:
            return

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir="/app/models"
        )

        # Configure quantization
        if self.quantization:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
        else:
            quantization_config = None

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            cache_dir="/app/models",
            torch_dtype=torch.float16
        )

        self.model.eval()
        self.loaded = True

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate dialogue."""
        if not self.loaded:
            await self.load()

        start_time = time.time()
        request_id = hashlib.md5(
            f"{request.context}:{request.character}:{request.sentiment}".encode()
        ).hexdigest()

        # Build prompt
        prompt = self._build_prompt(request)

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode
        dialogue = self.tokenizer.decode(
            output_ids[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        generation_time = (time.time() - start_time) * 1000

        return GenerationResponse(
            request_id=request_id,
            dialogue=dialogue.strip(),
            character=request.character,
            sentiment_used=request.sentiment,
            tokens=output_ids.shape[1] - inputs['input_ids'].shape[1],
            confidence=0.8,  # Placeholder
            from_cache=False,
            generation_time_ms=generation_time,
            model_version=self.model_name,
            timestamp=datetime.utcnow()
        )

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build prompt from request."""
        sentiment_desc = self._sentiment_to_description(request.sentiment)

        prompt = f"""You are {request.character}, a character in a live theatre performance.

Context: {request.context}
Current mood: {sentiment_desc}

Generate a response that fits this scene and mood:"""

        return prompt

    def _sentiment_to_description(self, sentiment: float) -> str:
        """Convert sentiment value to description."""
        if sentiment > 0.7:
            return "very happy and energetic"
        elif sentiment > 0.3:
            return "happy and positive"
        elif sentiment > -0.3:
            return "neutral and calm"
        elif sentiment > -0.7:
            return "sad and melancholic"
        else:
            return "very dark and troubled"
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 3.3: Create Prompt Manager

**Files:**
- Create: `services/SceneSpeak Agent/src/core/prompt_manager.py`

**Step 1: Write prompt_manager.py**

```python
"""Prompt template management."""
from pathlib import Path
import yaml
from typing import Dict, Any


class PromptManager:
    """Manages prompt templates."""

    def __init__(self, templates_path: str = "/app/configs/prompts"):
        self.templates_path = Path(templates_path)
        self.templates: Dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load prompt templates from files."""
        if not self.templates_path.exists():
            self._load_defaults()
            return

        for template_file in self.templates_path.glob("**/*.md"):
            name = template_file.stem
            with open(template_file) as f:
                self.templates[name] = f.read()

    def _load_defaults(self) -> None:
        """Load default prompts."""
        self.templates["dialogue-generation"] = self._default_dialogue_prompt()

    def _default_dialogue_prompt(self) -> str:
        """Default dialogue generation prompt."""
        return """Generate dialogue for a theatre character.

Context: {context}
Character: {character}
Sentiment: {sentiment}

Generate appropriate dialogue:"""

    def get_template(self, name: str) -> str:
        """Get a template by name."""
        return self.templates.get(name, "")

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables."""
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing variable: {e}")
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 3.4: Create Cache Layer

**Files:**
- Create: `services/SceneSpeak Agent/src/core/cache.py`

**Step 1: Write cache.py**

```python
"""Response caching layer."""
import hashlib
import json
from typing import Optional, Any
import redis.asyncio as redis


class ResponseCache:
    """Caches LLM responses."""

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl: int = 3600
    ):
        self.redis = redis_client
        self.ttl = ttl

    def _make_key(self, prompt: str, params: dict) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = f"{prompt}:{json.dumps(params, sort_keys=True)}"
        return f"chimera:scenespeak:cache:{hashlib.sha256(key_data.encode()).hexdigest()}"

    async def get(self, prompt: str, params: dict) -> Optional[Any]:
        """Get cached response."""
        key = self._make_key(prompt, params)
        cached = await self.redis.get(key)

        if cached:
            return json.loads(cached)
        return None

    async def set(self, prompt: str, params: dict, response: Any) -> None:
        """Cache a response."""
        key = self._make_key(prompt, params)
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(response)
        )

    async def clear(self) -> None:
        """Clear all cache."""
        # Delete all keys matching pattern
        for key in await self.redis.keys("chimera:scenespeak:cache:*"):
            await self.redis.delete(key)
```

**Step 2: Write tests**

**Step 3: Run tests**

**Step 4: Commit**

---

### Task 3.5: Create SceneSpeak Routes

**Files:**
- Create: `services/SceneSpeak Agent/src/routes/generation.py`

**Step 1: Write generation.py**

```python
"""Generation API routes."""
from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram

from ..models.request import GenerationRequest
from ..models.response import GenerationResponse
from ..core.llm_engine import LLMEngine
from ..core.cache import ResponseCache
import redis.asyncio as redis

router = APIRouter(prefix="/v1", tags=["generation"])

# Metrics
generation_counter = Counter('scenespeak_generations_total', 'Total generations', ['status'])
generation_duration = Histogram('scenespeak_generation_duration_seconds', 'Generation duration')

# Dependencies
_engine = None
_cache = None

async def get_engine() -> LLMEngine:
    global _engine
    return _engine

async def get_cache() -> ResponseCache:
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
                await cache.set(prompt, params, response.dict())

            return response

        except Exception as e:
            generation_counter.labels(status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Update main.py**

**Step 3: Write tests**

**Step 4: Run tests**

**Step 5: Commit**

---

### Task 3.6: Update SceneSpeak Config

**Files:**
- Modify: `services/SceneSpeak Agent/config.py`

**Step 1: Update config.py**

```python
"""SceneSpeak Agent configuration."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Service
    app_name: str = "SceneSpeak Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # Model
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"
    device: str = "cuda"
    quantization_enabled: bool = True
    model_download_path: str = "/app/models"
    model_cache_enabled: bool = True

    # Generation
    max_tokens_default: int = 256
    temperature_default: float = 0.8
    top_p_default: float = 0.95

    # Cache
    cache_enabled: bool = True
    cache_ttl: int = 3600

    # Redis
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_password: str = ""

    # Kafka
    kafka_bootstrap_servers: str = "kafka.shared.svc.cluster.local:9092"

    # Monitoring
    jaeger_host: str = "jaeger.shared.svc.cluster.local"
    jaeger_port: int = 6831

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 2: Commit**

---

## Phase 4-9: Other Services

Due to length constraints, the remaining services (Captioning, BSL, Sentiment, Lighting, Safety, Operator Console) follow the same pattern as OpenClaw and SceneSpeak:

For each service:
1. Create base models (request/response)
2. Create core module (main business logic)
3. Create routes (FastAPI endpoints)
4. Update config.py
5. Update requirements.txt
6. Update Kubernetes deployment
7. Write tests
8. Commit

**Key implementation notes:**

- **Captioning**: Use `openai/whisper-base` model, audio stream handling
- **BSL**: Use `Helsinki-NLP/opus-mt-en-ROMANCE` for translation
- **Sentiment**: Use `distilbert-base-uncased-finetuned-sst-2-english`
- **Lighting**: Implement sACN protocol using `sacn` library
- **Safety**: Word list + ML model (BERT) for content checking
- **Console**: WebSocket for real-time events, simple HTML/JS UI

---

## Phase 10: Integration & Testing

**Estimated Time:** 8-10 hours

### Task 10.1: Create Integration Tests

**Files:**
- Create: `tests/integration/test_full_pipeline.py`

**Step 1: Write full pipeline test**

```python
"""End-to-end integration test."""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_full_pipeline():
    """Test full pipeline from sentiment to dialogue to safety."""

    # This test would verify:
    # 1. Sentiment analysis works
    # 2. SceneSpeak generates dialogue
    # 3. Safety filter approves
    # 4. Events flow through Kafka

    pass
```

**Step 2: Commit**

---

### Task 10.2: Create Load Tests

**Files:**
- Update: `tests/load/locustfile.py`

**Step 1: Update locustfile.py**

```python
"""Load testing scenario."""
from locust import HttpUser, task, between

class ChimeraUser(HttpUser):
    """Simulates normal user load."""

    wait_time = between(1, 3)

    @task(7)
    def generate_dialogue(self):
        """Generate dialogue."""
        self.client.post(
            "/v1/generate",
            json={
                "context": "A garden scene",
                "character": "protagonist",
                "sentiment": 0.5
            }
        )

    @task(2)
    def check_sentiment(self):
        """Check sentiment."""
        self.client.post(
            "/v1/analyze",
            json={"text": "The audience seems excited!"}
        )

    @task(1)
    def check_safety(self):
        """Check content safety."""
        self.client.post(
            "/v1/check",
            json={"content": "This is a test message"}
        )
```

**Step 2: Commit**

---

## Phase 11: Monitoring & Documentation

**Estimated Time:** 6-8 hours

### Task 11.1: Create Grafana Dashboards

**Files:**
- Create: `infrastructure/kubernetes/base/monitoring/grafana/dashboards/chimera-overview.json`
- Create: `infrastructure/kubernetes/base/monitoring/grafana/dashboards/chimera-ai-services.json`

**Step 1: Create overview dashboard**

```json
{
  "dashboard": {
    "title": "Project Chimera - System Overview",
    "tags": ["chimera", "overview"],
    "timezone": "browser",
    "panels": [...]
  }
}
```

**Step 2: Commit**

---

### Task 11.2: Create API Documentation

**Files:**
- Create: `docs/api/openapi.yaml`

**Step 1: Create unified OpenAPI spec**

**Step 2: Commit**

---

## Phase 12: Open Source Prep

**Estimated Time:** 4-6 hours

### Task 12.1: Create Repository Files

**Files:**
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Update: `README.md`

**Step 1: Create LICENSE (MIT)**

**Step 2: Create CONTRIBUTING.md**

**Step 3: Create CODE_OF_CONDUCT.md**

**Step 4: Create SECURITY.md**

**Step 5: Update README.md**

**Step 6: Commit**

---

### Task 12.2: Create GitHub Templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

**Step 1: Create issue templates**

**Step 2: Create PR template**

**Step 3: Commit**

---

## Task List Summary

### Phase 1: Infrastructure (4-6h)
- [ ] 1.1 Fix Docker permissions
- [ ] 1.2 Configure k3s registry
- [ ] 1.3 Run bootstrap
- [ ] 1.4 Create documentation standards

### Phase 2: OpenClaw (6h)
- [ ] 2.1 Create base models
- [ ] 2.2 Create skill registry
- [ ] 2.3 Create GPU scheduler
- [ ] 2.4 Create router
- [ ] 2.5 Create policy engine
- [ ] 2.6 Create Kafka integration
- [ ] 2.7 Create FastAPI routes
- [ ] 2.8 Update config and requirements

### Phase 3: SceneSpeak (5h)
- [ ] 3.1 Create base models
- [ ] 3.2 Create LLM engine
- [ ] 3.3 Create prompt manager
- [ ] 3.4 Create cache layer
- [ ] 3.5 Create routes
- [ ] 3.6 Update config

### Phase 4-9: Other Services (20-25h)
- [ ] Captioning Agent (3h)
- [ ] BSL-Text2Gloss Agent (3h)
- [ ] Sentiment Agent (2h)
- [ ] Lighting Control (2h)
- [ ] Safety Filter (2h)
- [ ] Operator Console (2h)

### Phase 10: Integration (8-10h)
- [ ] 10.1 Integration tests
- [ ] 10.2 Load tests
- [ ] 10.3 Security tests

### Phase 11: Monitoring (6-8h)
- [ ] 11.1 Grafana dashboards
- [ ] 11.2 API documentation
- [ ] 11.3 Runbooks

### Phase 12: Open Source (4-6h)
- [ ] 12.1 Repository files
- [ ] 12.2 GitHub templates

**Total:** ~130 tasks over 12 phases

---

## Execution Notes

### Model Download

Models will be downloaded on first container start:
- Mistral-7B: ~4GB (quantized)
- Whisper-base: ~150MB
- DistilBERT: ~250MB
- OPUS-MT: ~300MB

**Total download:** ~5GB

### GPU Requirements

- 1x NVIDIA GPU with 8GB+ VRAM
- CUDA 11.8+ or 12.x
- nvidia-container-toolkit

### Testing Commands

```bash
# Run all tests
make test

# Run specific service tests
pytest tests/unit/test_scenespeak_agent.py -v

# Run integration tests
pytest tests/integration/ -v

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8001
```

### Deployment Commands

```bash
# Build specific service
make build-service SERVICE=SceneSpeak Agent

# Push to local registry
docker push localhost:30500/project-chimera/SceneSpeak Agent:latest

# Deploy specific service
kubectl rollout restart deployment/SceneSpeak Agent -n live

# Check logs
kubectl logs -f -n live deployment/SceneSpeak Agent
```

---

**End of Implementation Plan**

*This plan provides complete implementation guidance for Project Chimera. Execute tasks in order, committing after each task. Use TDD: write test, implement, verify, commit.*

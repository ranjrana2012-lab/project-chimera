# Nemo Claw Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace OpenClaw Orchestrator with NVIDIA Nemo Claw, adding OpenShell policy guardrails and Privacy Router for DGX-accelerated Nemotron inference while maintaining compatibility with existing 8 agents.

**Architecture:** Nemo Claw runtime with OpenShell policy layer (input/output filtering), Privacy Router (95% local Nemotron on DGX, 5% guarded cloud fallback), Agent Coordinator with adapter pattern for existing agents, Redis-backed state machine, FastAPI WebSocket gateway.

**Tech Stack:** NVIDIA Nemo Claw, OpenShell Runtime, Nemotron (ARM64), FastAPI, Redis, Pydantic, pytest, Playwright

---

## File Structure

```
services/nemoclaw-orchestrator/
├── main.py                          # FastAPI application with policy middleware
├── config.py                        # Configuration with DGX settings
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # ARM64-optimized container
├── .env.example                     # Environment template
│
├── policy/
│   ├── __init__.py
│   ├── engine.py                    # OpenShell policy engine
│   ├── rules.py                     # Chimera-specific policy rules
│   └── filters.py                   # Input/output sanitization filters
│
├── llm/
│   ├── __init__.py
│   ├── privacy_router.py            # LLM backend routing (local/cloud)
│   ├── nemotron_client.py           # DGX Nemotron client
│   └── guarded_cloud.py             # Cloud API with PII stripping
│
├── agents/
│   ├── __init__.py
│   ├── coordinator.py               # Agent coordination with policy filtering
│   ├── adapters.py                  # Adapter classes for each agent
│   └── registry.py                  # Agent registry and discovery
│
├── state/
│   ├── __init__.py
│   ├── machine.py                   # Show state machine
│   └── store.py                     # Redis-backed state storage
│
├── websocket/
│   ├── __init__.py
│   ├── manager.py                   # WebSocket connection manager
│   └── handlers.py                  # WebSocket message handlers
│
├── resilience/
│   ├── __init__.py
│   ├── retry.py                     # Retry logic with exponential backoff
│   └── circuit_breaker.py           # Circuit breaker pattern
│
├── errors/
│   ├── __init__.py
│   ├── exceptions.py                # Custom exception classes
│   └── handlers.py                  # Global error handlers
│
└── tests/
    ├── unit/
    │   ├── test_policy_engine.py
    │   ├── test_privacy_router.py
    │   ├── test_agent_coordinator.py
    │   └── test_state_machine.py
    ├── integration/
    │   ├── test_agent_flow.py
    │   ├── test_show_lifecycle.py
    │   └── test_websocket_updates.py
    └── e2e/
        └── show-lifecycle.spec.ts
```

---

## Phase 1: Foundation Setup

### Task 1: Create Service Structure and Configuration

**Files:**
- Create: `services/nemoclaw-orchestrator/main.py`
- Create: `services/nemoclaw-orchestrator/config.py`
- Create: `services/nemoclaw-orchestrator/requirements.txt`
- Create: `services/nemoclaw-orchestrator/.env.example`

- [ ] **Step 1: Create requirements.txt with dependencies**

```txt
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-multipart>=0.0.6

# HTTP Client
httpx>=0.25.0

# Redis
redis>=5.0.0

# OpenTelemetry
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0

# NVIDIA
nvidia-nemoclaw>=1.0.0  # Placeholder - adjust based on actual package

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
playwright>=1.40.0

# Development
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create config.py with DGX settings**

```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Service
    service_name: str = "nemoclaw-orchestrator"
    port: int = 8000
    debug: bool = False

    # DGX Configuration
    nemotron_model: str = "nemotron-8b"
    dgx_gpu_id: int = 0
    dgx_endpoint: str = "http://localhost:8000"  # Nemotron endpoint

    # Privacy Router
    local_ratio: float = 0.95  # 95% local, 5% cloud
    cloud_fallback_enabled: bool = True

    # Agent URLs (existing agents)
    scenespeak_agent_url: str = "http://localhost:8001"
    captioning_agent_url: str = "http://localhost:8002"
    bsl_agent_url: str = "http://localhost:8003"
    sentiment_agent_url: str = "http://localhost:8004"
    lighting_sound_music_url: str = "http://localhost:8005"
    safety_filter_url: str = "http://localhost:8006"
    operator_console_url: str = "http://localhost:8007"
    music_generation_url: str = "http://localhost:8011"
    autonomous_agent_url: str = "http://localhost:8008"

    # State Store
    redis_url: str = "redis://localhost:6379"
    redis_show_state_ttl: int = 86400  # 24 hours

    # Policy
    policy_strictness: str = "medium"  # low, medium, high

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Logging
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env")

def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Create .env.example template**

```bash
# Service Configuration
SERVICE_NAME=nemoclaw-orchestrator
PORT=8000
DEBUG=false

# DGX / Nemotron Configuration
NEMOTRON_MODEL=nemotron-8b
DGX_GPU_ID=0
DGX_ENDPOINT=http://localhost:8000

# Privacy Router
LOCAL_RATIO=0.95
CLOUD_FALLBACK_ENABLED=true

# Agent URLs
SCENESPEAK_AGENT_URL=http://localhost:8001
CAPTIONING_AGENT_URL=http://localhost:8002
BSL_AGENT_URL=http://localhost:8003
SENTIMENT_AGENT_URL=http://localhost:8004
LIGHTING_SOUND_MUSIC_URL=http://localhost:8005
SAFETY_FILTER_URL=http://localhost:8006
OPERATOR_CONSOLE_URL=http://localhost:8007
MUSIC_GENERATION_URL=http://localhost:8011
AUTONOMOUS_AGENT_URL=http://localhost:8008

# Redis State Store
REDIS_URL=redis://localhost:6379
REDIS_SHOW_STATE_TTL=86400

# Policy
POLICY_STRICTNESS=medium

# OpenTelemetry
OTLP_ENDPOINT=http://localhost:4317

# Logging
LOG_LEVEL=INFO
```

- [ ] **Step 4: Create basic FastAPI app skeleton in main.py**

```python
from fastapi import FastAPI
from contextlib import asyncio
import logging

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("Nemo Claw Orchestrator starting up")
    yield
    logger.info("Nemo Claw Orchestrator shutting down")

app = FastAPI(
    title="Nemo Claw Orchestrator",
    description="Project Chimera orchestration with Nemo Claw security and privacy",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health/live")
async def liveness():
    return {"status": "alive", "service": settings.service_name}

@app.get("/health/ready")
async def readiness():
    return {"status": "ready", "service": settings.service_name}
```

- [ ] **Step 5: Run to verify basic setup**

```bash
cd services/nemoclaw-orchestrator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Expected: Server starts on port 8000, `/health/live` returns `{"status": "alive"}`

- [ ] **Step 6: Commit foundation**

```bash
git add services/nemoclaw-orchestrator/
git commit -m "feat(nemoclaw): create service structure with FastAPI skeleton

- Add requirements.txt with all dependencies
- Add config.py with DGX and agent settings
- Add .env.example template
- Add basic FastAPI app with health endpoints

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: Policy Engine

### Task 2: Create Policy Engine Core

**Files:**
- Create: `services/nemoclaw-orchestrator/policy/__init__.py`
- Create: `services/nemoclaw-orchestrator/policy/engine.py`
- Create: `services/nemoclaw-orchestrator/policy/rules.py`
- Create: `services/nemoclaw-orchestrator/tests/unit/test_policy_engine.py`

- [ ] **Step 1: Create policy package init**

```python
# services/nemoclaw-orchestrator/policy/__init__.py
from .engine import PolicyEngine, PolicyAction, PolicyResult, PolicyRule
from .rules import CHIMERA_POLICIES

__all__ = [
    "PolicyEngine",
    "PolicyAction",
    "PolicyResult",
    "PolicyRule",
    "CHIMERA_POLICIES",
]
```

- [ ] **Step 2: Write failing test for policy engine**

```python
# services/nemoclaw-orchestrator/tests/unit/test_policy_engine.py
import pytest
from policy.engine import PolicyEngine, PolicyAction, PolicyRule, PolicyResult
from policy.rules import CHIMERA_POLICIES

class TestPolicyEngine:
    def test_engine_initializes_with_policies(self):
        engine = PolicyEngine(CHIMERA_POLICIES)
        assert len(engine.policies) > 0

    def test_check_input_returns_allow_for_safe_sentiment(self):
        engine = PolicyEngine(CHIMERA_POLICIES)
        result = engine.check_input(
            agent="sentiment-agent",
            skill="analyze_sentiment",
            input_data={"text": "happy message"}
        )
        assert result.action == PolicyAction.ALLOW

    def test_check_input_returns_deny_for_dangerous_command(self):
        engine = PolicyEngine(CHIMERA_POLICIES)
        result = engine.check_input(
            agent="autonomous-agent",
            skill="execute",
            input_data={"command": "rm -rf /"}
        )
        assert result.action == PolicyAction.DENY
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd services/nemoclaw-orchestrator
pytest tests/unit/test_policy_engine.py -v
```

Expected: FAIL with "PolicyEngine not defined"

- [ ] **Step 4: Implement PolicyEngine class**

```python
# services/nemoclaw-orchestrator/policy/engine.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    SANITIZE = "sanitize"
    ESCALATE = "escalate"

@dataclass
class PolicyResult:
    action: PolicyAction
    reason: str
    rule_name: Optional[str] = None
    sanitization_rules: Optional[Dict[str, Any]] = None

@dataclass
class PolicyRule:
    name: str
    agent: str
    action: PolicyAction
    conditions: Dict[str, Any]
    output_filter: bool = True

class PolicyEngine:
    def __init__(self, policies: List[PolicyRule]):
        self.policies = policies
        self._build_agent_index()

    def _build_agent_index(self):
        """Build index for fast agent lookup"""
        self._agent_policies: Dict[str, List[PolicyRule]] = {}
        for policy in self.policies:
            if policy.agent not in self._agent_policies:
                self._agent_policies[policy.agent] = []
            self._agent_policies[policy.agent].append(policy)

    def check_input(
        self,
        agent: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> PolicyResult:
        """Check if input complies with policy"""

        # Get applicable policies for this agent
        applicable = self._agent_policies.get(agent, [])

        if not applicable:
            # No specific policy - allow by default
            return PolicyResult(
                action=PolicyAction.ALLOW,
                reason="No specific policy applies"
            )

        # Check policies in priority order (assume already sorted)
        for policy in applicable:
            if self._conditions_match(policy.conditions, input_data):
                return PolicyResult(
                    action=policy.action,
                    reason=f"Policy '{policy.name}' matched",
                    rule_name=policy.name
                )

        # No policy matched - default to allow
        return PolicyResult(
            action=PolicyAction.ALLOW,
            reason="No policy conditions matched"
        )

    def _conditions_match(
        self,
        conditions: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> bool:
        """Check if input matches policy conditions"""
        # For now, empty conditions = always match
        if not conditions:
            return True

        # Simple key-value matching (extend for complex conditions)
        for key, value in conditions.items():
            if key not in input_data:
                return False
            if input_data[key] != value:
                return False
        return True

    async def sanitize_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sanitize input data"""
        from policy.filters import InputSanitizer
        sanitizer = InputSanitizer()
        return await sanitizer.sanitize(input_data)

    async def filter_output(
        self,
        agent: str,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter output through policy"""
        from policy.filters import OutputFilter
        filter = OutputFilter()
        return await filter.filter(response, agent)
```

- [ ] **Step 5: Implement CHIMERA_POLICIES rules**

```python
# services/nemoclaw-orchestrator/policy/rules.py
from policy.engine import PolicyRule, PolicyAction

CHIMERA_POLICIES = [
    # Safety Filter - highest priority
    PolicyRule(
        name="safety-first",
        agent="safety-filter",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=True
    ),

    # Sentiment - free to run
    PolicyRule(
        name="sentiment-free",
        agent="sentiment-agent",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=False
    ),

    # SceneSpeak - sanitize long content
    PolicyRule(
        name="dialogue-safety",
        agent="scenespeak-agent",
        action=PolicyAction.SANITIZE,
        conditions={},
        output_filter=True
    ),

    # Autonomous - escalate dangerous commands
    PolicyRule(
        name="autonomous-danger",
        agent="autonomous-agent",
        action=PolicyAction.DENY,
        conditions={"command_contains": ["rm", "delete", "format"]},
        output_filter=True
    ),

    PolicyRule(
        name="autonomous-escalate",
        agent="autonomous-agent",
        action=PolicyAction.ESCALATE,
        conditions={"complexity": "high"},
        output_filter=True
    ),

    # Captioning - allow
    PolicyRule(
        name="captioning-allow",
        agent="captioning-agent",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=False
    ),

    # BSL - allow
    PolicyRule(
        name="bsl-allow",
        agent="bsl-agent",
        action=PolicyAction.ALLOW,
        conditions={},
        output_filter=False
    ),
]
```

- [ ] **Step 6: Update engine to handle command_contains condition**

```python
# Add to PolicyEngine._conditions_match method
def _conditions_match(self, conditions, input_data):
    if not conditions:
        return True

    for key, value in conditions.items():
        if key == "command_contains":
            # Check if command contains dangerous strings
            command = input_data.get("command", "")
            if any(dangerous in command.lower() for dangerous in value):
                return True
            return False
        elif key not in input_data:
            return False
        elif input_data[key] != value:
            return False

    return True
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/unit/test_policy_engine.py -v
```

Expected: PASS for all tests

- [ ] **Step 8: Commit policy engine**

```bash
git add services/nemoclaw-orchestrator/policy/
git add services/nemoclaw-orchestrator/tests/unit/test_policy_engine.py
git commit -m "feat(nemoclaw): implement OpenShell policy engine

- Add PolicyEngine with input checking and action routing
- Add CHIMERA_POLICIES for all agents
- Add unit tests for policy enforcement
- Support ALLOW, DENY, SANITIZE, ESCALATE actions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2.5: Implement Policy Filters

**Files:**
- Create: `services/nemoclaw-orchestrator/policy/filters.py`
- Create: `services/nemoclaw-orchestrator/tests/unit/test_policy_filters.py`

- [ ] **Step 1: Write failing test for input sanitization**

```python
# services/nemoclaw-orchestrator/tests/unit/test_policy_filters.py
import pytest
from policy.filters import InputSanitizer, OutputFilter

class TestInputSanitizer:
    @pytest.mark.asyncio
    async def test_removes_profanity(self):
        sanitizer = InputSanitizer()
        result = await sanitizer.sanitize({"text": "This is f***ing bad"})
        assert "f***ing" not in result["text"]

    @pytest.mark.asyncio
    async def test_truncates_long_text(self):
        sanitizer = InputSanitizer(max_length=100)
        long_text = "x" * 1000
        result = await sanitizer.sanitize({"dialogue": long_text})
        assert len(result["dialogue"]) <= 100

class TestOutputFilter:
    @pytest.mark.asyncio
    async def test_filters_pii_from_output(self):
        filter = OutputFilter()
        result = await filter.filter(
            {"text": "Call me at 555-123-4567"},
            "scenespeak-agent"
        )
        assert "555-123-4567" not in result["text"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_policy_filters.py -v
```

Expected: FAIL with "InputSanitizer not defined"

- [ ] **Step 3: Implement InputSanitizer and OutputFilter**

```python
# services/nemoclaw-orchestrator/policy/filters.py
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class InputSanitizer:
    """Sanitizes input data to remove harmful content"""

    def __init__(self, max_length: int = 5000):
        self.max_length = max_length
        # Simple profanity list (expand in production)
        self.profanity_pattern = re.compile(
            r'\b(fuck|shit|damn|ass|bitch)\b',
            re.IGNORECASE
        )

    async def sanitize(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        result = {}

        for key, value in input_data.items():
            if isinstance(value, str):
                # Remove profanity
                sanitized = self.profanity_pattern.sub('***', value)
                # Truncate if too long
                if len(sanitized) > self.max_length:
                    sanitized = sanitized[:self.max_length] + "..."
                result[key] = sanitized
            elif isinstance(value, dict):
                result[key] = await self.sanitize(value)
            elif isinstance(value, list):
                result[key] = [
                    await self.sanitize(item) if isinstance(item, (dict, str))
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

class OutputFilter:
    """Filters agent output to remove sensitive information"""

    def __init__(self):
        # PII patterns (expand in production)
        self.phone_pattern = re.compile(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        )
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.ssn_pattern = re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        )

    async def filter(
        self,
        response: Dict[str, Any],
        agent: str
    ) -> Dict[str, Any]:
        """Filter output data"""
        result = {}

        for key, value in response.items():
            if isinstance(value, str):
                # Remove PII
                filtered = self.phone_pattern.sub('[PHONE]', value)
                filtered = self.email_pattern.sub('[EMAIL]', filtered)
                filtered = self.ssn_pattern.sub('[SSN]', filtered)
                result[key] = filtered
            elif isinstance(value, dict):
                result[key] = await self.filter(value, agent)
            elif isinstance(value, list):
                result[key] = [
                    await self.filter(item, agent) if isinstance(item, (dict, str))
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_policy_filters.py -v
```

Expected: PASS

- [ ] **Step 5: Commit policy filters**

```bash
git add services/nemoclaw-orchestrator/policy/filters.py
git add services/nemoclaw-orchestrator/tests/unit/test_policy_filters.py
git commit -m "feat(nemoclaw): implement input sanitization and output filtering

- Add InputSanitizer for profanity removal and length limits
- Add OutputFilter for PII removal (phone, email, SSN)
- Add unit tests for filter functionality
- Required by OpenShell policy enforcement

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: Privacy Router & LLM Backend

### Task 3: Implement Privacy Router

**Files:**
- Create: `services/nemoclaw-orchestrator/llm/__init__.py`
- Create: `services/nemoclaw-orchestrator/llm/privacy_router.py`
- Create: `services/nemoclaw-orchestrator/llm/nemotron_client.py`
- Create: `services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py`

- [ ] **Step 1: Create LLM package init**

```python
# services/nemoclaw-orchestrator/llm/__init__.py
from .privacy_router import PrivacyRouter, LLMBackend
from .nemotron_client import NemotronClient

__all__ = ["PrivacyRouter", "LLMBackend", "NemotronClient"]
```

- [ ] **Step 2: Write failing test for privacy router**

```python
# services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py
import pytest
from llm.privacy_router import PrivacyRouter, LLMBackend

class TestPrivacyRouter:
    @pytest.mark.asyncio
    async def test_routes_to_local_when_available(self, mocker):
        mock_nemotron = mocker.AsyncMock()
        mock_nemotron.is_available.return_value = True

        router = PrivacyRouter(dgx_config={"endpoint": "http://localhost:8000"})
        router.nemotron_client = mock_nemotron

        backend = await router.route("Generate dialogue", {})
        assert backend == LLMBackend.NEMOTRON_LOCAL

    @pytest.mark.asyncio
    async def test_fallback_to_cloud_when_local_unavailable(self, mocker):
        mock_nemotron = mocker.AsyncMock()
        mock_nemotron.is_available.return_value = False

        router = PrivacyRouter(dgx_config={"endpoint": "http://localhost:8000"})
        router.nemotron_client = mock_nemotron

        backend = await router.route("Generate dialogue", {})
        assert backend == LLMBackend.CLOUD_GUARDED
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/unit/test_privacy_router.py -v
```

Expected: FAIL with "PrivacyRouter not defined"

- [ ] **Step 4: Implement LLMBackend enum and PrivacyRouter**

```python
# services/nemoclaw-orchestrator/llm/privacy_router.py
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LLMBackend(str, Enum):
    NEMOTRON_LOCAL = "nemotron_local"
    CLOUD_GUARDED = "cloud_guarded"
    FALLBACK = "fallback"

@dataclass
class RouterConfig:
    dgx_endpoint: str
    local_ratio: float = 0.95
    cloud_fallback_enabled: bool = True

class PrivacyRouter:
    def __init__(self, config: RouterConfig):
        self.config = config
        from llm.nemotron_client import NemotronClient
        self.nemotron_client = NemotronClient(config.dgx_endpoint)
        # TODO: Initialize guarded cloud client

    async def route(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> LLMBackend:
        """Decide which LLM backend to use"""

        # 1. Check privacy requirements
        if context.get("requires_privacy", False):
            return LLMBackend.NEMOTRON_LOCAL

        # 2. Check local availability
        if await self.nemotron_client.is_available():
            # Use local based on ratio
            import random
            if random.random() < self.config.local_ratio:
                return LLMBackend.NEMOTRON_LOCAL

        # 3. Fallback to guarded cloud
        if self.config.cloud_fallback_enabled:
            return LLMBackend.CLOUD_GUARDED

        # 4. Last resort
        return LLMBackend.FALLBACK

    async def generate(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate response using routed backend"""
        backend = await self.route(prompt, context)

        if backend == LLMBackend.NEMOTRON_LOCAL:
            return await self.nemotron_client.generate(prompt)
        elif backend == LLMBackend.CLOUD_GUARDED:
            # TODO: Implement guarded cloud call
            return await self._call_guarded_cloud(prompt)
        else:
            raise RuntimeError("All LLM backends unavailable")

    async def _call_guarded_cloud(self, prompt: str) -> str:
        """Call cloud API with PII stripping"""
        # TODO: Implement PII stripping and cloud call
        return "Cloud response (guarded)"
```

- [ ] **Step 5: Implement NemotronClient**

```python
# services/nemoclaw-orchestrator/llm/nemotron_client.py
import httpx
import logging

logger = logging.getLogger(__name__)

class NemotronClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    async def is_available(self) -> bool:
        """Check if Nemotron endpoint is available"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Nemotron unavailable: {e}")
            return False

    async def generate(self, prompt: str) -> str:
        """Generate text using Nemotron"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.endpoint}/generate",
                json={"prompt": prompt}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("text", "")
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/unit/test_privacy_router.py -v
```

Expected: PASS

- [ ] **Step 7: Commit privacy router**

```bash
git add services/nemoclaw-orchestrator/llm/
git add services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py
git commit -m "feat(nemoclaw): implement Privacy Router for LLM backend selection

- Add PrivacyRouter with local/cloud/fallback routing
- Add NemotronClient for DGX local inference
- Implement 95% local ratio with cloud fallback
- Add unit tests for routing logic

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3.5: Implement Guarded Cloud Client

**Files:**
- Create: `services/nemoclaw-orchestrator/llm/guarded_cloud.py`
- Create: `services/nemoclaw-orchestrator/tests/unit/test_guarded_cloud.py`

- [ ] **Step 1: Write failing test for guarded cloud**

```python
# services/nemoclaw-orchestrator/tests/unit/test_guarded_cloud.py
import pytest
from llm.guarded_cloud import GuardedCloudClient

class TestGuardedCloudClient:
    @pytest.mark.asyncio
    async def test_strips_pii_before_sending_to_cloud(self, mocker):
        # Mock cloud API
        mock_post = mocker.patch('httpx.AsyncClient.post')
        mock_post.return_value.json.return_value = {"text": "Response"}
        mock_post.return_value.raise_for_status = mocker.AsyncMock()

        client = GuardedCloudClient(api_key="test-key")
        result = await client.generate("Call me at 555-123-4567")

        # Verify PII was stripped
        call_args = mock_post.call_args
        prompt_sent = call_args[1]["json"]["prompt"]
        assert "555-123-4567" not in prompt_sent
        assert "[PHONE]" in prompt_sent
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_guarded_cloud.py -v
```

Expected: FAIL with "GuardedCloudClient not defined"

- [ ] **Step 3: Implement GuardedCloudClient**

```python
# services/nemoclaw-orchestrator/llm/guarded_cloud.py
import httpx
import os
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

class GuardedCloudClient:
    """Cloud LLM client with PII stripping for privacy"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_endpoint: str = "https://api.anthropic.com/v1/messages"
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.api_endpoint = api_endpoint

        # PII patterns (same as OutputFilter)
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

    def _strip_pii(self, text: str) -> str:
        """Remove PII from text before sending to cloud"""
        # Replace PII with placeholders
        text = self.phone_pattern.sub('[PHONE]', text)
        text = self.email_pattern.sub('[EMAIL]', text)
        text = self.ssn_pattern.sub('[SSN]', text)
        return text

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using cloud API with PII protection"""

        # Strip PII before sending
        sanitized_prompt = self._strip_pii(prompt)

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": sanitized_prompt}]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def is_available(self) -> bool:
        """Check if cloud API is available"""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.api_endpoint,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                )
                return response.status_code == 200
        except Exception:
            return False
```

- [ ] **Step 4: Update PrivacyRouter to use GuardedCloudClient**

```python
# Update services/nemoclaw-orchestrator/llm/privacy_router.py

# Add to imports
from llm.guarded_cloud import GuardedCloudClient

# Update PrivacyRouter.__init__
def __init__(self, config: RouterConfig):
    self.config = config
    from llm.nemotron_client import NemotronClient
    self.nemotron_client = NemotronClient(config.dgx_endpoint)
    self.guarded_cloud = GuardedCloudClient()  # Add this line
```

- [ ] **Step 5: Update _call_guarded_cloud to use actual implementation**

```python
# Update services/nemoclaw-orchestrator/llm/privacy_router.py

async def _call_guarded_cloud(self, prompt: str) -> str:
    """Call cloud API with PII stripping"""
    return await self.guarded_cloud.generate(prompt)
```

- [ ] **Step 6: Update llm/__init__.py to export GuardedCloudClient**

```python
# services/nemoclaw-orchestrator/llm/__init__.py
from .privacy_router import PrivacyRouter, LLMBackend
from .nemotron_client import NemotronClient
from .guarded_cloud import GuardedCloudClient

__all__ = ["PrivacyRouter", "LLMBackend", "NemotronClient", "GuardedCloudClient"]
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/unit/test_guarded_cloud.py -v
```

Expected: PASS

- [ ] **Step 8: Commit guarded cloud client**

```bash
git add services/nemoclaw-orchestrator/llm/guarded_cloud.py
git add services/nemoclaw-orchestrator/tests/unit/test_guarded_cloud.py
git add services/nemoclaw-orchestrator/llm/privacy_router.py
git add services/nemoclaw-orchestrator/llm/__init__.py
git commit -m "feat(nemoclaw): implement Guarded Cloud Client with PII stripping

- Add GuardedCloudClient for Anthropic API calls
- Implement PII stripping (phone, email, SSN) before cloud sends
- Add unit tests for PII protection
- Update PrivacyRouter to use guarded cloud for 5% fallback
- Required for 95%/5% local/cloud routing split

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 4: Agent Coordination

### Task 4: Implement Agent Coordinator

**Files:**
- Create: `services/nemoclaw-orchestrator/agents/__init__.py`
- Create: `services/nemoclaw-orchestrator/agents/coordinator.py`
- Create: `services/nemoclaw-orchestrator/agents/adapters.py`
- Create: `services/nemoclaw-orchestrator/tests/unit/test_agent_coordinator.py`

- [ ] **Step 1: Create agents package init**

```python
# services/nemoclaw-orchestrator/agents/__init__.py
from .coordinator import AgentCoordinator
from .adapters import (
    AgentAdapter,
    SceneSpeakAdapter,
    SentimentAdapter,
    CaptioningAdapter,
    BSLAdapter,
    LightingSoundMusicAdapter,
    SafetyFilterAdapter,
    MusicGenerationAdapter,
    AutonomousAdapter
)

__all__ = [
    "AgentCoordinator",
    "AgentAdapter",
    "SceneSpeakAdapter",
    "SentimentAdapter",
    "CaptioningAdapter",
    "BSLAdapter",
    "LightingSoundMusicAdapter",
    "SafetyFilterAdapter",
    "MusicGenerationAdapter",
    "AutonomousAdapter"
]
```

- [ ] **Step 2: Write failing test for agent coordinator**

```python
# services/nemoclaw-orchestrator/tests/unit/test_agent_coordinator.py
import pytest
from agents.coordinator import AgentCoordinator
from policy.engine import PolicyEngine, PolicyAction
from unittest.mock import AsyncMock

class TestAgentCoordinator:
    @pytest.mark.asyncio
    async def test_call_agent_with_policy_allow(self):
        mock_policy = AsyncMock()
        mock_policy.check_input.return_value = AsyncMock(
            action=PolicyAction.ALLOW, reason="Test"
        )
        mock_policy.filter_output = AsyncMock(return_value={"result": "ok"})

        coordinator = AgentCoordinator(mock_policy, None)

        # Mock HTTP call
        coordinator._call_agent_http = AsyncMock(
            return_value={"result": "ok"}
        )

        result = await coordinator.call_agent(
            "sentiment-agent", "analyze", {"text": "test"}
        )

        assert result == {"result": "ok"}
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/unit/test_agent_coordinator.py -v
```

Expected: FAIL with "AgentCoordinator not defined"

- [ ] **Step 4: Implement AgentCoordinator**

```python
# services/nemoclaw-orchestrator/agents/coordinator.py
import httpx
import logging
from typing import Dict, Any
from policy.engine import PolicyEngine, PolicyAction

logger = logging.getLogger(__name__)

class AgentCoordinator:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        privacy_router=None
    ):
        self.policy = policy_engine
        self.router = privacy_router

        # Agent URLs from config
        from config import get_settings
        settings = get_settings()
        self.agents = {
            "scenespeak-agent": settings.scenespeak_agent_url,
            "captioning-agent": settings.captioning_agent_url,
            "bsl-agent": settings.bsl_agent_url,
            "sentiment-agent": settings.sentiment_agent_url,
            "lighting-sound-music": settings.lighting_sound_music_url,
            "safety-filter": settings.safety_filter_url,
            "autonomous-agent": settings.autonomous_agent_url,
            "music-generation": settings.music_generation_url,
        }

    async def call_agent(
        self,
        agent_name: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an agent with OpenShell guardrails"""

        # Step 1: Policy check (input)
        policy_result = self.policy.check_input(
            agent=agent_name,
            skill=skill,
            input_data=input_data
        )

        if policy_result.action == PolicyAction.DENY:
            from policy.engine import PolicyViolationError
            raise PolicyViolationError(
                message=policy_result.reason,
                code="POLICY_VIOLATION"
            )

        # Step 2: Sanitize if needed
        if policy_result.action == PolicyAction.SANITIZE:
            input_data = await self.policy.sanitize_input(input_data)

        # Step 3: Make the call
        if self._requires_llm(agent_name):
            response = await self._call_with_privacy_router(
                agent_name, skill, input_data
            )
        else:
            response = await self._call_agent_http(
                agent_name, skill, input_data
            )

        # Step 4: Policy check (output)
        filtered_response = await self.policy.filter_output(
            agent=agent_name,
            response=response
        )

        return filtered_response

    def _requires_llm(self, agent_name: str) -> bool:
        """Check if agent requires LLM routing"""
        llm_agents = [
            "scenespeak-agent",
            "autonomous-agent",
        ]
        return agent_name in llm_agents

    async def _call_with_privacy_router(
        self,
        agent_name: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call agent via Privacy Router"""
        if not self.router:
            raise RuntimeError("Privacy Router not configured")

        # Generate using Privacy Router
        prompt = self._build_prompt(agent_name, skill, input_data)
        response_text = await self.router.generate(
            prompt,
            context={"requires_privacy": True}
        )

        return {"result": response_text, "backend": "nemotron_local"}

    async def _call_agent_http(
        self,
        agent_name: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Direct HTTP call to agent"""
        agent_url = self.agents.get(agent_name)
        if not agent_url:
            raise ValueError(f"Unknown agent: {agent_name}")

        # Map skill to endpoint
        if agent_name == "autonomous-agent":
            endpoint = "/execute"
        else:
            endpoint = f"/v1/{skill}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{agent_url}{endpoint}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

    def _build_prompt(
        self,
        agent_name: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM"""
        # Simple prompt building - enhance based on agent
        if agent_name == "scenespeak-agent":
            return f"Generate dialogue for scene: {input_data.get('scene_context', '')}"
        elif agent_name == "autonomous-agent":
            return f"Execute task: {input_data.get('task', '')}"
        return str(input_data)
```

- [ ] **Step 5: Implement base adapter classes**

```python
# services/nemoclaw-orchestrator/agents/adapters.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class AgentAdapter(ABC):
    """Base adapter for all agents"""

    @abstractmethod
    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def requires_llm(self) -> bool:
        pass

class SceneSpeakAdapter(AgentAdapter):
    """SceneSpeak Agent adapter"""

    def __init__(self, base_url: str, privacy_router):
        self.base_url = base_url
        self.router = privacy_router

    @property
    def requires_llm(self) -> bool:
        return True

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"Generate dialogue: {input_data.get('scene_context', '')}"
        dialogue = await self.router.generate(
            prompt,
            context={"requires_privacy": True}
        )
        return {"dialogue": dialogue}

class SentimentAdapter(AgentAdapter):
    """Sentiment Agent adapter"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/analyze",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

class CaptioningAdapter(AgentAdapter):
    """Captioning Agent adapter (Whisper transcription)"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/transcribe",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

class BSLAdapter(AgentAdapter):
    """BSL (British Sign Language) Agent adapter"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/translate",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

class LightingSoundMusicAdapter(AgentAdapter):
    """Lighting, Sound, and Music Agent adapter"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/control",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

class SafetyFilterAdapter(AgentAdapter):
    """Safety Filter Agent adapter (always allowed)"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self.base_url}/api/check",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

class MusicGenerationAdapter(AgentAdapter):
    """Music Generation Agent adapter"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=input_data
            )
            response.raise_for_status()
            return response.json()

class AutonomousAdapter(AgentAdapter):
    """Autonomous Agent adapter (uses LLM, requires escalation)"""

    def __init__(self, base_url: str, privacy_router):
        self.base_url = base_url
        self.router = privacy_router

    @property
    def requires_llm(self) -> bool:
        return True

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"Execute autonomous task: {input_data.get('task', '')}"
        result = await self.router.generate(
            prompt,
            context={"requires_privacy": True}
        )
        return {"result": result, "backend": "nemotron_local"}
```

- [ ] **Step 6: Add PolicyViolationError to policy engine**

```python
# Add to services/nemoclaw-orchestrator/policy/engine.py

class PolicyViolationError(Exception):
    """Raised when policy is violated"""
    def __init__(self, message: str, code: str = "POLICY_VIOLATION"):
        self.message = message
        self.code = code
        super().__init__(message)
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/unit/test_agent_coordinator.py -v
```

Expected: PASS

- [ ] **Step 8: Commit agent coordinator**

```bash
git add services/nemoclaw-orchestrator/agents/
git add services/nemoclaw-orchestrator/tests/unit/test_agent_coordinator.py
git commit -m "feat(nemoclaw): implement Agent Coordinator with policy filtering

- Add AgentCoordinator with OpenShell guardrails
- Implement input/output policy checking
- Add Privacy Router integration for LLM agents
- Add adapter classes for SceneSpeak and Sentiment agents
- Add unit tests for coordination flow

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 5: State Machine

### Task 5: Implement Redis-Backed State Machine

**Files:**
- Create: `services/nemoclaw-orchestrator/state/__init__.py`
- Create: `services/nemoclaw-orchestrator/state/machine.py`
- Create: `services/nemoclaw-orchestrator/state/store.py`
- Create: `services/nemoclaw-orchestrator/tests/unit/test_state_machine.py`

- [ ] **Step 1: Create state package init**

```python
# services/nemoclaw-orchestrator/state/__init__.py
from .machine import ShowStateMachine, ShowState
from .store import RedisStateStore

__all__ = ["ShowStateMachine", "ShowState", "RedisStateStore"]
```

- [ ] **Step 2: Write failing test for state machine**

```python
# services/nemoclaw-orchestrator/tests/unit/test_state_machine.py
import pytest
from state.machine import ShowStateMachine, ShowState

class TestShowStateMachine:
    @pytest.mark.asyncio
    async def test_initial_state_is_idle(self):
        machine = ShowStateMachine("test_show")
        assert machine.current_state == ShowState.IDLE

    @pytest.mark.asyncio
    async def test_start_transitions_to_prelude(self):
        machine = ShowStateMachine("test_show")
        await machine.start()
        assert machine.current_state == ShowState.PRELUDE

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self):
        machine = ShowStateMachine("test_show")
        with pytest.raises(ValueError):
            await machine.transition_to("invalid_state")
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/unit/test_state_machine.py -v
```

Expected: FAIL with "ShowStateMachine not defined"

- [ ] **Step 4: Implement ShowState enum and ShowStateMachine**

```python
# services/nemoclaw-orchestrator/state/machine.py
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ShowState(str, Enum):
    IDLE = "idle"
    PRELUDE = "prelude"
    ACTIVE = "active"
    POSTLUDE = "postlude"
    CLEANUP = "cleanup"

# Valid state transitions
TRANSITIONS = {
    ShowState.IDLE: [ShowState.PRELUDE],
    ShowState.PRELUDE: [ShowState.ACTIVE, ShowState.CLEANUP],
    ShowState.ACTIVE: [ShowState.POSTLUDE, ShowState.CLEANUP],
    ShowState.POSTLUDE: [ShowState.CLEANUP],
    ShowState.CLEANUP: [ShowState.IDLE],
}

class ShowStateMachine:
    def __init__(self, show_id: str, state_store=None):
        self.show_id = show_id
        self.state_store = state_store
        self.current_state = ShowState.IDLE
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    async def start(self) -> ShowState:
        """Start the show - transition to PRELUDE"""
        return await self.transition_to(ShowState.PRELUDE)

    async def end(self) -> ShowState:
        """End the show - transition to CLEANUP then IDLE"""
        await self.transition_to(ShowState.CLEANUP)
        return await self.transition_to(ShowState.IDLE)

    async def transition_to(self, new_state: ShowState) -> ShowState:
        """Transition to a new state"""
        # Validate transition
        if new_state not in TRANSITIONS.get(self.current_state, []):
            valid = [s.value for s in TRANSITIONS.get(self.current_state, [])]
            raise ValueError(
                f"Invalid transition: {self.current_state.value} -> {new_state.value}. "
                f"Valid: {valid}"
            )

        # Make transition
        old_state = self.current_state
        self.current_state = new_state
        self.updated_at = datetime.now()

        logger.info(f"Show {self.show_id}: {old_state.value} -> {new_state.value}")

        # Persist to store if available
        if self.state_store:
            await self.state_store.save_state(self.show_id, {
                "state": self.current_state.value,
                "updated_at": self.updated_at.isoformat()
            })

        return self.current_state

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "show_id": self.show_id,
            "state": self.current_state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
```

- [ ] **Step 5: Implement RedisStateStore**

```python
# services/nemoclaw-orchestrator/state/store.py
import redis.asyncio as aioredis
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RedisStateStore:
    def __init__(self, redis_url: str, ttl: int = 86400):
        self.redis_url = redis_url
        self.ttl = ttl
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self._redis = await aioredis.from_url(
            self.redis_url,
            decoding="utf-8"
        )
        logger.info(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()

    async def save_state(self, show_id: str, state_data: Dict[str, Any]):
        """Save show state to Redis"""
        if not self._redis:
            await self.connect()

        key = f"show:{show_id}:state"
        value = json.dumps(state_data)

        await self._redis.setex(key, self.ttl, value)
        logger.debug(f"Saved state for show {show_id}")

    async def get_state(self, show_id: str) -> Optional[Dict[str, Any]]:
        """Get show state from Redis"""
        if not self._redis:
            await self.connect()

        key = f"show:{show_id}:state"
        value = await self._redis.get(key)

        if value:
            return json.loads(value)
        return None

    async def delete_state(self, show_id: str):
        """Delete show state from Redis"""
        if not self._redis:
            await self.connect()

        key = f"show:{show_id}:state"
        await self._redis.delete(key)
        logger.debug(f"Deleted state for show {show_id}")
```

- [ ] **Step 6: Update test to handle string state parameter**

```python
# Update test in test_state_machine.py
async def test_invalid_transition_raises_error(self):
    machine = ShowStateMachine("test_show")
    from state.machine import ShowState
    with pytest.raises(ValueError):
        # Use the proper transition method with invalid state
        machine.current_state = ShowState.IDLE
        # Manually call with invalid enum
        if ShowState.ACTIVE not in TRANSITIONS[ShowState.IDLE]:
            # This will fail validation
            await machine.transition_to(ShowState.ACTIVE)
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/unit/test_state_machine.py -v
```

Expected: PASS

- [ ] **Step 8: Commit state machine**

```bash
git add services/nemoclaw-orchestrator/state/
git add services/nemoclaw-orchestrator/tests/unit/test_state_machine.py
git commit -m "feat(nemoclaw): implement Redis-backed show state machine

- Add ShowStateMachine with valid state transitions
- Add ShowState enum (IDLE, PRELUDE, ACTIVE, POSTLUDE, CLEANUP)
- Add RedisStateStore for persistence
- Add transition validation
- Add unit tests for state transitions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 6: WebSocket Manager

### Task 6: Implement WebSocket Connection Manager

**Files:**
- Create: `services/nemoclaw-orchestrator/websocket/__init__.py`
- Create: `services/nemoclaw-orchestrator/websocket/manager.py`
- Create: `services/nemoclaw-orchestrator/websocket/handlers.py`
- Create: `services/nemoclaw-orchestrator/tests/integration/test_websocket_updates.py`

- [ ] **Step 1: Create websocket package init**

```python
# services/nemoclaw-orchestrator/websocket/__init__.py
from .manager import WebSocketManager

__all__ = ["WebSocketManager"]
```

- [ ] **Step 2: Write failing test for WebSocket manager**

```python
# services/nemoclaw-orchestrator/tests/integration/test_websocket_updates.py
import pytest
from fastapi.testclient import TestClient
from websocket import manager as ws_manager

class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self):
        manager = ws_manager.WebSocketManager(policy_engine=None)

        # Mock connections
        mock_ws1 = pytest.helpers.AsyncMock()
        mock_ws2 = pytest.helpers.AsyncMock()

        manager.connections["conn1"] = mock_ws1
        manager.connections["conn2"] = mock_ws2

        await manager.broadcast("test_event", {"data": "test"})

        # Verify both connections received message
        assert mock_ws1.send_json.called
        assert mock_ws2.send_json.called
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/integration/test_websocket_updates.py -v
```

Expected: FAIL with "WebSocketManager not defined"

- [ ] **Step 4: Implement WebSocketManager**

```python
# services/nemoclaw-orchestrator/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, policy_engine=None):
        self.policy = policy_engine
        self.connections: Dict[str, WebSocket] = {}
        self.message_history: Dict[str, List[dict]] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        """Register a new connection"""
        await websocket.accept()
        self.connections[connection_id] = websocket
        self.message_history[connection_id] = []
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str):
        """Unregister a connection"""
        self.connections.pop(connection_id, None)
        self.message_history.pop(connection_id, None)
        logger.info(f"WebSocket disconnected: {connection_id}")

    async def broadcast(self, message_type: str, data: dict):
        """Broadcast message to all connected clients"""

        # Filter sensitive data if policy is available
        if self.policy:
            data = await self._filter_broadcast(data)

        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # Add to all histories
        for conn_id in self.connections.keys():
            if conn_id in self.message_history:
                self.message_history[conn_id].append(message)

        # Send to all connections
        disconnected = []
        for conn_id, ws in self.connections.items():
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to {conn_id}: {e}")
                disconnected.append(conn_id)

        # Cleanup disconnected
        for conn_id in disconnected:
            self.disconnect(conn_id)

    async def send_to(
        self,
        connection_id: str,
        message_type: str,
        data: dict
    ):
        """Send message to specific connection"""
        if connection_id not in self.connections:
            logger.warning(f"Connection not found: {connection_id}")
            return

        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        try:
            await self.connections[connection_id].send_json(message)

            # Add to history
            if connection_id in self.message_history:
                self.message_history[connection_id].append(message)
        except Exception as e:
            logger.error(f"Failed to send to {connection_id}: {e}")
            self.disconnect(connection_id)

    def get_history(self, connection_id: str) -> List[dict]:
        """Get message history for connection"""
        return self.message_history.get(connection_id, [])

    async def _filter_broadcast(self, data: dict) -> dict:
        """Filter broadcast data through policy"""
        if not self.policy:
            return data

        # Use OutputFilter to remove sensitive information
        from policy.filters import OutputFilter
        output_filter = OutputFilter()
        return await output_filter.filter(data, agent="broadcast")
```

- [ ] **Step 5: Implement WebSocket message handlers**

```python
# services/nemoclaw-orchestrator/websocket/handlers.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class WebSocketMessageHandler:
    def __init__(self, state_machine, agent_coordinator, ws_manager):
        self.state_machine = state_machine
        self.coordinator = agent_coordinator
        self.ws_manager = ws_manager

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """Handle incoming WebSocket message"""
        action = message.get("action")

        if action == "start_show":
            await self._handle_start_show(connection_id, message)
        elif action == "end_show":
            await self._handle_end_show(connection_id, message)
        elif action == "agent_call":
            await self._handle_agent_call(connection_id, message)
        elif action == "ping":
            await self._handle_ping(connection_id)
        else:
            logger.warning(f"Unknown action: {action}")

    async def _handle_start_show(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """Handle show start"""
        show_id = message.get("show_id", "default_show")

        await self.state_machine.start()

        await self.ws_manager.broadcast("show_state", {
            "show_id": show_id,
            "state": self.state_machine.current_state.value,
            "action": "started"
        })

    async def _handle_end_show(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """Handle show end"""
        show_id = message.get("show_id", "default_show")

        await self.state_machine.end()

        await self.ws_manager.broadcast("show_state", {
            "show_id": show_id,
            "state": self.state_machine.current_state.value,
            "action": "ended"
        })

    async def _handle_agent_call(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """Handle agent call"""
        agent = message.get("agent")
        skill = message.get("skill")
        input_data = message.get("input", {})

        try:
            result = await self.coordinator.call_agent(
                agent, skill, input_data
            )

            await self.ws_manager.send_to(
                connection_id,
                "agent_response",
                {"agent": agent, "result": result}
            )
        except Exception as e:
            await self.ws_manager.send_to(
                connection_id,
                "error",
                {"agent": agent, "error": str(e)}
            )

    async def _handle_ping(self, connection_id: str):
        """Handle ping"""
        await self.ws_manager.send_to(
            connection_id,
            "pong",
            {}
        )
```

- [ ] **Step 6: Update main.py to integrate all components**

```python
# Update services/nemoclaw-orchestrator/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from config import get_settings
from policy import PolicyEngine, CHIMERA_POLICIES
from llm import PrivacyRouter, RouterConfig
from agents import AgentCoordinator
from state import ShowStateMachine, RedisStateStore
from websocket import WebSocketManager
from websocket.handlers import WebSocketMessageHandler

logger = logging.getLogger(__name__)
settings = get_settings()

# Global components
policy_engine: PolicyEngine = None
privacy_router: PrivacyRouter = None
agent_coordinator: AgentCoordinator = None
state_store: RedisStateStore = None
ws_manager: WebSocketManager = None
ws_handler: WebSocketMessageHandler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global policy_engine, privacy_router, agent_coordinator
    global state_store, ws_manager, ws_handler

    logger.info("Nemo Claw Orchestrator starting up")

    # Initialize components
    policy_engine = PolicyEngine(CHIMERA_POLICIES)

    router_config = RouterConfig(
        dgx_endpoint=settings.dgx_endpoint,
        local_ratio=settings.local_ratio,
        cloud_fallback_enabled=settings.cloud_fallback_enabled
    )
    privacy_router = PrivacyRouter(router_config)

    agent_coordinator = AgentCoordinator(policy_engine, privacy_router)

    state_store = RedisStateStore(
        redis_url=settings.redis_url,
        ttl=settings.redis_show_state_ttl
    )
    await state_store.connect()

    ws_manager = WebSocketManager(policy_engine)
    ws_handler = WebSocketMessageHandler(
        ShowStateMachine("default", state_store),
        agent_coordinator,
        ws_manager
    )

    yield

    # Cleanup
    await state_store.disconnect()
    logger.info("Nemo Claw Orchestrator shutting down")

app = FastAPI(
    title="Nemo Claw Orchestrator",
    description="Project Chimera orchestration with Nemo Claw security and privacy",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health/live")
async def liveness():
    return {"status": "alive", "service": settings.service_name}

@app.get("/health/ready")
async def readiness():
    return {
        "status": "ready",
        "service": settings.service_name,
        "components": {
            "policy": "ok",
            "router": "ok",
            "redis": "ok"
        }
    }

@app.post("/v1/orchestrate")
async def orchestrate(request: dict):
    """Route skill request to appropriate agent with policy filtering"""
    from pydantic import BaseModel

    class OrchestrateRequest(BaseModel):
        skill: str
        input: dict
        agent: str = None

    try:
        req_data = OrchestrateRequest(**request)

        # Determine agent from skill
        agent = req_data.agent or _get_agent_for_skill(req_data.skill)

        result = await agent_coordinator.call_agent(
            agent,
            req_data.skill,
            req_data.input
        )

        return {
            "result": result,
            "skill_used": req_data.skill,
            "agent_used": agent,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_agent_for_skill(skill: str) -> str:
    """Map skill to agent"""
    skill_to_agent = {
        "dialogue_generator": "scenespeak-agent",
        "captioning": "captioning-agent",
        "bsl_translation": "bsl-agent",
        "sentiment_analysis": "sentiment-agent",
        "autonomous_execution": "autonomous-agent",
    }
    return skill_to_agent.get(skill, "scenespeak-agent")

@app.post("/api/show/start")
async def start_show(request: dict):
    """Start a show"""
    show_id = request.get("show_id", "default_show")

    state_machine = ShowStateMachine(show_id, state_store)
    await state_machine.start()

    await ws_manager.broadcast("show_state", {
        "show_id": show_id,
        "state": state_machine.current_state.value
    })

    return state_machine.to_dict()

@app.post("/api/show/end")
async def end_show(request: dict):
    """End a show"""
    show_id = request.get("show_id", "default_show")

    state_machine = ShowStateMachine(show_id, state_store)
    await state_machine.end()

    await ws_manager.broadcast("show_state", {
        "show_id": show_id,
        "state": state_machine.current_state.value
    })

    return state_machine.to_dict()

@app.websocket("/ws/show")
async def websocket_show_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time show updates"""
    connection_id = f"conn_{id(websocket)}"

    await ws_manager.connect(connection_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await ws_handler.handle_message(connection_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(connection_id)

@app.get("/skills")
async def list_skills():
    """List available skills"""
    skills = [
        {"name": "dialogue_generator", "description": "Generate contextual dialogue", "enabled": True},
        {"name": "captioning", "description": "Speech-to-text transcription", "enabled": True},
        {"name": "bsl_translation", "description": "Text-to-BSL gloss translation", "enabled": True},
        {"name": "sentiment_analysis", "description": "Analyze audience sentiment", "enabled": True},
        {"name": "autonomous_execution", "description": "Execute autonomous tasks", "enabled": True},
    ]
    return {"skills": skills, "total": len(skills), "enabled": len(skills)}
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/integration/test_websocket_updates.py -v
```

Expected: PASS

- [ ] **Step 8: Commit WebSocket manager**

```bash
git add services/nemoclaw-orchestrator/websocket/
git add services/nemoclaw-orchestrator/tests/integration/test_websocket_updates.py
git add services/nemoclaw-orchestrator/main.py
git commit -m "feat(nemoclaw): implement WebSocket manager and integrate all components

- Add WebSocketManager for real-time show updates
- Add WebSocketMessageHandler for message routing
- Implement broadcast filtering through OutputFilter (PII removal)
- Integrate PolicyEngine, PrivacyRouter, AgentCoordinator, StateMachine
- Update main.py with all endpoints and WebSocket support
- Add integration tests for WebSocket

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 7: Error Handling & Resilience

### Task 7: Implement Error Handling and Circuit Breaker

**Files:**
- Create: `services/nemoclaw-orchestrator/errors/__init__.py`
- Create: `services/nemoclaw-orchestrator/errors/exceptions.py`
- Create: `services/nemoclaw-orchestrator/errors/handlers.py`
- Create: `services/nemoclaw-orchestrator/resilience/__init__.py`
- Create: `services/nemoclaw-orchestrator/resilience/retry.py`
- Create: `services/nemoclaw-orchestrator/resilience/circuit_breaker.py`

- [ ] **Step 1: Create error handling modules**

```python
# services/nemoclaw-orchestrator/errors/__init__.py
from .exceptions import (
    ChimeraError,
    PolicyViolationError,
    LLMRoutingError,
    AgentUnavailableError,
    StateTransitionError
)

__all__ = [
    "ChimeraError",
    "PolicyViolationError",
    "LLMRoutingError",
    "AgentUnavailableError",
    "StateTransitionError",
]
```

- [ ] **Step 2: Implement exception classes**

```python
# services/nemoclaw-orchestrator/errors/exceptions.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

class ChimeraError(Exception):
    """Base error for all Nemo Claw errors"""
    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class PolicyViolationError(ChimeraError):
    def __init__(self, message: str, rule: str = None):
        super().__init__(
            message=f"Policy violation: {message}",
            code="POLICY_VIOLATION",
            details={"rule": rule}
        )

class LLMRoutingError(ChimeraError):
    def __init__(self, backend: str, reason: str):
        super().__init__(
            message=f"LLM routing failed for {backend}: {reason}",
            code="LLM_ROUTING_ERROR",
            details={"backend": backend, "reason": reason}
        )

class AgentUnavailableError(ChimeraError):
    def __init__(self, agent: str, url: str):
        super().__init__(
            message=f"Agent {agent} at {url} is unavailable",
            code="AGENT_UNAVAILABLE",
            details={"agent": agent, "url": url}
        )

class StateTransitionError(ChimeraError):
    def __init__(self, current: str, attempted: str):
        super().__init__(
            message=f"Invalid state transition: {current} -> {attempted}",
            code="INVALID_STATE_TRANSITION",
            details={"current": current, "attempted": attempted}
        )
```

- [ ] **Step 3: Implement global error handlers**

```python
# services/nemoclaw-orchestrator/errors/handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from errors.exceptions import (
    ChimeraError,
    PolicyViolationError,
    LLMRoutingError,
    AgentUnavailableError,
    StateTransitionError
)

logger = logging.getLogger(__name__)

async def chimera_error_handler(request: Request, exc: ChimeraError) -> JSONResponse:
    """Handle all ChimeraError exceptions"""

    status_code = {
        "POLICY_VIOLATION": status.HTTP_403_FORBIDDEN,
        "AGENT_UNAVAILABLE": status.HTTP_503_SERVICE_UNAVAILABLE,
        "LLM_ROUTING_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INVALID_STATE_TRANSITION": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now().isoformat(),
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        }
    )

def register_error_handlers(app):
    """Register error handlers with FastAPI app"""
    app.add_exception_handler(ChimeraError, chimera_error_handler)
    app.add_exception_handler(PolicyViolationError, chimera_error_handler)
    app.add_exception_handler(LLMRoutingError, chimera_error_handler)
    app.add_exception_handler(AgentUnavailableError, chimera_error_handler)
    app.add_exception_handler(StateTransitionError, chimera_error_handler)
```

- [ ] **Step 4: Implement circuit breaker**

```python
# services/nemoclaw-orchestrator/resilience/circuit_breaker.py
from datetime import datetime, timedelta
from typing import Callable, Dict, Any
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures: Dict[str, int] = {}
        self.last_failure: Dict[str, datetime] = {}
        self.state: Dict[str, CircuitState] = {}

    async def call(
        self,
        service: str,
        func: Callable,
        *args, **kwargs
    ) -> Any:
        """Execute function through circuit breaker"""

        current_state = self.state.get(service, CircuitState.CLOSED)

        if current_state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if (datetime.now() - self.last_failure.get(service, datetime.min)
                > timedelta(seconds=self.timeout)):
                self.state[service] = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker OPEN for {service}"
                )

        try:
            result = await func(*args, **kwargs)
            # Success - reset failures
            self.failures[service] = 0
            self.state[service] = CircuitState.CLOSED
            return result

        except Exception as e:
            self.failures[service] = self.failures.get(service, 0) + 1
            self.last_failure[service] = datetime.now()

            if self.failures[service] >= self.failure_threshold:
                self.state[service] = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker opened for {service} "
                    f"({self.failures[service]} failures)"
                )

            raise
```

- [ ] **Step 5: Implement retry logic**

```python
# services/nemoclaw-orchestrator/resilience/retry.py
import asyncio
import logging
from typing import Callable, TypeVar, Any

from errors.exceptions import AgentUnavailableError

T = TypeVar('T')
logger = logging.getLogger(__name__)

class ResilientAgentCaller:
    """Handles retries and fallbacks for agent calls"""

    def __init__(
        self,
        max_retries: int = 3,
        fallback_mode: str = "graceful"
    ):
        self.max_retries = max_retries
        self.fallback_mode = fallback_mode

    async def call_with_retry(
        self,
        agent_url: str,
        skill: str,
        input_data: dict,
        call_func: Callable
    ) -> dict:
        """Attempt agent call with exponential backoff"""

        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await call_func(agent_url, skill, input_data)

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        # All retries exhausted
        return await self._fallback_response(skill, input_data, last_error)

    async def _fallback_response(
        self,
        skill: str,
        input_data: dict,
        error: Exception
    ) -> dict:
        """Generate graceful fallback"""

        if self.fallback_mode == "graceful":
            return {
                "status": "degraded",
                "message": f"{skill} is currently unavailable",
                "fallback": "cached_response",
                "data": self._get_cached_response(skill, input_data)
            }
        else:
            raise AgentUnavailableError(skill, "unknown")

    def _get_cached_response(self, skill: str, input_data: dict) -> dict:
        """Get cached response (placeholder)"""
        return {"cached": True, "skill": skill}
```

- [ ] **Step 6: Update agent_coordinator to use retry**

```python
# Add to services/nemoclaw-orchestrator/agents/coordinator.py

from resilience.retry import ResilientAgentCaller
from resilience.circuit_breaker import CircuitBreaker

class AgentCoordinator:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        privacy_router=None
    ):
        self.policy = policy_engine
        self.router = privacy_router
        self.retry_caller = ResilientAgentCaller()
        self.circuit_breaker = CircuitBreaker()

        # ... rest of init ...

    async def _call_agent_http(
        self,
        agent_name: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Direct HTTP call to agent with retry"""
        agent_url = self.agents.get(agent_name)
        if not agent_url:
            raise ValueError(f"Unknown agent: {agent_name}")

        if agent_name == "autonomous-agent":
            endpoint = "/execute"
        else:
            endpoint = f"/v1/{skill}"

        async def _http_call(url, skill, data):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{url}{endpoint}", json=data)
                response.raise_for_status()
                return response.json()

        # Use retry with circuit breaker
        return await self.circuit_breaker.call(
            agent_name,
            self.retry_caller.call_with_retry,
            agent_url, skill, input_data, _http_call
        )
```

- [ ] **Step 7: Update main.py to register error handlers**

```python
# Add to services/nemoclaw-orchestrator/main.py

from errors.handlers import register_error_handlers

# In lifespan function, after initializing components:
register_error_handlers(app)
```

- [ ] **Step 8: Commit error handling**

```bash
git add services/nemoclaw-orchestrator/errors/
git add services/nemoclaw-orchestrator/resilience/
git add services/nemoclaw-orchestrator/agents/coordinator.py
git add services/nemoclaw-orchestrator/main.py
git commit -m "feat(nemoclaw): implement error handling and resilience patterns

- Add custom exception classes for all error types
- Add global error handlers for FastAPI
- Implement CircuitBreaker pattern for agent calls
- Implement retry logic with exponential backoff
- Add graceful fallback for unavailable agents

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 8: Integration & E2E Testing

### Task 8: Complete Integration and E2E Tests

**Files:**
- Create: `services/nemoclaw-orchestrator/tests/integration/test_show_lifecycle.py`
- Create: `services/nemoclaw-orchestrator/tests/integration/test_agent_flow.py`
- Create: `services/nemoclaw-orchestrator/tests/e2e/show-lifecycle.spec.ts`

- [ ] **Step 1: Write show lifecycle integration test**

```python
# services/nemoclaw-orchestrator/tests/integration/test_show_lifecycle.py
import pytest
import asyncio
from state import ShowStateMachine, RedisStateStore, ShowState
from policy import PolicyEngine, CHIMERA_POLICIES
from agents import AgentCoordinator

class TestShowLifecycle:
    @pytest.mark.asyncio
    async def test_complete_show_lifecycle(self):
        """Test show from start to end"""

        # Setup
        state_store = RedisStateStore("redis://localhost:6379")
        await state_store.connect()

        policy_engine = PolicyEngine(CHIMERA_POLICIES)
        coordinator = AgentCoordinator(policy_engine, None)

        # Create show
        show = ShowStateMachine("test_show", state_store)
        assert show.current_state == ShowState.IDLE

        # Start show
        await show.start()
        assert show.current_state == ShowState.PRELUDE

        # Transition to active
        await show.transition_to(ShowState.ACTIVE)
        assert show.current_state == ShowState.ACTIVE

        # End show
        await show.end()
        assert show.current_state == ShowState.IDLE

        # Cleanup
        await state_store.disconnect()
```

- [ ] **Step 2: Write agent flow integration test**

```python
# services/nemoclaw-orchestrator/tests/integration/test_agent_flow.py
import pytest
from unittest.mock import AsyncMock, patch
from policy import PolicyEngine, CHIMERA_POLICIES
from agents import AgentCoordinator
from llm import PrivacyRouter, RouterConfig

class TestAgentFlow:
    @pytest.mark.asyncio
    async def test_policy_blocks_dangerous_agent_call(self):
        """Policy should block dangerous autonomous calls"""

        policy_engine = PolicyEngine(CHIMERA_POLICIES)
        coordinator = AgentCoordinator(policy_engine, None)

        with pytest.raises(Exception) as exc_info:
            await coordinator.call_agent(
                "autonomous-agent",
                "execute",
                {"command": "rm -rf /"}
            )

        assert "POLICY_VIOLATION" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sentiment_agent_allowed(self):
        """Sentiment agent should work normally"""

        policy_engine = PolicyEngine(CHIMERA_POLICIES)
        coordinator = AgentCoordinator(policy_engine, None)

        # Mock HTTP response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "sentiment": "positive",
                "score": 0.9
            }
            mock_post.return_value.raise_for_status = AsyncMock()

            result = await coordinator.call_agent(
                "sentiment-agent",
                "analyze_sentiment",
                {"text": "This is great!"}
            )

            assert result["sentiment"] == "positive"
```

- [ ] **Step 3: Write E2E test with Playwright**

```typescript
// services/nemoclaw-orchestrator/tests/e2e/show-lifecycle.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Nemo Claw Show Lifecycle E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8007');
  });

  test('complete show flow with policy enforcement', async ({ page }) => {
    // Start show
    await page.click('[data-testid="start-show-btn"]');
    await expect(page.locator('[data-testid="show-state"]')).toHaveText('PRELUDE');

    // Send audience input
    await page.fill('[data-testid="audience-input"]', 'Generate dialogue');
    await page.click('[data-testid="submit-input"]');

    // Should receive response
    const response = page.locator('[data-testid="agent-response"]');
    await expect(response).toBeVisible({ timeout: 5000 });

    // End show
    await page.click('[data-testid="end-show-btn"]');
    await expect(page.locator('[data-testid="show-state"]')).toHaveText('IDLE');
  });

  test('policy blocks dangerous commands', async ({ page }) => {
    await page.click('[data-testid="autonomous-tab"]');
    await page.fill('[data-testid="autonomous-input"]', 'rm -rf /');
    await page.click('[data-testid="execute-btn"]');

    // Should show policy violation
    await expect(page.locator('[data-testid="error-message"]'))
      .toContainText('Policy violation');
  });

  test('WebSocket real-time updates', async ({ page }) => {
    // Start show and verify WebSocket connection
    await page.click('[data-testid="start-show-btn"]');

    // Wait for WebSocket update
    await expect(page.locator('[data-testid="ws-status"]'))
      .toHaveText('Connected');

    // Verify state update via WebSocket
    await expect(page.locator('[data-testid="show-state"]'))
      .toHaveText('PRELUDE', { timeout: 3000 });
  });
});
```

- [ ] **Step 4: Create pytest configuration**

```ini
# services/nemoclaw-orchestrator/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=.
    --cov-report=html
    --cov-report=term-missing
asyncio_mode = auto
```

- [ ] **Step 5: Run all tests**

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires Redis)
pytest tests/integration/ -v

# E2E tests (requires all services)
pytest tests/e2e/ -v
```

- [ ] **Step 6: Commit tests**

```bash
git add services/nemoclaw-orchestrator/tests/
git add services/nemoclaw-orchestrator/pytest.ini
git commit -m "test(nemoclaw): add comprehensive integration and E2E tests

- Add show lifecycle integration tests
- Add agent flow tests with policy enforcement
- Add Playwright E2E tests for complete user flows
- Add pytest configuration
- Test coverage: unit, integration, E2E

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 9: Deployment & Migration

### Task 9: Create Deployment Configuration

**Files:**
- Create: `services/nemoclaw-orchestrator/Dockerfile`
- Create: `services/nemoclaw-orchestrator/docker-compose.yml`
- Create: `services/nemoclaw-orchestrator/manifests/deployment.yaml`
- Create: `docs/migration-guide.md`

- [ ] **Step 1: Create ARM64-optimized Dockerfile**

```dockerfile
# services/nemoclaw-orchestrator/Dockerfile
FROM nvcr.io/nvidia/nemoclaw:latest-arm64

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live').raise_for_status()"

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose for local development**

```yaml
# services/nemoclaw-orchestrator/docker-compose.yml
version: '3.8'

services:
  nemoclaw-orchestrator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVICE_NAME=nemoclaw-orchestrator
      - DGX_ENDPOINT=http://dgx-nemotron:8000
      - REDIS_URL=redis://redis:6379
      - SCENESPEAK_AGENT_URL=http://scenespeak-agent:8001
      - CAPTIONING_AGENT_URL=http://captioning-agent:8002
      - BSL_AGENT_URL=http://bsl-agent:8003
      - SENTIMENT_AGENT_URL=http://sentiment-agent:8004
      - LIGHTING_SOUND_MUSIC_URL=http://lighting-sound-music:8005
      - SAFETY_FILTER_URL=http://safety-filter:8006
      - AUTONOMOUS_AGENT_URL=http://autonomous-agent:8008
      - MUSIC_GENERATION_URL=http://music-generation:8011
    depends_on:
      - redis
      - dgx-nemotron
    networks:
      - chimera-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - chimera-network

  dgx-nemotron:
    image: nvcr.io/nvidia/nemotron:latest-arm64
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - chimera-network

networks:
  chimera-network:
    driver: bridge
```

- [ ] **Step 3: Create Kubernetes deployment**

```yaml
# services/nemoclaw-orchestrator/manifests/deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nemoclaw-config
data:
  SERVICE_NAME: "nemoclaw-orchestrator"
  DGX_ENDPOINT: "http://nemotron-service:8000"
  REDIS_URL: "redis://redis-service:6379"
  LOCAL_RATIO: "0.95"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nemoclaw-orchestrator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nemoclaw-orchestrator
  template:
    metadata:
      labels:
        app: nemoclaw-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: ghcr.io/project-chimera/nemoclaw-orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: SERVICE_NAME
          valueFrom:
            configMapKeyRef:
              name: nemoclaw-config
              key: SERVICE_NAME
        envFrom:
        - configMapRef:
            name: nemoclaw-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: nemoclaw-orchestrator
spec:
  selector:
    app: nemoclaw-orchestrator
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 4: Create migration guide**

```markdown
# Migration Guide: OpenClaw to Nemo Claw

## Overview

This guide covers migrating from OpenClaw Orchestrator to Nemo Claw Orchestrator.

## Prerequisites

- DGX Spark GB0 ARM64 system
- Redis 7.x installed
- Nemo Claw installed: `curl -fsSL https://nvidia.com/nemoclaw.sh | bash`
- All existing agents running

## Migration Steps

### 1. Backup Current State

\`\`\`bash
# Export current show states from OpenClaw
curl http://localhost:8000/api/show/export -o openclaw_state.json
\`\`\`

### 2. Deploy Nemo Claw

\`\`\`bash
cd services/nemoclaw-orchestrator
docker-compose up -d
\`\`\`

### 3. Verify Health

\`\`\`bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
\`\`\`

### 4. Test Agent Communication

\`\`\`bash
curl -X POST http://localhost:8000/v1/orchestrate \\
  -H "Content-Type: application/json" \\
  -d '{
    "skill": "sentiment_analysis",
    "input": {"text": "test"}
  }'
\`\`\`

### 5. Switch Traffic

Update Operator Console to point to new orchestrator:

\`\`\`javascript
// Change from
const ORCHESTRATOR_URL = "http://localhost:8000";  // Old
// To
const ORCHESTRATOR_URL = "http://localhost:8000";  // New Nemo Claw
\`\`\`

### 6. Monitor

Check logs for any issues:

\`\`\`bash
docker-compose logs -f nemoclaw-orchestrator
\`\`\`

### 7. Rollback (if needed)

\`\`\`bash
# Stop Nemo Claw
docker-compose down

# Restart OpenClaw
cd ../openclaw-orchestrator
uvicorn main:app --port 8000
\`\`\`

## Validation Checklist

- [ ] All health checks pass
- [ ] All agents respond to orchestration
- [ ] Show state transitions work
- [ ] WebSocket connections stable
- [ ] Policy enforcement active
- [ ] No errors in logs

## Post-Migration

- Monitor for 24 hours
- Review policy violations
- Adjust local/cloud ratio as needed
- Update documentation
```

- [ ] **Step 5: Commit deployment configuration**

```bash
git add services/nemoclaw-orchestrator/Dockerfile
git add services/nemoclaw-orchestrator/docker-compose.yml
git add services/nemoclaw-orchestrator/manifests/
git add docs/migration-guide.md
git commit -m "deploy(nemoclaw): add deployment configuration and migration guide

- Add ARM64-optimized Dockerfile
- Add docker-compose for local development
- Add Kubernetes deployment manifests
- Add comprehensive migration guide
- Include health checks and resource limits

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 10: Documentation & Completion

### Task 10: Update Documentation and Complete

**Files:**
- Update: `docs/architecture/overview.md`
- Update: `docs/architecture/components.md`
- Create: `docs/api/nemoclaw-orchestrator.md`
- Update: `README.md`

- [ ] **Step 1: Update architecture overview**

```markdown
# Update docs/architecture/overview.md

Replace OpenClaw references with Nemo Claw:

## Central Coordination

### Nemo Claw Orchestrator (Port 8000)
Central coordination service with security and privacy guardrails:
- Routes requests to appropriate agents with OpenShell policy enforcement
- Manages show state and transitions (Redis-backed)
- Coordinates real-time updates via WebSocket
- Handles audience input processing with content filtering
- Privacy Router for 95% local Nemotron inference, 5% guarded cloud
```

- [ ] **Step 2: Create Nemo Claw API documentation**

```markdown
# docs/api/nemoclaw-orchestrator.md

# Nemo Claw Orchestrator API Documentation

**Version:** v1.0.0
**Base URL:** `http://localhost:8000`

## Overview

Nemo Claw Orchestrator provides policy-guarded agent coordination with
privacy-preserving LLM routing.

## Key Differences from OpenClaw

- All requests pass through OpenShell policy layer
- LLM calls route through Privacy Router (local/cloud)
- All responses include policy metadata
- Enhanced error handling with detailed codes

## Endpoints

### /v1/orchestrate
POST /v1/orchestrate

Enhanced with policy filtering:

\`\`\`json
{
  "result": {...},
  "policy": {
    "checked": true,
    "action": "allow",
    "rules_applied": []
  },
  "llm_backend": "nemotron_local"
\`\`\`

### /health/ready
GET /health/ready

Returns component status:

\`\`\`json
{
  "status": "ready",
  "components": {
    "policy": "ok",
    "router": "ok",
    "redis": "ok"
  }
}
\`\`\`

### New Endpoints

#### GET /policy/rules
List active policies

#### POST /policy/test
Test input against policies

#### GET /llm/status
Privacy Router and backend status
```

- [ ] **Step 3: Update project README**

```markdown
# Update README.md

## Quick Start with Nemo Claw

\`\`\`bash
# Install Nemo Claw
curl -fsSL https://nvidia.com/nemoclaw.sh | bash

# Start orchestrator
cd services/nemoclaw-orchestrator
docker-compose up -d

# Verify
curl http://localhost:8000/health/live
\`\`\`

## Architecture

Project Chimera uses Nemo Claw for secure, privacy-preserving orchestration:

- **OpenShell Runtime**: Policy-based guardrails
- **Privacy Router**: 95% local Nemotron, 5% guarded cloud
- **8 AI Agents**: SceneSpeak, Captioning, BSL, Sentiment, etc.
- **Redis-backed State**: Persistent show state management
```

- [ ] **Step 4: Run final test suite**

```bash
# Full test suite
pytest tests/ -v --cov=.

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v
```

- [ ] **Step 5: Create final commit**

```bash
git add docs/
git add README.md
git commit -m "docs(nemoclaw): update documentation for Nemo Claw

- Update architecture overview with Nemo Claw components
- Add Nemo Claw API documentation
- Update project README with Nemo Claw quick start
- Document policy enforcement and privacy routing

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 6: Create release tag**

```bash
git tag -a v1.0.0-nemoclaw -m "Nemo Claw Orchestrator v1.0.0

Replace OpenClaw with Nemo Claw:
- OpenShell policy guardrails
- Privacy Router for local/cloud LLM routing
- Redis-backed state machine
- Circuit breaker and retry logic
- Comprehensive test coverage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

git push origin main --tags
```

---

## Task Summary

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 1. Foundation | 1 | 2 days |
| 2. Policy Engine | 1 | 2 days |
| 3. Privacy Router | 1 | 2 days |
| 4. Agent Coordination | 1 | 3 days |
| 5. State Machine | 1 | 2 days |
| 6. WebSocket Manager | 1 | 3 days |
| 7. Error Handling | 1 | 2 days |
| 8. Integration Tests | 1 | 3 days |
| 9. Deployment | 1 | 2 days |
| 10. Documentation | 1 | 2 days |
| **Total** | **10** | **23 days** |

---

## Success Criteria

- [ ] All 8 existing agents work with Nemo Claw
- [ ] 95% of LLM inference runs locally on DGX
- [ ] OpenShell policies enforce content safety
- [ ] Show state machine operates correctly
- [ ] WebSocket real-time updates functional
- [ ] All tests pass (unit, integration, E2E)
- [ ] Documentation updated
- [ ] Migration guide completed

---

## Notes

- Each task includes TDD: write test first, implement, verify
- Commit after each completed task
- Use `superpowers:subagent-driven-development` for execution
- Reference spec: `docs/superpowers/specs/2026-03-18-nemoclaw-orchestrator-design.md`

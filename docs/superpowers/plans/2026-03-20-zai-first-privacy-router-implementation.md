# Z.AI-First Privacy Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Anthropic API with Z.AI API as primary LLM backend, implementing Z.AI-first routing with credit exhaustion detection and graceful fallback to local Nemotron.

**Architecture:** Z.AI-first routing with three models (GLM-5-Turbo for orchestration, GLM-4.7 for programming, GLM-4.7-FlashX for fast tasks), Redis-backed credit exhaustion cache with TTL-based auto-recovery, and seamless fallback to local DGX Nemotron.

**Tech Stack:** Python 3.10+, FastAPI, OpenAI SDK (with custom base_url), Redis 7.x, pytest

---

## Task 1: Create Z.AI Client Implementation

**Files:**
- Create: `services/nemoclaw-orchestrator/llm/zai_client.py`
- Modify: `services/nemoclaw-orchestrator/llm/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `services/nemoclaw-orchestrator/tests/unit/test_zai_client.py`:

```python
# services/nemoclaw-orchestrator/tests/unit/test_zai_client.py
import pytest
from unittest.mock import Mock, patch
from llm.zai_client import ZAIClient, ZAIModel


class TestZAIModel:
    def test_model_enum_values(self):
        assert ZAIModel.PRIMARY.value == "glm-5-turbo"
        assert ZAIModel.PROGRAMMING.value == "glm-4.7"
        assert ZAIModel.FAST.value == "glm-4.7-flashx"


class TestZAIClient:
    def test_client_initializes_with_api_key(self):
        client = ZAIClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.z.ai/api/paas/v4/"

    @patch.dict('os.environ', {'ZAI_API_KEY': 'env-key'})
    def test_client_reads_api_key_from_env(self):
        import os
        client = ZAIClient()
        assert client.api_key == "env-key"

    @patch('llm.zai_client.OpenAI')
    def test_generate_makes_api_request(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"

        mock_completion = Mock()
        mock_completion.create.return_value = mock_response
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test prompt", model=ZAIModel.PRIMARY)

        assert result["text"] == "Generated response"
        assert result["model_used"] == "glm-5-turbo"
        assert result["credits_exhausted"] is False

        mock_completion.create.assert_called_once()
        call_kwargs = mock_completion.create.call_args[1]
        assert call_kwargs["model"] == "glm-5-turbo"
        assert call_kwargs["messages"][0]["content"] == "Test prompt"
        assert call_kwargs["thinking"]["type"] == "enabled"

    @patch('llm.zai_client.OpenAI')
    def test_generate_detects_credit_exhaustion_402(self, mock_openai):
        import openai
        mock_openai.AuthenticationError = openai.AuthenticationError
        mock_openai.RateLimitError = openai.RateLimitError

        # Mock 402 error
        error = Exception("Insufficient credits")
        error.status_code = 402
        mock_completion = Mock()
        mock_completion.create.side_effect = error
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test prompt", model=ZAIModel.PRIMARY)

        assert result["error"] == "credit_exhausted"
        assert "Insufficient credits" in result["details"]

    @patch('llm.zai_client.OpenAI')
    def test_generate_detects_credit_exhaustion_403(self, mock_openai):
        # Mock 403 error with "insufficient credits" message
        error = Exception("Error: insufficient credits quota exceeded")
        error.status_code = 403
        mock_completion = Mock()
        mock_completion.create.side_effect = error
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test prompt", model=ZAIModel.PRIMARY)

        assert result["error"] == "credit_exhausted"

    @patch('llm.zai_client.OpenAI')
    def test_generate_with_thinking_disabled(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"

        mock_completion = Mock()
        mock_completion.create.return_value = mock_response
        mock_openai.return_value.chat.completions = mock_completion

        client = ZAIClient(api_key="test-key")
        result = client.generate("Test", model=ZAIModel.PRIMARY, thinking=False)

        call_kwargs = mock_completion.create.call_args[1]
        assert call_kwargs.get("thinking") is None

    @patch('llm.zai_client.OpenAI')
    def test_close_closes_client(self, mock_openai):
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance

        client = ZAIClient(api_key="test-key")
        client.close()

        mock_client_instance.close.assert_called_once()
```

Run: `cd services/nemoclaw-orchestrator && pytest tests/unit/test_zai_client.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'llm.zai_client'"

- [ ] **Step 2: Create ZAIClient implementation**

Create `services/nemoclaw-orchestrator/llm/zai_client.py`:

```python
# services/nemoclaw-orchestrator/llm/zai_client.py
from openai import OpenAI
from enum import Enum
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class ZAIModel(str, Enum):
    """Z.AI model options"""
    PRIMARY = "glm-5-turbo"      # OpenClaw-optimized, tool invocation
    PROGRAMMING = "glm-4.7"      # Enhanced programming, reasoning
    FAST = "glm-4.7-flashx"      # Simple, repetitive tasks


class ZAIClient:
    """Client for Z.AI API using OpenAI SDK with custom base_url"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.z.ai/api/paas/v4/"
    ):
        """
        Initialize Z.AI client

        Args:
            api_key: Z.AI API key (defaults to ZAI_API_KEY env var)
            base_url: Z.AI API base URL
        """
        self.api_key = api_key or os.getenv("ZAI_API_KEY", "")
        self.base_url = base_url
        self._client: Optional[OpenAI] = None

        if not self.api_key:
            logger.warning("ZAI_API_KEY not set - Z.AI client will fail")

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def _is_credit_error(self, error: Exception) -> bool:
        """
        Check if error indicates credit exhaustion

        Args:
            error: Exception to check

        Returns:
            True if error is credit exhaustion, False otherwise
        """
        error_str = str(error).lower()
        error_status = getattr(error, "status_code", None)

        # Check status code
        if error_status in (402, 403):
            return True

        # Check error message for credit-related keywords
        credit_keywords = [
            "insufficient credits",
            "quota exceeded",
            "credit exhausted",
            "billing",
            "payment required"
        ]
        return any(keyword in error_str for keyword in credit_keywords)

    def generate(
        self,
        prompt: str,
        model: ZAIModel = ZAIModel.PRIMARY,
        max_tokens: int = 512,
        temperature: float = 0.7,
        thinking: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Z.AI API

        Args:
            prompt: Input prompt
            model: Z.AI model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            thinking: Whether to enable thinking parameter
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        try:
            client = self._get_client()

            # Build request
            request_params = {
                "model": model.value,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            # Add thinking parameter if enabled
            if thinking:
                request_params["thinking"] = {"type": "enabled"}

            response = client.chat.completions.create(**request_params)

            return {
                "text": response.choices[0].message.content,
                "model_used": model.value,
                "credits_exhausted": False,
                "usage": getattr(response, "usage", {})
            }

        except Exception as e:
            # Check for credit exhaustion
            if self._is_credit_error(e):
                logger.warning(f"Z.AI credit exhaustion detected: {e}")
                return {
                    "error": "credit_exhausted",
                    "details": str(e),
                    "model_used": model.value
                }

            # Re-raise other errors
            logger.error(f"Z.AI generation error: {e}")
            raise

    def close(self):
        """Close OpenAI client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

- [ ] **Step 3: Run test to verify it passes**

Run: `cd services/nemoclaw-orchestrator && pytest tests/unit/test_zai_client.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 4: Update llm/__init__.py to export ZAIClient**

Modify `services/nemoclaw-orchestrator/llm/__init__.py`:

```python
# services/nemoclaw-orchestrator/llm/__init__.py
from .privacy_router import LLMBackend, RouterConfig, PrivacyRouter
from .nemotron_client import NemotronClient
from .guarded_cloud import GuardedCloudClient
from .zai_client import ZAIClient, ZAIModel

__all__ = [
    "LLMBackend",
    "RouterConfig",
    "PrivacyRouter",
    "NemotronClient",
    "GuardedCloudClient",
    "ZAIClient",
    "ZAIModel",
]
```

- [ ] **Step 5: Commit**

```bash
cd services/nemoclaw-orchestrator
git add llm/zai_client.py llm/__init__.py tests/unit/test_zai_client.py
git commit -m "feat: add Z.AI client with GLM model support

- Add ZAIClient using OpenAI SDK with custom base_url
- Support GLM-5-Turbo, GLM-4.7, and GLM-4.7-FlashX models
- Implement credit exhaustion detection (402/403 errors)
- Add thinking parameter support for enhanced reasoning
- Add comprehensive unit tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Create Credit Status Cache

**Files:**
- Create: `services/nemoclaw-orchestrator/llm/credit_cache.py`
- Test: `services/nemoclaw-orchestrator/tests/unit/test_credit_cache.py`

- [ ] **Step 1: Write the failing test**

Create `services/nemoclaw-orchestrator/tests/unit/test_credit_cache.py`:

```python
# services/nemoclaw-orchestrator/tests/unit/test_credit_cache.py
import pytest
import time
from unittest.mock import Mock, patch
from llm.credit_cache import CreditStatusCache


class TestCreditStatusCache:
    @pytest.fixture
    def mock_redis(self):
        with patch('llm.credit_cache.redis') as mock_redis_module:
            mock_client = Mock()
            mock_redis_module.from_url.return_value = mock_client
            yield mock_client

    def test_cache_initializes_with_defaults(self, mock_redis):
        cache = CreditStatusCache()
        mock_redis_module.from_url.assert_called_once_with("redis://localhost:6379")

    def test_cache_initializes_with_custom_url(self, mock_redis):
        cache = CreditStatusCache(redis_url="redis://custom:6380")
        mock_redis_module.from_url.assert_called_once_with("redis://custom:6380")

    def test_cache_initializes_with_custom_ttl(self, mock_redis):
        cache = CreditStatusCache(ttl=7200)
        assert cache.ttl == 7200

    def test_is_available_returns_true_when_no_flag(self, mock_redis):
        mock_redis.exists.return_value = 0
        cache = CreditStatusCache()
        assert cache.is_available() is True

    def test_is_available_returns_false_when_flag_exists(self, mock_redis):
        mock_redis.exists.return_value = 1
        cache = CreditStatusCache()
        assert cache.is_available() is False

    def test_mark_exhausted_sets_redis_key_with_ttl(self, mock_redis):
        cache = CreditStatusCache(ttl=3600)
        cache.mark_exhausted()

        mock_redis.setex.assert_called_once_with("zai:credit:status", 3600, "exhausted")

    def test_reset_deletes_redis_key(self, mock_redis):
        cache = CreditStatusCache()
        cache.reset()

        mock_redis.delete.assert_called_once_with("zai:credit:status")

    def test_mark_exhausted_then_is_available_false(self, mock_redis):
        mock_redis.exists.return_value = 1
        cache = CreditStatusCache()
        cache.mark_exhausted()

        assert cache.is_available() is False

    def test_reset_then_is_available_true(self, mock_redis):
        mock_redis.exists.return_value = 0
        cache = CreditStatusCache()
        cache.mark_exhausted()
        cache.reset()

        mock_redis.delete.assert_called_once()
        mock_redis.exists.return_value = 0
        assert cache.is_available() is True

    @patch('llm.credit_cache.os.getenv')
    def test_cache_reads_redis_url_from_env(self, mock_getenv, mock_redis):
        mock_getenv.return_value = "redis://env:6379"
        cache = CreditStatusCache()
        mock_getenv.assert_called_with("REDIS_URL")
```

Run: `cd services/nemoclaw-orchestrator && pytest tests/unit/test_credit_cache.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'llm.credit_cache'"

- [ ] **Step 2: Create CreditStatusCache implementation**

Create `services/nemoclaw-orchestrator/llm/credit_cache.py`:

```python
# services/nemoclaw-orchestrator/llm/credit_cache.py
import redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CreditStatusCache:
    """
    Manage Z.AI credit exhaustion status in Redis with TTL

    Uses Redis to store whether Z.AI credits are exhausted, with automatic
    expiration (TTL) to allow auto-recovery when credits are replenished.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl: int = 3600
    ):
        """
        Initialize credit status cache

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
            ttl: Time-to-live for exhausted flag in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self.key = "zai:credit:status"

        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None
        self._redis_url = url

    @property
    def redis(self) -> redis.Redis:
        """Get or create Redis client (lazy initialization)"""
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def is_available(self) -> bool:
        """
        Check if Z.AI is available (not marked as exhausted)

        Returns:
            True if Z.AI is available, False if marked exhausted
        """
        try:
            return not self.redis.exists(self.key)
        except Exception as e:
            logger.error(f"Redis error checking credit status: {e}")
            # Assume available on Redis error (fail-open)
            return True

    def mark_exhausted(self):
        """Mark Z.AI as exhausted with TTL"""
        try:
            self.redis.setex(self.key, self.ttl, "exhausted")
            logger.info(f"Z.AI marked as exhausted for {self.ttl}s")
        except Exception as e:
            logger.error(f"Redis error marking exhausted: {e}")

    def reset(self):
        """Manually reset the exhausted flag"""
        try:
            deleted = self.redis.delete(self.key)
            if deleted:
                logger.info("Z.AI credit status reset manually")
        except Exception as e:
            logger.error(f"Redis error resetting credit status: {e}")

    def close(self):
        """Close Redis connection"""
        if self._redis:
            self._redis.close()
            self._redis = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

- [ ] **Step 3: Run test to verify it passes**

Run: `cd services/nemoclaw-orchestrator && pytest tests/unit/test_credit_cache.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 4: Update llm/__init__.py to export CreditStatusCache**

Modify `services/nemoclaw-orchestrator/llm/__init__.py`:

```python
# services/nemoclaw-orchestrator/llm/__init__.py
from .privacy_router import LLMBackend, RouterConfig, PrivacyRouter
from .nemotron_client import NemotronClient
from .guarded_cloud import GuardedCloudClient
from .zai_client import ZAIClient, ZAIModel
from .credit_cache import CreditStatusCache

__all__ = [
    "LLMBackend",
    "RouterConfig",
    "PrivacyRouter",
    "NemotronClient",
    "GuardedCloudClient",
    "ZAIClient",
    "ZAIModel",
    "CreditStatusCache",
]
```

- [ ] **Step 5: Commit**

```bash
cd services/nemoclaw-orchestrator
git add llm/credit_cache.py llm/__init__.py tests/unit/test_credit_cache.py
git commit -m "feat: add Redis-based credit status cache for Z.AI

- Add CreditStatusCache with TTL-based auto-recovery
- Store Z.AI availability status in Redis
- Support manual reset and automatic expiration
- Fail-open on Redis errors (assume available)
- Add comprehensive unit tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Update Privacy Router for Z.AI-First Routing

**Files:**
- Modify: `services/nemoclaw-orchestrator/llm/privacy_router.py`
- Modify: `services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py`

- [ ] **Step 1: Update LLMBackend enum**

In `services/nemoclaw-orchestrator/llm/privacy_router.py`, replace the `LLMBackend` enum:

```python
# Replace existing LLMBackend enum with:
class LLMBackend(str, Enum):
    """Available LLM backends"""
    ZAI_PRIMARY = "zai_primary"
    ZAI_PROGRAMMING = "zai_programming"
    ZAI_FAST = "zai_fast"
    NEMOTRON_LOCAL = "nemotron_local"
```

- [ ] **Step 2: Update RouterConfig dataclass**

Replace the `RouterConfig` dataclass:

```python
# Replace existing RouterConfig with:
@dataclass
class RouterConfig:
    """Configuration for privacy router"""
    dgx_endpoint: str
    nemotron_model: str = "nemotron-8b"

    # Z.AI Configuration
    zai_api_key: str = ""
    zai_primary_model: str = "glm-5-turbo"
    zai_programming_model: str = "glm-4.7"
    zai_fast_model: str = "glm-4.7-flashx"
    zai_cache_ttl: int = 3600
    zai_thinking_enabled: bool = True

    # Legacy config (kept for backward compatibility)
    local_ratio: float = 0.0  # No longer used (Z.AI-first)
    cloud_fallback_enabled: bool = True  # Now means Nemotron fallback
```

- [ ] **Step 3: Update PrivacyRouter imports**

Add imports at top of file:

```python
# Add to existing imports:
from llm.zai_client import ZAIClient, ZAIModel
from llm.credit_cache import CreditStatusCache
import time
```

- [ ] **Step 4: Update PrivacyRouter.__init__**

Replace the `__init__` method:

```python
def __init__(self, config: RouterConfig):
    """
    Initialize privacy router with Z.AI-first routing

    Args:
        config: Router configuration
    """
    self.config = config

    # Z.AI clients
    self.zai_client = ZAIClient(
        api_key=config.zai_api_key or None
    )
    self.credit_cache = CreditStatusCache(
        ttl=config.zai_cache_ttl
    )

    # Local Nemotron client (fallback)
    self.local_client = NemotronClient(
        endpoint=config.dgx_endpoint,
        model=config.nemotron_model
    )
```

- [ ] **Step 5: Add task type mapping helper**

Add new method after `__init__`:

```python
def _select_zai_model(self, task_type: str) -> LLMBackend:
    """
    Select Z.AI model based on task type

    Args:
        task_type: Type of task (tool_invocation, programming, simple, etc.)

    Returns:
        LLMBackend for the selected Z.AI model
    """
    if task_type in ["tool_invocation", "persistent", "orchestration", "default"]:
        return LLMBackend.ZAI_PRIMARY
    elif task_type in ["programming", "code_generation", "debugging"]:
        return LLMBackend.ZAI_PROGRAMMING
    elif task_type in ["simple", "repetitive", "quick", "classification"]:
        return LLMBackend.ZAI_FAST
    else:
        return LLMBackend.ZAI_PRIMARY  # Default to primary
```

- [ ] **Step 6: Replace route() method**

Replace the `route()` method:

```python
def route(self, prompt: str, task_type: str = "default") -> LLMBackend:
    """
    Determine which backend to use for a request (Z.AI-first)

    Args:
        prompt: Input prompt
        task_type: Type of task for model selection

    Returns:
        LLMBackend to use
    """
    # Check if Z.AI is available (not marked as exhausted)
    if not self.credit_cache.is_available():
        logger.debug("Z.AI marked exhausted, routing to local Nemotron")
        return LLMBackend.NEMOTRON_LOCAL

    # Select Z.AI model based on task type
    return self._select_zai_model(task_type)
```

- [ ] **Step 7: Replace generate() method**

Replace the `generate()` method:

```python
def generate(
    self,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    force_backend: Optional[LLMBackend] = None,
    task_type: str = "default",
    **kwargs
) -> Dict[str, Any]:
    """
    Generate text using appropriate backend (Z.AI-first)

    Args:
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        force_backend: Force specific backend (for testing)
        task_type: Type of task for model selection
        **kwargs: Additional parameters

    Returns:
        Dict with generated text and metadata
    """
    start_time = time.time()
    backend = force_backend or self.route(prompt, task_type)

    try:
        # Z.AI backends
        if backend in (LLMBackend.ZAI_PRIMARY, LLMBackend.ZAI_PROGRAMMING, LLMBackend.ZAI_FAST):
            return self._generate_with_zai(
                prompt=prompt,
                backend=backend,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

        # Local Nemotron fallback
        elif backend == LLMBackend.NEMOTRON_LOCAL:
            return self._generate_with_nemotron(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

        else:
            raise ValueError(f"Unknown backend: {backend}")

    except Exception as e:
        logger.error(f"Generation failed with backend {backend.value}: {e}")

        # Attempt fallback to Nemotron
        if backend != LLMBackend.NEMOTRON_LOCAL and self.config.cloud_fallback_enabled:
            logger.info("Attempting fallback to local Nemotron")
            return self._generate_with_nemotron(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

        raise
```

- [ ] **Step 8: Add helper methods**

Add these methods after `generate()`:

```python
def _generate_with_zai(
    self,
    prompt: str,
    backend: LLMBackend,
    max_tokens: int,
    temperature: float,
    **kwargs
) -> Dict[str, Any]:
    """Generate using Z.AI client"""
    # Map backend to model
    model_map = {
        LLMBackend.ZAI_PRIMARY: ZAIModel.PRIMARY,
        LLMBackend.ZAI_PROGRAMMING: ZAIModel.PROGRAMMING,
        LLMBackend.ZAI_FAST: ZAIModel.FAST,
    }

    model = model_map[backend]
    logger.debug(f"Routing to Z.AI model: {model.value}")

    result = self.zai_client.generate(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        thinking=self.config.zai_thinking_enabled,
        **kwargs
    )

    # Check for credit exhaustion
    if "error" in result and result["error"] == "credit_exhausted":
        logger.warning("Z.AI credits exhausted, marking and falling back")
        self.credit_cache.mark_exhausted()

        # Retry with Nemotron
        return self._generate_with_nemotron(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    result["backend"] = backend.value
    return result


def _generate_with_nemotron(
    self,
    prompt: str,
    max_tokens: int,
    temperature: float,
    **kwargs
) -> Dict[str, Any]:
    """Generate using local Nemotron client"""
    logger.debug("Routing to local DGX Nemotron")

    result = self.local_client.generate(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )

    result["backend"] = LLMBackend.NEMOTRON_LOCAL.value
    return result
```

- [ ] **Step 9: Update close() method**

Replace the `close()` method:

```python
def close(self):
    """Close all clients"""
    self.zai_client.close()
    self.local_client.close()
    self.credit_cache.close()
```

- [ ] **Step 10: Write updated tests**

Update `services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py`:

```python
# services/nemoclaw-orchestrator/tests/unit/test_privacy_router.py
import pytest
from unittest.mock import Mock, patch
from llm.privacy_router import LLMBackend, RouterConfig, PrivacyRouter


class TestRouterConfig:
    def test_creates_config_with_zai_defaults(self):
        config = RouterConfig(dgx_endpoint="http://localhost:8000")
        assert config.zai_primary_model == "glm-5-turbo"
        assert config.zai_programming_model == "glm-4.7"
        assert config.zai_fast_model == "glm-4.7-flashx"
        assert config.zai_cache_ttl == 3600
        assert config.zai_thinking_enabled is True


class TestLLMBackend:
    def test_backend_enum_values(self):
        assert LLMBackend.ZAI_PRIMARY.value == "zai_primary"
        assert LLMBackend.ZAI_PROGRAMMING.value == "zai_programming"
        assert LLMBackend.ZAI_FAST.value == "zai_fast"
        assert LLMBackend.NEMOTRON_LOCAL.value == "nemotron_local"


class TestPrivacyRouter:
    @pytest.fixture
    def config(self):
        return RouterConfig(
            dgx_endpoint="http://localhost:8000",
            zai_api_key="test-key"
        )

    @pytest.fixture
    def mock_zai_client(self):
        with patch('llm.privacy_router.ZAIClient') as mock:
            yield mock

    @pytest.fixture
    def mock_nemotron_client(self):
        with patch('llm.privacy_router.NemotronClient') as mock:
            yield mock

    @pytest.fixture
    def mock_credit_cache(self):
        with patch('llm.privacy_router.CreditStatusCache') as mock:
            yield mock

    @pytest.fixture
    def router(self, config, mock_zai_client, mock_nemotron_client, mock_credit_cache):
        return PrivacyRouter(config)

    def test_router_initializes(self, router):
        assert router.zai_client is not None
        assert router.local_client is not None
        assert router.credit_cache is not None

    def test_select_zai_model_for_tool_invocation(self, router):
        backend = router._select_zai_model("tool_invocation")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_select_zai_model_for_programming(self, router):
        backend = router._select_zai_model("programming")
        assert backend == LLMBackend.ZAI_PROGRAMMING

    def test_select_zai_model_for_simple_tasks(self, router):
        backend = router._select_zai_model("simple")
        assert backend == LLMBackend.ZAI_FAST

    def test_route_returns_zai_when_available(self, router, mock_credit_cache):
        mock_credit_cache.return_value.is_available.return_value = True
        backend = router.route("test", "default")
        assert backend == LLMBackend.ZAI_PRIMARY

    def test_route_returns_nemotron_when_exhausted(self, router, mock_credit_cache):
        mock_credit_cache.return_value.is_available.return_value = False
        backend = router.route("test", "default")
        assert backend == LLMBackend.NEMOTRON_LOCAL

    @patch('llm.privacy_router.time')
    def test_generate_with_zai_primary(self, mock_time, router, mock_zai_client):
        mock_time.time.return_value = 0.0
        mock_zai_client.return_value.generate.return_value = {
            "text": "response",
            "model_used": "glm-5-turbo",
            "credits_exhausted": False
        }

        result = router.generate("test", task_type="tool_invocation")

        assert result["text"] == "response"
        assert result["backend"] == "zai_primary"

    @patch('llm.privacy_router.time')
    def test_generate_falls_back_on_credit_exhaustion(self, mock_time, router, mock_zai_client, mock_nemotron_client):
        mock_time.time.return_value = 0.0

        # Z.AI returns credit exhaustion
        mock_zai_client.return_value.generate.return_value = {
            "error": "credit_exhausted",
            "details": "Insufficient credits"
        }

        # Nemotron returns success
        mock_nemotron_client.return_value.generate.return_value = {
            "text": "local response",
            "model": "nemotron-8b",
            "backend": "nemotron_local"
        }

        result = router.generate("test", task_type="tool_invocation")

        assert result["text"] == "local response"
        assert result["backend"] == "nemotron_local"
```

- [ ] **Step 11: Run updated tests**

Run: `cd services/nemoclaw-orchestrator && pytest tests/unit/test_privacy_router.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 12: Commit**

```bash
cd services/nemoclaw-orchestrator
git add llm/privacy_router.py tests/unit/test_privacy_router.py
git commit -m "feat: implement Z.AI-first routing in PrivacyRouter

- Replace Anthropic cloud client with Z.AI client
- Add three Z.AI models: PRIMARY, PROGRAMMING, FAST
- Implement credit exhaustion detection and caching
- Add task type to model mapping
- Update RouterConfig with Z.AI settings
- Add comprehensive unit tests for new behavior
- Remove old local_ratio routing (now Z.AI-first)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Update Configuration Files

**Files:**
- Modify: `services/nemoclaw-orchestrator/config.py`
- Modify: `services/nemoclaw-orchestrator/.env.example`
- Modify: `services/nemoclaw-orchestrator/docker-compose.yml`
- Modify: `services/nemoclaw-orchestrator/requirements.txt`

- [ ] **Step 1: Update config.py**

Add Z.AI configuration to `services/nemoclaw-orchestrator/config.py`:

```python
# Add to Settings class (after existing fields):

    # Z.AI Configuration (Primary LLM backend)
    zai_api_key: str = ""
    zai_primary_model: str = "glm-5-turbo"
    zai_programming_model: str = "glm-4.7"
    zai_fast_model: str = "glm-4.7-flashx"
    zai_cache_ttl: int = 3600
    zai_thinking_enabled: bool = True
```

- [ ] **Step 2: Update .env.example**

Add Z.AI variables to `services/nemoclaw-orchestrator/.env.example`:

```bash
# Add after Privacy Router section:

# Z.AI Configuration (Primary LLM Backend)
ZAI_API_KEY=your-zai-api-key-here
ZAI_PRIMARY_MODEL=glm-5-turbo
ZAI_PROGRAMMING_MODEL=glm-4.7
ZAI_FAST_MODEL=glm-4.7-flashx
ZAI_CACHE_TTL=3600
ZAI_THINKING_ENABLED=true
```

- [ ] **Step 3: Update docker-compose.yml**

Add Z.AI environment variables to `services/nemoclaw-orchestrator/docker-compose.yml`:

```yaml
# Add to nemoclaw-orchestrator service environment section:
      # Z.AI Configuration
      ZAI_API_KEY: ${ZAI_API_KEY}
      ZAI_PRIMARY_MODEL: glm-5-turbo
      ZAI_PROGRAMMING_MODEL: glm-4.7
      ZAI_FAST_MODEL: glm-4.7-flashx
      ZAI_CACHE_TTL: 3600
      ZAI_THINKING_ENABLED: "true"
```

- [ ] **Step 4: Update requirements.txt**

Add OpenAI SDK to `services/nemoclaw-orchestrator/requirements.txt`:

```txt
# Add after httpx:
openai>=1.0.0
```

- [ ] **Step 5: Commit**

```bash
cd services/nemoclaw-orchestrator
git add config.py .env.example docker-compose.yml requirements.txt
git commit -m "feat: add Z.AI configuration to all config files

- Add ZAI_API_KEY and model settings to config.py
- Add Z.AI environment variables to .env.example
- Add Z.AI environment variables to docker-compose.yml
- Add openai>=1.0.0 to requirements.txt

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Write Comprehensive Tests

**Files:**
- Create: `services/nemoclaw-orchestrator/tests/integration/test_zai_routing.py`
- Create: `services/nemoclaw-orchestrator/tests/integration/test_zai_live.py`

- [ ] **Step 1: Write integration tests**

Create `services/nemoclaw-orchestrator/tests/integration/test_zai_routing.py`:

```python
# services/nemoclaw-orchestrator/tests/integration/test_zai_routing.py
import pytest
import time
from unittest.mock import Mock, patch
from llm.privacy_router import LLMBackend, RouterConfig, PrivacyRouter


@pytest.mark.integration
class TestZAIRoutingIntegration:
    """Integration tests for Z.AI-first routing"""

    @pytest.fixture
    def config(self):
        return RouterConfig(
            dgx_endpoint="http://localhost:8000",
            zai_api_key="test-key",
            zai_cache_ttl=2  # Short TTL for testing
        )

    @pytest.fixture
    def router(self, config):
        with patch('llm.privacy_router.CreditStatusCache'), \
             patch('llm.privacy_router.ZAIClient'), \
             patch('llm.privacy_router.NemotronClient'):
            return PrivacyRouter(config)

    def test_full_request_flow_zai_success(self, router):
        """Test successful Z.AI request flow"""
        with patch.object(router.zai_client, 'generate') as mock_zai:
            mock_zai.return_value = {
                "text": "Z.AI response",
                "model_used": "glm-5-turbo",
                "credits_exhausted": False
            }

            result = router.generate("test prompt", task_type="tool_invocation")

            assert result["text"] == "Z.AI response"
            assert result["backend"] == "zai_primary"
            assert router.credit_cache.is_available()

    def test_credit_exhaustion_fallback_flow(self, router):
        """Test credit exhaustion → fallback → cache flow"""
        # Z.AI returns credit exhaustion
        with patch.object(router.zai_client, 'generate') as mock_zai, \
             patch.object(router.local_client, 'generate') as mock_local:

            mock_zai.return_value = {
                "error": "credit_exhausted",
                "details": "Insufficient credits"
            }
            mock_local.return_value = {
                "text": "Local response",
                "model": "nemotron-8b",
                "backend": "nemotron_local"
            }

            result = router.generate("test prompt")

            assert result["text"] == "Local response"
            assert result["backend"] == "nemotron_local"
            assert not router.credit_cache.is_available()

    def test_ttl_expiration_recovery(self, router):
        """Test Z.AI recovery after TTL expiration"""
        router.credit_cache.mark_exhausted()

        # Verify exhausted
        assert not router.credit_cache.is_available()

        # Wait for TTL (2 seconds)
        time.sleep(2.5)

        # Cache should be cleared by Redis TTL
        # (In real Redis, key would expire; mock needs manual clearing)
        router.credit_cache.reset()

        assert router.credit_cache.is_available()

    def test_task_type_model_selection(self, router):
        """Test model selection based on task type"""
        test_cases = [
            ("tool_invocation", LLMBackend.ZAI_PRIMARY),
            ("persistent", LLMBackend.ZAI_PRIMARY),
            ("programming", LLMBackend.ZAI_PROGRAMMING),
            ("code_generation", LLMBackend.ZAI_PROGRAMMING),
            ("simple", LLMBackend.ZAI_FAST),
            ("repetitive", LLMBackend.ZAI_FAST),
            ("unknown", LLMBackend.ZAI_PRIMARY),  # Default
        ]

        for task_type, expected_backend in test_cases:
            backend = router._select_zai_model(task_type)
            assert backend == expected_backend, f"Failed for {task_type}"

    def test_concurrent_requests_same_exhaustion(self, router):
        """Test multiple concurrent requests handle exhaustion correctly"""
        with patch.object(router.zai_client, 'generate') as mock_zai, \
             patch.object(router.local_client, 'generate') as mock_local:

            mock_zai.return_value = {
                "error": "credit_exhausted",
                "details": "Insufficient credits"
            }
            mock_local.return_value = {
                "text": "Local response",
                "model": "nemotron-8b",
                "backend": "nemotron_local"
            }

            # Simulate concurrent requests
            results = []
            for _ in range(5):
                result = router.generate("test")
                results.append(result)

            # All should fall back to local
            assert all(r["backend"] == "nemotron_local" for r in results)
            assert router.credit_cache.mark_exhausted.call_count >= 1
```

- [ ] **Step 2: Write live API tests (optional)**

Create `services/nemoclaw-orchestrator/tests/integration/test_zai_live.py`:

```python
# services/nemoclaw-orchestrator/tests/integration/test_zai_live.py
import pytest
import os
from llm.zai_client import ZAIClient, ZAIModel


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ZAI_API_KEY"),
    reason="ZAI_API_KEY not set"
)
class TestZAILiveAPI:
    """Live tests against real Z.AI API (requires API key)"""

    @pytest.fixture
    def client(self):
        return ZAIClient()

    def test_generate_with_primary_model(self, client):
        """Test actual API call with GLM-5-Turbo"""
        result = client.generate(
            prompt="Say 'Hello, World!' in exactly those words.",
            model=ZAIModel.PRIMARY,
            max_tokens=50
        )

        assert "text" in result
        assert result["model_used"] == "glm-5-turbo"
        assert "Hello, World!" in result["text"] or len(result["text"]) > 0

    def test_generate_with_programming_model(self, client):
        """Test actual API call with GLM-4.7"""
        result = client.generate(
            prompt="Write a Python function that adds two numbers.",
            model=ZAIModel.PROGRAMMING,
            max_tokens=100
        )

        assert "text" in result
        assert result["model_used"] == "glm-4.7"
        assert "def " in result["text"] or len(result["text"]) > 0

    def test_generate_with_fast_model(self, client):
        """Test actual API call with GLM-4.7-FlashX"""
        result = client.generate(
            prompt="What is 2+2?",
            model=ZAIModel.FAST,
            max_tokens=20
        )

        assert "text" in result
        assert result["model_used"] == "glm-4.7-flashx"

    def test_thinking_parameter(self, client):
        """Test thinking parameter is accepted"""
        result = client.generate(
            prompt="Count to 5.",
            model=ZAIModel.PRIMARY,
            thinking=True
        )

        assert "text" in result
        assert result["credits_exhausted"] is False
```

- [ ] **Step 3: Run integration tests**

Run: `cd services/nemoclaw-orchestrator && pytest tests/integration/test_zai_routing.py -v`
Expected: PASS (all tests pass)

Run: `cd services/nemoclaw-orchestrator && pytest tests/integration/test_zai_live.py -v`
Expected: SKIP (no ZAI_API_KEY set)

- [ ] **Step 4: Run all tests**

Run: `cd services/nemoclaw-orchestrator && pytest tests/ -v --cov=llm --cov-report=term-missing`
Expected: 85%+ coverage on llm module

- [ ] **Step 5: Commit**

```bash
cd services/nemoclaw-orchestrator
git add tests/integration/test_zai_routing.py tests/integration/test_zai_live.py
git commit -m "test: add integration tests for Z.AI routing

- Add full request flow tests with mocked clients
- Add credit exhaustion and fallback tests
- Add TTL expiration recovery tests
- Add task type model selection tests
- Add concurrent request handling tests
- Add live API tests (skip without ZAI_API_KEY)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Update Documentation and Deployment

**Files:**
- Modify: `services/nemoclaw-orchestrator/README.md`
- Modify: `services/nemoclaw-orchestrator/main.py`
- Create: `services/nemoclaw-orchestrator/docs/api/zai-endpoints.md`
- Modify: `services/nemoclaw-orchestrator/status.sh`

- [ ] **Step 1: Update README.md**

Update the "Key Features" section in `services/nemoclaw-orchestrator/README.md`:

```markdown
# Replace "Privacy Router" bullet with:
- **Z.AI-First Privacy Router** - Z.AI API as primary with 3 models (GLM-5-Turbo, GLM-4.7, GLM-4.7-FlashX), credit exhaustion caching, graceful Nemotron fallback
```

Update the "What's New vs OpenClaw" table:

```markdown
| Privacy Router | ❌ All cloud | ✅ 95% local, 5% cloud → ✅ Z.AI-first with Nemotron fallback |
```

Update the "Prerequisites" section:

```markdown
- Z.AI API key (for primary LLM backend) - get from https://platform.z.ai/
```

Update the "Installation" section:

```bash
# Edit .env with your settings
# IMPORTANT: Set ZAI_API_KEY for primary LLM backend
```

- [ ] **Step 2: Add admin API endpoints to main.py**

Add to `services/nemoclaw-orchestrator/main.py`:

```python
# Add after existing imports:
from llm.credit_cache import CreditStatusCache
from llm.zai_client import ZAIClient, ZAIModel

# Add new endpoints after existing endpoints:

@app.get("/llm/zai/status")
async def get_zai_status(settings: Settings):
    """Get current Z.AI availability status"""
    cache = CreditStatusCache(ttl=settings.zai_cache_ttl)
    available = cache.is_available()
    cache.close()

    return {
        "available": available,
        "models": {
            "primary": settings.zai_primary_model,
            "programming": settings.zai_programming_model,
            "fast": settings.zai_fast_model
        },
        "cache_ttl": settings.zai_cache_ttl,
        "thinking_enabled": settings.zai_thinking_enabled
    }


@app.post("/llm/zai/reset")
async def reset_zai_status(settings: Settings):
    """Manually reset Z.AI credit exhaustion flag"""
    cache = CreditStatusCache(ttl=settings.zai_cache_ttl)
    cache.reset()
    cache.close()

    return {"status": "reset", "message": "Z.AI status reset successfully"}


@app.get("/llm/backends")
async def list_backends(settings: Settings):
    """List all available LLM backends with status"""
    cache = CreditStatusCache(ttl=settings.zai_cache_ttl)
    zai_available = cache.is_available()
    cache.close()

    return {
        "backends": [
            {
                "name": "zai_primary",
                "model": settings.zai_primary_model,
                "available": zai_available,
                "description": "GLM-5-Turbo - OpenClaw optimized"
            },
            {
                "name": "zai_programming",
                "model": settings.zai_programming_model,
                "available": zai_available,
                "description": "GLM-4.7 - Programming and reasoning"
            },
            {
                "name": "zai_fast",
                "model": settings.zai_fast_model,
                "available": zai_available,
                "description": "GLM-4.7-FlashX - Fast simple tasks"
            },
            {
                "name": "nemotron_local",
                "model": settings.nemotron_model,
                "available": True,  # Always available as fallback
                "description": "Local DGX Nemotron"
            }
        ]
    }
```

- [ ] **Step 3: Update status.sh**

Add Z.AI status check to `services/nemoclaw-orchestrator/status.sh`:

```bash
# Add after "🔗 Service Endpoints:" section:

echo ""
echo "🤖 LLM Backends:"
ZAI_STATUS=$(curl -s http://localhost:8000/llm/zai/status 2>/dev/null || echo '{"available":false}')
if echo "$ZAI_STATUS" | grep -q '"available".*true'; then
    echo -e "  ${GREEN}✓ Z.AI Available${NC}"
else
    echo -e "  ${YELLOW}⚠️  Z.AI Unavailable (credits exhausted or not configured)${NC}"
fi
echo ""
echo "  Backend Status:"
curl -s http://localhost:8000/llm/backends | python3 -m json.tool 2>/dev/null | grep -E '"name"|"model"|"available"' | sed 's/^[[:space:]]*//' | sed 's/"//g' | sed 's/: */: /' | while read line; do
    echo "    $line"
done
```

- [ ] **Step 4: Create API documentation**

Create `services/nemoclaw-orchestrator/docs/api/zai-endpoints.md`:

```markdown
# Z.AI Endpoints API Documentation

## Overview

The Nemo Claw Orchestrator provides administrative endpoints for monitoring and managing the Z.AI integration.

## Endpoints

### GET /llm/zai/status

Get current Z.AI availability and configuration.

**Response:**
```json
{
  "available": true,
  "models": {
    "primary": "glm-5-turbo",
    "programming": "glm-4.7",
    "fast": "glm-4.7-flashx"
  },
  "cache_ttl": 3600,
  "thinking_enabled": true
}
```

### POST /llm/zai/reset

Manually reset the Z.AI credit exhaustion flag. Use this after replenishing credits.

**Response:**
```json
{
  "status": "reset",
  "message": "Z.AI status reset successfully"
}
```

### GET /llm/backends

List all available LLM backends with their status.

**Response:**
```json
{
  "backends": [
    {
      "name": "zai_primary",
      "model": "glm-5-turbo",
      "available": true,
      "description": "GLM-5-Turbo - OpenClaw optimized"
    },
    {
      "name": "zai_programming",
      "model": "glm-4.7",
      "available": true,
      "description": "GLM-4.7 - Programming and reasoning"
    },
    {
      "name": "zai_fast",
      "model": "glm-4.7-flashx",
      "available": true,
      "description": "GLM-4.7-FlashX - Fast simple tasks"
    },
    {
      "name": "nemotron_local",
      "model": "nemotron-8b",
      "available": true,
      "description": "Local DGX Nemotron"
    }
  ]
}
```
```

- [ ] **Step 5: Update deployment script**

Update `services/nemoclaw-orchestrator/deploy.sh` to mention Z.AI configuration:

```bash
# Add to the echo statements after .env creation:
    echo "  - ZAI_API_KEY (for primary LLM backend - required)"
```

- [ ] **Step 6: Verify all tests still pass**

Run: `cd services/nemoclaw-orchestrator && pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
cd services/nemoclaw-orchestrator
git add README.md main.py status.sh docs/api/zai-endpoints.md deploy.sh
git commit -m "docs: update documentation for Z.AI integration

- Update README with Z.AI-first routing information
- Add admin endpoints: /llm/zai/status, /llm/zai/reset, /llm/backends
- Update status.sh to show Z.AI availability
- Add Z.AI endpoints API documentation
- Update deploy.sh with ZAI_API_KEY instructions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

- [ ] **Step 8: Final verification**

Run: `cd services/nemoclaw-orchestrator && ./status.sh`
Expected: All health checks pass, Z.AI status shows available

---

## Rollback Plan

If issues arise after deployment:

1. **Quick rollback** - Set empty ZAI_API_KEY to force Nemotron-only mode:
   ```bash
   docker compose down
   echo "ZAI_API_KEY=" >> .env
   docker compose up -d
   ```

2. **Full rollback** - Revert to previous commit:
   ```bash
   git revert HEAD~6..HEAD
   docker compose up -d --build
   ```

---

**Document Version:** 1.0
**Last Updated:** 2026-03-20
**Spec:** docs/superpowers/specs/2026-03-20-zai-first-privacy-router-design.md

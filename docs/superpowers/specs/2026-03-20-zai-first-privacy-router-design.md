# Z.AI-First Privacy Router Design Specification

**Date:** 2026-03-20
**Author:** Claude Code
**Status:** Approved
**Related:** Nemo Claw Orchestrator Enhancement

---

## Overview

This specification defines the architectural changes to the Nemo Claw Orchestrator's Privacy Router to prioritize Z.AI API usage over local Nemotron inference. The router will use Z.AI models (GLM-5-Turbo, GLM-4.7, GLM-4.7-FlashX) as primary backends with graceful fallback to local Nemotron when credits are exhausted or the service is unavailable.

**Key Requirements:**
- Z.AI-first routing (not 95% local, 5% cloud)
- Credit exhaustion detection and caching
- Automatic recovery after TTL expires
- Three Z.AI models for different use cases
- Seamless fallback to local Nemotron

---

## Architecture

### High-Level Flow

```
Request → Check Redis for Z.AI status →
  If Z.AI available: Select model based on task type → Call Z.AI
    On success: Return response
    On credit error: Set Redis flag (TTL 1hr), retry with Nemotron
  If Z.AI marked unavailable: Use Nemotron directly
  After TTL expires: Try Z.AI again (auto-recovery)
```

### Circuit Breaker States

| State | Description | Transition |
|-------|-------------|------------|
| CLOSED | Z.AI available, route normally | → OPEN on credit exhaustion |
| OPEN | Z.AI exhausted, use Nemotron | → HALF_OPEN when TTL expires |
| HALF_OPEN | TTL expired, try Z.AI on next request | → CLOSED if success, OPEN if failed |

---

## Components

### 1. ZAIClient (`llm/zai_client.py`)

**Purpose:** Client for Z.AI API, replacing GuardedCloudClient (Anthropic).

**Implementation:**
```python
from openai import OpenAI
from enum import Enum

class ZAIModel(str, Enum):
    PRIMARY = "glm-5-turbo"      # OpenClaw-optimized, tool invocation
    PROGRAMMING = "glm-4.7"      # Enhanced programming, reasoning
    FAST = "glm-4.7-flashx"      # Simple, repetitive tasks

class ZAIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.z.ai/api/paas/v4/"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, model: ZAIModel, max_tokens: int = 512,
                 temperature: float = 0.7, thinking: bool = True):
        try:
            response = self.client.chat.completions.create(
                model=model.value,
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "enabled"} if thinking else None,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.choices[0].message.content,
                "model_used": model.value,
                "credits_exhausted": False
            }
        except Exception as e:
            # Check for credit exhaustion
            if self._is_credit_error(e):
                return {"error": "credit_exhausted", "details": str(e)}
            raise
```

### 2. CreditStatusCache (`llm/credit_cache.py`)

**Purpose:** Manage Z.AI availability state in Redis with TTL.

**Implementation:**
```python
import redis
import os

class CreditStatusCache:
    def __init__(self, redis_url: str = None, ttl: int = 3600):
        self.redis = redis.from_url(redis_url or os.getenv("REDIS_URL"))
        self.ttl = ttl
        self.key = "zai:credit:status"

    def is_available(self) -> bool:
        """Check if Z.AI is available (not marked as exhausted)."""
        return not self.redis.exists(self.key)

    def mark_exhausted(self):
        """Mark Z.AI as exhausted with TTL."""
        self.redis.setex(self.key, self.ttl, "exhausted")

    def reset(self):
        """Manually reset the exhausted flag."""
        self.redis.delete(self.key)
```

### 3. PrivacyRouter Modifications (`llm/privacy_router.py`)

**Changes:**
- New `LLMBackend` enum values: `ZAI_PRIMARY`, `ZAI_PROGRAMMING`, `ZAI_FAST`, `NEMOTRON_LOCAL`
- New config options: `zai_primary_model`, `zai_programming_model`, `zai_fast_model`, `zai_cache_ttl`
- Modified `route()` method for Z.AI-first logic
- Task type to model mapping

**Updated routing logic:**
```python
def route(self, prompt: str, task_type: str = "default") -> LLMBackend:
    # Check cache first
    if not self.credit_cache.is_available():
        return LLMBackend.NEMOTRON_LOCAL

    # Select Z.AI model based on task type
    if task_type in ["tool_invocation", "persistent", "orchestration"]:
        return LLMBackend.ZAI_PRIMARY
    elif task_type in ["programming", "code_generation"]:
        return LLMBackend.ZAI_PROGRAMMING
    elif task_type in ["simple", "repetitive", "quick"]:
        return LLMBackend.ZAI_FAST
    else:
        return LLMBackend.ZAI_PRIMARY  # Default
```

### 4. Config Updates (`config.py`)

**New environment variables:**
```python
class Settings(BaseSettings):
    # Z.AI Configuration
    ZAI_API_KEY: str = ""  # Required
    ZAI_PRIMARY_MODEL: str = "glm-5-turbo"
    ZAI_PROGRAMMING_MODEL: str = "glm-4.7"
    ZAI_FAST_MODEL: str = "glm-4.7-flashx"
    ZAI_CACHE_TTL: int = 3600  # 1 hour
    ZAI_THINKING_ENABLED: bool = True

    # Existing Nemotron config (fallback)
    nemotron_model: str = "nemotron-8b"
    dgx_endpoint: str = "http://localhost:8000"
```

---

## Data Flow

### Request Routing Sequence

```
1. Orchestration layer calls PrivacyRouter.generate(prompt, task_type)

2. PrivacyRouter.route() determines backend:
   - Check Redis: Is Z.AI marked as exhausted?
     - If YES (within TTL): Go to step 6
     - If NO or expired: Continue to step 3

3. Select Z.AI model based on task_type:
   - "tool_invocation" or "persistent" → glm-5-turbo
   - "programming" or "code_generation" → glm-4.7
   - "simple" or "repetitive" → glm-4.7-flashx

4. Call ZAIClient.generate()
   - On success: Return response
   - On HTTP 402/403 with "insufficient credits":
     - Call CreditStatusCache.mark_exhausted() (sets Redis key with TTL)
     - Log warning: "Z.AI credits exhausted, falling back to Nemotron"
     - Continue to step 5
   - On other errors: Try next Z.AI model, then fallback to Nemotron

5. Retry with NemotronClient.generate()
   - On success: Return response with backend="nemotron_local"
   - On error: Raise LLMUnavailableError

6. If Z.AI marked exhausted, use NemotronClient.generate() directly
   - After TTL expires, next request will try Z.AI again (auto-recovery)
```

### Response Format

```json
{
  "text": "generated response text",
  "backend": "zai_primary|zai_programming|zai_fast|nemotron_local",
  "model_used": "glm-5-turbo|glm-4.7|glm-4.7-flashx|nemotron-8b",
  "credits_exhausted": false,
  "execution_time": 0.234
}
```

---

## Error Handling

### Error Categories

| Category | Detection | Action | User Impact |
|----------|-----------|--------|-------------|
| **Credit Exhaustion** | HTTP 402/403 with "insufficient credits" | Mark exhausted, retry with Nemotron | None (seamless) |
| **Z.AI Unavailable** | HTTP 500/502/503/504, timeout | Retry with backoff (3x), then fallback | Brief delay |
| **Nemotron Unavailable** | DGX not responding, GPU errors | Return `LLMUnavailableError` | Request fails |
| **Invalid Request** | Malformed prompt, policy violation | Return `InvalidRequestError` | Clear error |

### Circuit Breaker Logic

```python
# In PrivacyRouter.generate()
try:
    result = self.zai_client.generate(prompt, selected_model)
    return result
except CreditExhaustedError:
    self.credit_cache.mark_exhausted()
    logger.warning("Z.AI credits exhausted, falling back to Nemotron")
    # Retry with Nemotron
    return self.nemotron_client.generate(prompt)
except TransientError:
    # Retry with backoff, then fallback
    return self._retry_with_backoff(prompt, selected_model)
```

---

## Testing

### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_zai_client.py` | ZAIClient generation, error detection, auth |
| `tests/unit/test_credit_cache.py` | Cache operations, TTL, Redis errors |
| `tests/unit/test_privacy_router.py` | Routing logic, model selection, circuit breaker |

### Integration Tests

| Test File | Coverage |
|-----------|----------|
| `tests/integration/test_zai_routing.py` | Full request flow, credit exhaustion, TTL recovery |
| `tests/integration/test_zai_live.py` | Real API calls (requires ZAI_API_KEY) |

### Coverage Target

- **Unit Tests:** 85%+ coverage
- **Integration Tests:** Full request flow coverage
- **Edge Cases:** TTL expiration, concurrent requests, all error types

---

## Configuration Examples

### Environment Variables (.env)

```bash
# Z.AI Configuration (Primary)
ZAI_API_KEY=your-zai-api-key-here
ZAI_PRIMARY_MODEL=glm-5-turbo
ZAI_PROGRAMMING_MODEL=glm-4.7
ZAI_FAST_MODEL=glm-4.7-flashx
ZAI_CACHE_TTL=3600
ZAI_THINKING_ENABLED=true

# Nemotron Configuration (Fallback)
NEMOTRON_MODEL=nemotron-8b
DGX_ENDPOINT=http://dgx-nemotron:8000

# Redis (for cache)
REDIS_URL=redis://redis:6379
```

### Docker Compose Updates

```yaml
services:
  nemoclaw-orchestrator:
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - ZAI_PRIMARY_MODEL=glm-5-turbo
      - ZAI_PROGRAMMING_MODEL=glm-4.7
      - ZAI_FAST_MODEL=glm-4.7-flashx
      - ZAI_CACHE_TTL=3600
```

---

## Dependencies

### New Requirements

```txt
# Z.AI client (uses OpenAI SDK with custom base_url)
openai>=1.0.0

# Redis for credit status cache
redis>=5.0.0
```

### Removed Dependencies

```txt
# Anthropic (no longer needed)
# anthropic>=0.18.0
```

---

## Migration Path

### Step 1: Add Z.AI Client
- Create `llm/zai_client.py`
- Implement ZAIClient class

### Step 2: Add Credit Cache
- Create `llm/credit_cache.py`
- Implement CreditStatusCache class

### Step 3: Update Privacy Router
- Modify `llm/privacy_router.py`
- Add Z.AI-first routing logic
- Update LLMBackend enum

### Step 4: Update Configuration
- Add Z.AI environment variables to `.env.example`
- Update `config.py` Settings class

### Step 5: Update Tests
- Modify existing tests for new behavior
- Add Z.AI-specific tests

### Step 6: Deploy and Verify
- Update Docker Compose configuration
- Deploy to DGX Spark GB0
- Run integration tests
- Monitor credit exhaustion behavior

---

## Rollback Plan

If issues arise:

1. **Quick rollback:** Set `ZAI_CACHE_TTL=0` and `ZAI_API_KEY=""` to force Nemotron-only mode
2. **Full rollback:** Revert to previous GuardedCloudClient implementation
3. **Configuration rollback:** Use environment variable to enable/disable Z.AI routing

---

## Monitoring

### Key Metrics

- Z.AI request rate vs Nemotron rate
- Credit exhaustion events (timestamp, frequency)
- TTL cache hit/miss ratio
- Fallback latency (time to switch to Nemotron)
- Model usage distribution (primary vs programming vs fast)

### Logging

```python
logger.info(f"LLM request: backend={backend}, model={model}, task_type={task_type}")
logger.warning(f"Z.AI credit exhaustion detected, marking exhausted for {TTL}s")
logger.info(f"Z.AI recovered after TTL expiration, resuming normal routing")
```

---

## API Endpoints

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/llm/zai/status` | GET | Current Z.AI availability status |
| `/llm/zai/reset` | POST | Manually reset credit exhaustion flag |
| `/llm/backends` | GET | List all available backends with status |

### Existing Endpoints (Enhanced)

| Endpoint | Enhancement |
|----------|-------------|
| `/llm/status` | Add Z.AI fields to response |
| `/v1/orchestrate` | Include `backend` and `model_used` in response |

---

## References

- [GLM-5-Turbo Documentation](https://docs.z.ai/guides/llm/glm-5-turbo)
- [GLM-4.7 Documentation](https://docs.z.ai/guides/llm/glm-4.7)
- [Z.AI API Base URL](https://api.z.ai/api/paas/v4/)
- [Nemo Claw Orchestrator README](../../../services/nemoclaw-orchestrator/README.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-03-20

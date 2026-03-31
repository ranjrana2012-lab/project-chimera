# Z.AI Rate Limits & Optimization Guide

**Last Updated**: March 31, 2026
**Service**: NemoClaw Orchestrator
**Models**: GLM-5.1 Turbo, GLM-4.7, GLM-4.7-FlashX

---

## Overview

This document covers Z.AI (智谱AI) rate limits, pricing, and optimization strategies for Project Chimera's NemoClaw Orchestrator.

---

## Current Configuration

### Model Cascade (Priority Order)

| Priority | Model | Speed | Purpose | When Used |
|----------|-------|-------|---------|-----------|
| **1st** | GLM-5.1 Turbo (`glm-5-turbo`) | ⚡ Fast | General orchestration, tool calls | Default for all tasks |
| **2nd** | GLM-4.7 (`glm-4.7`) | Medium | Complex programming, reasoning | Fallback from 5.1 |
| **3rd** | GLM-4.7-FlashX (`glm-4.7-flashx`) | ⚡⚡ Fastest | Simple tasks, classification | Fallback from 4.7 |
| **4th** | Nemotron 120B (local) | Slow | Offline fallback | When Z.AI exhausted |
| **5th** | Ollama (local) | Slow | Final fallback | When all cloud unavailable |

---

## Z.AI Pricing & Rate Limits (2026)

### Token Pricing (per 1K tokens)

| Model | Input | Output | Context Window |
|-------|-------|--------|----------------|
| **GLM-5.1 Turbo** | ¥0.5 | ¥0.5 | 32K |
| **GLM-4.7** | ¥0.5 | ¥0.5 | 128K |
| **GLM-4.7-FlashX** | ¥0.05 | ¥0.05 | 128K |

### Rate Limits (Free Tier)

| Limit | Value | Notes |
|-------|-------|-------|
| **Requests/hour** | ~60-100 | Varies by account |
| **Tokens/minute** | ~10K-30K | Burst rate |
| **Daily quota** | 4000 prompts/5hrs | Promotional quota |

### Rate Limits (Paid Tier)

| Limit | Value | Notes |
|-------|-------|-------|
| **Concurrent requests** | 5-10 | Parallel processing |
| **RPM** | 100-500 | Depends on plan level |
| **TPM** | 300K-1M | Depends on plan level |

---

## Current Rate Limiting Configuration

### Application-Level Rate Limits (FastAPI)

Located in `/services/shared/rate_limit.py`:

```python
RATE_LIMIT_PER_MINUTE=60    # Default: 60 requests/minute
RATE_LIMIT_PER_HOUR=1000     # Default: 1000 requests/hour
```

**Applied via middleware** to all Chimera services:
- OpenClaw Orchestrator (Port 8000)
- NemoClaw Orchestrator (Port 9000)
- All agent services (8001-8011)

### Z.AI Client Rate Limiting

The Z.AI client uses OpenAI SDK with built-in retry logic:

```python
# Credit exhaustion detection with auto-fallback
# Error codes: 402, 403, "1113" (insufficient balance)
# Automatic TTL: 3600 seconds (1 hour) before retry
```

---

## Credit Exhaustion Handling

### Current Implementation

**File**: `/services/nemoclaw-orchestrator/llm/credit_cache.py`

```python
class CreditStatusCache:
    """Manages Z.AI credit exhaustion status in Redis"""

    def __init__(self, ttl: int = 3600):
        """
        Args:
            ttl: Time-to-live for exhausted flag (default: 1 hour)
                 After TTL, automatically retry Z.AI
        """
        self.key = "zai:credit:status"
```

### Behavior

| Event | Action | TTL |
|-------|--------|-----|
| Z.AI returns 402/403 error | Mark as "exhausted" in Redis | 3600s (1 hour) |
| TTL expires | Auto-retry Z.AI on next request | - |
| Manual reset | `redis.delete zai:credit:status` | - |

---

## Optimization Strategies

### 1. Model Selection Strategy

**Current Cascade** (Recommended):
```
GLM-5.1 Turbo (fastest) → GLM-4.7 (reliable) → GLM-4.7-FlashX (cheap) → Local
```

**Rationale**:
- GLM-5.1 Turbo: Best speed for most tasks
- GLM-4.7: Higher reliability for complex tasks
- GLM-4.7-FlashX: Cheapest for simple tasks (90% cost reduction)

### 2. Token Optimization

**Prompt Compression**:
```python
# BAD: Verbose prompt
prompt = "Please analyze the following text and tell me what the sentiment is..."

# GOOD: Concise prompt
prompt = "Sentiment analysis: " + text
```

**Max Tokens Management**:
```python
# For simple tasks: limit output
zai_client.generate(
    prompt="Classify: positive/negative/neutral",
    max_tokens=10  # Only need 1 token for classification
)

# For complex tasks: allow more
zai_client.generate(
    prompt="Write a scene with dialogue...",
    max_tokens=2000  # Full scene generation
)
```

### 3. Caching Strategy

**Current TTL**: 3600 seconds (1 hour) for credit status

**Recommended adjustments**:
- Development: `ZAI_CACHE_TTL=1800` (30 min) - Faster recovery
- Production: `ZAI_CACHE_TTL=7200` (2 hours) - More stability

### 4. Request Batching

**For multiple similar requests**:
```python
# BAD: Separate requests
for item in items:
    zai_client.generate(f"Analyze: {item}")

# GOOD: Batch request
batch = "\n".join([f"Analyze: {item}" for item in items])
zai_client.generate(batch)
```

---

## Monitoring & Alerting

### Key Metrics to Track

**Z.AI Usage**:
- `zai_requests_total` - Total requests made
- `zai_requests_success` - Successful requests
- `zai_requests_failed` - Failed requests
- `zai_credits_exhausted_count` - Times marked exhausted
- `zai_model_distribution` - Which model used

**Fallback Usage**:
- `fallback_to_nemotron_count` - Times fell back to local
- `fallback_to_ollama_count` - Times fell back to Ollama

### Prometheus Metrics (Current)

Already tracked in `/services/nemoclaw-orchestrator/metrics.py`:
```python
# Add these to track Z.AI usage
zai_requests = Counter("zai_requests_total", ["model", "status"])
zai_tokens_used = Histogram("zai_tokens_total", buckets=[100, 500, 1000, 5000])
```

---

## Environment Variables

### Z.AI Configuration

```bash
# .env for nemoclaw-orchestrator

# Primary Models
ZAI_API_KEY=your_api_key_here
ZAI_PRIMARY_MODEL=glm-5-turbo           # GLM-5.1 Turbo
ZAI_PROGRAMMING_MODEL=glm-4.7           # GLM-4.7
ZAI_FAST_MODEL=glm-4.7-flashx           # GLM-4.7-FlashX

# Credit Cache TTL (seconds)
ZAI_CACHE_TTL=3600                     # 1 hour before auto-retry

# Enable Thinking Mode (if supported)
ZAI_THINKING_ENABLED=false              # Disabled by default

# Local Fallback (optional)
NEMOTRON_ENABLED=false                 # Disable for cloud-only
LOCAL_RATIO=0.0                        # 0% = cloud only
```

### Application Rate Limits

```bash
# .env at project root

# Per-service rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

---

## Best Practices

### 1. Use GLM-5.1 Turbo for Most Tasks

**Best for**:
- Show orchestration
- Tool invocation
- Real-time responses
- General dialogue

**Avoid for**:
- Extremely long code generation
- Very complex reasoning (use GLM-4.7 instead)

### 2. Use GLM-4.7-FlashX for Simple Tasks

**Best for**:
- Classification (positive/negative/neutral)
- Short responses
- Repetitive tasks

**Cost savings**: 90% compared to GLM-4.7

### 3. Monitor Credit Status

**Check current status**:
```bash
# From within container
docker exec chimera-redis redis-cli GET zai:credit:status

# Reset manually if needed
docker exec chimera-redis redis-cli DEL zai:credit:status
```

### 4. Implement Circuit Breaker Pattern

**Current implementation**: `/services/nemoclaw-orchestrator/resilience/circuit_breaker.py`

Automatically opens circuit when Z.AI fails repeatedly, preventing request pile-up.

---

## Quarterly Maintenance Checklist

- [ ] Review Z.AI pricing changes (they update frequently)
- [ ] Update model pricing table in this document
- [ ] Check rate limit adjustments in Z.AI console
- [ ] Review `ZAI_CACHE_TTL` - adjust based on usage patterns
- [ ] Analyze fallback metrics - increase local capacity if needed
- [ ] Update `ZAI_API_KEY` if rotated
- [ ] Review model cascade strategy - is GLM-5.1 still best primary?

---

## Troubleshooting

### Issue: "Rate limit exceeded"

**Symptoms**: 429 errors, slow responses

**Solutions**:
1. Check `ZAI_CACHE_TTL` - reduce if too long
2. Check `RATE_LIMIT_PER_MINUTE` - may be too aggressive
3. Review logs: `docker-compose logs nemoclaw-orchestrator | grep rate`

### Issue: "Credit exhausted"

**Symptoms**: All requests falling back to local models

**Solutions**:
1. Verify Z.AI account has credits
2. Check API key is valid
3. Reset credit cache: `redis-cli DEL zai:credit:status`

### Issue: "Slow responses"

**Symptoms**: Requests taking >10 seconds

**Solutions**:
1. Switch to GLM-5.1 Turbo (faster)
2. Reduce `max_tokens` for simple tasks
3. Enable request batching

---

## Cost Optimization

### Estimated Monthly Costs (Based on 100K requests)

| Model Mix | Cost | Notes |
|----------|------|-------|
| 70% GLM-5.1 Turbo | ¥35,000 | Fast, capable |
| 20% GLM-4.7 | ¥10,000 | Complex tasks |
| 10% GLM-4.7-FlashX | ¥500 | Simple tasks |
| **Total** | **¥45,500** | Per 100K requests |

### Cost Reduction Strategies

1. **Increase FlashX usage** to 20-30% (saves ~¥1,000/month)
2. **Implement prompt caching** for repeated queries
3. **Batch similar requests** together
4. **Use local models** for non-critical tasks during off-hours

---

## Z.AI Account Management

### Dashboard Access

- URL: https://open.bigmodel.cn/
- Monitor: API usage, billing, quota
- Manage: API keys, rate limits

### Key Pages

1. **API Keys**: https://open.bigmodel.cn/usercenter/apikeys
2. **Billing**: https://open.bigmodel.cn/usercenter/balance
3. **Usage**: https://open.bigmodel.cn/usercenter/usage

---

## Related Documentation

- `/services/nemoclaw-orchestrator/llm/privacy_router.py` - Router implementation
- `/services/nemoclaw-orchestrator/llm/zai_client.py` - Z.AI client
- `/services/nemoclaw-orchestrator/llm/credit_cache.py` - Credit cache
- `/docs/dual-stack-architecture.md` - Overall architecture
- `/docs/Z_AI_INTEGRATION_GUIDE.md` - Setup guide

---

**Maintained By**: Project Chimera Team
**Last Review**: March 31, 2026
**Next Review**: June 30, 2026 (Quarterly)

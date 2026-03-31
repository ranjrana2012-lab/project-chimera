# Z.AI Max Plan Optimization Guide

**Last Updated**: March 31, 2026
**Service**: NemoClaw Orchestrator
**Plan**: Z.AI Max Plan with Promotional Quota

---

## Overview

This guide covers optimizing NemoClaw Orchestrator for **Z.AI Max Plan** users who have the generous **4000 prompts/5 hours** promotional quota. The goal is to maximize intelligence quality while fully utilizing the available quota.

---

## Current Configuration (Optimal for Max Plan)

### Model Cascade Priority

```
┌─────────────────────────────────────────────────────────────┐
│  NEMOCLAW Z.AI MAX PLAN CASCADE                             │
├─────────────────────────────────────────────────────────────┤
│  1. GLM-5.1 Turbo (glm-5-turbo)     ← PRIMARY              │
│     → Best intelligence, fastest response                   │
│     → 32K context, ¥0.5/1K tokens                           │
│     → Use for: orchestration, general tasks                 │
├─────────────────────────────────────────────────────────────┤
│  2. GLM-4.7 (glm-4.7)               ← FALLBACK 1           │
│     → Enhanced programming & reasoning                     │
│     → 128K context, ¥0.5/1K tokens                          │
│     → Use for: complex code, deep reasoning                 │
├─────────────────────────────────────────────────────────────┤
│  3. GLM-4.7-FlashX (glm-4.7-flashx) ← FALLBACK 2           │
│     → Fast, lightweight for simple tasks                    │
│     → 128K context, ¥0.05/1K tokens (90% savings!)          │
│     → Use for: classification, quick responses              │
├─────────────────────────────────────────────────────────────┤
│  4. Local Nemotron 120B             ← SAFETY NET            │
│     → Offline fallback when Z.AI quota exhausted            │
│     → Only activated after credit_exhausted flag            │
└─────────────────────────────────────────────────────────────┘
```

---

## Intelligent Task Routing

The privacy router automatically selects the optimal model based on task complexity:

### Task → Model Mapping

| Task Type | Model | Why |
|-----------|-------|-----|
| **Simple/Classification** | GLM-4.7-FlashX (direct) | Saves premium quota, still accurate |
| **Programming/Code Gen** | GLM-4.7 → GLM-5.1 Turbo | Best for complex code |
| **Tool Invocation** | GLM-5.1 Turbo | Fast, reliable |
| **Show Orchestration** | GLM-5.1 Turbo | Best overall intelligence |
| **Sentiment Analysis** | GLM-4.7-FlashX | Simple classification |
| **Caption Generation** | GLM-5.1 Turbo | Needs quality |
| **Music Generation** | GLM-4.7 → GLM-5.1 Turbo | Creative tasks |

### Code Reference (`privacy_router.py`)

```python
def _select_zai_model(self, task_type: str) -> LLMBackend:
    # FlashX directly for simple tasks (saves premium quota)
    if task_type in ["simple", "repetitive", "quick", "classification"]:
        return LLMBackend.ZAI_FAST  # glm-4.7-flashx

    # GLM-4.7 for complex programming
    if task_type in ["programming", "code_generation", "debugging", "complex"]:
        return LLMBackend.ZAI_PROGRAMMING  # glm-4.7

    # Default: GLM-5.1 Turbo (best intelligence)
    return LLMBackend.ZAI_PRIMARY  # glm-5-turbo
```

---

## Max Plan Configuration

### Environment Variables (`.env`)

```bash
# Z.AI Max Plan Configuration
ZAI_API_KEY=your-max-plan-api-key
ZAI_PRIMARY_MODEL=glm-5-turbo           # GLM-5.1 Turbo - Best intelligence
ZAI_PROGRAMMING_MODEL=glm-4.7           # GLM-4.7 - Enhanced reasoning
ZAI_FAST_MODEL=glm-4.7-flashx           # GLM-4.7-FlashX - Cost optimization

# Credit Cache TTL (Max Plan: shorter for faster retry)
ZAI_CACHE_TTL=1800                     # 30 minutes (was 3600s)
                                        # Faster recovery when quota resets

# Local Fallback (Safety Net, not primary)
NEMOTRON_ENABLED=true                  # Keep for offline scenarios
LOCAL_RATIO=0.0                        # 0% = Z.AI-first

# Thinking Mode (GLM-5.1 Turbo supports extended reasoning)
ZAI_THINKING_ENABLED=true              # Enable for complex tasks
```

### Key Max Plan Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| `ZAI_CACHE_TTL` | `1800` (30 min) | Faster retry when quota resets vs 3600s (1 hour) |
| `NEMOTRON_ENABLED` | `true` | Safety net for quota exhaustion |
| `LOCAL_RATIO` | `0.0` | Z.AI-first, local only when exhausted |
| `ZAI_THINKING_ENABLED` | `true` | Maximize GLM-5.1 Turbo reasoning |

---

## Quota Utilization Strategy

### Understanding Your 5-Hour Promotional Quota

**Z.AI Promotional Quota**: 4000 prompts per 5 hours

```
Hour 1: ████████ 800 prompts used
Hour 2: ████████ 800 prompts used
Hour 3: ████████ 800 prompts used
Hour 4: ████████ 800 prompts used
Hour 5: ████████ 800 prompts used
         ↓
      Quota Resets
```

### Maximizing Quota Usage

**Do's** ✅
- Use GLM-5.1 Turbo for everything that needs intelligence
- Use FlashX for simple tasks (saves quota for complex ones)
- Monitor usage with Prometheus metrics
- Let the automatic cascade handle fallbacks

**Don'ts** ❌
- Don't artificially limit requests to "save quota"
- Don't disable local fallback (safety net is essential)
- Don't reduce `max_tokens` unnecessarily (quality loss)
- Don't manually reset credit cache (let TTL expire naturally)

---

## Credit Exhaustion Handling

### Automatic Fallback Behavior

```
Request to GLM-5.1 Turbo
    ↓
402/403 Error (Credit Exhausted)
    ↓
1. Mark as exhausted in Redis (TTL: 1800s)
2. Fallback to GLM-4.7
3. If GLM-4.7 fails → Fallback to FlashX
4. If FlashX fails → Fallback to Local Nemotron
5. After TTL expires → Auto-retry Z.AI
```

### Redis Key Structure

```
Key: zai:credit:status
Value: "exhausted"
TTL:  1800 seconds (30 minutes for max plan)
```

### Manual Commands

```bash
# Check current status
docker exec chimera-redis redis-cli GET zai:credit:status

# Manually reset (if quota replenished early)
docker exec chimera-redis redis-cli DEL zai:credit:status

# Check TTL remaining
docker exec chimera-redis redis-cli TTL zai:credit:status
```

---

## Monitoring & Metrics

### Prometheus Metrics to Track

Add to `/services/nemoclaw-orchestrator/metrics.py`:

```python
from prometheus_client import Counter, Histogram

# Z.AI Usage Metrics
zai_requests_total = Counter(
    "zai_requests_total",
    "Total Z.AI requests",
    ["model", "status"]
)

zai_tokens_used = Histogram(
    "zai_tokens_used",
    "Z.AI tokens consumed",
    buckets=[100, 500, 1000, 5000, 10000, 50000]
)

zai_quota_exhausted_count = Counter(
    "zai_quota_exhausted_count",
    "Times Z.AI quota was marked exhausted"
)

zai_model_cascade_count = Counter(
    "zai_model_cascade_count",
    "Model fallback events",
    ["from_model", "to_model"]
)
```

### Grafana Dashboard Queries

```promql
# Requests per model
sum(rate(zai_requests_total{model="glm-5-turbo"}[5m]))
sum(rate(zai_requests_total{model="glm-4.7"}[5m]))
sum(rate(zai_requests_total{model="glm-4.7-flashx"}[5m]))

# Quota exhaustion rate
increase(zai_quota_exhausted_count[1h])

# Token consumption rate
rate(zai_tokens_used_sum[5m])

# Cascade events
zai_model_cascade_count
```

---

## Cost Analysis (Max Plan)

### Estimated Monthly Usage (100K requests)

| Model Mix | Requests | Cost | Quota Usage |
|-----------|----------|------|-------------|
| 60% GLM-5.1 Turbo | 60,000 | ¥30,000 | 60% of quota |
| 30% GLM-4.7 | 30,000 | ¥15,000 | 30% of quota |
| 10% GLM-4.7-FlashX | 10,000 | ¥500 | 10% of quota |
| **Total** | **100,000** | **¥45,500** | **100%** |

### Optimization Savings

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| FlashX for simple tasks | 90% cost reduction | Already enabled |
| Request batching | 20-30% fewer API calls | Manual implementation |
| Prompt compression | 30-40% fewer tokens | Manual optimization |
| Response caching | Up to 50% cache hit rate | Depends on workload |

---

## Best Practices for Max Plan

### 1. Always Use GLM-5.1 Turbo First

```python
# GOOD: Let the router decide
router.generate(prompt, task_type="default")

# BAD: Force cheaper model prematurely
router.generate(prompt, force_backend=LLMBackend.ZAI_FAST)
```

### 2. Leverage Thinking Mode

```python
# Enable for complex orchestration
result = router.generate(
    prompt="Analyze audience sentiment and adjust lighting...",
    thinking=True,  # Extended reasoning
    max_tokens=2000
)
```

### 3. Use Appropriate Token Limits

```python
# Simple classification: Low token limit
result = router.generate(
    prompt="Classify: positive/negative",
    max_tokens=10  # Only need 1 token
)

# Complex generation: Higher token limit
result = router.generate(
    prompt="Generate a scene with dialogue...",
    max_tokens=2000  # Full scene
)
```

### 4. Monitor Quota in Real-Time

```bash
# Watch Redis credit status
watch -n 5 'docker exec chimera-redis redis-cli GET zai:credit:status'

# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=zai_requests_total
```

---

## Troubleshooting

### Issue: All requests falling back to local

**Symptoms**: `zai:credit:status` shows "exhausted", local models always used

**Solutions**:
1. Check Z.AI dashboard for actual quota status
2. Verify `ZAI_CACHE_TTL` isn't too long (reduce to 1800s for max plan)
3. Manually reset if quota was replenished: `redis-cli DEL zai:credit:status`
4. Check API key validity in Z.AI console

### Issue: Not using full quota

**Symptoms**: Low request volume, quota not fully utilized

**Solutions**:
1. Remove artificial rate limits
2. Check `RATE_LIMIT_PER_MINUTE` setting
3. Verify `ZAI_THINKING_ENABLED=true` for best quality
4. Review logs for unnecessary fallbacks to local models

### Issue: FlashX being used too much

**Symptoms**: High FlashX usage, low GLM-5.1 Turbo usage

**Solutions**:
1. Review task_type classifications in `privacy_router.py`
2. Consider if tasks marked "simple" actually need more intelligence
3. Adjust task type mapping if needed

---

## Quarterly Maintenance Checklist

- [ ] Review Z.AI max plan terms (they update frequently)
- [ ] Check if promotional quota (4000/5hrs) still applies
- [ ] Update pricing table in this document
- [ ] Review `ZAI_CACHE_TTL` - adjust based on quota reset patterns
- [ ] Analyze model distribution metrics - optimize for intelligence
- [ ] Verify API key hasn't expired (max plan keys may rotate)
- [ ] Test credit exhaustion and recovery flow
- [ ] Review Prometheus metrics for anomalies
- [ ] Update local model fallback configuration if needed

---

## Related Documentation

- `/docs/Z_AI_RATE_LIMITS_AND_OPTIMIZATION.md` - General Z.AI guide
- `/docs/dual-stack-architecture.md` - NemoClaw architecture
- `/services/nemoclaw-orchestrator/llm/privacy_router.py` - Router implementation
- `/services/nemoclaw-orchestrator/llm/zai_client.py` - Z.AI client
- `/services/nemoclaw-orchestrator/llm/credit_cache.py` - Credit cache

---

**Maintained By**: Project Chimera Team
**Last Review**: March 31, 2026
**Next Review**: June 30, 2026 (Quarterly)

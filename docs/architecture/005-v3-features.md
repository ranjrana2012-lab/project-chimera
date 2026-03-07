# ADR-005: v0.5.0 Feature Enhancements

**Status:** Accepted
**Date:** 2026-03-04
**Context:** Project Chimera v0.5.0

---

## Context

Project Chimera v0.5.0 introduces significant feature enhancements across multiple services to improve AI capabilities, content moderation, accessibility, and operator oversight.

### Problems Being Solved

1. **Limited dialogue variation** - SceneSpeak produced same style regardless of genre
2. **Basic safety filtering** - Single-layer pattern matching insufficient
3. **No visual accessibility** - BSL translation was text-only
4. **No real-time oversight** - Operator console had to refresh for updates
5. **No performance optimization** - No profiling or caching utilities

---

## Decision

Implement four major feature enhancements:

### 1. SceneSpeak LoRA Adapters

**Purpose:** Genre-specific dialogue styling using Low-Rank Adaptation

**Architecture:**
```
SceneSpeak Agent
    ├── Base Model (LLM)
    ├── LoRA Manager
    │   ├── Load Adapter
    │   ├── Switch Adapter
    │   └── Benchmark Adapter
    └── Adapter Library
        ├── dramatic-theatre
        ├── comedy
        └── noir
```

**Benefits:**
- Efficient fine-tuning (LoRA vs full fine-tune)
- Quick adapter switching (<500ms)
- Genre-appropriate dialogue
- A/B testing capability

**API:**
- `GET /v1/adapters` - List adapters
- `POST /v1/adapters/load` - Load adapter
- `POST /v1/adapters/switch` - Switch adapters
- `POST /v1/adapters/benchmark` - Benchmark performance

### 2. Multi-Layer Safety Filtering

**Purpose:** Comprehensive content moderation using three-layer approach

**Architecture:**
```
Safety Filter
    ├── Layer 1: Pattern Matching
    │   └── Regex-based known harmful patterns
    ├── Layer 2: ML Classification
    │   └── Toxic/hateful/sexual/violent classifier
    ├── Layer 3: Context-Aware Analysis
    │   └── Transformer-based conversation context
    └── Audit Log
        └── All decisions logged
```

**Filter Flow:**
```
Content Input
    │
    ▼
┌───────────────────┐
│ Pattern Match     │──► Block ───┐
└───────────────────┘             │
    │ Pass                        │
    ▼                             │
┌───────────────────┐             │
│ ML Classification │──► Flag ────┤
└───────────────────┘             │
    │ Pass                        │
    ▼                             │
┌───────────────────┐             │
│ Context Analysis  │──► Flag ────┤
└───────────────────┘             │
    │ Pass                        ▼
    ▼                        ┌─────────┐
┌──────────────┐              │ Output  │
│    Allow     │              └─────────┘
└──────────────┘
```

**Benefits:**
- Multiple detection methods reduce false positives/negatives
- Context-aware understanding
- Complete audit trail
- Configurable thresholds

### 3. BSL Avatar Rendering

**Purpose:** Real-time sign language visualization for accessibility

**Architecture:**
```
BSL Agent
    ├── Text-to-Gloss Translator
    ├── Gesture Library
    │   └── Cached sign gestures
    └── Avatar Renderer
        ├── 3D Avatar Model
        ├── Gesture Queue
        └── Real-time Animation
```

**Avatar States:**
- `idle` - Waiting for input
- `signing` - Currently signing
- `transitioning` - Between gestures
- `error` - Error occurred

**Benefits:**
- Visual accessibility for deaf audiences
- Real-time signing (~30 FPS)
- Session-based avatar management
- Performance metrics tracking

**API:**
- `POST /api/v1/avatar/sign` - Queue text for signing
- `GET /api/v1/avatar/state` - Get avatar state
- `GET /api/v1/avatar/list` - List active avatars

### 4. Real-Time Console Updates

**Purpose:** WebSocket-based live metrics and alerts for operators

**Architecture:**
```
Operator Console
    ├── WebSocket Server
    ├── Connection Manager
    │   ├── Subscribe/Unsubscribe
    │   └── Broadcast Loop (30 FPS)
    ├── Metrics Collector
    │   └── Poll all services every 5s
    └── Alert Manager
        └── Real-time alert broadcasting
```

**Message Types:**
- `metric` - Service metrics (CPU, memory, etc.)
- `alert` - Alert notifications
- `status` - Service status changes
- `control` - Control events

**Benefits:**
- No more manual refresh
- Sub-second updates
- Channel-based subscriptions
- Reduced bandwidth vs polling

**WebSocket Protocol:**
```javascript
// Subscribe
{"action": "subscribe", "channels": ["metrics:*", "alerts"]}

// Metric update
{"type": "metric", "service": "SceneSpeak Agent",
 "metric": "cpu_percent", "value": 45.2, "unit": "%"}

// Alert
{"type": "alert", "severity": "warning",
 "title": "High CPU", "message": "CPU exceeded 80%"}
```

---

## Performance Optimizations

### Performance Profiler

```python
@profiler.profile("dialogue_generation")
def generate_dialogue(context):
    # Automatic timing and call counting
    pass
```

**Features:**
- Function-level profiling
- Call count tracking
- Min/max/avg timing
- Error tracking

### Cache Manager

```python
@cache.cached(ttl=300)
def expensive_computation(input_data):
    # Redis + local cache
    return result
```

**Features:**
- Redis backend with local fallback
- Configurable TTL
- Automatic cache invalidation
- Performance metrics

### Resource Monitor

```python
monitor = ResourceMonitor()
metrics = monitor.get_metrics()
# {"cpu_percent": 45.2, "memory_mb": 1024, ...}
```

**Features:**
- CPU/memory monitoring
- Thread count tracking
- File descriptor tracking
- Alert on thresholds

---

## Benefits Summary

| Feature | Key Benefit |
|---------|-------------|
| LoRA Adapters | Genre-appropriate dialogue without retraining |
| Multi-Layer Safety | Fewer false blocks, better context understanding |
| BSL Avatar | Visual accessibility for deaf audiences |
| Real-Time Updates | Immediate operator awareness |
| Performance Tools | Identify and fix bottlenecks |

---

## Alternatives Considered

### Alternative 1: Full Model Fine-Tuning

**Rejected because:**
- Requires full model copy per genre
- Expensive storage and memory
- Slow switching between genres

**LoRA advantages:**
- Small adapter files (~10MB vs 4GB)
- Fast switching (<500ms)
- Shared base model

### Alternative 2: Single-Layer Safety

**Rejected because:**
- High false positive rate with pattern matching
- No context understanding
- Difficult to tune

**Multi-layer advantages:**
- Progressive filtering (fast to slow)
- Context awareness
- Better accuracy

### Alternative 3: Polling for Updates

**Rejected because:**
- Higher bandwidth usage
- Delayed updates (poll interval)
- Server load

**WebSocket advantages:**
- Instant updates
- Lower bandwidth
- Channel subscriptions

---

## Implementation Status

- [x] LoRA adapter support - 20 tests passing
- [x] Multi-layer safety filter - 25 tests passing
- [x] BSL avatar rendering - Implementation complete
- [x] Real-time WebSocket updates - 30 tests passing
- [x] Performance profiler - 10 tests passing
- [x] Cache manager - 10 tests passing
- [x] Resource monitor - Implementation complete

---

## Related Decisions

- [ADR-002: FastAPI for Microservices](002-fastapi-services.md)
- [ADR-003: OpenClaw Skills Architecture](003-openclaw-skills.md)
- [ADR-004: Chimera Quality Platform](004-quality-platform.md)

---

*Decision Record: ADR-005*
*Project Chimera v0.5.0*

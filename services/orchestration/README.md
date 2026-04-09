# Service Orchestration Patterns

**Project Chimera Phase 2 - Distributed Service Coordination**

This module provides enterprise-grade orchestration patterns for coordinating multiple Phase 2 services in live theatrical performances.

## Overview

The orchestration layer enables:

- **Coordinated scene changes** across lighting, audio, and BSL
- **Adaptive responses** based on audience sentiment
- **Resilient communication** with circuit breakers
- **Atomic operations** with two-phase commit
- **Graceful failure handling** with saga pattern

## Patterns

### 1. Circuit Breaker

Prevents cascading failures by tripping open when a service fails repeatedly.

```python
from services.orchestration.patterns import CircuitBreaker

# Create circuit breaker
cb = CircuitBreaker("dmx-controller", failure_threshold=5)

# Use before service call
if cb.is_closed():
    try:
        result = await call_dmx_service()
        cb.record_success()
    except Exception:
        cb.record_failure()
```

**States:**
- **Closed**: Normal operation, requests allowed
- **Open**: Service failing, requests blocked
- **Half-Open**: Testing if service recovered

**Configuration:**
- `failure_threshold`: Failures before opening (default: 5)
- `timeout_seconds`: Seconds before trying again (default: 60)
- `half_open_attempts`: Successes needed to close (default: 3)

### 2. Two-Phase Commit

Ensures atomic operations across multiple services.

```python
from services.orchestration.patterns import TwoPhaseCommit

# Define operations
prepare_ops = {
    "dmx": prepare_dmx_scene,
    "audio": prepare_audio_track,
    "bsl": prepare_bsl_translation
}

commit_ops = {
    "dmx": commit_dmx_scene,
    "audio": commit_audio_track,
    "bsl": commit_bsl_translation
}

rollback_ops = {
    "dmx": rollback_dmx_scene,
    "audio": rollback_audio_track,
    "bsl": rollback_bsl_translation
}

# Execute 2PC
tpc = TwoPhaseCommit(["dmx", "audio", "bsl"])

if await tpc.prepare(prepare_ops):
    result = await tpc.commit(commit_ops)
    if not result.success:
        await tpc.rollback(rollback_ops)
```

**Phases:**
1. **Prepare**: Ask all services if they can execute
2. **Commit**: Execute the operation on all services
3. **Rollback**: Undo if any service fails

### 3. Saga Pattern

Executes operations with compensating transactions.

```python
from services.orchestration.patterns import SagaOrchestrator

saga = SagaOrchestrator()

# Execute steps with compensation
success = await saga.execute_step(
    "activate_dmx_scene",
    operation=activate_scene,
    compensation=deactivate_scene
)

if success:
    await saga.execute_step(
        "play_audio_track",
        operation=play_track,
        compensation=stop_track
    )
```

**Benefits:**
- Long-running transactions
- Graceful degradation
- Partial completion support

### 4. Adaptive Orchestration

Coordinates services based on audience sentiment.

```python
from services.orchestration.patterns import AdaptiveOrchestrator, SentimentLevel

orchestrator = AdaptiveOrchestrator(
    dmx_client=dmx_client,
    audio_client=audio_client,
    bsl_client=bsl_client
)

# Execute adaptive response
result = await orchestrator.execute_adaptive_response(
    sentiment=SentimentLevel.POSITIVE,
    dialogue_text="Thank you for being here!"
)
```

**Sentiment Mappings:**

| Sentiment | Lighting Scene | Audio Track | Volume |
|-----------|---------------|-------------|--------|
| Very Negative | somber_scene | ambient_dark | -30dB |
| Negative | tense_scene | tension_builder | -20dB |
| Neutral | neutral_scene | neutral_ambiance | -15dB |
| Positive | bright_scene | uplifting_melody | -10dB |
| Very Positive | celebration_scene | celebration_fanfare | -8dB |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Adaptive Orchestrator                       │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │ Circuit Break │  │ Two-Phase     │  │ Saga         │ │
│  │   Pattern     │  │   Commit      │  │ Pattern      │ │
│  └───────┬───────┘  └───────┬───────┘  └──────┬───────┘ │
│          │                  │                  │          │
└──────────┼──────────────────┼──────────────────┼──────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ DMX Service │    │ Audio Service│    │ BSL Service │
    │   :8001     │    │   :8002      │    │   :8003     │
    └─────────────┘    └─────────────┘    └─────────────┘
```

## Usage Examples

### Basic Scene Activation

```python
from services.orchestration.patterns import TwoPhaseCommit

async def activate_coordinated_scene(scene_name: str):
    """Activate scene across all services."""

    async def prepare_dmx():
        return await dmx_client.check_available()

    async def prepare_audio():
        return await audio_client.check_available()

    async def commit_dmx():
        return await dmx_client.activate_scene(scene_name)

    async def commit_audio():
        return await audio_client.play_scene_music(scene_name)

    tpc = TwoPhaseCommit(["dmx", "audio"])

    if await tpc.prepare({"dmx": prepare_dmx, "audio": prepare_audio}):
        result = await tpc.commit({
            "dmx": commit_dmx,
            "audio": commit_audio
        })
        return result.success
```

### Adaptive Performance

```python
from services.orchestration.patterns import AdaptiveOrchestrator

async def adaptive_performance_loop():
    """Continuously adapt to audience sentiment."""

    orchestrator = AdaptiveOrchestrator(
        dmx_client=dmx_client,
        audio_client=audio_client,
        bsl_client=bsl_client
    )

    while True:
        # Get current sentiment
        sentiment = await sentiment_analyzer.analyze()

        # Get latest dialogue
        dialogue = await dialogue_generator.get_latest()

        # Execute adaptive response
        result = await orchestrator.execute_adaptive_response(
            sentiment=sentiment,
            dialogue_text=dialogue
        )

        if not result.success:
            logger.error(f"Adaptive response failed: {result.failed_services}")

        await asyncio.sleep(1)
```

### Emergency Procedures

```python
from services.orchestration.patterns import AdaptiveOrchestrator

async def emergency_shutdown():
    """Execute emergency stop across all services."""

    orchestrator = AdaptiveOrchestrator(
        dmx_client=dmx_client,
        audio_client=audio_client
    )

    result = await orchestrator.execute_emergency_stop()

    if result.success:
        print("Emergency stop successful")
    else:
        print(f"Emergency stop failures: {result.failed_services}")
```

## Best Practices

### 1. Always Use Circuit Breakers

```python
# GOOD
if circuit_breaker.is_closed():
    try:
        result = await service_call()
        circuit_breaker.record_success()
    except Exception:
        circuit_breaker.record_failure()

# BAD
result = await service_call()  # No protection
```

### 2. Handle Partial Failures

```python
result = await orchestrator.execute_adaptive_response(sentiment)

if not result.success:
    # Some services failed
    for service in result.failed_services:
        logger.error(f"Service {service} failed")

    # Continue with healthy services
    if result.services_involved:
        logger.info(f"Continuing with: {result.services_involved}")
```

### 3. Set Timeouts

```python
try:
    result = await asyncio.wait_for(
        orchestrator.execute_adaptive_response(sentiment),
        timeout=5.0
    )
except asyncio.TimeoutError:
    logger.error("Orchestration timed out")
```

### 4. Monitor Circuit Breaker State

```python
if not circuit_breaker.is_closed():
    logger.warning(f"Circuit breaker open for {circuit_breaker.service_name}")
    # Implement fallback logic
    await execute_fallback()
```

## Testing

### Unit Tests

```python
import pytest
from services.orchestration.patterns import CircuitBreaker

def test_circuit_breaker_trips():
    cb = CircuitBreaker("test", failure_threshold=3)

    # Record failures
    for _ in range(3):
        cb.record_failure()

    # Should be open
    assert not cb.is_closed()

def test_circuit_breaker_resets():
    cb = CircuitBreaker("test", failure_threshold=3)

    # Trip the breaker
    for _ in range(3):
        cb.record_failure()

    # Should be open
    assert not cb.is_closed()

    # Record success after timeout
    cb.record_success()

    # Should be closed again
    assert cb.is_closed()
```

### Integration Tests

```python
import pytest
from services.orchestration.patterns import AdaptiveOrchestrator

@pytest.mark.asyncio
async def test_adaptive_response():
    orchestrator = AdaptiveOrchestrator(
        dmx_client=MockDMXClient(),
        audio_client=MockAudioClient(),
        bsl_client=MockBSLClient()
    )

    result = await orchestrator.execute_adaptive_response(
        sentiment=SentimentLevel.POSITIVE,
        dialogue_text="Hello world"
    )

    assert result.success
    assert len(result.services_involved) == 3
    assert result.duration_ms < 1000
```

## Performance Considerations

### Latency Budget

- **Circuit breaker check**: <1ms
- **Two-phase commit**: <500ms
- **Adaptive response**: <1s
- **Emergency stop**: <100ms

### Optimization Strategies

1. **Parallel Execution**: Use `asyncio.gather()` for independent operations
2. **Caching**: Cache sentiment analysis results
3. **Batch Operations**: Combine multiple service calls
4. **Connection Pooling**: Reuse HTTP connections

## Troubleshooting

### Circuit Breaker Won't Close

```python
# Check state
print(f"State: {cb._state}")
print(f"Failures: {cb._failure_count}")

# Manually reset if needed
cb._state = "closed"
cb._failure_count = 0
```

### Two-Phase Commit Hangs

```python
# Add timeouts
result = await asyncio.wait_for(
    tpc.commit(commit_ops),
    timeout=10.0
)
```

### Adaptive Response Slow

```python
# Check which service is slow
result = await orchestrator.execute_adaptive_response(sentiment)
print(f"Duration: {result.duration_ms}ms")

# Verify circuit breakers aren't blocking
for name, cb in orchestrator.circuit_breakers.items():
    print(f"{name}: {cb._state}")
```

## Migration Guide

### From Manual Coordination

**Before:**
```python
# Manual coordination
await dmx.activate_scene(scene)
await audio.play_track(track)
await bsl.translate(text)
```

**After:**
```python
# Orchestrated coordination
result = await orchestrator.execute_adaptive_response(
    sentiment=sentiment,
    dialogue_text=text
)
```

## References

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Two-Phase Commit](https://en.wikipedia.org/wiki/Two-phase_commit_protocol)
- [Saga Pattern](https://microservices.io/patterns/data/saga/)
- [Adaptive Systems](https://en.wikipedia.org/wiki/Adaptive_system)

## License

MIT License - See Project Chimera LICENSE file for details.

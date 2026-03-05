# ADR-008: OpenTelemetry Integration Standard

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Need to document distributed tracing implementation decisions

## Context

Project Chimera requires distributed tracing for root cause analysis and performance optimization. The Production Observability Enhancement implemented OpenTelemetry across all services.

## Decision

Adopt OpenTelemetry as the standard for distributed tracing:

### Instrumentation Standard

**Per-Service Span Attributes:**

**SceneSpeak Agent:**
- `show.id` - Show identifier
- `scene.number` - Scene number
- `adapter.name` - Adapter used
- `tokens.input` - Input token count
- `tokens.output` - Output token count
- `dialogue.lines_count` - Lines generated

**Captioning Agent:**
- `caption_latency_ms` - Caption processing latency

**BSL Agent:**
- `translation.request_id` - Translation request ID
- `sign_language` - Sign language variant

**Sentiment Agent:**
- `sentiment.score` - Sentiment value
- `audience.size` - Audience count

**Safety Filter:**
- `safety.action` - Action taken (allow/block/flag)
- `pattern.matched` - Pattern that matched
- `content.length` - Content length

### Sampling Strategy

- **10% sampling** for production traces
- Configurable per-service sampling
- Head sampling for critical operations

### Backend

- **Jaeger** for trace storage and visualization
- **Port:** 16686 (default Jaeger UI)
- **Service Discovery:** Kubernetes service DNS

## Components

```
platform/monitoring/telemetry/
└── __init__.py                # setup_telemetry() function

services/*/tracing.py           # Per-service tracing modules
├── SceneSpeak Agent/tracing.py
├── Captioning Agent/tracing.py
├── BSL Agent/tracing.py
├── Sentiment Agent/tracing.py
└── safety-filter/tracing.py

scripts/
├── analyze-trace.py            # Trace analysis CLI
└── dependency-graph.py         # Service dependency mapper

docs/runbooks/
├── distributed-tracing.md      # Tracing guide
└── performance-analysis.md     # Performance investigation
```

## Consequences

### Positive
- Consistent tracing across all services
- Rich business context in spans
- Standard instrumentation patterns
- Powerful trace analysis tools

### Negative
- Additional instrumentation overhead
- Jaeger infrastructure maintenance
- Need trace retention policies

### Mitigations
- 10% sampling minimizes overhead
- Asynchronous span export
- Automated trace cleanup policies

## Alternatives Considered

1. **Zipkin** - Rejected due to less active development
2. **Jaeger-only without OpenTelemetry** - Rejected for lack of standardization
3. **No tracing** - Rejected due to production requirements

## References

- [Distributed Tracing Runbook](../runbooks/distributed-tracing.md)
- [Trace Analyzer Documentation](../platform/monitoring/trace-analyzer/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/reference/specification/)

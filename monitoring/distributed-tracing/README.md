# Project Chimera - Distributed Tracing

**Phase 2 Observability**

This directory contains distributed tracing infrastructure for Project Chimera Phase 2 services using OpenTelemetry and Jaeger.

## Overview

Distributed tracing provides end-to-end visibility into requests as they flow through the system:

- Track requests from ingress to egress
- Identify performance bottlenecks
- Debug service-to-service communication issues
- Understand latency across service boundaries

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  DMX Controller │────▶│  Audio Controller│────▶│  BSL Avatar     │
│   (port 8001)   │     │   (port 8002)   │     │   (port 8003)   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Jaeger Agent   │
                        │  (port 6831)    │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Jaeger UI      │
                        │  (port 16686)   │
                        └─────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r monitoring/distributed-tracing/requirements.txt
```

### 2. Start Jaeger

```bash
./monitoring/distributed-tracing/setup-tracing.sh --action start
```

Or using Docker Compose directly:

```bash
docker-compose -f monitoring/distributed-tracing/docker-compose.tracing.yml up -d
```

### 3. Verify Jaeger is Running

```bash
curl http://localhost:16686/api/health
```

### 4. Access Jaeger UI

Open browser: http://localhost:16686

## Usage

### Python Code Integration

```python
from monitoring.distributed_tracing.tracer import ChimeraTracer, get_dmx_tracer

# Get service-specific tracer
tracer = get_dmx_tracer()

# Use as decorator
@tracer.trace_request("activate_scene")
def activate_scene(scene_name: str):
    # Your code here
    pass

# Use as context manager
with tracer.trace_operation("calculate_scene"):
    # Your code here
    pass
```

### Service Integration

Add to your service initialization:

```python
from monitoring.distributed_tracing.tracer import get_dmx_tracer

class DMXController:
    def __init__(self):
        self.tracer = get_dmx_tracer()

    def activate_scene(self, scene_name: str):
        with self.tracer.trace_operation("activate_scene"):
            # Scene activation logic
            pass
```

## Tracing Concepts

### Spans

A span represents a unit of work in the system:

- **Root Span**: The initial entry point (e.g., HTTP request)
- **Child Spans**: Operations within the request
- **Span Attributes**: Key-value metadata
- **Span Events**: Timestamped events within a span

### Trace Context

Trace context propagates across service boundaries:

- **Trace ID**: Unique identifier for the entire request
- **Span ID**: Unique identifier for the current span
- **Parent Span ID**: Links child spans to parent

## Configuration

Environment variables:

```bash
# Jaeger configuration
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831

# Sampling rate (0.0 to 1.0)
TRACE_SAMPLE_RATE=1.0
```

## Viewing Traces

### Jaeger UI

1. Navigate to http://localhost:16686
2. Select service from dropdown (e.g., "dmx-controller")
3. Click "Find Traces"
4. Click on a trace to see details

### Trace Search Filters

- Service Name
- Operation Name
- Tags/Attributes
- Time Range
- Minimum Duration

## Troubleshooting

### Jaeger Not Starting

```bash
# Check if port is already in use
sudo lsof -i :16686

# Check Docker logs
docker logs chimera-jaeger
```

### No Traces Appearing

```bash
# Verify service is sending traces
curl http://localhost:8001/health

# Check Jaeger agent is receiving
docker logs chimera-jaeger | grep "Reporting"

# Verify network connectivity
docker network inspect chimera-network
```

### High CPU Usage

Reduce sampling rate:

```bash
export TRACE_SAMPLE_RATE=0.1
```

## Performance Impact

Distributed tracing has minimal overhead:

- **Span creation**: ~1-2 microseconds
- **Context propagation**: ~5-10 microseconds per hop
- **Export**: Asynchronous, non-blocking

For production, adjust sampling rate based on traffic volume.

## Advanced Usage

### Custom Attributes

```python
tracer.add_span_attributes({
    "scene_name": scene_name,
    "fixture_count": len(fixtures),
    "transition_time_ms": 5000
})
```

### Span Events

```python
tracer.add_span_event("scene_activated", {
    "scene": scene_name,
    "timestamp": time.time()
})
```

### Baggage Propagation

```python
# Add baggage (propagates across all child spans)
tracer.add_span_attributes({"user_id": "12345"})
```

## Exporting Trace Data

### Export to JSON

```bash
curl http://localhost:16686/api/traces?service=dmx-controller > traces.json
```

### Export Trace Metrics

```bash
curl http://localhost:16686/api/metrics
```

## Security Considerations

- Jaeger UI should not be exposed publicly
- Use authentication in production environments
- Sanitize sensitive data from span attributes
- Use HTTPS for remote collectors

## Maintenance

### Backup Trace Data

Jaeger uses in-memory storage by default. For persistence:

```yaml
# docker-compose.tracing.yml
environment:
  - SPAN_STORAGE_TYPE=elasticsearch
  - ES_SERVER_URLS=http://elasticsearch:9200
```

### Cleanup Old Traces

Configure TTL in Jaeger:

```yaml
environment:
  - ES_TTL_SPAN=72h
```

## References

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/reference/specification/)

## License

MIT License - See Project Chimera LICENSE file for details.

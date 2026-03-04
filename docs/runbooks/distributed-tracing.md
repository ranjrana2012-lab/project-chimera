# Distributed Tracing Runbook

## Overview

Project Chimera uses OpenTelemetry and Jaeger for distributed tracing across all services.

## Access Jaeger

**URL:** http://jaeger.shared.svc.cluster.local:16686

**Port Forward:**
```bash
kubectl port-forward -n shared svc/jaeger 16686:16686
```

## Searching Traces

### By Service

1. Select service from dropdown
2. Set time range (last hour, today, etc.)
3. Click "Find Traces"

### By Trace ID

If you have a trace ID from logs:
1. Enter Trace ID in search box
2. Click "Find Traces"

### By Operation

1. Select service
2. Enter operation name (e.g., "generate_dialogue")
3. Add tags/filters as needed

## Analyzing Traces

### Reading a Trace

**Timeline View:**
- Each bar = one span
- Width = duration
- Color = status (red = error, yellow = warning)

**Span Details:**
- Click span to view details
- Check logs for errors
- View tags for context

### Common Issues

**High Latency:**
- Look for wide spans
- Check database/external calls
- Review trace timeline

**Missing Spans:**
- Service not instrumented
- Sampling dropped trace
- Network issue

**Error Spans:**
- Red color indicates error
- Click span for error details
- Check logs for stack trace

## Trace Analysis Tools

### Analyze Trace Script

```bash
./scripts/analyze-trace.py <trace-id>
```

Output:
- Trace quality score
- Slow spans identified
- Missing spans listed
- Recommendations provided

### Dependency Graph

```bash
./scripts/dependency-graph.py
```

Generates service dependency visualization.

# Performance Analysis Runbook

## Tools

- **Jaeger:** Distributed tracing
- **Grafana:** Metrics dashboards
- **Prometheus:** Raw metrics queries

## Performance Investigation

### 1. Identify Slow Request

**In Jaeger:**
1. Search for operation (e.g., "generate_dialogue")
2. Sort by duration (descending)
3. Click slowest trace

**In Prometheus:**
```promql
topk(10, histogram_quantile(0.95,
  sum(rate(request_duration_seconds_bucket[5m])) by (le, service)
))
```

### 2. Analyze Trace

- Find widest span
- Check external calls
- Look for N+1 queries
- Review cache usage

### 3. Check Resources

```bash
# Service resource usage
kubectl top pods -n live -l app=<service>

# Pod details
kubectl describe pod -n live <pod-name>
```

### 4. Common Patterns

**Slow Database:**
- Add connection pooling
- Implement caching
- Optimize queries

**Slow LLM:**
- Increase cache hit rate
- Use smaller models
- Batch requests

**Network Latency:**
- Check service placement
- Review network policies
- Consider service mesh

## Optimization

### Before Optimization

1. Establish baseline
2. Set target (e.g., reduce P95 by 50%)
3. Document current state

### After Optimization

1. Verify improvement
2. Check for regressions
3. Update documentation

## Alerting on Performance

**Latency Alerts:**
- P95 > 2 seconds (warning)
- P95 > 5 seconds (critical)
- P99 > 10 seconds (critical)

**Throughput Alerts:**
- Request rate drops 50% (warning)
- Queue depth > 100 (warning)
- Queue depth > 500 (critical)

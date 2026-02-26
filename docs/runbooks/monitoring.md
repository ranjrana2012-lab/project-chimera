# Monitoring Runbook

This runbook covers monitoring and alerting for Project Chimera.

## Key Metrics

### Service Health

| Metric | Description | Threshold |
|--------|-------------|----------|
| SceneSpeak latency | Dialogue generation p95 | < 2000ms |
| Safety block rate | Blocked content ratio | < 10% |
| GPU utilization | GPU usage percentage | < 90% |
| Cache hit rate | Skill cache effectiveness | > 50% |

### Viewing Metrics

**Grafana Dashboards:**
```
http://grafana.shared.svc.cluster.local:3000
```

**Prometheus Queries:**
```bash
# Access Prometheus
kubectl port-forward -n shared svc/prometheus 9090:9090

# Query in browser or CLI
curl 'http://localhost:9090/api/v1/query?query=up{job="scenespeak-agent"}'
```

## Health Checks

### Check All Services

```bash
#!/bin/bash
for service in openclaw-orchestrator scenespeak-agent captioning-agent \
              bsl-text2gloss-agent sentiment-agent lighting-control \
              safety-filter operator-console; do
    echo "Checking $service..."
    kubectl exec -n live $service-0 -- curl -s http://localhost:8000/health/live
done
```

### Check GPU Status

```bash
for pod in scenespeak-agent openclaw-orchestrator; do
    echo "GPU status for $pod:"
    kubectl exec -n live $pod-0 -- nvidia-smi
    echo ""
done
```

## Alert Investigation

### High Latency Alert

1. **Identify the service:** Check alert labels
2. **Check correlation:** Are other services also slow?
3. **Check dependencies:** Is Redis/Kafka responding?
4. **Check GPU:** Is GPU memory full?
5. **Check cache:** Is cache working?

### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n live --containers=true | sort -k6

# Check for memory leaks
kubectl logs -n live <pod> --previous | grep -i memory
```

### High Safety Block Rate

This may indicate:
1. Legitimate increase in problematic content
2. Overly aggressive filtering rules
3. Model generating borderline content

Investigation steps:
1. Review blocked content samples
2. Check filter thresholds
3. Update policies if needed

## Distributed Tracing

**Jaeger UI:**
```
http://jaeger.shared.svc.cluster.local:16686
```

### Tracing a Request

1. Get trace ID from service response headers
2. Search in Jaeger UI
3. Analyze span timeline
4. Identify bottlenecks

## Performance Tuning

### Adjust Cache TTL

Based on cache hit rate, adjust TTL values:
- Low hit rate (< 30%): Increase TTL
- High hit rate (> 70%): TTL may be too long

### Scale Services

```bash
# Scale up a service
kubectl scale deployment/scenespeak-agent --replicas=2 -n live

# Scale with HPA (if configured)
kubectl autoscale deployment/scenespeak-agent \
  --min=1 --max=3 --cpu-percent=70 -n live
```

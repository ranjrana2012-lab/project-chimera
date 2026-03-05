# Incident Response Runbook

This runbook covers incident response procedures for Project Chimera.

## Incident Severity Levels

| Level | Name | Response Time | Example |
|-------|------|---------------|---------|
| 1 | Critical | 15 minutes | Complete system outage |
| 2 | High | 1 hour | Major service degradation |
| 3 | Medium | 4 hours | Partial service impact |
| 4 | Low | 1 day | Minor issue |

## Common Incidents

### SceneSpeak High Latency

**Symptoms:**
- Dialogue generation taking > 3 seconds
- p95 latency > 2000ms

**Investigation:**
```bash
# Check latency metrics
curl http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(scenespeak_generation_duration_seconds_bucket[5m]))

# Check GPU usage
kubectl exec -n live SceneSpeak Agent-0 -- nvidia-smi

# Check model loading
kubectl logs -n live SceneSpeak Agent-0 --tail=100
```

**Resolution:**
1. Restart affected pod if memory leak suspected
2. Scale up replicas if under load
3. Check if fallback model is being used

### Safety Filter Blocking Everything

**Symptoms:**
- All content being blocked
- Review queue full

**Investigation:**
```bash
# Check safety filter status
kubectl exec -n live safety-filter-0 -- curl http://localhost:8006/health/live

# Review recent blocks
kubectl exec -n live safety-filter-0 -- curl http://localhost:8006/api/v1/review-queue
```

**Resolution:**
1. Check policy configuration
2. Review blocked patterns
3. Temporarily disable strict mode if needed

### OpenClaw Orchestrator Down

**Symptoms:**
- Skill invocations failing
- 503 errors from /api/v1/orchestration/invoke

**Investigation:**
```bash
# Check orchestrator health
kubectl get pods -n live -l app=openclaw-orchestrator

# Check logs
kubectl logs -n live openclaw-orchestrator-0 --tail=100
```

**Resolution:**
1. Restart orchestrator pod
2. Check skill registry
3. Verify shared services (Redis, Kafka)

## Emergency Procedures

### Complete System Shutdown

```bash
# Scale down all deployments
kubectl scale deployment --all=0 -n live

# Stop shared services last
kubectl scale deployment --all=0 -n shared
```

### Emergency Blackout

```bash
# Invoke blackout via lighting control
kubectl exec -n live lighting-control-0 -- curl -X POST \
  http://localhost:8005/api/v1/lighting/blackout
```

## Post-Incident Actions

1. Document the incident
2. Create post-mortem report
3. Update runbooks if needed
4. Implement prevention measures

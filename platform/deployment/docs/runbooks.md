# Operations Runbooks

**Version:** 1.0.0
**Date:** 2026-03-04

---

## Incident Response Runbooks

### Service Down

**Symptoms:**
- Health checks failing
- Service unreachable
- Alerts firing for ServiceDown

**Diagnosis:**
1. Check pod status: `kubectl get pods -n chimera-live`
2. Check pod logs: `kubectl logs <pod-name> -n chimera-live`
3. Check events: `kubectl get events -n chimera-live --sort-by=.lastTimestamp`

**Resolution:**
1. If pod is CrashLoopBackOff:
   - Check logs for errors
   - Verify configuration
   - Restart deployment: `kubectl rollout restart deployment/<service> -n chimera-live`
2. If pod is Pending:
   - Check resource requests
   - Check node availability
   - Check for taints/tolerations

### High Latency

**Symptoms:**
- P95 latency > 2s
- Slow response times
- User complaints

**Diagnosis:**
1. Check metrics in Grafana
2. Check GPU utilization
3. Check database queries (if applicable)

**Resolution:**
1. Scale up deployment: `kubectl scale deployment/<service> --replicas=2 -n chimera-live`
2. Check for resource bottlenecks
3. Review recent code changes

### High Memory Usage

**Symptoms:**
- Memory usage > 90%
- OOMKilled events
- Pods restarting

**Diagnosis:**
1. Check memory usage: `kubectl top pods -n chimera-live`
2. Check memory limits: `kubectl describe pod <pod-name> -n chimera-live`

**Resolution:**
1. Increase memory limits in Helm values
2. Investigate memory leaks
3. Restart affected pods

### Quality Gate Failure

**Symptoms:**
- Quality gate failed alert
- PR blocked from merging
- Coverage drop detected

**Diagnosis:**
1. Check quality gate report
2. Review failed tests
3. Check coverage report

**Resolution:**
1. Fix failing tests
2. Improve coverage
3. Re-run quality gate

---

## Deployment Runbooks

### Deploy to Pre-Production

1. Update version in values.yaml
2. Run: `./platform/cicd/pipelines/scripts/deploy.sh preprod <version>`
3. Monitor smoke tests
4. Verify deployment

### Deploy to Production

1. Ensure preprod tests pass
2. Get technical lead approval
3. Run: `./platform/cicd/pipelines/scripts/deploy.sh production <version>`
4. Monitor smoke tests
5. Verify health checks

### Rollback

1. Identify issue
2. Run: `./platform/cicd/pipelines/scripts/rollback.sh production`
3. Verify rollback completed
4. Create incident ticket

---

**Status:** ✅ Runbooks Defined

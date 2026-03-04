# SLO Breach Response

## Overview

This runbook provides procedures for responding to Service Level Objective (SLO) breaches and elevated burn rates in Project Chimera services.

## Quick Reference

| Condition | Action | Escalation |
|-----------|--------|------------|
| Burn Rate 2x | Monitor and assess | Tech Lead @ 5x |
| Burn Rate 10x | Block deployments | Page on-call |
| SLO < 100% | Investigate immediately | Tech Lead |
| Budget < 10% | Emergency mode | Emergency review |
| Budget < 5% | Critical incident | Director |

---

## Burn Rate Warning (2x)

**Symptom:** Error budget burning 2x faster than normal rate

**What this means:** At current pace, you will breach your SLO in half the expected time. This warrants investigation but is not yet critical.

### Assessment

```bash
# Calculate current error budget status
./scripts/calculate-error-budget.py

# Check burn rate trend
kubectl prometheus-query 'slo:error_burn_rate' --last 1h

# Review recent alerts
kubectl logs -n shared deployment/alertmanager --tail=50
```

### Actions

1. **Identify affected service**
   ```bash
   # List services with elevated burn rate
   kubectl prometheus-query 'slo:error_burn_rate > 2'
   ```

2. **Check recent changes**
   ```bash
   # Review recent deployments
   kubectl rollout history deployment/<service> -n live

   # Check recent configuration changes
   git log --since="2 hours ago" -- infrastructure/kubernetes/
   ```

3. **Review error patterns**
   ```bash
   # Check recent errors
   kubectl logs -n live deployment/<service> --since=2h | grep ERROR

   # View error rate in Prometheus
   # Query: rate(http_requests_total{status=~"5.."}[5m])
   ```

4. **Consider deployment freeze**
   - Pause non-emergency deployments to affected service
   - Communicate status to team

5. **Document findings**
   - Create incident ticket if impact is significant
   - Note burn rate and error budget status

### Escalation

- **Technical Lead** if burn rate exceeds 5x
- **Director** if budget drops below 25%

---

## Burn Rate Critical (10x)

**Symptom:** Error budget burning 10x faster than normal rate

**What this means:** Critical condition. At this pace, you will breach your SLO very quickly. Immediate action required.

### Immediate Actions

1. **Block all deployments** to affected service
   ```bash
   # Set deployment freeze annotation
   kubectl annotate deployment/<service> -n live \
     deployment.freeze="Burn rate 10x - $(date)" \
     --overwrite
   ```

2. **Page on-call engineer** if not already engaged
   - Use PagerDuty or on-call rotation
   - Mark as high severity incident

3. **Enable enhanced monitoring**
   - Increase scrape interval for affected service
   - Enable debug logging if needed
   - Set up additional alerts

4. **Begin incident response**
   - Create incident ticket
   - Join incident bridge call
   - Assign incident commander

### Investigation

```bash
# Check recent deployments
kubectl rollout history deployment/<service> -n live

# Identify last known good state
kubectl rollout history deployment/<service> -n live | tail -5

# Check error patterns
kubectl logs -n live deployment/<service> --tail=1000 | grep ERROR

# Check resource usage
kubectl top pods -n live -l app=<service>

# Check for external dependencies
kubectl prometheus-query 'up{job=~".*external.*"}'
```

### Resolution Steps

1. **Identify root cause**
   - Use distributed tracing (Jaeger)
   - Review application logs
   - Check dependencies

2. **Implement fix**
   - Rollback if recent change is cause
   - Apply hotfix for critical bug
   - Scale resources if capacity issue

3. **Verify SLO recovery**
   ```bash
   # Monitor burn rate
   watch -n 30 './scripts/calculate-error-budget.py'

   # Check service health
   kubectl prometheus-query 'slo:*_success_rate:30d'
   ```

4. **Conduct post-mortem**
   - Document root cause
   - Identify prevention measures
   - Update runbooks if needed

---

## SLO Not Met

**Symptom:** Service SLO below target for 5+ minutes

**What this means:** The service is currently not meeting its SLO target. The SLO may have already been breached, or will be soon.

### Verification

```bash
# Confirm SLO status
./scripts/calculate-error-budget.py

# Check SLO compliance
kubectl prometheus-query 'slo:*_success_rate:30d < <slo-target>'

# Check error budget remaining
kubectl prometheus-query 'slo:error_budget_remaining:30d'
```

### Actions

1. **Verify SLO breach** with error budget script
2. **Check error budget status** - is it exhausted?
3. **Block deployments** if budget < 10%
4. **Escalate to Technical Lead** immediately

### Do NOT

- Deploy new features
- Make configuration changes
- Scale down the service
- Ignore the alert

---

## Error Budget Exhausted (<10% remaining)

**Symptom:** Error budget nearly depleted, less than 10% remaining

**What this means:** The service is in critical condition. Any additional errors will cause an SLO breach.

### Immediate Actions

1. **EMERGENCY MODE** - Block all changes
   ```bash
   # Emergency freeze annotation
   kubectl annotate deployment/<service> -n live \
     emergency.mode="Error budget <10% - $(date)" \
     deployment.freeze=true \
     --overwrite
   ```

2. **Emergency review meeting**
   -召集 reliability team
   - Involve service owner
   - Include engineering management

3. **Prioritize stability over features**
   - Cancel non-essential work
   - Focus on reliability improvements
   - Reduce change velocity

4. **Consider rollback** if recent change
   ```bash
   # Rollback to previous version
   kubectl rollout undo deployment/<service> -n live
   ```

### Recovery Process

1. **Fix underlying issues**
   - Address root cause
   - Apply patches
   - Improve monitoring

2. **Monitor burn rate**
   ```bash
   # Continuous monitoring
   watch -n 60 './scripts/calculate-error-budget.py'

   # Wait for positive trend
   kubectl prometheus-query 'slo:error_burn_rate < 1'
   ```

3. **Wait for budget recovery**
   - 30-day rolling window will reset
   - May take weeks to fully recover
   - Maintain conservative approach

4. **Document lessons learned**
   - What caused the breach?
   - How was it detected?
   - What can be improved?

---

## SLO Breach Post-Mortem

After any SLO breach or critical burn rate event:

### Document

1. **Timeline of events**
2. **Root cause analysis**
3. **Impact assessment**
4. **Resolution steps taken**
5. **Prevention measures**

### Template

```markdown
# SLO Breach Post-Mortem: [Service] - [Date]

## Summary
[Brief description of the breach]

## Impact
- Duration: [X hours/minutes]
- Affected users: [X users or percentage]
- SLO target: [X%]
- Actual performance: [Y%]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | ... |

## Root Cause
[What caused the breach]

## Resolution
[How it was fixed]

## Prevention
[How to prevent recurrence]

## Action Items
- [ ] Task 1
- [ ] Task 2
```

---

## Communication

### Internal

- **Slack**: #incidents channel for real-time updates
- **Email**: Post-mortem summary to engineering team
- **Wiki**: Document learnings and improvements

### External (if applicable)

- **Status page**: Update service status
- **Customer notifications**: If SLA breach
- **Stakeholder updates**: Management and product teams

---

## Related Documentation

- [SLO Handbook](slo-handbook.md) - SLO definitions and policies
- [Incident Response](incident-response.md) - General incident procedures
- [Alerts Runbook](alerts.md) - Alert configuration and management
- [On-Call Handbook](on-call.md) - On-call procedures and responsibilities

## Tools

```bash
# Calculate error budget
./scripts/calculate-error-budget.py

# Generate SLO compliance report
./scripts/slo-compliance-report.sh

# View SLO dashboard
# Grafana: http://grafana.shared.svc.cluster.local:3000/d/slo-overview

# Check burn rate alerts
# Prometheus: http://prometheus.shared.svc.cluster.local:9090/alerts
```

---

*Last Updated: 2026-03-04*
*Version: 1.0*

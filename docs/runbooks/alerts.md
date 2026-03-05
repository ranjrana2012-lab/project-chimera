# Project Chimera - Alert Response Procedures

This document outlines standard procedures for responding to alerts from the Project Chimera monitoring system.

## Alert Severity Levels

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| Critical | Service affecting production | Immediate | On-call engineer |
| Warning | Potential issue detected | Within 1 hour | Team lead |
| Info | Informational | No action required | N/A |

## Critical Alerts

### SceneSpeakHighErrorRate

**Condition**: Error rate > 5% for 5 minutes

**Impact**: Users cannot generate dialogue

**Response Steps**:
1. Check Grafana dashboard: Project Chimera - SceneSpeak
2. Verify service is running: `kubectl get pods -n live -l app=scenespeak-agent`
3. Check recent logs: `kubectl logs -n live deployment/scenespeak-agent --tail=100`
4. Verify GPU availability
5. If GPU unavailable, restart the pod
6. If error persists, check Redis connectivity
7. Escalate if not resolved in 15 minutes

### SceneSpeakHighLatency

**Condition**: P95 latency > 2 seconds for 10 minutes

**Impact**: Degraded user experience

**Response Steps**:
1. Check current latency in Grafana
2. Verify GPU memory usage: `kubectl exec -n live deployment/scenespeak-agent -- nvidia-smi`
3. Check cache hit rate (should be > 70%)
4. Consider scaling if under high load
5. Restart pod if memory is fragmented
6. Document findings

### LiveServiceDown

**Condition**: Service in live namespace not responding

**Impact**: Loss of critical functionality

**Response Steps**:
1. Identify which service is down
2. Check pod status: `kubectl get pods -n live`
3. Check pod logs for errors
4. Describe pod for events: `kubectl describe pod -n live <pod-name>`
5. Restart if needed: `kubectl rollout restart deployment/<service> -n live`
6. Monitor recovery
7. Escalate immediately if multiple services down

### LightingControlUnresponsive

**Condition**: Lighting control service down for 2+ minutes

**Impact**: Cannot control lighting during performance

**Response Steps**:
1. **URGENT**: This affects live performances
2. Check service status: `kubectl get pods -n live -l app=lighting-control`
3. Verify DMX connection
4. Restart service: `kubectl rollout restart deployment/lighting-control -n live`
5. Manual override may be needed if automation fails
6. Alert venue technical staff

### OpenClawGPUNotAvailable

**Condition**: No GPU resources available for 1 minute

**Impact**: All ML model inference fails

**Response Steps**:
1. Check node status: `kubectl get nodes`
2. Verify GPU resources: `kubectl describe nodes | grep nvidia.com/gpu`
3. Check for GPU-hogging pods
4. Restart OpenClaw orchestrator
5. If hardware issue, alert infrastructure team
6. Consider fallback to CPU (degraded performance)

## Warning Alerts

### SceneSpeakCacheHitRateLow

**Condition**: Cache hit rate < 70% for 15 minutes

**Impact**: Increased latency and cost

**Response Steps**:
1. Check cache configuration
2. Verify Redis is healthy
3. Review cache eviction policy
4. Consider increasing cache size
5. Monitor for 1 hour after action

### HighCPUUsage / HighMemoryUsage

**Condition**: Resource usage > 80% for 10 minutes

**Impact**: Potential performance degradation

**Response Steps**:
1. Identify consuming pods: `kubectl top pods -n <namespace>`
2. Check if scaling is needed
3. Review resource limits
4. Look for memory leaks in application logs
5. Plan capacity increase if sustained

### SentimentAnalysisBacklog

**Condition**: Queue size > 100 for 5 minutes

**Impact**: Delayed sentiment updates

**Response Steps**:
1. Check processing rate vs arrival rate
2. Verify workers are healthy
3. Scale horizontally: `kubectl scale deployment sentiment-agent -n live --replicas=2`
4. Monitor queue drain
5. Adjust worker pool size if needed

### RedisHighMemoryUsage

**Condition**: Memory usage > 90%

**Impact**: Potential Redis eviction/crash

**Response Steps**:
1. Review cache keys: `kubectl exec -n shared deployment/redis -- redis-cli KEYS '*' | wc -l`
2. Check largest keys
3. Adjust TTL settings
4. Scale Redis if needed
5. Monitor for OOM

### KafkaConsumerLag

**Condition**: Consumer lag > 1000 messages

**Impact**: Delayed event processing

**Response Steps**:
1. Identify affected consumer group
2. Check consumer health
3. Verify consumers are running
4. Scale consumer pods
5. Review processing logic

## Alert Triage Process

### First Responder Actions

1. **Acknowledge the alert** - Prevent duplicates
2. **Assess severity** - Confirm impact on production
3. **Check dashboards** - Get visual overview
4. **Review recent changes** - Deployments, config changes
5. **Document actions** - Log all steps taken

### Investigation Steps

1. **Identify scope** - Single service or platform-wide?
2. **Check dependencies** - Are upstream/downstream services affected?
3. **Review metrics** - Look for correlated changes
4. **Examine logs** - Search for errors around alert time
5. **Test reproducibility** - Can the issue be reproduced?

### Resolution Steps

1. **Implement fix** - Apply appropriate remedy
2. **Monitor recovery** - Verify metrics return to baseline
3. **Document resolution** - Record what was done
4. **Prevent recurrence** - Update runbooks/config
5. **Post-mortem** - For critical incidents

## Escalation Procedures

### Level 1: On-Call Engineer

- Handles all critical and warning alerts
- First point of contact
- Expected to resolve most issues

### Level 2: Team Lead

- Escalated after 15 minutes without resolution
- Consulted for complex issues
- Makes decision to wake senior staff

### Level 3: Senior Staff/Architect

- Escalated for critical platform issues
- Consulted for architectural problems
- Available for major incidents

### Level 4: Management

- Escalated for service outages > 30 minutes
- Business impact decisions
- Customer communication

## Communication Guidelines

### During Active Incident

1. Update incident channel with status
2. Provide ETA for resolution when known
3. Communicate blockers clearly
4. Request help early, not late

### Post-Incident

1. Draft post-mortem within 24 hours
2. Include timeline, root cause, and fixes
3. Share with team
4. Update runbooks

## Alert Maintenance

### Weekly

- Review alert firing patterns
- Tune thresholds if needed
- Update runbooks with learnings
- Check for stale alerts

### Monthly

- Audit all alerts for relevance
- Remove or adjust ignored alerts
- Add alerts for new services
- Review escalation paths

### Quarterly

- Full alert architecture review
- Consider new monitoring tools
- Update contact information
- Training on new alert types

## On-Call Procedures

### Before Shift

- Review recent incidents
- Check runbook access
- Verify alert delivery (Slack/email/PagerDuty)
- Know escalation contacts

### During Shift

- Respond to critical alerts immediately
- Document all actions
- Ask for help when unsure
- Maintain handoff notes

### After Shift

- Complete shift report
- Hand off open issues
- Update runbooks
- Share learnings

## Testing Alert Rules

### Procedure

1. Put alert rules in test mode
2. Simulate condition (e.g., scale down service)
3. Verify alert fires
4. Check notification delivery
5. Restore service
6. Document results

### Schedule

- Test critical alerts monthly
- Test warning alerts quarterly
- After any alert rule changes
- After monitoring system upgrades

## AlertManager Procedures

### AlertManager Overview

AlertManager is responsible for deduplicating, grouping, and routing alerts to the appropriate receivers (Slack channels, email, etc.). It handles alert silencing, inhibition, and notification management.

**Access AlertManager:**
- Web UI: `http://alertmanager.shared.svc.cluster.local:9093` (from cluster)
- Web UI: `http://localhost:9093` (after port-forward)
- API: `http://alertmanager.shared.svc.cluster.local:9093/api/v2`

### AlertManager Alert Workflow

1. **Prometheus fires alert** → AlertManager receives it
2. **Grouping** → Similar alerts grouped together
3. **Inhibition** → Dependent alerts suppressed
4. **Silencing** → Matched alerts silenced
5. **Routing** → Sent to appropriate receiver
6. **Notification** → Delivered via Slack/email/PagerDuty

### Managing Alert Silences

Silences temporarily mute alerts matching specific criteria. Use silences during:
- Planned maintenance windows
- Known issues being worked on
- Deployment activities
- Testing/debugging

#### Creating Silences via Web UI

1. Access AlertManager UI: `kubectl port-forward -n shared svc/alertmanager 9093:9093`
2. Navigate to http://localhost:9093
3. Click "Silence" → "New Silence"
4. Configure matcher(s):
   - **alertname**: Name of the alert to silence
   - **service**: Specific service
   - **severity**: Alert severity level
5. Set duration and optional comment
6. Click "Create"

#### Creating Silences via CLI/API

```bash
# Set AlertManager URL
export ALERTMANAGER_URL="http://alertmanager.shared.svc.cluster.local:9093"

# Silence a specific alert for 1 hour
curl -s -X POST "$ALERTMANAGER_URL/api/v2/silences" \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "SceneSpeakHighErrorRate", "isRegex": false}
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "endsAt": "'$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "createdBy": "oncall@example.com",
    "comment": "Maintenance window - investigating GPU issue"
  }' | jq .

# Silence all warnings for a service
curl -s -X POST "$ALERTMANAGER_URL/api/v2/silences" \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [
      {"name": "service", "value": "scenespeak-agent", "isRegex": false},
      {"name": "severity", "value": "warning", "isRegex": false}
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "endsAt": "'$(date -u -d '+2 hours' +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "createdBy": "oncall@example.com",
    "comment": "Planned deployment - ignore warnings"
  }'

# Silence with regex pattern (silence multiple alerts)
curl -s -X POST "$ALERTMANAGER_URL/api/v2/silences" \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [
      {"name": "alertname", "value": ".*HighLatency", "isRegex": true}
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "endsAt": "'$(date -u -d '+30 minutes' +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "createdBy": "oncall@example.com",
    "comment": "Performance testing - ignore latency alerts"
  }'
```

#### Viewing and Managing Silences

```bash
# List all active silences
curl -s "$ALERTMANAGER_URL/api/v2/silences" | jq '.[] | select(.status.state == "active")'

# List expired silences
curl -s "$ALERTMANAGER_URL/api/v2/silences" | jq '.[] | select(.status.state == "expired")'

# Get specific silence details
SILENCE_ID="<silence_id>"
curl -s "$ALERTMANAGER_URL/api/v2/silences/$SILENCE_ID" | jq .

# Delete (expire) a silence
curl -X DELETE "$ALERTMANAGER_URL/api/v2/silences/$SILENCE_ID"

# View silences in browser
echo "Open: http://localhost:9093/#/silences"
```

### Alert Notification Channels

#### Slack Integration

AlertManager sends notifications to Slack channels based on severity:

| Receiver | Channel | Purpose |
|----------|---------|---------|
| critical-alerts | #chimera-critical | Critical alerts requiring immediate attention |
| warning-alerts | #chimera-alerts | Warning and informational alerts |
| default | #chimera-alerts | All other alerts |

**Testing Slack Integration:**

```bash
# Trigger test alert
kubectl exec -n shared deployment/prometheus -- \
  wget -qO- --post-data='' \
  'http://localhost:9090/api/v1/alerts' \
  --header='Content-Type: application/json'

# Verify AlertManager received it
kubectl logs -n shared deployment/alertmanager --tail=50
```

### AlertManager Troubleshooting

#### Alerts Not Firing

1. Check Prometheus rules are loaded:
   ```bash
   kubectl exec -n shared deployment/prometheus -- \
     wget -qO- http://localhost:9090/api/v1/rules | jq .
   ```

2. Check AlertManager is receiving from Prometheus:
   ```bash
   kubectl exec -n shared deployment/prometheus -- \
     wget -qO- http://localhost:9090/api/v1/alertmanagers | jq .
   ```

3. Check AlertManager logs:
   ```bash
   kubectl logs -n shared deployment/alertmanager --tail=100
   ```

#### Notifications Not Delivered

1. Check AlertManager status:
   ```bash
   kubectl port-forward -n shared svc/alertmanager 9093:9093
   # Open http://localhost:9093/#/status
   ```

2. Verify webhook configuration:
   ```bash
   kubectl get configmap alertmanager-config -n shared -o yaml
   ```

3. Test webhook directly:
   ```bash
   # Test Slack webhook
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test notification from AlertManager"}'
   ```

### AlertManager Configuration

**Location:** `platform/monitoring/config/alertmanager.yaml`

**Key Settings:**
- `group_wait`: Time to wait before sending first notification
- `group_interval`: Time to wait before sending notification about new alerts
- `repeat_interval`: Time to wait before resending notification
- `resolve_timeout`: Time after which alerts are auto-resolved

**Reloading Configuration:**

```bash
# Update ConfigMap
kubectl create configmap alertmanager-config \
  -n shared \
  --from-file=platform/monitoring/config/alertmanager.yaml \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart AlertManager to pick up changes
kubectl rollout restart deployment/alertmanager -n shared

# Verify configuration loaded
kubectl logs -n shared deployment/alertmanager --tail=20 | grep "Completed loading"
```

### Alert Inhibition

AlertManager uses inhibition rules to suppress certain alerts when others are firing:

```yaml
# If a critical alert is firing, suppress warning alerts for same service
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'service']
```

This prevents alert spam during major incidents.

### Best Practices

1. **Always add comments** to silences explaining why they were created
2. **Set appropriate durations** - don't create permanent silences
3. **Use specific matchers** - avoid broad silences that mute important alerts
4. **Clean up expired silences** - review and remove them periodically
5. **Document planned maintenance** - create silences before starting work
6. **Test notification channels** - verify Slack/webhook integration regularly

### AlertManager Alerting Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Prometheus │────▶│ AlertManager │────▶│    Slack    │
│  ( firing  )│     │ (grouping)   │     │ (#critical) │
└─────────────┘     └──────────────┘     └─────────────┘
                          │
                          ├─── Inhibition (suppressed)
                          │
                          └─── Silences (muted)
```

## Useful Commands

### AlertManager Commands

```bash
# Port-forward to access AlertManager UI
kubectl port-forward -n shared svc/alertmanager 9093:9093

# Get all active silences
export ALERTMANAGER_URL="http://alertmanager.shared.svc.cluster.local:9093"
curl -s "$ALERTMANAGER_URL/api/v2/silences" | jq '.[] | select(.status.state == "active")'

# Get AlertManager status
curl -s "$ALERTMANAGER_URL/api/v2/status" | jq .

# Get alert groups
curl -s "$ALERTMANAGER_URL/api/v2/alerts/groups" | jq .

# Get receiver information
curl -s "$ALERTMANAGER_URL/api/v2/receivers" | jq .
```

### Prometheus Commands

```bash
# Get alert status from Prometheus
kubectl exec -n shared deployment/prometheus -- \
  wget -qO- http://localhost:9090/api/v1/alerts | jq .

# Check firing alerts
kubectl exec -n shared deployment/prometheus -- \
  wget -qO- http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# View ServiceMonitor resources
kubectl get servicemonitor -n shared

# Check Prometheus targets
kubectl exec -n shared deployment/prometheus -- \
  wget -qO- http://localhost:9090/api/v1/targets | jq .

# Check Prometheus to AlertManager connectivity
kubectl exec -n shared deployment/prometheus -- \
  wget -qO- http://localhost:9090/api/v1/alertmanagers | jq .
```

## Contact Information

| Role | Contact | Hours |
|------|---------|-------|
| On-Call Engineer | oncall@chimera.example.com | 24/7 |
| Team Lead | lead@chimera.example.com | Business hours + on-call |
| Platform Architect | architect@chimera.example.com | Business hours + emergency |
| Management | management@chimera.example.com | Business hours |

## Related Documentation

- [Monitoring Runbook](monitoring.md)
- [Incident Response](incident-response.md)
- [Deployment Guide](deployment.md)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [AlertManager API](https://prometheus.io/docs/alerting/latest/api/)

---

**Last Updated**: 2026-03-04
**Version**: 2.0

## Related Documentation

- [Observability Guide](../observability.md) - Overview of observability platform
- [On-Call Procedures](on-call.md) - On-call rotation and escalation
- [SLO Response](slo-response.md) - SLO breach procedures

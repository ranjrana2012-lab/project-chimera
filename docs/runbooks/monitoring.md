# Project Chimera - Monitoring Runbook

This runbook provides comprehensive guidance for monitoring, troubleshooting, and maintaining the Project Chimera platform.

## Table of Contents

- [Overview](#overview)
- [Monitoring Stack](#monitoring-stack)
- [Key Metrics](#key-metrics)
- [Dashboards](#dashboards)
- [Common Issues and Resolutions](#common-issues-and-resolutions)
- [Maintenance Procedures](#maintenance-procedures)

## Overview

Project Chimera uses a comprehensive monitoring stack consisting of:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Jaeger**: Distributed tracing
- **Service-specific metrics**: Each service exposes Prometheus-compatible metrics

## Monitoring Stack

### Prometheus

**Access**: `http://prometheus.shared.svc.cluster.local:9090`

Prometheus scrapes metrics from all services every 15 seconds and stores them for 30 days.

#### Key Prometheus Queries

```promql
# Overall service health
up{job="chimera-live-services"}

# Request rate by service
sum(rate(scenespeak_requests_total[5m])) by (service)

# Error rate
sum(rate(scenespeak_requests_total{status="error"}[5m])) /
sum(rate(scenespeak_requests_total[5m]))

# P95 latency
histogram_quantile(0.95, sum(rate(scenespeak_request_duration_seconds_bucket[5m])) by (le))
```

### Grafana

**Access**: `http://grafana.shared.svc.cluster.local:3000`

Default credentials (change in production):
- Username: `admin`
- Password: `chimera-admin-change-me`

#### Available Dashboards

1. **Project Chimera - Services Overview** (`chimera-services`)
   - Request rates across all services
   - Error rates
   - Latency percentiles
   - Cache hit rates
   - Resource utilization

2. **Project Chimera - SceneSpeak** (`chimera-scenespeak`)
   - Dialogue generation metrics
   - Token processing rates
   - Model-specific performance
   - Cache utilization

3. **Project Chimera - Sentiment Analysis** (`chimera-sentiment`)
   - Audience sentiment trends
   - Emotion distribution
   - Queue metrics
   - Processing latency

### Jaeger

**Access**: `http://jaeger.shared.svc.cluster.local:16686`

Jaeger provides distributed tracing for all service-to-service communication.

## Common Issues and Resolutions

### High Error Rates

#### SceneSpeak High Error Rate

**Symptom**: Error rate > 5% for 5+ minutes

**Resolution**:
1. Check model loading status: `kubectl logs -n live deployment/SceneSpeak Agent`
2. Verify GPU availability: `kubectl describe nodes | grep nvidia.com/gpu`
3. Test Redis connectivity: `kubectl exec -n live deployment/SceneSpeak Agent -- redis-cli -h redis.shared ping`

### High Latency

#### SceneSpeak P95 Latency > 2s

**Resolution**:
1. Check GPU memory: `nvidia-smi` on the node
2. Review cache hit rate: should be > 70%
3. Consider scaling replicas during high demand

### Queue Issues

#### Sentiment Queue Backlog

**Resolution**:
1. Check worker pod status: `kubectl get pods -n live -l app=Sentiment Agent`
2. Scale horizontally: `kubectl scale deployment Sentiment Agent -n live --replicas=2`

## Emergency Procedures

### Service Degradation During Live Show

If services degrade during a live performance:

1. Check Grafana for affected services
2. Scale affected services
3. Consider rollback if recent deployment
4. Document all actions taken

### Complete Service Outage

If a service is completely down:

1. Check cluster health
2. Restart affected pods
3. Scale to minimum viable capacity
4. Investigate root cause

## Access and Credentials

| Service | Username | Password | Change Required |
|---------|----------|----------|-----------------|
| Grafana | admin | chimera-admin-change-me | Yes |

---

**Last Updated**: 2026-02-27
**Version**: 1.0

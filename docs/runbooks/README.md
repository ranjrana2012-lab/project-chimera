# Project Chimera - Runbooks

This directory contains operational runbooks for Project Chimera.

**Version:** 3.0.0

---

## Available Runbooks

### Core Operations

- [Bootstrap Setup](bootstrap-setup.md) - Initial environment setup with k3s
- [Deployment](deployment.md) - Deployment procedures for services
- [Incident Response](incident-response.md) - Incident handling procedures
- [Monitoring](monitoring.md) - Monitoring and alerting procedures
- [Alerts](alerts.md) - Alert types and responses
- **[Testing Guide](testing-guide.md)** - Comprehensive testing procedures (NEW)

### Observability Runbooks

- [On-Call Procedures](on-call.md) - On-call rotation and response procedures
- [SLO Handbook](slo-handbook.md) - Service Level Objectives and error budgets
- [SLO Response](slo-response.md) - SLO breach response procedures
- [Distributed Tracing](distributed-tracing.md) - OpenTelemetry and Jaeger guide
- [Performance Analysis](performance-analysis.md) - Performance investigation guide

---

## Quick Reference

| Task | Runbook | Command |
|------|---------|---------|
| Initial setup | Bootstrap Setup | `make bootstrap` |
| Check status | Monitoring | `make bootstrap-status` |
| Deploy changes | Deployment | `kubectl apply -f ...` |
| Run tests | Testing Guide | `make test` |
| Handle incident | Incident Response | See runbook |
| Check alerts | Alerts | Check Operator Console |

---

## Testing Guide Contents

The [Testing Guide](testing-guide.md) covers:

- **Unit Tests** - 300+ unit tests for all services
- **Integration Tests** - Service integration testing
- **Load Tests** - Performance and load testing
- **Service-Specific Testing** - Each service's test procedures
- **New v0.4.0 Features** - Testing for LoRA adapters, ML safety, BSL avatar, real-time updates
- **Troubleshooting** - Common test issues and solutions

---

## Common Operations

### Health Check All Services

```bash
# Core services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done

# Platform services
for port in 8010 8011 8012 8013; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done
```

### Run All Tests

```bash
make test
# Or
pytest tests/ -v
```

### View Logs

```bash
# All services
make logs-all

# Specific service
kubectl logs -f -n live deployment/scenespeak-agent
```

---

## Emergency Procedures

| Issue | Action | Runbook |
|-------|--------|---------|
| Service down | Check logs, restart pod | Incident Response |
| High CPU/Memory | Check metrics, scale up | Monitoring |
| Failed tests | Check test output, fix issues | Testing Guide |
| Critical alert | Acknowledge, investigate | Alerts |
| Deployment failure | Rollback, investigate | Deployment |

---

## Service Ports

| Service | Port | Documentation |
|---------|------|---------------|
| OpenClaw | 8000 | [API Docs](../api/openclaw-orchestrator.md) |
| SceneSpeak | 8001 | [API Docs](../api/scenespeak-agent.md) |
| Captioning | 8002 | [API Docs](../api/captioning-agent.md) |
| BSL | 8003 | [API Docs](../api/bsl-agent.md) |
| Sentiment | 8004 | [API Docs](../api/sentiment-agent.md) |
| Lighting | 8005 | [API Docs](../api/lighting-service.md) |
| Safety | 8006 | [API Docs](../api/safety-filter.md) |
| Console | 8007 | [API Docs](../api/operator-console.md) |
| Dashboard | 8010 | [API Docs](../api/dashboard-service.md) |
| Test Orchestrator | 8011 | [API Docs](../api/test-orchestrator.md) |
| CI/CD Gateway | 8012 | [API Docs](../api/cicd-gateway.md) |
| Quality Gate | 8013 | [API Docs](../api/quality-gate.md) |

---

*Last Updated: March 2026*
*Runbooks v0.4.0*

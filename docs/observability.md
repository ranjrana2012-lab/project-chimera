# Production Observability at Project Chimera

## Overview

Project Chimera's production observability stack provides complete visibility into service health, business metrics, SLO compliance, and distributed tracing.

## Components

### 1. Alerting Foundation
- **AlertManager:** Intelligent alert routing
- **Slack Integration:** Real-time notifications
- **On-Call Rotation:** 24/7 coverage

### 2. Business Visibility
- **Show Overview Dashboard:** Real-time show status
- **Dialogue Quality Dashboard:** Content generation metrics
- **Audience Engagement Dashboard:** Sentiment and interaction

### 3. Reliability Framework
- **SLOs:** 99-99.9% targets for core services
- **Error Budgets:** Track remaining allowance
- **Quality Gate:** Block deployments on SLO breach

### 4. Deep Observability
- **OpenTelemetry:** Distributed tracing
- **Jaeger:** Trace analysis
- **Anomaly Detection:** Automated issue detection

## Quick Links

| Tool | URL | Credentials |
|------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |
| AlertManager | http://localhost:9093 | - |

## Runbooks

- [Alerts](runbooks/alerts.md)
- [On-Call](runbooks/on-call.md)
- [SLO Handbook](runbooks/slo-handbook.md)
- [SLO Response](runbooks/slo-response.md)
- [Distributed Tracing](runbooks/distributed-tracing.md)
- [Performance Analysis](runbooks/performance-analysis.md)
- [Testing Guide](runbooks/testing-guide.md)

## Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/silence-alerts.sh` | Silence alerts for maintenance |
| `./scripts/calculate-error-budget.py` | Calculate error budget status |
| `./scripts/slo-compliance-report.sh` | Generate SLO compliance report |
| `./scripts/analyze-trace.py` | Analyze a specific trace |
| `./scripts/dependency-graph.py` | Generate service dependency graph |

## Metrics Reference

### Service Health

- `up{job="chimera-services"}` - Service availability
- `rate(http_requests_total{status=~"5.."}[5m])` - Error rate

### Business Metrics

- `scenespeak_lines_generated_total` - Dialogue lines
- `sentiment_audience_avg` - Audience sentiment
- `captioning_latency_seconds` - Caption timing
- `bsl_active_sessions` - BSL avatar sessions

### SLO Metrics

- `slo:*_success_rate:30d` - SLO compliance
- `slo:error_budget_remaining:30d` - Error budget
- `slo:error_burn_rate` - Burn rate

## Support

For issues or questions:
- Check relevant runbook
- Contact on-call engineer
- Escalate to Technical Lead

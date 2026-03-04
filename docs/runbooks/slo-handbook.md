# SLO Handbook

## Overview

This handbook defines Service Level Objectives (SLOs) for Project Chimera services. SLOs are a key part of our reliability engineering approach, providing clear targets for service performance and availability.

## What are SLOs?

Service Level Objectives (SLOs) are specific, measurable targets for service reliability. They define the expected level of service performance over a given time period. SLOs help us:

- Set clear expectations with stakeholders
- Make data-driven decisions about feature development vs. reliability
- Prioritize incidents and issues
- Balance innovation with stability

## SLO Definitions

### Core Services

| Service | SLO | Measurement Period | Error Budget | Description |
|---------|-----|-------------------|--------------|-------------|
| OpenClaw | 99.9% | Rolling 30 days | 43.2 min/month | Core AI agent service |
| SceneSpeak | 99.5% | Rolling 30 days | 3.6 hrs/month | Content generation |
| Captioning | 99.5% | Rolling 30 days | 3.6 hrs/month | Real-time captioning |
| BSL | 99% | Rolling 30 days | 7.2 hrs/month | Sign language avatar |
| Safety | 99.9% | Rolling 30 days | 43.2 min/month | Content safety filter |
| Console | 99.5% | Rolling 30 days | 3.6 hrs/month | Operator console |

### Platform Services

| Service | SLO | Measurement Period | Error Budget | Description |
|---------|-----|-------------------|--------------|-------------|
| Dashboard | 99% | Rolling 7 days | 1.68 hrs/week | Monitoring dashboard |
| Test Orchestrator | 95% | Calendar month | 36 hrs/month | Test automation |
| CI/CD Gateway | 95% | Calendar month | 36 hrs/month | Build and deployment |

## Error Budget Policy

The error budget represents the amount of downtime or errors we can tolerate while still meeting our SLO. It's not a goal to use - it's a limit to stay within.

### Burn Rate Thresholds

| Burn Rate | Meaning | Action Required |
|-----------|---------|-----------------|
| 1x | Normal operation | No action required |
| 2x | Warning level | Assess impact, monitor closely |
| 5x | Elevated concern | Prepare for deployment freeze |
| 10x | Critical | Block all deployments immediately |

### Budget Thresholds

| Remaining Budget | Status | Action |
|------------------|--------|--------|
| > 50% | Healthy | Normal operations |
| 25-50% | Caution | Monitor closely, reduce risk |
| 10-25% | Warning | Block non-essential changes |
| < 10% | Critical | Emergency mode, block all changes |
| < 5% | Emergency | Emergency review required |

## SLO Calculations

### Success Rate

```
Success Rate = (Successful Requests / Total Requests) × 100
```

A successful request is one that:
- Returns HTTP status 2xx or 3xx
- Completes within the latency threshold
- Returns valid, complete data

### Error Budget

```
Error Budget (%) = ((SLO Target - Actual Success Rate) / SLO Target) × 100
Error Budget (time) = (Measurement Period) × (1 - SLO Target)
```

Example for SceneSpeak (99.5% SLO, 30-day period):
- Total period: 30 days × 24 hours = 720 hours
- Error budget: 720 × (1 - 0.995) = 3.6 hours

### Burn Rate

```
Burn Rate = Current Error Rate / Allowed Error Rate
```

Burn rate indicates how fast we're consuming our error budget:
- 1x = Normal pace, will meet SLO
- 2x = On track to breach in half the time
- 10x = On track to breach in 1/10th the time

## SLO Measurement

### Metrics Tracked

1. **Availability**: Service uptime and responsiveness
2. **Latency**: Request duration (P50, P95, P99)
3. **Error Rate**: Failed requests per time period
4. **Quality**: Content validation and safety checks

### Data Sources

- **Prometheus**: Raw metrics and SLO calculations
- **Grafana**: SLO dashboards and visualization
- **AlertManager**: Burn rate alerts
- **Custom Scripts**: Error budget calculations

## Review Process

### Daily

- Automated burn rate monitoring
- Alert on burn rate > 2x
- Check error budget status

### Weekly

- Generate SLO compliance report
- Review services approaching budget limits
- Track trends and patterns

### Monthly

- SLO target review and adjustment
- Error budget reset (for 30-day rolling windows)
- Service reliability assessment
- Stakeholder communication

## SLO Best Practices

### DO

- Monitor SLOs continuously
- Investigate burn rate changes promptly
- Communicate SLO status to stakeholders
- Use error budget to prioritize work
- Learn from SLO breaches

### DON'T

- Treat error budget as a target to use
- Ignore burn rate warnings
- Deploy features when budget is critical
- Change SLOs retroactively
- Blame individuals for SLO breaches

## Related Documentation

- [SLO Response Runbook](slo-response.md) - How to respond to SLO breaches
- [Alerts Runbook](alerts.md) - Alert configuration and response
- [Incident Response](incident-response.md) - Incident management procedures

## Tools and Scripts

```bash
# Calculate current error budget status
./scripts/calculate-error-budget.py

# Generate SLO compliance report
./scripts/slo-compliance-report.sh

# View SLO dashboard
# URL: http://grafana.shared.svc.cluster.local:3000/d/slo-overview
```

## Questions?

Contact the reliability team or check the #reliability Slack channel for questions about SLOs, error budgets, or burn rates.

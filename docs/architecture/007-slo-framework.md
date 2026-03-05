# ADR-007: SLO Framework and Error Budget Adoption

**Status:** Accepted
**Date:** 2026-03-05
**Context:** Need to document SLO framework implementation decisions

## Context

Project Chimera requires Service Level Objectives (SLOs) to ensure reliability and set appropriate expectations for service performance. The Production Observability Enhancement implemented a comprehensive SLO framework.

## Decision

Adopt Google SRE practices for SLOs and error budgets:

### SLO Targets

| Service | SLO | SLI | Window | Error Budget |
|---------|-----|-----|--------|--------------|
| OpenClaw | 99.9% | Successful orchestrations / total | 30d | 43.2min/month |
| SceneSpeak | 99.5% | Successful generations / total | 30d | 3.6hrs/month |
| Captioning | 99.5% | Captions delivered / speech | 30d | 3.6hrs/month |
| BSL | 99% | Successful translations / total | 30d | 7.2hrs/month |
| Safety | 99.9% | Requests processed / total | 30d | 43.2min/month |
| Console | 99.5% | Dashboard loads / requests | 30d | 3.6hrs/month |

### Error Budget & Burn Rate

```
Burn Rate = (Current Error Rate) / (Allowed Error Rate)

Burn Rate 1x = On track
Burn Rate 2x = Warning (5m threshold)
Burn Rate 10x = Critical (1m threshold)
```

### Quality Gate

Deployments blocked when:
- SLO compliance < 95%
- Error budget remaining < 10%

## Components

```
platform/quality-gate/
└── gate/slo_gate.py          # SLO-based deployment blocking

platform/monitoring/config/
├── slo-recording-rules.yaml # 30-day rolling window SLOs
└── slo-alerting-rules.yaml   # Burn rate alerts

scripts/
├── calculate-error-budget.py # Error budget status
└── slo-compliance-report.sh  # Weekly SLO reports
```

## Consequences

### Positive
- Data-driven reliability decisions
- Clear deployment blocking criteria
- Automated alerting on SLO breaches
- Weekly SLO compliance reports

### Negative
- Additional metrics infrastructure
- Deployment friction when SLO not met
- Requires ongoing SLO calibration

### Mitigations
- Start with conservative SLO targets
- Regular SLO review and calibration
- Clear escalation procedures
- Error budget "hero mode" procedures

## References

- [SLO Handbook](../runbooks/slo-handbook.md)
- [SLO Response Runbook](../runbooks/slo-response.md)
- [Observability Guide](../observability.md)

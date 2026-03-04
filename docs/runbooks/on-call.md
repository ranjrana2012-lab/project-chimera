# On-Call Handbook

## Overview

This handbook covers on-call procedures for Project Chimera production operations.

## Rotation

- **Primary On-Call:** [Name] - [Contact]
- **Secondary On-Call:** [Name] - [Contact]
- **Escalation:** Technical Lead - [Contact]

## Alert Severity

### Critical
- Service down
- Error rate > 5%
- Data loss risk
- Action required within 5 minutes

### Warning
- High resource usage
- Elevated error rates
- Degraded performance
- Action required within 30 minutes

## Response Procedure

1. **Acknowledge** alert in Slack
2. **Assess** impact using Grafana
3. **Check** related runbook
4. **Resolve** or escalate
5. **Document** actions taken

## During Live Shows

**Hero Mode:** All alerts go to dedicated #chimera-show channel
- Escalation immediately to Technical Lead
- No non-emergency changes
- Post-show review required

## Handoff

Use this checklist:

- [ ] No active incidents
- [ ] All alerts acknowledged
- [ ] Outstanding issues documented
- [ ] Recent changes noted
- [ ] Next on-contact confirmed

## Emergency Contacts

- Technical Lead: [Phone/Slack]
- Infrastructure Lead: [Phone/Slack]
- Theatre Staff: [Phone]

## Maintenance Windows

Request silence using:
```bash
./scripts/silence-alerts.sh 2h "Deploying v1.2.3" service=scenespeak
```

Always:
- Schedule in advance in #chimera-planning
- Avoid during show hours
- Update on-call calendar

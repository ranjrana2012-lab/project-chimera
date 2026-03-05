# Monday Demo Documentation

**Date:** March 3, 2026
**Purpose:** Onboard 15 AI students to Project Chimera

## Quick Links

- [Demo Script](./demo-script.md) - 60-minute agenda
- [GitHub Setup Guide](./github-setup-guide.md) - Project configuration
- [Pre-Monday Checklist](./pre-monday-checklist.md) - Verification steps
- [Student Quick Start](../quick-start.md) - Student guide
- [Student Roles](../roles.md) - Role assignments

## What Students Will Learn

1. **GitHub Workflow** - Issues, PRs, code review
2. **Microservices** - 8 AI services working together
3. **Kubernetes** - k3s cluster management
4. **Testing** - Unit tests, coverage, CI/CD
5. **Trust System** - Earn auto-merge through quality contributions

## Trust Score System

- **New (0 PRs)** - Manual review required
- **Learning (1-2 PRs)** - Manual review required
- **Trusted (3+ PRs)** - Auto-merge eligible

## Services Status

| Service | Status | Port | Demo Ready? |
|---------|--------|------|-------------|
| OpenClaw Orchestrator | ✅ Working | 8000 | Yes |
| SceneSpeak Agent | ✅ Working | 8001 | Yes |
| Captioning Agent | ⚠️ Partial | 8002 | Partial |
| BSL Translation | ⚠️ Partial | 8003 | Partial |
| Sentiment Agent | ⚠️ Partial | 8004 | Partial |
| Lighting Control | ✅ Working | 8005 | Yes |
| Safety Filter | ⚠️ Partial | 8006 | Partial |
| Operator Console | ✅ Working | 8007 | Yes |

## GitHub Automation

- **4 Workflows** - PR validation, trust check, auto-merge, onboarding
- **15 Issues** - Sprint 0 onboarding tasks
- **27 Labels** - Trust, sprint, component labels
- **Project Board** - Single shared board with role views

## Emergency Contacts

- Technical Lead: [GitHub @technical-lead]
- University Support: [email/phone]

## Rollback Plan

If GitHub automation fails:
1. Disable workflows: `gh workflow disable`
2. Fall back to manual review
3. Continue with k3s demo
4. Fix and re-enable workflows

---

**Good luck with the demo! The students will love Project Chimera.**

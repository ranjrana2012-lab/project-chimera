# Pre-Monday Verification Checklist

## GitHub Setup

- [ ] GitHub Project board created and configured
- [ ] Custom fields created (Status, Priority, Role, Sprint, Trust Level)
- [ ] Views created (By Role, By Sprint, Monday Onboarding)
- [ ] Issue templates created (feature, bug, documentation)
- [ ] PR template created
- [ ] CODEOWNERS file configured
- [ ] Branch protection rules enabled (main, develop)
- [ ] GitHub labels created (trust, sprint, component)

## Workflows

- [ ] pr-validation.yml created and tested
- [ ] trust-check.yml created and tested
- [ ] auto-merge.yml created and tested
- [ ] onboarding.yml created and tested
- [ ] All workflows pushed to GitHub
- [ ] Sample PR tested successfully

## Student Onboarding

- [ ] 15 student accounts invited
- [ ] Write permissions granted
- [ ] Sprint 0 onboarding issues created
- [ ] Student usernames added to workflow
- [ ] Onboarding workflow triggered successfully

## Documentation

- [ ] GitHub setup guide created
- [ ] Demo script created
- [ ] Student quick start guide exists
- [ ] MASTER_DOCUMENTATION_MONDAY.md available
- [ ] Student roles documented

## Demo Environment

- [ ] k3s cluster running
- [ ] All services deployed
- [ ] Services accessible via port-forward
- [ ] Grafana accessible at localhost:3000
- [ ] Test data prepared

## Final Checks

- [ ] Run: `gh workflow list` - should show 4 workflows
- [ ] Run: `gh label list` - should show 27+ labels
- [ ] Run: `gh issue list --label sprint-0` - should show 15 issues
- [ ] Run: `gh project list` - should show student project
- [ ] Run: `curl http://localhost:8000/health/live` - should return healthy
- [ ] Run: `curl http://localhost:8001/health/live` - should return healthy
- [ ] Run: `curl http://localhost:8005/health/live` - should return healthy
- [ ] Run: `curl http://localhost:8007/health/live` - should return healthy

## Monday Morning (Final Prep)

- [ ] Verify all workflows still working
- [ ] Re-run onboarding workflow if needed
- [ ] Check all student invitations accepted
- [ ] Prepare demo environment
- [ ] Open demo script
- [ ] Print role cards for students
- [ ] Test projector/screen sharing
- [ ] Have backup plan ready

---

## Complete Student Onboarding Package (NEW)

### Documentation
- [ ] Student welcome email template created
- [ ] Communication channels guide created
- [ ] Code of Conduct exists (comprehensive)
- [ ] Extended Contributing Guide exists (comprehensive)
- [ ] Student FAQ created
- [ ] Office Hours schedule created
- [ ] Sprint definitions created
- [ ] Evaluation criteria created
- [ ] GitHub Project Board setup guide created
- [ ] CONTRIBUTORS.md template created
- [ ] README updated with student links
- [ ] CHANGELOG updated

### GitHub Setup
- [ ] GitHub Project Board created
- [ ] Custom fields configured (Status, Priority, Role, Sprint, Trust Level, Points)
- [ ] Views created (By Role, By Sprint, Kanban, Monday Onboarding)
- [ ] Labels created (sprint-0, good-first-issue, etc.)
- [ ] Repository linked to project
- [ ] CODEOWNERS exists
- [ ] Branch protection rules exist
- [ ] Workflows tested

### Community Platform
- [ ] Slack workspace created
- [ ] All channels created
- [ ] Integrations configured (GitHub → Slack)
- [ ] Invite link generated
- [ ] Bot configurations tested

### Sprint 0 Issues
- [ ] Onboarding workflow exists
- [ ] All 45 Sprint 0 issues ready to create
- [ ] Issue templates exist
- [ ] Assignee mappings ready

### Email Preparation
- [ ] Email template ready
- [ ] Placeholders documented (names, emails, roles, mentors)
- [ ] Links placeholder format (repository, docs, Slack, Zoom)
- [ ] Schedule template (location, time, Zoom link)

---

**You're ready for Monday! 🚀**

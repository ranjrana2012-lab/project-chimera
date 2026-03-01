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

**You're ready for Monday! 🚀**

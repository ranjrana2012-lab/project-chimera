# Pre-4pm Demo Checklist

**Run through this checklist before the 4pm student onboarding call**

---

## ✅ Printed Materials (Ready in local ignored `demo-materials-2026-03-02/`)

- [ ] **12 copies** of `student-handout.md` (10 students + 2 spare)
- [ ] **1 copy** of `demo-commands-cheat-sheet.md` (for you)
- [ ] **1 copy** of `4pm-demo-script.md` (for you)

---

## ✅ Technical Setup

### Services Running
- [ ] k3s cluster is running: `sudo k3s kubectl get nodes`
- [ ] Run demo prep script: `./scripts/demo-prep.sh`
  - Should check all 8 services (ports 8000-8007)
  - Fix any failing services before demo

### Browser Tabs Open
- [ ] Operator Console: http://localhost:8007
- [ ] GitHub Repository: https://github.com/ranjrana2012-lab/project-chimera
- [ ] GitHub Project Board: https://github.com/users/ranjrana2012-lab/projects/1
- [ ] Documentation (if applicable)

### Terminal Ready
- [ ] Terminal window open with project directory
- [ ] `gh` CLI authenticated: `gh auth status`
- [ ] Can run: `curl http://localhost:8000/health/live`

---

## ✅ GitHub Setup

- [ ] **All commits pushed to GitHub** (run: `git status` - should be clean)
- [ ] **Sprint 0 issues created** (run: `gh issue list --limit 50`)
  - Should see 30 issues (3 per student × 10 students)
- [ ] **Project board has views configured**
- [ ] **Labels exist**: sprint-0, onboarding, good-first-issue, component:*

---

## ✅ Student Data

- [ ] `data/students.csv` has all 10 students
- [ ] Names and preferred names are correct
- [ ] Email addresses are verified

---

## ✅ Demo Script Review

- [ ] Read through `4pm-demo-script.md` once
- [ ] Familiarize yourself with the 6 timed sections:
  1. Welcome & Overview (0:00-0:10)
  2. GitHub Tour (0:10-0:20)
  3. Live Demo (0:20-0:40)
  4. Role Assignments (0:40-0:50)
  5. Contribution Workflow (0:50-0:55)
  6. Q&A (0:55-1:00)

---

## ✅ Quick Commands Reference

```bash
# Health check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "Port $port:"
    curl -s http://localhost:$port/health/live | jq . || echo "Not responding"
done

# Test OpenClaw
curl http://localhost:8000/v1/skills

# Test SceneSpeak
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello actor"}'

# Check GitHub issues
gh issue list --label sprint-0

# Check project board
gh project view PVT_kwHODhT54s4BQjG4
```

---

## ✅ Emergency Backup

If something goes wrong during demo:

- [ ] Know how to restart k3s: `sudo systemctl restart k3s`
- [ ] Know how to restart individual services (see cheat sheet)
- [ ] Have backup talking points if services fail
- [ ] Can pivot to documentation/code walkthrough if demo fails

---

## ✅ Final Check

- [ ] Time: Start setup at least 30 minutes before 4pm
- [ ] Environment: Quiet room, stable internet
- [ ] Monitor: Screen share ready if virtual
- [ ] Audio: Microphone tested if virtual
- [ ] Water/coffee: Stay hydrated! 💧

---

**You're ready! Good luck with the demo! 🚀**

---

*Generated: 2026-03-02*
*Demo time: 4:00 PM*

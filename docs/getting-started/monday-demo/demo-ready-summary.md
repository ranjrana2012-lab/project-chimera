# 4pm Demo - Ready Package Summary

**Everything you need for the 4pm student onboarding call**

---

## 📦 What's Been Prepared

### 1. Student Handout
**Location:** `docs/getting-started/monday-demo/student-handout.md`
- One-page printable handout for students
- Project overview, architecture diagram, links
- Role assignment fill-in section
- First 3 steps to get started
- Support channels and office hours

**Print:** 12 copies (10 students + 2 spare)

---

### 2. Demo Script (60 Minutes)
**Location:** `docs/getting-started/monday-demo/4pm-demo-script.md`
- Complete timed script with 6 sections
- Talking points, commands, screen actions
- Interactive elements and Q&A prep
- Backup plan for tech failures

**Print:** 1 copy (for presenter)

---

### 3. Commands Cheat Sheet
**Location:** `docs/getting-started/monday-demo/demo-commands-cheat-sheet.md`
- Quick health check commands
- Service endpoints to demo
- Architecture demo commands
- Git workflow demo
- Troubleshooting commands

**Print:** 1 copy (keep at podium)

---

### 4. Pre-Demo Checklist
**Location:** `docs/getting-started/monday-demo/pre-4pm-checklist.md`
- Printed materials checklist
- Technical setup verification
- GitHub setup confirmation
- Quick commands reference
- Emergency backup procedures

**Use:** Run through 30 minutes before demo

---

### 5. Student Data CSV
**Location:** `data/students.csv`
- 10 students with names, preferred names, emails
- Ready for personalized welcome emails

---

### 6. Welcome Email Script
**Location:** `scripts/send-welcome-emails.py`
- Python script to send personalized emails
- Supports dry-run mode for testing
- Role assignments and mentor contacts

**Usage:** `python scripts/send-welcome-emails.py --data data/students.csv --dry-run`

---

### 7. Sprint 0 Onboarding Workflow
**Location:** `.github/workflows/sprint-0-issues.yml`
- Creates 30 issues automatically (3 per student)
- Environment setup, first PR, role-specific tasks
- Ready to run after GitHub push

**Usage:** `gh workflow run sprint-0-issues.yml -f create_issues=true`

---

### 8. Demo Prep Script
**Location:** `scripts/demo-prep.sh`
- Checks k3s cluster status
- Verifies all 8 services are running
- Provides startup commands if needed

**Usage:** Run before demo: `./scripts/demo-prep.sh`

---

### 9. Print Materials Script
**Location:** `scripts/print-demo-materials.sh`
- Creates organized print package
- Copies all handouts to dated folder
- Provides printing instructions

**Usage:** Run once: `./scripts/print-demo-materials.sh`
**Output:** local ignored `demo-materials-2026-03-02/`

---

## 🚀 Quick Start for 4pm Demo

### 30 Minutes Before (3:30 PM)

```bash
# 1. Run demo prep check
./scripts/demo-prep.sh

# 2. Verify GitHub is ready
git status  # should be clean
gh issue list --limit 50  # should show 30 Sprint 0 issues

# 3. Open browser tabs
# - Operator Console: http://localhost:8007
# - GitHub Repo: https://github.com/ranjrana2012-lab/project-chimera
# - Project Board: https://github.com/users/ranjrana2012-lab/projects/1

# 4. Open terminal with cheat sheet ready
# Have docs/getting-started/monday-demo/demo-commands-cheat-sheet.md open
```

### During Demo (4:00 PM)

1. **Welcome** (10 min) - Hand out student handouts, introduce project
2. **GitHub Tour** (10 min) - Show repo, project board, issues
3. **Live Demo** (20 min) - Show services running, demonstrate features
4. **Role Assignments** (10 min) - Assign roles, create GitHub issues
5. **Workflow Demo** (5 min) - Show branch, commit, PR process
6. **Q&A** (5 min) - Answer questions, remind about office hours

### After Demo (5:00 PM)

```bash
# Send welcome emails with role assignments
python scripts/send-welcome-emails.py --data data/students.csv

# Follow up with students who missed the call
# Schedule 1:1s for students needing extra help
```

---

## 📋 Role Assignments (To be filled during demo)

| ID | Student Information (Removed for Privacy) | Role | Component | Mentor |
|----|------|-----------|-------|------|-----------|--------|
| 1 | [Student 1] | Tech Lead | OpenClaw (8000) | TBD |
| 2 | [Student 2] | AI-ML Lead | SceneSpeak (8001) | TBD |
| 3 | [Student 3] | AI-ML Lead | Captioning (8002) | TBD |
| 4 | [Student 4] | AI-ML Lead | BSL Translation (8003) | TBD |
| 5 | [Student 5] | AI-ML Lead | Sentiment (8004) | TBD |
| 6 | [Student 6] | Infra Lead | Lighting Control (8005) | TBD |
| 7 | [Student 7] | QA Lead | Safety Filter (8006) | TBD |
| 8 | [Student 8] | Frontend Lead | Operator Console (8007) | TBD |
| 9 | [Student 9] | Infrastructure | Infrastructure | TBD |
| 10 | [Student 10] | QA | QA & Testing | TBD |

---

## 🔗 Quick Links

- **GitHub Repo:** https://github.com/ranjrana2012-lab/project-chimera
- **Project Board:** https://github.com/users/ranjrana2012-lab/projects/1
- **Documentation:** See README.md for full docs
- **Issue Tracker:** https://github.com/ranjrana2012-lab/project-chimera/issues

---

## ✅ Status: READY FOR 4PM DEMO

All materials prepared and tested. You're ready to go!

**Good luck! You've got this! 🚀**

---

*Generated: 2026-03-02*
*Demo: 4:00 PM*
*Students: 10*

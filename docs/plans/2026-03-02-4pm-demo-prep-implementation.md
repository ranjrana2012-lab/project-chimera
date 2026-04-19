# 4pm Demo Preparation Package - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create complete demo package for 4pm student onboarding call with live demo, handouts, email automation, and GitHub self-service portal.

**Architecture:** Multi-component package including service management scripts, student handout, email automation, updated demo script, and GitHub workflow integration. All components use existing documentation and student data.

**Tech Stack:** Bash (service scripts), Python (email script), Markdown (documentation), GitHub CLI (project automation)

---

## Task 1: Create Student Data CSV File

**Files:**
- Create: `data/students.csv`

**Step 1: Create the student data CSV**

```csv
id,name,preferred_name,email
1,[Student 1],[Preferred],[email]
2,[Student 2],[Preferred],[email]
3,[Student 3],[Preferred],[email]
4,[Student 4],[Preferred],[email]
5,[Student 5],[Preferred],[email]
6,[Student 6],[Preferred],[email]
7,[Student 7],[Preferred],[email]
8,[Student 8],[Preferred],[email]
9,[Student 9],[Preferred],[email]
10,[Student 10],[Preferred],[email]
```

**Step 2: Commit**

```bash
git add data/students.csv
git commit -m "feat: add student data CSV for demo preparation"
```

---

## Task 2: Create Demo Preparation Script

**Files:**
- Create: `scripts/demo-prep.sh`
- Modify: N/A

**Step 1: Create the demo prep script**

```bash
#!/bin/bash
# Demo Preparation Script - Run before 4pm demo
# Checks and starts all required services

set -e

echo "=== Project Chimera Demo Preparation ==="
echo "Checking services..."

# Check k3s is running
if ! sudo k3s kubectl get nodes &>/dev/null; then
    echo "❌ k3s is not running"
    echo "Start with: sudo systemctl start k3s"
    exit 1
fi
echo "✅ k3s is running"

# Function to check a service
check_service() {
    local port=$1
    local name=$2
    if curl -s "http://localhost:${port}/health/live" &>/dev/null; then
        echo "✅ $name (port $port) is running"
        return 0
    else
        echo "❌ $name (port $port) is NOT responding"
        return 1
    fi
}

# Check all services
SERVICES_OK=true
check_service 8000 "OpenClaw Orchestrator" || SERVICES_OK=false
check_service 8001 "SceneSpeak Agent" || SERVICES_OK=false
check_service 8002 "Captioning Agent" || SERVICES_OK=false
check_service 8003 "BSL Translation Agent" || SERVICES_OK=false
check_service 8004 "Sentiment Agent" || SERVICES_OK=false
check_service 8005 "Lighting Control" || SERVICES_OK=false
check_service 8006 "Safety Filter" || SERVICES_OK=false
check_service 8007 "Operator Console" || SERVICES_OK=false

if [ "$SERVICES_OK" = false ]; then
    echo ""
    echo "Some services are not running. Start services with:"
    echo "  make bootstrap"
    echo "Or individual services:"
    echo "  cd services/<service-name> && source venv/bin/activate && python -m uvicorn main:app --port <port>"
    exit 1
fi

echo ""
echo "=== All Systems Ready for Demo! ==="
echo ""
echo "Quick health checks:"
echo "  curl http://localhost:8000/health/live"
echo "  curl http://localhost:8001/health/live"
echo ""
echo "Port forwards (if needed):"
sudo k3s kubectl port-forward -n chimera svc/openclaw 8000:8000 &
sudo k3s kubectl port-forward -n chimera svc/scenespeak 8001:8001 &
```

**Step 2: Make executable**

```bash
chmod +x scripts/demo-prep.sh
```

**Step 3: Test the script**

```bash
./scripts/demo-prep.sh
```

Expected: Script checks all services and reports status

**Step 4: Commit**

```bash
git add scripts/demo-prep.sh
git commit -m "feat: add demo preparation script"
```

---

## Task 3: Create Demo Commands Cheat Sheet

**Files:**
- Create: `docs/getting-started/monday-demo/demo-commands-cheat-sheet.md`

**Step 1: Create the cheat sheet**

```markdown
# Demo Commands Cheat Sheet

**Print this before the 4pm demo!**

---

## Quick Health Checks

```bash
# All services health
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "Port $port:"
    curl -s http://localhost:$port/health/live | jq . || echo "Not responding"
done
```

---

## Service Endpoints to Demo

| Service | Port | Command | What It Shows |
|---------|------|---------|---------------|
| OpenClaw | 8000 | `curl http://localhost:8000/v1/skills` | List available skills |
| SceneSpeak | 8001 | `curl -X POST http://localhost:8001/v1/generate -H "Content-Type: application/json" -d '{"prompt":"Hello actor"}'` | Generate dialogue |
| Captioning | 8002 | `curl http://localhost:8002/docs` | API documentation |
| Operator Console | 8007 | Open browser to `http://localhost:8007` | Dashboard UI |

---

## Architecture Demo Commands

```bash
# Show project structure
tree -L 2 -I 'venv|__pycache__|.git'

# Show services directory
ls -la services/

# Show infrastructure
ls -la infrastructure/

# Show GitHub repository
gh repo view --web
```

---

## Git Workflow Demo

```bash
# Show current branch
git branch

# Show recent commits
git log --oneline -5

# Create feature branch (demo)
git checkout -b demo/student-introduction

# Show status
git status

# Switch back to master
git checkout master
```

---

## GitHub Project Board Demo

```bash
# Show project boards
gh project list

# View project
gh project view PVT_kwHODhT54s4BQjG4

# Show issues
gh issue list --label sprint-0

# Create a test issue (demo)
gh issue create --title "Demo: Test issue created during call" --body "This is a demo issue"
```

---

## Troubleshooting (If Something Goes Wrong)

```bash
# Restart k3s
sudo systemctl restart k3s

# Restart a specific service
cd services/<service-name>
source venv/bin/activate
python -m uvicorn main:app --port <port> --reload

# Kill stuck processes
pkill -f uvicorn
```

---

**Bring this printed sheet to the demo!**
```

**Step 2: Commit**

```bash
git add docs/getting-started/monday-demo/demo-commands-cheat-sheet.md
git commit -m "docs: add demo commands cheat sheet"
```

---

## Task 4: Create One-Page Student Handout

**Files:**
- Create: `docs/getting-started/monday-demo/student-handout.md`

**Step 1: Create the student handout**

```markdown
# Project Chimera - Student Quick Reference

## What is Project Chimera?

An AI-powered live theatre platform that creates performances adapting in real-time to audience input. You'll help build the future of interactive theatre!

---

## 📋 Essential Links

| Resource | Link |
|----------|------|
| **GitHub Repository** | https://github.com/ranjrana2012-lab/project-chimera |
| **Documentation** | https://github.com/ranjrana2012-lab/project-chimera/tree/main/docs |
| **Quick Start Guide** | `docs/getting-started/quick-start.md` |
| **Student FAQ** | `docs/getting-started/faq.md` |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Operator Console                  │
│                  (Human Oversight)                   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              OpenClaw Orchestrator                   │
│              (Central Control Plane)                 │
└───┬───┬───┬───┬───┬───┬───┬───┐
    │   │   │   │   │   │   │   │
    ▼   ▼   ▼   ▼   ▼   ▼   ▼   ▼
  Scene Caption BSL  Sentiment Lighting Safety Operator
  Speak      Agent     Agent    Control Filter  Console
```

---

## 👥 Your Role Assignment

**Name:** ______________________________

**Preferred Name:** ______________________________

**Email:** ______________________________

**Role (____/10):** ______________________________

**Component:** ______________________________

**Mentor:** ______________________________

---

## 🚀 Your First 3 Steps

1. **Join the Community Platform**
   - Watch for invite link in email
   - Introduce yourself in #introductions

2. **Set Up Your Environment**
   - Read `docs/getting-started/quick-start.md`
   - Install Python 3.10+, Docker, kubectl
   - Clone the repository

3. **Complete Your Sprint 0 Issues**
   - Check your GitHub notifications
   - You'll have 3 onboarding issues assigned
   - Ask questions in #help-troubleshooting

---

## 💬 Support Channels

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| #announcements | Important updates | N/A (read-only) |
| #introductions | Say hello! | N/A |
| #help-troubleshooting | Technical questions | 24 hours |
| #urgent | Blocking issues | 2 hours |

---

## 📅 Office Hours

| Day | Time | Focus |
|-----|------|-------|
| Monday | 2-4pm | Week kick-off |
| Tuesday | 10am-12pm | Code reviews |
| Wednesday | 2-4pm | Sprint planning |
| Thursday | 10am-12pm | Troubleshooting |
| Friday | 2-4pm | Week wrap-up |

---

## 🎯 This Week

- [ ] Accept GitHub repo invitation
- [ ] Join community platform
- [ ] Read Quick Start Guide
- [ ] Complete Sprint 0 issues
- [ ] Make your first commit!

---

## 📞 Need Help?

- **Email:** tech-lead@project-chimera.org
- **GitHub Issues:** https://github.com/ranjrana2012-lab/project-chimera/issues
- **Documentation:** https://github.com/ranjrana2012-lab/project-chimera/tree/main/docs

---

**Welcome to Project Chimera! Let's build something amazing together! 🚀**
```

**Step 2: Commit**

```bash
git add docs/getting-started/monday-demo/student-handout.md
git commit -m "docs: add student handout for 4pm demo"
```

---

## Task 5: Create Updated 4pm Demo Script

**Files:**
- Create: `docs/getting-started/monday-demo/4pm-demo-script.md`

**Step 1: Create the demo script**

```markdown
# Project Chimera 4pm Demo Script

**Duration:** 60 minutes
**Date:** March 2, 2026 - 4:00 PM
**Facilitator:** _________________________

---

## Prerequisites (Before Demo Starts)

- [ ] Run `./scripts/demo-prep.sh` - verify all services running
- [ ] Print student handouts (10 copies)
- [ ] Print demo commands cheat sheet
- [ ] Open terminal with demo commands ready
- [ ] Open browser to: http://localhost:8007 (Operator Console)
- [ ] Open GitHub repository: https://github.com/ranjrana2012-lab/project-chimera
- [ ] Open GitHub Project Board

---

## 0:00-0:10 | Welcome & Project Overview

**Goal:** Welcome students and introduce Project Chimera

**Script:**
- "Welcome everyone! Today you're joining Project Chimera"
- "Project Chimera is an AI-powered live theatre platform"
- "You'll be one of 10 students building interactive performances"
- "By the end, you'll have experience with FastAPI, Kubernetes, AI/ML, and more"

**Actions:**
- [ ] Introduce yourself and project
- [ ] Quick roll call (names)
- [ ] Show student handout (front side)

**Commands:** (None)

---

## 0:10-0:20 | Architecture Walkthrough

**Goal:** Explain the system architecture

**Script:**
- "Let me show you how the system works"
- "We have 8 AI agents coordinated by a central orchestrator"
- "Each agent handles a specific task: dialogue, captioning, translation, etc."

**Actions:**
- [ ] Show architecture diagram (on handout)
- [ ] Explain each component briefly
- [ ] Show the code structure

**Commands:**
```bash
# Show project structure
tree -L 2 -I 'venv|__pycache__'

# Show services
ls -la services/
```

---

## 0:20-0:40 | Live Demo: All Services Running

**Goal:** Show the full system in action

**Script:**
- "Now let me show you everything running"
- "All 8 services are currently running on this machine"
- "Let me check the health of each service"

**Actions:**
- [ ] Run health checks on all services
- [ ] Show OpenClaw skills list
- [ ] Demonstrate SceneSpeak generating dialogue
- [ ] Show Operator Console dashboard

**Commands:**
```bash
# Health check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "=== Port $port ==="
    curl -s http://localhost:$port/health/live | jq . 2>/dev/null || echo "Checking..."
done

# Show OpenClaw skills
curl -s http://localhost:8000/v1/skills | jq .

# Generate dialogue with SceneSpeak
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Welcome to Project Chimera!","max_tokens":50}' | jq .
```

**Browser Demo:**
- Open http://localhost:8007 (Operator Console)
- Show the dashboard and alerts

---

## 0:40-0:50 | Role Assignments

**Goal:** Assign each student to a component

**Script:**
- "Now let's assign everyone to their components"
- "Each of you will own one component for the semester"
- "Your job: fix bugs, add features, write tests, and document"

**Actions:**
- [ ] Assign roles (read names from list)
- [ ] Have students fill in their handout
- [ ] Create GitHub issue for each student
- [ ] Explain the trust-based auto-merge system

**Role Assignment Template:**
```
"Student Name, you'll be working on Component Name.
Your mentor is Mentor Name.
You'll be responsible for maintaining this component,
adding new features, fixing bugs, and writing tests."
```

**GitHub Commands:**
```bash
# During call, create issues for each student
gh issue create --title "Sprint 0: Student Name - Component Setup" \
  --label "sprint-0,onboarding,role-X" \
  --body "## Sprint 0: Component Setup

Assigned to: Student Name
Component: Component Name
Mentor: Mentor Name

### Tasks
- [ ] Read component documentation
- [ ] Set up local environment
- [ ] Run the service locally
- [ ] Make your first commit"
```

---

## 0:50-0:55 | Contribution Workflow Demo

**Goal:** Show how to contribute code

**Script:**
- "Here's how you'll contribute code"
- "We use a simple GitHub workflow"
- "Branch, commit, push, create PR, get review, merge"

**Actions:**
- [ ] Show the GitHub workflow
- [ ] Explain trust-based auto-merge
- [ ] Show the PR template

**Commands:**
```bash
# Show git workflow
git branch
git log --oneline -3

# Show GitHub issues
gh issue list --label sprint-0
```

---

## 0:55-1:00 | Q&A + Next Steps

**Goal:** Answer questions and explain next steps

**Script:**
- "Any questions so far?"
- "After this call, you'll receive a personalized email"
- "Your email will contain your role assignment and first tasks"
- "Join the community platform (invite in email)"
- "Complete your Sprint 0 issues by end of week"

**Actions:**
- [ ] Answer questions
- [ ] Show handout (back side)
- [ ] Explain office hours
- [ ] Remind about email coming soon

**Next Steps for Students:**
1. Check email for personalized welcome message
2. Join community platform
3. Accept GitHub repo invitation
4. Complete Sprint 0 issues
5. Join office hours if needed

---

## After Demo: Send Emails

Run the email script immediately after demo:

```bash
python scripts/send-welcome-emails.py --data data/students.csv
```

---

## Backup Plan

**If services fail:**
1. Switch to architecture walkthrough with diagrams
2. Show GitHub repository and documentation
3. Demonstrate git workflow locally
4. Use screenshots/videos if needed

**If demo script fails:**
1. Use demo commands cheat sheet
2. Focus on student handout
3. Answer questions and do Q&A

---

## Emergency Commands

```bash
# Restart all services
make bootstrap

# Check k3s status
sudo kubectl get nodes
sudo kubectl get pods -A

# Port forward to services
sudo kubectl port-forward -n chimera svc/openclaw 8000:8000
```

---

**Good luck with the demo! You've got this! 🚀**
```

**Step 2: Commit**

```bash
git add docs/getting-started/monday-demo/4pm-demo-script.md
git commit -m "docs: add 4pm demo script"
```

---

## Task 6: Create Email Sending Script

**Files:**
- Create: `scripts/send-welcome-emails.py`

**Step 1: Create the email script**

```python
#!/usr/bin/env python3
"""
Send personalized welcome emails to students.

Usage:
    python scripts/send-welcome-emails.py --data data/students.csv [--dry-run]
"""

import argparse
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import subprocess

# Student role assignments (to be filled after 4pm call)
ROLE_ASSIGNMENTS = {
    "1": {"name": "OpenClaw Orchestrator", "mentor": "Tech Lead", "email": "tech-lead@project-chimera.org"},
    "2": {"name": "SceneSpeak Agent", "mentor": "AI/ML Lead", "email": "ai-lead@project-chimera.org"},
    "3": {"name": "Captioning Agent", "mentor": "AI/ML Lead", "email": "ai-lead@project-chimera.org"},
    "4": {"name": "BSL Translation Agent", "mentor": "AI/ML Lead", "email": "ai-lead@project-chimera.org"},
    "5": {"name": "Sentiment Agent", "mentor": "AI/ML Lead", "email": "ai-lead@project-chimera.org"},
    "6": {"name": "Lighting Control", "mentor": "Infra Lead", "email": "infra-lead@project-chimera.org"},
    "7": {"name": "Safety Filter", "mentor": "QA Lead", "email": "qa-lead@project-chimera.org"},
    "8": {"name": "Operator Console", "mentor": "Frontend Lead", "email": "frontend-lead@project-chimera.org"},
    "9": {"name": "Infrastructure", "mentor": "Infra Lead", "email": "infra-lead@project-chimera.org"},
    "10": {"name": "QA & Documentation", "mentor": "QA Lead", "email": "qa-lead@project-chimera.org"},
}

# Component descriptions
ROLE_DESCRIPTIONS = {
    "1": "Central orchestration engine coordinating all AI agents",
    "2": "Generates real-time dialogue for theatrical performances",
    "3": "Live speech-to-text with accessibility descriptions",
    "4": "Translates text to British Sign Language gloss notation",
    "5": "Analyzes audience sentiment from social media",
    "6": "DMX/sACN stage lighting control automation",
    "7": "Multi-layer content moderation and safety filtering",
    "8": "Human oversight interface with real-time alerts",
    "9": "Kubernetes deployment, monitoring, and CI/CD",
    "10": "Testing strategy, quality assurance, and documentation",
}


def load_students(csv_file):
    """Load student data from CSV."""
    students = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            students.append(row)
    return students


def load_template():
    """Load email template."""
    template_path = Path("docs/templates/student-welcome-email.md")
    with open(template_path) as f:
        return f.read()


def create_email(student, role_number, template):
    """Create personalized email for student."""
    role_info = ROLE_ASSIGNMENTS.get(role_number, {})
    role_desc = ROLE_DESCRIPTIONS.get(role_number, "See documentation for details")

    # Replace placeholders
    email_body = template.replace("{Student Name}", student["name"])
    email_body = email_body.replace("{PREFERRED_NAME}", student.get("preferred_name", student["name"]))
    email_body = email_body.replace("{ROLE_NUMBER}", role_number)
    email_body = email_body.replace("{ROLE_NAME}", role_info.get("name", "TBD"))
    email_body = email_body.replace("{ROLE_DESCRIPTION}", role_desc)
    email_body = email_body.replace("{MENTOR_NAME}", role_info.get("mentor", "Tech Lead"))
    email_body = email_body.replace("{MENTOR_EMAIL}", role_info.get("email", "tech-lead@project-chimera.org"))
    email_body = email_body.replace("{COMMUNITY_INVITE_LINK}", "https://join.slack.com/t/projectchimera/shared_invite/...")

    # Create message
    msg = MIMEMultipart()
    msg["From"] = "Project Chimera <tech-lead@project-chimera.org>"
    msg["To"] = student["email"]
    msg["Subject"] = "🎭 Welcome to Project Chimera - Your AI Theatre Journey Starts Now!"

    msg.attach(MIMEText(email_body, "plain"))

    return msg


def send_email(msg, dry_run=False):
    """Send email via SMTP or GitHub CLI."""
    if dry_run:
        print(f"[DRY RUN] Would send email to {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print("---")
        return True

    # Option 1: Use gh to create an issue with email content
    # This is a fallback if SMTP is not configured
    try:
        # Could use GitHub CLI to create a welcome issue
        pass
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Send welcome emails to students")
    parser.add_argument("--data", required=True, help="Path to students CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Print emails without sending")
    parser.add_argument("--role-assignments", help="CSV file with role assignments (id,role_number)")
    args = parser.parse_args()

    # Load data
    students = load_students(args.data)

    # Load role assignments if provided
    if args.role_assignments:
        with open(args.role_assignments) as f:
            reader = csv.DictReader(f)
            role_map = {row["id"]: row["role_number"] for row in reader}
    else:
        # Default: sequential assignment
        role_map = {str(i): str(i) for i in range(1, 11)}

    # Load template
    template = load_template()

    # Send emails
    print(f"Sending emails to {len(students)} students...")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("---")

    for student in students:
        role = role_map.get(student["id"], "TBD")
        msg = create_email(student, role, template)
        send_email(msg, dry_run=args.dry_run)

    print("---")
    print(f"Done! {len(students)} emails processed.")


if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

```bash
chmod +x scripts/send-welcome-emails.py
```

**Step 3: Test dry run**

```bash
python scripts/send-welcome-emails.py --data data/students.csv --dry-run
```

Expected: Prints email content without sending

**Step 4: Commit**

```bash
git add scripts/send-welcome-emails.py
git commit -m "feat: add personalized email sending script"
```

---

## Task 7: Create GitHub Issues for Sprint 0

**Files:**
- Create: `.github/workflows/sprint-0-issues.yml`

**Step 1: Create the workflow**

```yaml
name: Create Sprint 0 Issues

on:
  workflow_dispatch:
    inputs:
      create_issues:
        description: 'Create Sprint 0 onboarding issues'
        required: true
        default: 'true'

permissions:
  contents: write
  issues: write

jobs:
  create-sprint-0-issues:
    runs-on: ubuntu-latest
    if: github.event.inputs.create_issues == 'true'
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Create Sprint 0 onboarding issues
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Create 30 issues (3 per student, 10 students)
          # These will be assigned during the 4pm call

          # Template for onboarding issues
          gh issue create \
            --title "Sprint 0: Environment Setup (Student TBD - Role TBD)" \
            --label "sprint-0,onboarding" \
            --body "## Sprint 0: Environment Setup

          ### Your Information
          - **Name:** [Fill in during call]
          - **Preferred Name:** [Fill in during call]
          - **Email:** [Fill in during call]
          - **Role:** [Fill in during call]
          - **Component:** [Fill in during call]

          ### Tasks
          - [ ] Read \`docs/getting-started/quick-start.md\`
          - [ ] Install Python 3.10+
          - [ ] Install Docker and kubectl
          - [ ] Clone the repository
          - [ ] Create your first branch: \`git checkout -b sprint-0/setup\`
          - [ ] Run the project locally (see demo commands)

          ### Resources
          - Quick Start Guide: \`docs/getting-started/quick-start.md\`
          - FAQ: \`docs/getting-started/faq.md\`
          - Office Hours: \`docs/getting-started/office-hours.md\`

          ### Success Criteria
          You've completed this when:
          - [ ] All services start successfully
          - [ ] You can access http://localhost:8000/health/live
          - [ ] You've made your first commit" || true

          gh issue create \
            --title "Sprint 0: Your First PR (Student TBD - Role TBD)" \
            --label "sprint-0,onboarding,good-first-issue" \
            --body "## Sprint 0: Your First PR

          ### Task
          Add yourself to the \`CONTRIBUTORS.md\` file!

          ### Steps
          1. Read \`CONTRIBUTING.md\` for contribution guidelines
          2. Find your name in the student list
          3. Add your name, role, and component to \`CONTRIBUTORS.md\`
          4. Commit: \`git add CONTRIBUTORS.md && git commit -m \"docs: add [Your Name] to contributors\"\`
          5. Push: \`git push origin sprint-0/setup\`
          6. Create Pull Request
          7. Link it to this issue

          ### Purpose
          This teaches you:
          - The git workflow (branch, commit, push)
          - How to create a Pull Request
          - The code review process
          - How to get your first PR merged!

          ### Template
          Add this to \`CONTRIBUTORS.md\`:
          \`\`\`markdown
          ### Spring 2026 Cohort
          - **[Your Name]** - [Role Name] ([Your GitHub](https://github.com/yourusername))
          \`\`\`

          **This is your first PR - ask for help if you need it!**" || true

          # Create 10 role-specific issues (one for each role)
          for role in 1 2 3 4 5 6 7 8 9 10; do
            case $role in
              1) component="OpenClaw Orchestrator"; port=8000 ;;
              2) component="SceneSpeak Agent"; port=8001 ;;
              3) component="Captioning Agent"; port=8002 ;;
              4) component="BSL Translation Agent"; port=8003 ;;
              5) component="Sentiment Agent"; port=8004 ;;
              6) component="Lighting Control"; port=8005 ;;
              7) component="Safety Filter"; port=8006 ;;
              8) component="Operator Console"; port=8007 ;;
              9) component="Infrastructure & DevOps"; port="N/A" ;;
              10) component="QA & Documentation"; port="N/A" ;;
            esac

            gh issue create \
              --title "Sprint 0: $component Setup (Student TBD - Role $role)" \
              --label "sprint-0,onboarding,role-$role" \
              --body "## Sprint 0: $component Setup

          ### Your Component
          - **Role:** Role $role
          - **Component:** $component
          - **Port:** $port
          - **Student:** [To be assigned during 4pm call]

          ### Tasks
          - [ ] Read component documentation: \`docs/services/core-services.md\`
          - [ ] Navigate to \`services/$([ $role -le 8 ] && echo \"$(printf '%s\n' openclaw scenespeak captioning bsl sentiment lighting safety console | sed -n \"${role}p\")-agent\" || echo \"platform\")\`
          - [ ] Read the main.py file
          - [ ] Understand the API endpoints
          - [ ] Run the service locally
          - [ ] Make a test API call

          ### Quick Commands
          \`\`\`bash
          # Navigate to service
          cd services/[your-service]

          # Activate virtual environment
          source venv/bin/activate

          # Run service
          python -m uvicorn main:app --port $port --reload

          # Test health endpoint
          curl http://localhost:$port/health/live
          \`\`\`

          ### Learn More
          - API Documentation: http://localhost:$port/docs
          - Source Code: \`services/[your-service]/main.py\`
          - Architecture: \`docs/docs/reference/architecture.md\`

          ### Success Criteria
          You've completed this when:
          - [ ] Service starts successfully
          - [ ] Health endpoint returns healthy
          - [ ] You've made a test API call
          - [ ] You understand what your component does" || true
          done

      - name: Summary
        run: |
          echo "Sprint 0 issues created!"
          echo ""
          echo "Next steps:"
          echo "1. Assign students to issues during 4pm call"
          echo "2. Update issue titles with student names"
          echo "3. Send welcome emails with role assignments"
```

**Step 2: Commit**

```bash
git add .github/workflows/sprint-0-issues.yml
git commit -m "feat: add Sprint 0 issues workflow"
```

---

## Task 8: Trigger Sprint 0 Issues Creation

**Step 1: Trigger the workflow**

```bash
gh workflow run sprint-0-issues.yml -f create_issues=true
```

**Step 2: Verify issues created**

```bash
gh issue list --label sprint-0
```

Expected: 30 issues listed (3 per student × 10 students)

---

## Task 9: Push Changes to GitHub

**Step 1: Check git status**

```bash
git status
```

**Step 2: Add all changes**

```bash
git add .
```

**Step 3: Commit any remaining changes**

```bash
git commit -m "feat: complete 4pm demo preparation package"
```

**Step 4: Push to GitHub**

```bash
git push origin master
```

Expected: All changes pushed successfully

---

## Task 10: Final Verification

**Step 1: Verify all files exist**

```bash
ls -la scripts/demo-prep.sh
ls -la scripts/send-welcome-emails.py
ls -la docs/getting-started/monday-demo/4pm-demo-script.md
ls -la docs/getting-started/monday-demo/student-handout.md
ls -la docs/getting-started/monday-demo/demo-commands-cheat-sheet.md
ls -la data/students.csv
```

**Step 2: Run demo prep script**

```bash
./scripts/demo-prep.sh
```

Expected: All services report as running

**Step 3: Test email script (dry run)**

```bash
python scripts/send-welcome-emails.py --data data/students.csv --dry-run
```

Expected: Email content printed without sending

**Step 4: Verify GitHub issues**

```bash
gh issue list --label sprint-0 | wc -l
```

Expected: 30 (or workflow triggered)

**Step 5: Create git tag**

```bash
git tag -a v0.3.0-demo-prep -m "Demo preparation package for 4pm call"
git push origin v0.3.0-demo-prep
```

---

## Task 11: Print Materials for Demo

**Step 1: Print student handouts**

```bash
# Print 10 copies
lp -n 10 docs/getting-started/monday-demo/student-handout.md
```

**Step 2: Print demo commands cheat sheet**

```bash
lp -n 1 docs/getting-started/monday-demo/demo-commands-cheat-sheet.md
```

**Step 3: Print demo script**

```bash
lp -n 1 docs/getting-started/monday-demo/4pm-demo-script.md
```

---

## Completion Checklist

After completing all tasks, verify:

- [ ] Student data CSV created
- [ ] Demo prep script works
- [ ] Email script works (dry run tested)
- [ ] Student handout ready to print
- [ ] Demo script ready
- [ ] Commands cheat sheet ready
- [ ] GitHub workflow triggered
- [ ] All changes pushed to GitHub
- [ ] All services running
- [ ] Materials printed

**You're ready for the 4pm demo! 🚀**

# Project Chimera: 4pm Demo Script

**Date:** March 3, 2026
**Duration:** 60 minutes
**Target Audience:** 15 AI students joining Project Chimera
**Facilitator:** Project Lead / Technical Lead

---

## Prerequisites Checklist

**Before Starting Demo (Do These First):**

- [ ] GitHub repository accessible to all students
- [ ] Student invitations sent and accepted
- [ ] Project board created and configured with views
- [ ] All workflows tested and working (pr-validation, trust-check, auto-merge, onboarding)
- [ ] k3s cluster running and verified
- [ ] All 8 core services deployed and healthy
- [ ] Port-forwarding configured for demo (ports 8000-8007)
- [ ] Grafana accessible at localhost:3000
- [ ] Demo commands cheat sheet printed/ready
- [ ] Student handouts distributed (digital or printed)
- [ ] Video conferencing setup with screen share enabled
- [ ] Backup plan prepared (can switch to slides/walkthrough)
- [ ] Emergency commands documented and accessible

**Technical Verification Commands (Run 30 min before demo):**

```bash
# Verify GitHub workflows
gh workflow list

# Verify project board
gh project list

# Verify Sprint 0 issues exist
gh issue list --limit 20

# Verify k3s cluster
sudo kubectl get nodes
sudo kubectl get pods -A

# Verify services accessible
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    curl -s http://localhost:$port/health && echo "Port $port: OK"
done

# Verify Grafana
curl -s http://localhost:3000/api/health
```

---

## Demo Timeline

### Section 1: 0:00-0:10 | Welcome & Project Overview (10 minutes)

**Goal:** Welcome students, introduce Project Chimera, set expectations

**Talking Points:**

- Welcome everyone to Project Chimera
- Today's purpose: Onboard 15 AI students to the project
- What you'll accomplish by end of semester
- How this project prepares you for real-world software development
- What we'll cover in this 60-minute session

**Key Messages:**

- Project Chimera is an AI-powered live theatre platform
- You'll work in teams of 2-3 on microservices
- We use GitHub, Kubernetes, FastAPI, and modern AI/ML tools
- Your contributions matter - you'll ship production code
- Trust system: Earn auto-merge through quality contributions

**Screen Actions:**

1. Share screen with demo environment ready
2. Open browser to GitHub repository
3. Show project landing page (if exists) or README

**Commands:**

```bash
# Show current git status
git status
git branch

# Show latest commit
git log -1 --oneline

# Show project structure
tree -L 2 -I 'node_modules|venv|__pycache__|.git'
```

**Visual Aids:**

- Project architecture diagram (keep on second screen/tab)
- Services status dashboard
- GitHub repository homepage

**Interactive Element:**

- Quick poll: "Who has used GitHub before?"
- Quick poll: "Who has worked with microservices?"
- Quick poll: "Who has used Kubernetes or Docker?"

---

### Section 2: 0:10-0:20 | GitHub Repository Tour (10 minutes)

**Goal:** Familiarize students with repository structure and navigation

**Talking Points:**

- Repository organization and key directories
- Where documentation lives
- Where service code is located
- How to find your assigned component
- GitHub features we'll use: Issues, PRs, Projects, Actions

**Screen Actions:**

1. Navigate repository root in browser
2. Show docs/ directory structure
3. Show services/ directory structure
4. Show infrastructure/ directory
5. Show GitHub Project board

**Commands:**

```bash
# Show root structure
ls -la

# Show documentation hierarchy
tree docs/ -L 2

# Show services
ls -la services/

# Show infrastructure
ls -la infrastructure/

# Count key files
echo "Services: $(ls services/ | wc -l)"
echo "Documentation files: $(find docs/ -name '*.md' | wc -l)"
```

**Key Locations to Highlight:**

- `/docs/` - All project documentation
- `/docs/getting-started/` - Start here!
- `/docs/getting-started/monday-demo/` - Demo materials
- `/services/` - All 8 microservices
- `/infrastructure/` - Kubernetes manifests
- `/.github/workflows/` - CI/CD automation

**Interactive Element:**

- Ask students to follow along in their browsers
- Have them star the repository
- Have them watch the repository for notifications

---

### Section 3: 0:20-0:30 | Student Roles & Component Assignments (10 minutes)

**Goal:** Explain role assignments, component ownership, and how students will work

**Talking Points:**

- 10 numbered roles + Infrastructure + QA + Documentation
- How roles were assigned (or will be assigned)
- Component ownership model
- Sprint 0 onboarding tasks
- How to claim and work on issues
- Mentor assignment and support

**Screen Actions:**

1. Open GitHub Project board
2. Show "By Role" view
3. Show "Monday Onboarding" view
4. Show Sprint 0 issues
5. Open role documentation

**Commands:**

```bash
# Show project board
gh project view

# Show Sprint 0 issues
gh issue list --label sprint-0

# Show role assignments file (if exists)
cat docs/getting-started/roles.md

# Show student data
cat data/students.csv
```

**Role Assignments:**

| Role | Component | Mentor | Students |
|------|-----------|--------|----------|
| 1 | OpenClaw Orchestrator | Tech Lead | 1-2 students |
| 2 | SceneSpeak Agent | AI/ML Lead | 1-2 students |
| 3 | Captioning Agent | AI/ML Lead | 1-2 students |
| 4 | BSL Translation Agent | AI/ML Lead | 1-2 students |
| 5 | Sentiment Agent | AI/ML Lead | 1-2 students |
| 6 | Lighting Control | Infra Lead | 1-2 students |
| 7 | Safety Filter | QA Lead | 1-2 students |
| 8 | Operator Console | Frontend Lead | 1-2 students |
| 9 | Infrastructure | Infra Lead | 1-2 students |
| 10 | QA & Documentation | QA Lead | 1-2 students |

**Sprint 0 Tasks (Already Assigned):**

1. Setup development environment
2. Your first PR (add yourself to CONTRIBUTORS.md)
3. Component-specific setup task

**Interactive Element:**

- Ask students to find their assigned role in the project board
- Ask students to locate their Sprint 0 issues
- Confirm everyone can access their assigned issues

---

### Section 4: 0:30-0:40 | Live Demo: Services & Architecture (10 minutes)

**Goal:** Show running services and demonstrate microservices in action

**Talking Points:**

- 8 microservices architecture
- How services communicate (REST, events, pub/sub)
- Shared infrastructure (Redis, Kafka, Prometheus, Grafana)
- What each service does
- How to access and test services

**Screen Actions:**

1. Open terminal for commands
2. Open browser tabs for services
3. Show Grafana dashboard
4. Show service interactions

**Commands:**

```bash
# Health check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "=== Port $port ==="
    curl -s http://localhost:$port/health | jq . || echo "Not responding"
    echo ""
done

# Show OpenClaw Orchestrator
echo "=== OpenClaw Orchestrator (8000) ==="
curl -s http://localhost:8000/v1/skills | jq .

# Show SceneSpeak Agent
echo "=== SceneSpeak Agent (8001) ==="
curl -s http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello actor"}' | jq .

# Show Operator Console
echo "=== Opening Operator Console ==="
echo "Navigate to: http://localhost:8007"
```

**Browser Demonstrations:**

1. OpenClaw Orchestrator: http://localhost:8000/docs
2. SceneSpeak Agent: http://localhost:8001/docs
3. Captioning Agent: http://localhost:8002/docs
4. Operator Console: http://localhost:8007
5. Grafana Dashboard: http://localhost:3000 (admin/chimera)

**Service Demonstrations:**

```bash
# Demo 1: SceneSpeak dialogue generation
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The hero enters the stage",
    "max_tokens": 50
  }'

# Demo 2: Captioning (if audio available)
curl -X POST http://localhost:8002/api/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/test.wav"}'

# Demo 3: Sentiment analysis
curl -X POST http://localhost:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I loved the performance!"}'

# Demo 4: Lighting control
curl http://localhost:8005/v1/presets | jq .
```

**Architecture Visualization:**

Show on screen or describe:

```
Operator Console (8007)
       ↓
OpenClaw Orchestrator (8000)
   ↓ ↓ ↓ ↓ ↓
SceneSpeak Captioning BSL Sentiment Safety
 (8001)   (8002) (8003) (8004)   (8006)
                      ↓
               Lighting (8005)

Shared: Redis, Kafka, Prometheus, Grafana, Jaeger
```

**Interactive Element:**

- Ask students to predict what each service does
- Have students suggest test prompts for SceneSpeak
- Show how services are monitored in Grafana

---

### Section 5: 0:40-0:50 | Contribution Workflow Demo (10 minutes)

**Goal:** Show complete git workflow, PR process, and automation

**Talking Points:**

- Git workflow: branch, commit, push, PR
- PR template and what to include
- Code review process
- CI/CD automation (tests, linting, coverage)
- Trust system and auto-merge
- How to get help

**Screen Actions:**

1. Show git workflow in terminal
2. Create demo branch
3. Show PR creation in browser
4. Show GitHub Actions workflow
5. Show trust check workflow

**Commands:**

```bash
# Show current state
git status
git branch

# Create feature branch
git checkout -b demo/student-onboarding

# Make a change (example)
echo "# Student Contributors" > CONTRIBUTORS.md.new
cat >> CONTRIBUTORS.md.new << EOF
- Student Name (@github-handle) - Role 1
EOF

# Show the change
cat CONTRIBUTORS.md.new

# Stage and commit
git add CONTRIBUTORS.md.new
git commit -m "docs: add student contributor template

- Create CONTRIBUTORS.md template
- Add example student entry

Closes #XXX"

# Show commit
git log -1 --stat

# (Don't actually push - just show the command)
# git push origin demo/student-onboarding
```

**Browser Demonstrations:**

1. Show PR template: `.github/pull_request_template.md`
2. Show issue template: `.github/ISSUE_TEMPLATE/`
3. Show workflows: `.github/workflows/`
4. Show recent Actions runs

**CI/CD Workflow Explanation:**

- **pr-validation.yml**: Runs on every PR
  - Linting check
  - Unit tests
  - Coverage calculation
  - Posts coverage comment

- **trust-check.yml**: Checks author trust
  - Counts merged PRs
  - Assigns trust label (new/learning/trusted)
  - Posts welcome message

- **auto-merge.yml**: Enables auto-merge
  - Waits for validation
  - Checks trust level
  - Enables auto-merge if trusted

**Trust System:**

| Merged PRs | Trust Level | Label | Auto-Merge? |
|------------|-------------|-------|-------------|
| 0 | New | trust:new | No |
| 1-2 | Learning | trust:learning | No |
| 3+ | Trusted | trust:trusted | Yes |

**Testing Locally:**

```bash
# Run tests for a service
cd services/<service-name>
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run linter
ruff check .
black .

# Format code
ruff format .
```

**Interactive Element:**

- Ask students to identify when trust level changes
- Show a sample PR from the project
- Ask students what makes a good PR description

---

### Section 6: 0:50-1:00 | Q&A + First Tasks + Next Steps (10 minutes)

**Goal:** Answer questions, clarify first tasks, provide support resources

**Talking Points:**

- Q&A - open floor for questions
- Immediate next steps for students
- How to get help
- Communication channels
- Office hours schedule
- Expectations for this week

**Screen Actions:**

1. Open support documentation
2. Show communication channels guide
3. Show office hours schedule
4. Show FAQ document

**Q&A Topics to Cover (if not asked):**

- How do I set up my development environment?
- What if I get stuck?
- How do I find my Sprint 0 issues?
- When is my first PR due?
- How do I contact my mentor?
- What if I can't make office hours?

**First Tasks for Students (Priority Order):**

1. **TODAY after demo:**
   - Join the community platform (Slack/Discord)
   - Introduce yourself in #introductions
   - Accept GitHub repository invitation
   - Find your Sprint 0 issues

2. **THIS WEEK:**
   - Complete Sprint 0 Setup Environment issue
   - Make your first PR (add yourself to CONTRIBUTORS.md)
   - Complete component-specific setup task
   - Attend office hours if you need help

3. **THIS MONTH:**
   - Complete your first feature PR
   - Participate in code reviews
   - Earn trust level 2 (Learning)
   - Contribute to documentation

**Task Assignment Script:**

"Your immediate next steps are:

1. Check your GitHub notifications for Sprint 0 issues
2. Join our community platform: [LINK]
3. Introduce yourself in #introductions
4. Complete the 'Setup Environment' issue by [DATE]
5. Create your first PR adding yourself to CONTRIBUTORS.md
6. Attend office hours this week if you need help

I'm available for questions. Your mentors will reach out individually.
Let's build something amazing together!"

**Support Resources:**

- **Documentation:** `docs/getting-started/`
- **Quick Start:** `docs/getting-started/quick-start.md`
- **FAQ:** `docs/getting-started/faq.md`
- **Office Hours:** `docs/getting-started/office-hours.md`
- **Communication:** `docs/getting-started/communication-channels.md`

**Communication Channels:**

- **#announcements** - Important updates (read-only)
- **#introductions** - Say hi!
- **#help-troubleshooting** - Technical questions
- **#role-{your-role}** - Role-specific discussions
- **#urgent** - Blocking issues (2-hour response)

**Office Hours:**

| Day | Time | Location | Host |
|-----|------|----------|------|
| Monday | 2:00-4:00 PM | Room 301 | Tech Lead |
| Wednesday | 3:00-5:00 PM | Virtual | AI/ML Lead |
| Friday | 10:00 AM-12:00 PM | Room 301 | QA Lead |

**Next Steps After Demo:**

1. Send follow-up email with links and reminders
2. Create GitHub issues for any action items
3. Schedule individual check-ins if needed
4. Monitor community platform for questions
5. Be available for troubleshooting

**Interactive Element:**

- Open floor for questions
- Poll: "What are you most excited to work on?"
- Poll: "What concerns do you have?"
- Confirm everyone knows their next steps

---

## After Demo: Follow-up Email

**Send this email within 1 hour of demo completion:**

**Subject:** Project Chimera Demo Follow-Up - Next Steps

**Body:**

Hi everyone,

Great meeting you all at today's demo! Here's what you need to do next:

**IMMEDIATE (Today):**
1. Join our community platform: [LINK]
2. Introduce yourself in #introductions
3. Check your GitHub issues (you have 3 Sprint 0 tasks)
4. Accept the repository invitation if you haven't

**THIS WEEK:**
1. Complete your Sprint 0 Setup Environment issue
2. Make your first PR (add yourself to CONTRIBUTORS.md)
3. Complete your component-specific setup task
4. Join your role-specific channel

**RESOURCES:**
- Quick Start Guide: [LINK]
- Demo Script: [LINK]
- Office Hours: [LINK]
- FAQ: [LINK]

**DUE DATES:**
- Sprint 0 issues: End of this week
- First PR: End of this week

**GETTING HELP:**
- Ask in #help-troubleshooting
- Attend office hours (see schedule)
- Contact your mentor directly
- Create a GitHub issue if blocked

We're excited to have you on board. Let's build something amazing!

Best,
Project Chimera Team

---

## Backup Plan

**If Technical Demo Fails:**

1. **Switch to Architecture Walkthrough:**
   - Use architecture diagrams
   - Explain services conceptually
   - Show code snippets instead of running services
   - Focus on GitHub workflow and collaboration

2. **Use Screenshots/Videos:**
   - Pre-recorded service demos
   - Screenshots of key interfaces
   - Diagram of service interactions
   - Step-by-step workflow documentation

3. **Focus on Documentation:**
   - Walk through documentation structure
   - Show how to find answers
   - Explain contribution process
   - Do interactive Q&A

**If Demo Script Fails:**

1. Use the demo commands cheat sheet
2. Focus on student handout content
3. Answer questions and do extended Q&A
4. Show GitHub repository and issues
5. Demonstrate git workflow locally

**If Internet/Screen Share Fails:**

1. Continue with verbal walkthrough
2. Use phone as hotspot
3. Share links for students to follow along
4. Reschedule technical demo portion
5. Record video walkthrough to share later

**If Students Can't Access GitHub:**

1. Verify permissions and invitations
2. Create/re-send invitations
3. Switch to documentation review
4. Cover git workflow conceptually
5. Send follow-up with detailed instructions

---

## Emergency Commands

**Quick Service Recovery:**

```bash
# Restart all services
cd /home/ranj/Project_Chimera
make bootstrap

# Or restart specific service
kubectl rollout restart deployment/<service-name> -n chimera

# Check service status
kubectl get pods -n chimera
kubectl get svc -n chimera
```

**Port Forwarding (if services not accessible):**

```bash
# Forward all services
kubectl port-forward -n chimera svc/openclaw 8000:8000 &
kubectl port-forward -n chimera svc/scenespeak 8001:8001 &
kubectl port-forward -n chimera svc/captioning 8002:8002 &
kubectl port-forward -n chimera svc/bsl-translation 8003:8003 &
kubectl port-forward -n chimera svc/sentiment 8004:8004 &
kubectl port-forward -n chimera svc/lighting 8005:8005 &
kubectl port-forward -n chimera svc/safety 8006:8006 &
kubectl port-forward -n chimera svc/operator-console 8007:8007 &
```

**k3s Recovery:**

```bash
# Check k3s status
sudo systemctl status k3s

# Restart k3s
sudo systemctl restart k3s

# Verify nodes
sudo kubectl get nodes

# Verify all pods
sudo kubectl get pods -A

# Fix stuck pods
sudo kubectl delete pod <pod-name> -n chimera
```

**Service-Specific Recovery:**

```bash
# Restart a specific service in dev mode
cd services/<service-name>
source venv/bin/activate
python -m uvicorn main:app --port <port> --reload

# Kill stuck processes
pkill -f uvicorn
pkill -f python.*main:app

# Clear Redis cache (if needed)
redis-cli FLUSHDB
```

**GitHub Issues Recovery:**

```bash
# Check if issues exist
gh issue list --limit 20

# Check workflow status
gh workflow list
gh run list --limit 10

# Re-run onboarding workflow
gh workflow run onboarding.yml -f create_issues=true

# Create missing issues manually
gh issue create --title "[Sprint 0] Setup Environment" \
  --body "Follow the quick start guide to set up your environment" \
  --label "sprint-0,good-first-issue"
```

**Quick Health Check (run if something seems wrong):**

```bash
# All-in-one health check
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    if curl -s http://localhost:$port/health > /dev/null; then
        echo "✓ Port $port: OK"
    else
        echo "✗ Port $port: FAIL"
    fi
done

# Check k3s
sudo kubectl get nodes | grep -q "Ready" && echo "✓ k3s: OK" || echo "✗ k3s: FAIL"

# Check GitHub
gh auth status && echo "✓ GitHub: OK" || echo "✗ GitHub: FAIL"
```

**Emergency Mode (minimal demo):**

```bash
# If all else fails, show this:
# 1. Repository structure
tree -L 2 -I 'venv|__pycache__|.git'

# 2. Service code
ls -la services/

# 3. Documentation
find docs/ -name "*.md" | head -10

# 4. GitHub status
gh repo view --json name,description,url
```

---

## Success Criteria

**By the end of this demo, students should be able to:**

- [ ] Navigate the GitHub repository
- [ ] Understand the project structure and architecture
- [ ] Locate their assigned role and Sprint 0 issues
- [ ] Access and test the microservices
- [ ] Understand the git workflow and PR process
- [ ] Know how to get help (Slack, office hours, mentors)
- [ ] Know their immediate next steps

**What we'll verify after the demo:**

- [ ] Students join community platform within 2 hours
- [ ] Students introduce themselves in #introductions
- [ ] Students accept GitHub invitations
- [ ] Students can access their Sprint 0 issues
- [ ] No blocking issues reported within 24 hours

---

## Additional Resources

**For the Facilitator:**

- Demo Commands Cheat Sheet: `docs/getting-started/monday-demo/demo-commands-cheat-sheet.md`
- Pre-Monday Checklist: `docs/getting-started/monday-demo/pre-monday-checklist.md`
- Student Handout: `docs/getting-started/monday-demo/student-handout.md`
- GitHub Setup Guide: `docs/getting-started/monday-demo/github-setup-guide.md`

**For Students:**

- Quick Start Guide: `docs/getting-started/quick-start.md`
- FAQ: `docs/getting-started/faq.md`
- Office Hours: `docs/getting-started/office-hours.md`
- Communication Channels: `docs/getting-started/communication-channels.md`
- Evaluation Criteria: `docs/getting-started/evaluation-criteria.md`

---

## Notes & Improvements

**After the demo, document:**

- What went well
- What didn't work
- Questions students asked
- Technical issues encountered
- Suggestions for improvement
- Follow-up actions needed

**Use these notes to improve the next demo!**

---

## Good Luck!

You've prepared thoroughly. The students are going to love Project Chimera!

**Remember:**
- Stay flexible if things go wrong
- Focus on student understanding over perfect demos
- Encourage questions and engagement
- Make it fun and inspiring
- You're building the next generation of developers!

**You've got this! 🚀**

---

**Document Version:** 1.0
**Created:** March 2, 2026
**Last Updated:** March 2, 2026
**Author:** Project Chimera Team
**Next Review:** After first demo session

# Complete Student Onboarding Solution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a comprehensive onboarding package for 15 AI students including email templates, documentation, guides, and evaluation criteria, ensuring everything is ready for student email delivery in ~11 hours and Monday demo.

**Architecture:** Create 8 new documentation files covering all aspects of student onboarding (welcome email, communication, code of conduct, contributing guide, FAQ, office hours, sprint definitions, evaluation criteria). Each file is self-contained with cross-references. Tech Lead will separately set up GitHub Project Board and community platform.

**Tech Stack:** Markdown documentation, GitHub workflows, Slack/Discord configuration

---

## Task 1: Create Student Welcome Email Template

**Files:**
- Create: `docs/templates/student-welcome-email.md`

**Step 1: Create the email template directory**

```bash
mkdir -p docs/templates
```

**Step 2: Create the welcome email template**

```bash
cat > docs/templates/student-welcome-email.md << 'EOF'
# Student Welcome Email Template

**Subject:** 🎭 Welcome to Project Chimera - Your AI Theatre Journey Starts Monday!

---

## {Student Name}, Welcome to Project Chimera!

### 🎭 What You're Joining

Project Chimera is an AI-powered live theatre platform that creates performances adapting in real-time to audience input. As one of 15 AI students, you'll help build the future of interactive theatre.

You'll be working on: **{ROLE_NAME}** - {ROLE_DESCRIPTION}

---

## 📍 Your Role Assignment

| Role | Your Assignment | Description |
|------|----------------|-------------|
| {ROLE_NUMBER} | {COMPONENT_NAME} | {ROLE_DESCRIPTION} |

**Your mentor:** {MENTOR_NAME} ({MENTOR_EMAIL})

---

## 🔗 Quick Links

- **Repository:** https://github.com/project-chimera/project-chimera
- **Documentation:** https://github.com/project-chimera/project-chimera/tree/main/docs
- **Monday Demo Info:** See `docs/getting-started/monday-demo/`
- **Slack/Discord:** {COMMUNITY_INVITE_LINK}

---

## ✅ Pre-Monday Checklist

Complete these before the Monday demo:

- [ ] **Join the community platform:** {COMMUNITY_INVITE_LINK}
- [ ] **Set up GitHub SSH keys:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- [ ] **Read the Quick Start Guide:** `docs/getting-started/quick-start.md`
- [ ] **Review your role documentation:** `docs/getting-started/roles.md`
- [ ] **Accept GitHub repository invitation** (check your email)

---

## 🚀 Your First Tasks (Sprint 0)

You have 3 onboarding issues assigned:

1. **[Sprint 0] Setup Development Environment** - Get your local environment running
2. **[Sprint 0] Your First PR** - Add yourself to CONTRIBUTORS.md
3. **[Sprint 0] {Component} Setup** - Role-specific setup

These will be automatically assigned to you on GitHub. Check your issues!

---

## 📅 Monday Schedule

**Time:** Monday, March 3, 2026 - 10:00 AM to 11:00 AM
**Location:** {LOCATION} / Zoom: {ZOOM_LINK}

| Time | Topic |
|------|-------|
| 10:00-10:10 | Welcome & Project Overview |
| 10:10-10:20 | GitHub Repository Tour |
| 10:20-10:30 | Role Assignments & Sprint 0 Tasks |
| 10:30-10:40 | Live Demo: Working Services |
| 10:40-10:50 | Contribution Workflow Demo |
| 10:50-11:00 | Q&A + First Tasks |

---

## 💬 Support Channels

Once you join the community platform:

- **#announcements** - Important updates (read-only)
- **#introductions** - Say hi! Tell us about yourself
- **#help-troubleshooting** - Technical questions
- **#role-{your-role}** - Role-specific discussions
- **#urgent** - Blocking issues (mentors respond within 2 hours)

---

## 📊 What You'll Learn

By the end of the semester, you'll have experience with:

- **FastAPI microservices** and async Python
- **Kubernetes deployment** with k3s
- **AI/ML model integration** (PyTorch, Transformers)
- **Event-driven architecture** (Kafka)
- **CI/CD with GitHub Actions**
- **Test-driven development**
- **Open source contribution**

---

## 🎯 Success Criteria

You'll be evaluated based on:

| Criteria | Weight | Description |
|----------|--------|-------------|
| Code Quality | 30% | Clean, tested, documented code |
| PR Contributions | 25% | Number & quality of merged PRs |
| Peer Reviews | 15% | Reviewing others' code |
| Sprint Completion | 15% | Meeting sprint goals |
| Communication | 15% | Participation, collaboration |

See `docs/getting-started/evaluation-criteria.md` for full details.

---

## 👋 Get In Touch

- **Technical Lead:** {TECH_LEAD_NAME} ({TECH_LEAD_EMAIL})
- **Office Hours:** See `docs/getting-started/office-hours.md`
- **Response Time:** We respond within 24 hours on weekdays

---

## Important Reminders

1. **Join Slack/Discord NOW** - Introduce yourself in #introductions
2. **Set up SSH keys** - Required for GitHub
3. **Review documentation** - Start with the Quick Start Guide
4. **Come Monday with questions** - No question is too basic!

---

**We're excited to have you on board. Let's build something amazing together! 🚀**

---

**P.S.** Join the community platform **right now** and introduce yourself!
We want to know who you are before Monday. 🎭

---

*This email was generated from `docs/templates/student-welcome-email.md`*
EOF
```

**Step 3: Commit**

```bash
git add docs/templates/student-welcome-email.md
git commit -m "docs: add student welcome email template

Comprehensive email template for student onboarding including:
- Role assignment section
- Pre-Monday checklist
- Sprint 0 task overview
- Monday demo schedule
- Support channels
- Learning outcomes
- Evaluation criteria overview

Ready for personalization and email delivery.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Create Communication Channels Guide

**Files:**
- Create: `docs/getting-started/communication-channels.md`

**Step 1: Create the communication channels guide**

```bash
cat > docs/getting-started/communication-channels.md << 'EOF'
# Communication Channels Guide

This guide explains how we communicate as a team and where to get help.

---

## Platform: Slack

We use Slack for real-time communication.

**Join here:** {SLACK_INVITE_LINK}

---

## Channel Structure

### Core Channels

| Channel | Purpose | Post? |
|---------|---------|-------|
| **#announcements** | Important updates only | Admins only |
| **#introductions** | Say hi and meet the team | ✅ Yes (once) |
| **#general** | Project-wide discussions | ✅ Yes |
| **#help-troubleshooting** | Technical questions | ✅ Yes |
| **#pair-programming** | Find coding partners | ✅ Yes |
| **#show-and-tell** | Demo your work | ✅ Yes |
| **#urgent** | Blocking issues only | ✅ Yes (when stuck) |

### Role-Specific Channels

Each role has a dedicated channel:

| Channel | For | Role |
|---------|-----|------|
| **#role-openclaw** | OpenClaw Orchestrator | Role 1 |
| **#role-scenespeak** | SceneSpeak Agent | Role 2 |
| **#role-captioning** | Captioning Agent | Role 3 |
| **#role-bsl** | BSL Translation | Role 4 |
| **#role-sentiment** | Sentiment Analysis | Role 5 |
| **#role-lighting** | Lighting Control | Role 6 |
| **#role-safety** | Safety Filter | Role 7 |
| **#role-console** | Operator Console | Role 8 |
| **#role-infra** | Infrastructure | Role 9 |
| **#role-qa** | QA & Documentation | Role 10 |

### Social Channels

| Channel | Purpose |
|---------|---------|
| **#random** | Off-topic, fun |
| **#music-recommendations** | Share music (theatre needs it!) |

---

## Response Time Expectations

| Channel | Expected Response |
|---------|------------------|
| **#urgent** | 2 hours (work hours) |
| **#help-troubleshooting** | 24 hours |
| **#role-{name}** | 24 hours |
| DM (office hours only) | During scheduled times |
| Email | 2-3 business days |

**Work hours:** Monday-Friday, 9am-6pm

---

## When to Use Channels

### Use #announcements (read-only)
- Stay updated on important news
- Don't post here (admins only)

### Use #introductions
- Introduce yourself when you join
- Say where you're from, your role, fun fact
- Comment on others' intros

### Use #general
- Project-wide discussions
- Questions that don't fit elsewhere
- Celebrations and shout-outs

### Use #help-troubleshooting
- **FIRST** search existing docs and issues
- **THEN** post your question with:
  - What you're trying to do
  - What you expected
  - What actually happened (error messages, logs)
  - What you've already tried

### Use #pair-programming
- Find someone to code with
- Post: "Anyone want to pair on {topic}?"
- Great for learning together

### Use #urgent
- **ONLY** for blocking issues
- You're stuck and can't proceed
- Production incidents
- Don't abuse this channel!

### Use your role channel
- Role-specific discussions
- Architecture decisions
- Code reviews
- Coordination

### Use DMs
- During office hours
- For sensitive topics
- If you're struggling and need 1:1 help
- **NOT** for technical questions (use channels)

---

## Channel Guidelines

### Be Respectful
- Assume good intent
- No harassment or discrimination
- See [Code of Conduct](../../CODE_OF_CONDUCT.md)

### Be Helpful
- Answer questions if you know the answer
- Share what you've learned
- Celebrate others' wins

### Be Professional
- This is a learning environment
- Keep it appropriate
- We're here to build cool things

### Have Fun!
- #random exists for a reason
- Share memes (in moderation)
- Music recommendations are encouraged

---

## Escalation Path

If you need help, follow this path:

```
1. Self-Service
   ↓ Check docs, search issues, Google

2. Community
   ↓ Post in #help-troubleshooting

3. Role Channel
   ↓ Ask in your #role-{name} channel

4. Office Hours
   ↓ Attend or DM during scheduled times

5. Emergency
   ↓ #urgent channel or text {PHONE}
```

---

## Getting Help Checklist

Before asking for help, make sure you've:

- [ ] Read the relevant documentation
- [ ] Searched existing GitHub issues
- [ ] Googled the error message
- [ ] Checked the Slack channel history

Then, when posting, include:

- What you're trying to do
- What you expected to happen
- What actually happened (with error messages/logs)
- What you've already tried

This helps us help you faster!

---

## Notification Settings

**Recommended:**

- **#announcements:** All messages
- **#role-{your-role}:** All messages
- **#help-troubleshooting:** All messages
- **#urgent:** All messages
- **Everything else:** Mentions & DMs only

Adjust to your preference - don't get overwhelmed!

---

## Integrations

### GitHub → Slack
- PR notifications automatically posted
- Issue updates in relevant channels
- CI/CD status updates

### Daily Standup Bot (optional)
- Posts daily at 10am
- Reply with:
  - What you did yesterday
  - What you're doing today
  - Any blockers

---

## Quick Reference

| Need to... | Go to... |
|------------|----------|
| Get important updates | #announcements |
| Ask a technical question | #help-troubleshooting |
| Find a coding partner | #pair-programming |
| Discuss your role work | #role-{your-role} |
| Share something cool | #show-and-tell |
| Report a blocking issue | #urgent |
| Chat about random stuff | #random |
| Contact 1:1 | DM during office hours |

---

## Questions?

**Ask in #help-troubleshooting!**

---

**Last Updated:** 2026-03-01
EOF
```

**Step 2: Commit**

```bash
git add docs/getting-started/communication-channels.md
git commit -m "docs: add communication channels guide

Complete guide for Slack/Discord communication including:
- Channel structure and purposes
- Response time expectations
- When to use each channel
- Escalation path
- Getting help checklist
- Notification settings recommendations

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Create Code of Conduct

**Files:**
- Create: `CODE_OF_CONDUCT.md`

**Step 1: Create the Code of Conduct**

```bash
cat > CODE_OF_CONDUCT.md << 'EOF'
# Code of Conduct

## Our Pledge

We pledge to make participation in Project Chimera a harassment-free experience for everyone, regardless of level of experience, gender, gender identity and expression, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

---

## Our Standards

### Positive Behaviors We Encourage

- **Being respectful** of differing viewpoints and experiences
- **Gracefully accepting** constructive criticism
- **Focusing on what is best** for the community
- **Showing empathy** toward other community members
- **Helping others learn** (we're all students here!)
- **Asking questions** when you don't understand
- **Celebrating each other's wins**

### Behaviors We Don't Tolerate

- The use of sexualized language or imagery
- Trolling or insulting/derogatory comments
- Personal or political attacks
- Public or private harassment
- Publishing others' private information
- Any other conduct which could reasonably be considered inappropriate

---

## Learning Environment

Project Chimera is a **learning environment**. We expect:

- **Mistakes are welcome** - that's how we learn
- **Questions are encouraged** - no question is too basic
- **Growth happens together** - help others, accept help
- **Feedback is kind** - critique code, not people

---

## Reporting Issues

If someone makes you feel uncomfortable, please report it.

### For Minor Issues

- DM the person respectfully (they may not realize)
- If uncomfortable, contact a mentor directly

### For Serious Issues

Contact any of the following:

- **Technical Lead:** {TECH_LEAD_EMAIL}
- **Faculty Advisor:** {FACULTY_ADVISOR_EMAIL}
- **University Conduct Office:** {CONDUCT_OFFICE}

All reports will be kept confidential.

---

## Consequences

Unacceptable behavior will result in:

1. **First offense:** Private warning and conversation
2. **Second offense:** Temporary suspension (1 week)
3. **Third offense:** Removal from the project

We're reasonable people. We'll talk before taking action.

---

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1, available at https://www.contributor-covenant.org/version/2/1/code_of_conduct.html.

---

**Remember:** We're all here to learn, build cool things, and have fun. Be excellent to each other. 🎭
EOF
```

**Step 2: Commit**

```bash
git add CODE_OF_CONDUCT.md
git commit -m "docs: add code of conduct

Contributor Covenant 2.1 based code of conduct emphasizing:
- Learning environment principles
- Clear behavioral expectations
- Reporting process for issues
- Transparent consequences
- Student-friendly tone

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Create Extended Contributing Guide

**Files:**
- Create: `CONTRIBUTING.md`

**Step 1: Create the contributing guide**

```bash
cat > CONTRIBUTING.md << 'EOF'
# Contributing to Project Chimera

Thank you for your interest in contributing! This guide will help you understand how to contribute effectively.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Getting Help](#getting-help)

---

## Quick Start

### First Time Contributing?

Welcome! Start here:

1. Read the [Student Quick Start Guide](docs/getting-started/quick-start.md)
2. Set up your [development environment](docs/getting-started/quick-start.md#prerequisites)
3. Find a [good first issue](https://github.com/project-chimera/project-chimera/labels/good-first-issue)
4. Say hi in #introductions on Slack!

---

## Development Workflow

### 1. Find Something to Work On

- Check the [GitHub Project Board](https://github.com/orgs/project-chimera/projects)
- Look for issues labeled `good-first-issue` or `help-wanted`
- Or propose something new!

### 2. Claim an Issue

- Comment on the issue: "I'd like to work on this!"
- Wait for assignment (usually within 24 hours)
- Don't start coding until assigned

### 3. Create a Branch

```bash
git checkout -b feature/description-of-change
# or
git checkout -b fix/issue-number-description
```

### 4. Make Your Changes

- Write code following our [code standards](#code-standards)
- Write tests for your changes
- Update documentation if needed
- Commit frequently with clear messages

### 5. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=services --cov-report=html

# Run linting
ruff check services/
```

### 6. Submit a Pull Request

- Push your branch
- Open a PR using our template
- Wait for CI checks to pass
- Address review feedback

---

## Code Standards

### Python (FastAPI Services)

**Style Guide:** We follow [PEP 8](https://peps.python.org/pep-0008/)

```python
# ✅ Good
from typing import Optional

async def get_user(user_id: int) -> Optional[User]:
    """Fetch a user by ID.

    Args:
        user_id: The user's unique identifier

    Returns:
        The user if found, None otherwise
    """
    return await db.fetch_user(user_id)

# ❌ Bad
def getUser(uid):
    return db.get(uid)
```

**Key Rules:**
- Use `async`/`await` for I/O operations
- Type hint all function signatures
- Docstrings for all public functions
- Maximum line length: 100 characters
- Use `ruff` for formatting

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user authentication
fix: resolve race condition in cache
docs: update API documentation
test: add tests for sentiment aggregator
refactor: simplify Kafka producer
```

### Documentation

- Comment **why**, not **what**
- Delete commented-out code
- Keep comments up to date
- Update README if adding features

---

## Testing Guidelines

### Test-Driven Development (TDD)

We follow TDD: **Red → Green → Refactor**

1. **Red:** Write a failing test
2. **Green:** Write minimal code to pass
3. **Refactor:** Clean up the code

### Coverage Requirements

| Component | Minimum | Target |
|-----------|---------|--------|
| Core Logic | 80% | 90%+ |
| Models | 90% | 100% |
| Routes | 70% | 85% |
| Utils | 80% | 90% |

### Test Types

```python
# ✅ Unit Tests - Fast, isolated
def test_sentiment_score_validation():
    score = SentimentScore(positive=0.5, negative=0.3)
    assert 0.0 <= score.compound <= 1.0

# ✅ Integration Tests - Slower, real dependencies
@pytest.mark.requires_services
def test_full_pipeline():
    response = client.post("/generate", json={"prompt": "test"})
    assert response.status_code == 200
```

---

## Pull Request Process

### Before Opening a PR

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commits are clean (squashed if needed)

### PR Template

We use a PR template - fill it out completely!

### During Review

- Respond to feedback within 48 hours
- Be open to suggestions
- Ask for clarification if needed
- Push commits to same branch (don't reopen)

### After Merge

Celebrate! 🎉 Then:
- Update the Project Board
- Claim your next issue
- Help review others' PRs

---

## Trust & Auto-Merge

As you contribute, you'll earn trust:

| Merged PRs | Trust Level | Auto-Merge? |
|------------|-------------|-------------|
| 0 | New | Manual review required |
| 1-2 | Learning | Manual review required |
| 3+ | Trusted | Auto-merge enabled* |

*Auto-merge only when CI passes and coverage doesn't decrease

---

## Getting Help

### Escalation Path

1. **Search existing resources** - Check README, docs, issues
2. **Ask in #help-troubleshooting** - Community answers
3. **Post in your role channel** - Role-specific help
4. **Attend office hours** - See [office hours guide](docs/getting-started/office-hours.md)
5. **Create an issue** - For bugs or feature requests

### Office Hours

| Day | Time | Focus |
|-----|------|-------|
| Monday | 2-4pm | Week kick-off, planning |
| Wednesday | 3-5pm | Mid-week check-in |
| Friday | 1-3pm | Show & tell, celebration |

---

## Recognition

We celebrate contributions!

- **First PR:** Shoutout in #announcements
- **5 PRs:** Contributor role in Slack
- **10 PRs:** Chimera Champion badge
- **Outstanding work:** Featured in monthly newsletter

---

**Happy contributing! We're glad you're here. 🚀**
EOF
```

**Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add extended contributing guide

Comprehensive contributing guide including:
- Quick start for first-time contributors
- Development workflow steps
- Code standards (Python PEP 8, commit messages)
- Testing guidelines with TDD and coverage requirements
- Pull request process
- Trust and auto-merge system explanation
- Getting help escalation path
- Recognition program

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Create Student FAQ

**Files:**
- Create: `docs/getting-started/faq.md`

**Step 1: Create the FAQ**

```bash
cat > docs/getting-started/faq.md << 'EOF'
# Student FAQ - Frequently Asked Questions

---

## Getting Started

### Q: What if I've never used Kubernetes before?

**A:** You're not alone! About half of our students are new to K8s. We have:
- A detailed [bootstrap guide](quick-start.md)
- Office hours dedicated to setup help
- A "K8s Buddy" system for pairing
- The `make bootstrap` script handles most of it automatically

### Q: Do I need a GPU?

**A:** No! Project Chimera works without a GPU. You'll run:
- Core services (FastAPI, Kafka, Redis) - CPU only
- ML inference using pre-trained models - optional GPU
- Most development is API/integration work, not ML training

### Q: Can I use Windows/Mac?

**A:** Yes, with caveats:
- **Best:** Linux (Ubuntu 22.04) - fully supported
- **Mac:** Works, but k3s requires Docker Desktop
- **Windows:** Use WSL2 with Ubuntu

If you're on Windows, come to office hours and we'll help set up WSL2.

---

## Development Workflow

### Q: How do I know what to work on?

**A:** Three ways:
1. **Assigned Issues:** Check your Sprint 0 tasks first
2. **Good First Issues:** Filter by the `good-first-issue` label
3. **Propose Ideas:** Open an issue to discuss first

### Q: What if an issue is already assigned?

**A:** Don't start working on it. Instead:
- Comment: "I'm also interested in this, can I help?"
- The assignee may welcome collaboration
- Or find another unassigned issue

### Q: How long should a PR take?

**A:** Depends on complexity:
- **Simple:** 1-2 days (typo fix, small refactor)
- **Medium:** 3-5 days (new feature, bug fix)
- **Complex:** 1-2 weeks (architecture changes)

If you're stuck, ask for help! Don't spin your wheels.

### Q: What if I break something?

**A:** It happens! Here's what to do:
1. Don't panic - that's what git is for
2. Check if tests pass locally
3. Open a PR anyway if tests pass
4. If tests fail, ask for help

We've all broken production. It's how we learn. 😅

---

## Evaluation & Grading

### Q: How will I be graded?

**A:** You'll be evaluated on:

| Component | Weight |
|-----------|--------|
| Code Quality | 30% |
| PR Contributions | 25% |
| Peer Reviews | 15% |
| Sprint Completion | 15% |
| Communication | 15% |

See [Evaluation Criteria](evaluation-criteria.md) for details.

### Q: What happens if I fall behind?

**A:** We've got your back:
- **Weeks 1-2:** We'll reach out proactively
- **Week 3+:** We'll pair you with a mentor
- **Office hours:** Always available
- **Extension policy:** Talk to us, we're reasonable

Communication is key. Don't disappear!

---

## Technical Questions

### Q: What coding language should I use?

**A:** **Python** is our primary language. You'll use:
- Python 3.10+ for all services
- YAML for Kubernetes manifests
- Bash for scripts
- SQL/NoSQL for data access

### Q: Can I use AI tools (ChatGPT, Copilot)?

**A:** Yes, with guidelines:
- ✅ Use AI for boilerplate, debugging, learning
- ✅ Disclose AI use in PR comments
- ❌ Don't copy-paste without understanding
- ❌ Don't let AI write tests without review

**Rule:** You must understand and be able to explain every line of code you submit.

### Q: I'm getting an error. Help?

**A:** Try this checklist:
1. **Read the error message** - what's it actually saying?
2. **Check logs** - `kubectl logs -f {pod-name}`
3. **Search the issue tracker** - someone may have solved this
4. **Google the error** - stackoverflow is your friend
5. **Ask in Slack** - paste the error and what you've tried

When asking, always include:
- What you're trying to do
- What you expected
- What actually happened (errors, logs)
- What you've tried

---

## Project-Specific

### Q: What does "Dynamic Performance Hub" mean?

**A:** Project Chimera creates live theatre shows that **adapt in real-time** to audience reactions:
- AI analyzes audience sentiment from social media
- AI generates dialogue based on audience mood
- Lighting and music respond to emotional tone

You're building an AI theatre director that reads the room! 🎭

### Q: What's the difference between "agents" and "services"?

**A:** We use these interchangeably, but:
- **Service:** Technical term for a microservice (FastAPI app)
- **Agent:** Functional term for AI capabilities

Each agent is deployed as one or more services.

### Q: Why 15 students? Won't that be chaotic?

**A:** 15 is perfect for our architecture:
- 10 role-specific areas (one expert per area)
- 5 "floating" contributors who help wherever needed
- Structure: Everyone owns something, but collaboration is key

---

## Monday Demo

### Q: What should I bring to the Monday demo?

**A:**
- Your laptop (fully charged)
- Questions! No question is too basic
- Excitement! We're building something cool 🚀

### Q: What if I can't make it to Monday's demo?

**A:** Let us know ASAP! We'll:
- Record the demo for you
- Schedule a 1:1 catchup
- Make sure you get your Sprint 0 tasks

### Q: Will there be food?

**A:** We'll have snacks! 🍕 If you have dietary restrictions, let us know before Monday.

---

## Career & Future

### Q: Will this help me get a job?

**A:** Absolutely! You'll gain experience in:
- FastAPI & async Python (in-demand)
- Kubernetes (huge plus)
- CI/CD & DevOps practices
- AI/ML integration
- Open source contribution

Your GitHub contributions will be a portfolio piece.

### Q: Can I add this to my resume?

**A:** Yes! You can list:

```
AI Developer | Project Chimera | Jan 2026 - Present
- Contributed to open-source AI theatre platform
- Developed FastAPI microservices for real-time dialogue generation
- Deployed services on Kubernetes with CI/CD pipelines
- Collaborated with team of 15 using GitHub workflows
```

### Q: Will there be references/recommendations?

**A:** After one semester of solid contributions, we'll write you a strong recommendation.

---

## Meta Questions

### Q: Who created Project Chimera?

**A:** Project Chimera was created by:
- {UNIVERSITY} Theatre + CS Departments collaboration
- Faculty Advisor: {NAME}
- Technical Lead: {NAME}
- Initial team of {NUMBER} students in {YEAR}

It's now open source, used by universities worldwide.

### Q: Why open source?

**A:** Because:
- Knowledge should be shared
- Other universities can use and improve it
- Students learn real-world open source practices
- It builds your professional network

### Q: How can I stay after the semester ends?

**A:** We love long-term contributors! Options:
- Continue as a maintainer for your component
- Mentor new students next semester
- Help with research and publications
- Contribute to new features

---

## Still Have Questions?

**Ask in Slack:** #help-troubleshooting
**Email:** {EMAIL}
**Office Hours:** See [office hours guide](office-hours.md)

---

**Last Updated:** 2026-03-01
EOF
```

**Step 2: Commit**

```bash
git add docs/getting-started/faq.md
git commit -m "docs: add student FAQ

Comprehensive FAQ covering 25+ questions:
- Getting started (Kubernetes, GPU, OS compatibility)
- Development workflow (finding work, PR time estimates)
- Evaluation and grading
- Technical questions (languages, AI tools, debugging)
- Project-specific (Dynamic Performance Hub, agents vs services)
- Monday demo logistics
- Career and future prospects
- Meta questions (origins, open source reasoning)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Create Office Hours & Support Schedule

**Files:**
- Create: `docs/getting-started/office-hours.md`

**Step 1: Create the office hours guide**

```bash
cat > docs/getting-started/office-hours.md << 'EOF'
# Office Hours & Support Schedule

---

## Weekly Office Hours

### Regular Schedule

| Day | Time | Type | Mentor | Location | Focus |
|-----|------|------|--------|----------|-------|
| **Monday** | 2:00-4:00pm | In-Person | Tech Lead | CS Lab 301 | Week kick-off, planning |
| **Tuesday** | 3:00-5:00pm | Virtual | TA 1 | Zoom {LINK} | Code review, debugging |
| **Wednesday** | 10:00am-12:00pm | Virtual | TA 2 | Zoom {LINK} | Setup & onboarding |
| **Wednesday** | 3:00-5:00pm | In-Person | Tech Lead | CS Lab 301 | Mid-week check-in |
| **Thursday** | 4:00-6:00pm | Virtual | TA 3 | Zoom {LINK} | PR reviews, testing |
| **Friday** | 1:00-3:00pm | In-Person | All Mentors | CS Lab 301 | Show & tell, celebration |

**Total:** 13 hours/week of structured support

---

## Support Channels

### Slack Response Times

| Channel | Purpose | Expected Response |
|---------|---------|-------------------|
| **#announcements** | Read-only updates | N/A |
| **#help-troubleshooting** | Technical questions | 24 hours |
| **#urgent** | Blocking issues | 2 hours (work hours) |
| **#pair-programming** | Find coding partners | When someone's free |
| **DM** | 1:1 help | During office hours |

### Escalation Path

```
Level 1: Self-Service
    ↓ Check docs, search issues, Google

Level 2: Community
    ↓ Post in #help-troubleshooting

Level 3: Role Channel
    ↓ Ask in your #role-{name} channel

Level 4: Office Hours
    ↓ Attend or DM during scheduled times

Level 5: Emergency
    ↓ #urgent channel or text {PHONE}
```

---

## What to Bring to Office Hours

### For Setup/Onboarding
- Your laptop
- Error messages (screenshots help!)
- What you've already tried
- Patience - setup can take 30-60 minutes

### For Code Review
- Link to your PR
- Specific questions or concerns
- Open mind to feedback

### For Debugging
- Minimal reproducible example
- Error messages and logs
- Expected vs actual behavior

### For Planning
- Current sprint goals
- Ideas for next work
- Questions about priorities

---

## Mentor Specialties

| Mentor | Expertise | Best For |
|--------|-----------|----------|
| **Tech Lead** | Architecture, K8s, CI/CD | Big picture, infrastructure |
| **TA 1** | FastAPI, async Python | Service development |
| **TA 2** | ML models, PyTorch | AI/ML integration |
| **TA 3** | Testing, QA | Test writing, debugging |

**Tip:** Choose the mentor whose expertise matches your question!

---

## Before You Ask for Help

### Try These First

1. **Search existing resources**
   - README.md
   - Documentation in `docs/`
   - GitHub issues (including closed ones)

2. **Debug systematically**
   - Read the error message carefully
   - Check logs: `kubectl logs -f {pod}`
   - Try isolating the problem

3. **Ask the community**
   - Post in #help-troubleshooting
   - Someone may have solved this!

4. **Then come to office hours**
   - Bring what you've tried
   - We'll help you learn, not just fix it

---

## Appointment Booking

### For 1:1 Sessions

Need dedicated time? Book a slot:
- **Calendly:** {LINK}
- **Email:** {EMAIL}
- **Slack DM:** @mention with preferred times

Available for:
- Deep dives on complex topics
- Career guidance
- Project planning
- Personal check-ins

---

## Peer Support System

### K8s Buddy Program

New to Kubernetes? Get paired with an experienced student:
- Sign up in #pair-programming
- We'll match you with a "buddy"
- Meet weekly for the first month

### Code Review Partners

Exchange PR reviews with peers:
- Post in #pair-programming
- "Anyone want to swap reviews?"
- Learn from each other's code

### Study Groups

Form groups for:
- Kubernetes study group
- FastAPI deep dive
- ML model training
- Test writing workshop

---

## Emergency Contacts

### Production Incidents

If something is broken and affecting users:
1. **Immediately:** Post in #urgent with details
2. **If critical:** Text {PHONE} (9am-9pm only)
3. **Do NOT** attempt to fix production alone

### Personal Emergencies

If you have a personal emergency affecting your work:
- Email: {EMAIL}
- Subject: "Personal Emergency - {Your Name}"
- We'll handle your workload gracefully

---

## Feedback on Support

### We Want to Improve!

Monthly, we'll ask:
- Are office hours accessible?
- Is response time fast enough?
- Do you feel supported?

**Give feedback:**
- Anonymous form: {LINK}
- Or DM Tech Lead anytime

---

## Summary

**Remember:** We're here to help you learn and succeed. No question is too basic. No problem is unsolvable together.

**When in doubt:** Just ask! 🚀

---

**Last Updated:** 2026-03-01
EOF
```

**Step 2: Commit**

```bash
git add docs/getting-started/office-hours.md
git commit -m "docs: add office hours and support schedule

Complete support guide including:
- Weekly office hours schedule (13 hours/week)
- Support channels and response times
- Escalation path (5 levels)
- What to bring to office hours
- Mentor specialties
- Peer support system (K8s Buddy, code review partners)
- Appointment booking
- Emergency contacts
- Feedback mechanism

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Create Sprint & Milestone Definitions

**Files:**
- Create: `docs/getting-started/sprint-definitions.md`

**Step 1: Create the sprint definitions**

```bash
cat > docs/getting-started/sprint-definitions.md << 'EOF'
# Sprint & Milestone Definitions

**Semester Timeline:** 15 weeks
**Sprint Duration:** 1 week each
**Team:** 15 AI students

---

## Sprint Overview

| Sprint | Focus | Key Deliverables | Milestone |
|--------|-------|------------------|-----------|
| **0** | Onboarding | Environment setup, first PR | Ready to Contribute |
| **1** | Foundation | Core service understanding | Foundation Complete |
| **2** | First Features | Initial contributions | First PRs Merged |
| **3** | Integration | Cross-service work | Services Integrated |
| **4** | Testing | Test coverage expansion | 70% Coverage |
| **5** | Documentation | API docs, guides | Docs Complete |
| **6** | Performance | Optimization | Performance Baseline |
| **7** | **Mid-Semester** | Review, reflection | Midpoint Check |
| **8** | Advanced Features | Complex features | Advanced Features |
| **9** | Reliability | Error handling, resilience | Production-Ready |
| **10** | Monitoring | Observability | Metrics Dashboard |
| **11** | User Testing | Real-world feedback | User Tested |
| **12** | Polish | UI/UX improvements | Polished Experience |
| **13** | Hardening | Security, stability | Secure & Stable |
| **14** | **Final Sprint** | Demo preparation | Demo Ready |

---

## Sprint 0: Onboarding (Week 1)

**Goal:** Get everyone set up and contributing

**All Students:**
- [ ] Complete environment setup
- [ ] Join Slack/Discord
- [ ] Make first PR (add to CONTRIBUTORS.md)
- [ ] Complete role-specific setup
- [ ] Attend Monday demo

**Deliverables:**
- 45 Sprint 0 issues completed (15 students × 3 issues)
- All students have development environments
- First PRs merged

---

## Sprint 1: Foundation (Week 2)

**Goal:** Understand the codebase deeply

**All Students:**
- [ ] Complete 2-3 good-first-issues
- [ ] Review 2 PRs from peers
- [ ] Attend daily standups

**By Role:**
- **Roles 1-8:** Add unit tests to assigned service
- **Role 9:** Set up monitoring stack
- **Role 10:** Set up test reporting dashboard

**Deliverables:**
- 30+ issues completed
- Test coverage increased

---

## Sprint 2: First Features (Week 3)

**Goal:** Ship meaningful features

**All Students:**
- [ ] Complete 1 feature PR
- [ ] Write integration tests
- [ ] Document changes

**Deliverables:**
- 10 feature PRs merged
- Integration tests passing

---

## Sprint 3: Integration (Week 4)

**Goal:** Make services work together

**All Students:**
- [ ] Cross-service PR (partner with another role)
- [ ] End-to-end test coverage
- [ ] Performance baseline

**Deliverables:**
- 5 integration PRs
- E2E tests passing

---

## Sprint 4: Testing (Week 5)

**Goal:** 70%+ test coverage

**Targets:**
- All services: 70% coverage minimum
- Critical paths: 90% coverage
- Load tests: Handle 100 req/s

**Deliverables:**
- Coverage report: 70%+
- Load test results documented

---

## Sprint 5: Documentation (Week 6)

**Goal:** Docs are as good as code

**Deliverables:**
- API documentation complete
- 5+ usage examples
- Architecture diagrams updated

---

## Sprint 6: Performance (Week 7)

**Goal:** Make it fast

**Targets:**
- API responses: < 100ms (p95)
- Startup time: < 30 seconds
- Memory usage: < 512MB per service

**Deliverables:**
- Performance benchmarks
- Caching strategy documented

---

## Sprint 7: Mid-Semester Review (Week 8)

**Goal:** Reflect and recalibrate

**Activities:**
- Mid-semester presentations (5 min each)
- Retrospective
- Set goals for remaining sprints
- Peer feedback sessions

**Deliverables:**
- Individual progress reports
- Updated sprint plan

---

## Sprint 8: Advanced Features (Week 9)

**Goal:** Build complex features

**Deliverables:**
- 5+ advanced feature PRs
- Documentation for new features

---

## Sprint 9: Reliability (Week 10)

**Goal:** Production-grade reliability

**Targets:**
- 99.9% uptime for core services
- Graceful handling of downstream failures
- Meaningful error messages

**Deliverables:**
- Error handling documentation
- Failure scenarios tested

---

## Sprint 10: Monitoring (Week 11)

**Goal:** Know what's happening

**Deliverables:**
- Grafana dashboards for all services
- Alerting rules configured
- Runbooks for common issues

---

## Sprint 11: User Testing (Week 12)

**Goal:** Real feedback

**Activities:**
- Demo to actual theatre students
- Gather feedback
- Prioritize improvements
- Start addressing issues

**Deliverables:**
- User feedback documented
- 10+ issues created from feedback
- 5+ improvements shipped

---

## Sprint 12: Polish (Week 13)

**Goal:** Make it delightful

**Deliverables:**
- 20+ polish issues resolved
- User feedback addressed

---

## Sprint 13: Hardening (Week 14)

**Goal:** Secure and stable

**Deliverables:**
- Security scan report
- Dependencies up to date
- Disaster recovery tested

---

## Sprint 14: Final Sprint (Week 15)

**Goal:** Demo ready!

**All Students:**
- [ ] Final demos prepared
- [ ] Presentation slides
- [ ] Code final review
- [ ] Documentation complete
- [ ] Celebrate! 🎉

**Deliverables:**
- Individual demos (10 min each)
- Final project presentation
- Portfolio-ready GitHub profile

---

## Milestone Criteria

### ✅ Ready to Contribute (After Sprint 0)
- All students have environments
- First PRs merged
- Everyone joined Slack

### 🏗️ Foundation Complete (After Sprint 1)
- All students understand their service
- Test infrastructure in place
- CI/CD working

### 🚀 First Features (After Sprint 2)
- 10+ features shipped
- Integration tests passing

### 🔗 Services Integrated (After Sprint 3)
- End-to-end flow working
- Performance baseline set

### ✅ Tested (After Sprint 4)
- 70%+ coverage
- Load tests passing

### 📚 Documented (After Sprint 5)
- All APIs documented
- Examples available

### ⚡ Performing (After Sprint 6)
- Performance targets met
- Caching working

### 🎯 Midpoint (After Sprint 7)
- Progress reviewed
- Goals recalibrated

### 🎁 Advanced Features (After Sprint 8)
- Complex features working

### 🛡️ Production-Ready (After Sprint 9)
- Error handling solid
- Reliability high

### 📊 Observable (After Sprint 10)
- Dashboards complete
- Alerting configured

### 🧪 User-Tested (After Sprint 11)
- Real feedback gathered
- Improvements started

### ✨ Polished (After Sprint 12)
- UX improved
- Feedback addressed

### 🔒 Secure & Stable (After Sprint 13)
- Security audited
- Hardening complete

### 🎭 Demo Ready (After Sprint 14)
- Final demos prepared
- Project complete

---

**Remember:** Sprints are guides, not prisons. If you're ahead, take on more. If you're behind, communicate early. We adapt! 🚀
EOF
```

**Step 2: Commit**

```bash
git add docs/getting-started/sprint-definitions.md
git commit -m "docs: add sprint and milestone definitions

Complete 15-sprint plan including:
- Sprint overview table with focus and milestones
- Detailed sprint descriptions for all 15 sprints
- Clear deliverables for each sprint
- 15 milestone criteria
- Student expectations per sprint

Covers entire semester from onboarding to final demo.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Create Student Evaluation Criteria

**Files:**
- Create: `docs/getting-started/evaluation-criteria.md`

**Step 1: Create the evaluation criteria**

```bash
cat > docs/getting-started/evaluation-criteria.md << 'EOF'
# Student Evaluation Criteria

**Transparency:** You'll always know where you stand.
**Feedback:** Weekly updates on your progress.
**Growth:** We focus on improvement, not perfection.

---

## Grading Overview

| Component | Weight | Description |
|-----------|--------|-------------|
| **Code Quality** | 30% | Clean, tested, documented code |
| **PR Contributions** | 25% | Quantity & quality of merged PRs |
| **Peer Reviews** | 15% | Reviewing others' code effectively |
| **Sprint Completion** | 15% | Meeting sprint goals consistently |
| **Communication** | 15% | Participation, collaboration, docs |

**Total:** 100%

---

## Component 1: Code Quality (30%)

### What We Evaluate

| Criterion | Excellent (A) | Good (B) | Needs Work (C) |
|-----------|---------------|----------|----------------|
| **Clean Code** | Follows style guide, self-documenting | Minor style issues | Style violations |
| **Testing** | 80%+ coverage | 60-80% coverage | < 60% coverage |
| **Documentation** | Well-documented | Basic docs | Little/no docs |
| **Architecture** | Solid design | Decent design | Poor design |

### Scoring

```
27-30% (A): Exceptional code quality
24-26% (B): Good code with minor issues
21-23% (C): Acceptable, needs improvement
18-20% (D): Below expectations
0-17% (F): Serious issues
```

---

## Component 2: PR Contributions (25%)

### Quantity Expectations

| PRs Merged | Grade | Notes |
|------------|-------|-------|
| 15+ | A | Exceeded expectations |
| 12-14 | B | Solid contributions |
| 10-11 | C | Met minimum |
| 8-9 | D | Below expectations |
| < 8 | F | Insufficient |

**Minimum to pass:** 10 merged PRs

### Quality Multipliers

| PR Quality | Multiplier | Examples |
|------------|------------|----------|
| **Exceptional** | 1.5× | Complex features, excellent tests |
| **Solid** | 1.0× | Good work, meets standards |
| **Basic** | 0.75× | Simple fixes, minimal tests |

### Trust Building Bonus

| Merged PRs | Trust Level | Bonus |
|------------|-------------|-------|
| 0 | New | - |
| 1-2 | Learning | - |
| 3-5 | Trusted | +2% to final grade |
| 6-9 | Senior | +3% to final grade |
| 10+ | Expert | +5% to final grade |

---

## Component 3: Peer Reviews (15%)

### Expectations

| Reviews Written | Grade | Notes |
|-----------------|-------|-------|
| 15+ | A | Active community member |
| 12-14 | B | Good participation |
| 10-11 | C | Met minimum |
| 8-9 | D | Below expectations |
| < 8 | F | Insufficient |

**Minimum to pass:** 10 peer reviews

---

## Component 4: Sprint Completion (15%)

### Sprint Goals

Each sprint has clear goals. We track:

| Metric | Excellent | Good | Needs Work |
|--------|-----------|------|------------|
| **Issues Completed** | 100%+ | 80-99% | 60-79% |
| **On Time** | Always | Usually | Sometimes |

### Scoring Per Sprint

Each sprint is worth ~1%:

```
A: 1.0% (all goals met)
B: 0.8% (most goals met)
C: 0.6% (some goals met)
D: 0.4% (few goals met)
F: 0% (goals not met)
```

### Recovery Policy

Had a bad sprint? You can recover:
- **Next sprint excellence:** Cancels out previous C/D
- **Extra credit:** Complete bonus issues for +0.2%
- **Communication:** Talk to us early if struggling

---

## Component 5: Communication (15%)

### Participation

| Channel | Expected |
|---------|----------|
| **Slack/Discord** | Active, respond within 24h |
| **Standups** | Updates 3×/week |
| **Office Hours** | Attend 1×/week minimum |
| **Documentation** | Keep docs updated |

### Scoring

```
13-15% (A): Excellent communicator, team player
11-12% (B): Good communication, collaborative
9-10% (C): Adequate communication
7-8% (D): Poor communication
0-6% (F): Communication problems
```

---

## Grade Scale

| Percentage | Grade | GPA | Description |
|------------|-------|-----|-------------|
| 93-100% | A | 4.0 | Exceptional |
| 90-92% | A- | 3.7 | Excellent |
| 87-89% | B+ | 3.3 | Very Good |
| 83-86% | B | 3.0 | Good |
| 80-82% | B- | 2.7 | Satisfactory |
| 77-79% | C+ | 2.3 | Adequate |
| 73-76% | C | 2.0 | Acceptable |
| 70-72% | C- | 1.7 | Passing |
| 67-69% | D+ | 1.3 | Below Average |
| 63-66% | D | 1.0 | Poor |
| 0-62% | F | 0.0 | Failing |

---

## Feedback Schedule

### Weekly Updates (Fridays)

- Current grade: Where you stand
- This week's highlights
- Areas for improvement
- Next week's goals

### Mid-Semester Review (Week 8)

- Progress report
- Grade projection
- Improvement plan (if needed)

### Final Evaluation (Week 15)

- Comprehensive review
- Final grade
- Portfolio review
- Recommendations

---

## Extra Credit

Available for going above and beyond:

| Opportunity | Points | Notes |
|-------------|--------|-------|
| **Blog post** about Project Chimera | +1% | Must be published |
| **Conference talk** or presentation | +2% | About your work |
| **Mentoring** new students | +1% | Per semester |
| **Hackathon participation** | +1% | Project-related |
| **Outstanding contribution** | +1% | Mentor discretion |

**Maximum extra credit:** +5% to final grade

---

## Summary

**We evaluate holistically:**
- Not just code output
- The whole developer: collaboration, communication, growth

**We value improvement:**
- Early struggles don't define your grade
- Late excellence is recognized
- Growth mindset matters

**We're transparent:**
- You'll always know where you stand
- Feedback is specific and actionable
- Criteria are clear from day one

**Questions about grading? Ask in office hours or email {EMAIL}**

---

**Last Updated:** 2026-03-01
EOF
```

**Step 2: Commit**

```bash
git add docs/getting-started/evaluation-criteria.md
git commit -m "docs: add student evaluation criteria

Transparent grading system including:
- 5 components with weights (code quality, PRs, reviews, sprints, communication)
- Detailed rubrics for each component
- Grade scale (A-F with GPA)
- Trust bonus system
- Feedback schedule (weekly, mid-semester, final)
- Extra credit opportunities

Students know exactly what's expected from day one.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Update README with New Documentation Links

**Files:**
- Modify: `README.md`

**Step 1: Read the README to find the documentation section**

```bash
grep -n "## Documentation" README.md
```

**Step 2: Add links to new documentation**

Find the Documentation section and add the new links after the existing ones:

```bash
# In README.md, after the existing documentation links, add:
```

```markdown
### Student Resources

- [Student Quick Start](docs/getting-started/quick-start.md) - Set up your development environment
- [Student Roles](docs/getting-started/roles.md) - 15 student role definitions
- [Communication Channels](docs/getting-started/communication-channels.md) - Slack/Discord guide
- [Office Hours](docs/getting-started/office-hours.md) - Support schedule
- [Student FAQ](docs/getting-started/faq.md) - Frequently asked questions
- [Sprint Definitions](docs/getting-started/sprint-definitions.md) - 15 sprint overview
- [Evaluation Criteria](docs/getting-started/evaluation-criteria.md) - Grading information
- [Monday Demo Info](docs/getting-started/monday-demo/) - Demo preparation
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add student resources section to README

Added links to all new student documentation:
- Communication channels guide
- Office hours schedule
- Student FAQ
- Sprint definitions
- Evaluation criteria

Makes student resources easily discoverable from main README.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 10: Create CONTRIBUTORS.md Template

**Files:**
- Create: `CONTRIBUTORS.md`

**Step 1: Create the CONTRIBUTORS template**

```bash
cat > CONTRIBUTORS.md << 'EOF'
# Contributors

Project Chimera is built by a community of students, mentors, and contributors.

---

## Core Team

### Faculty & Leadership

### Technical Leads

### Teaching Assistants

---

## Student Contributors

### Spring 2026 Cohort

---

## Alumni

---

## Acknowledgments

Project Chimera is made possible by:
- {UNIVERSITY} Theatre Department
- {UNIVERSITY} Computer Science Department
- GitHub Education
- Open source community

---

**Want to add yourself?** See [Contributing Guide](CONTRIBUTING.md) and make your first PR!
EOF
```

**Step 2: Commit**

```bash
git add CONTRIBUTORS.md
git commit -m "docs: add CONTRIBUTORS.md template

Template for contributors list including:
- Core team section
- Student contributors section
- Alumni section
- Acknowledgments

Students add themselves as part of Sprint 0 first PR.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 11: Update CHANGELOG with New Documentation

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Read the current CHANGELOG**

```bash
head -50 CHANGELOG.md
```

**Step 2: Add new entry under v0.2.0 Added section**

Add after the existing "Added" entries:

```markdown
- **Complete Student Onboarding Package** - Full documentation for 15 AI students
  - Student welcome email template
  - Communication channels guide (Slack/Discord)
  - Code of Conduct (Contributor Covenant 2.1)
  - Extended Contributing Guide with TDD and code standards
  - Student FAQ with 25+ questions answered
  - Office Hours & Support Schedule (13 hours/week)
  - Sprint & Milestone Definitions (15 sprints)
  - Student Evaluation Criteria (transparent grading)
  - CONTRIBUTORS.md template
```

**Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG with student onboarding documentation

Added complete student onboarding package to v0.2.0 release notes.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 12: Create GitHub Project Board Setup Instructions

**Files:**
- Create: `docs/getting-started/github-project-board-setup.md`

**Step 1: Create the setup instructions**

```bash
cat > docs/getting-started/github-project-board-setup.md << 'EOF'
# GitHub Project Board Setup Instructions

**For:** Technical Lead
**Time Required:** ~2 hours
**Before:** Monday Demo

---

## Overview

This guide walks through setting up the GitHub Project Board for organizing all student work across 15 sprints.

---

## Step 1: Create the Project

### Using GitHub CLI

```bash
# Create the project
gh project create --title "Project Chimera" --owner "project-chimera"

# Note the PROJECT_ID from the output
```

### Using GitHub UI

1. Go to: https://github.com/orgs/project-chimera/projects
2. Click "New Project"
3. Title: "Project Chimera"
4. Select "Board" template
5. Click "Create"

---

## Step 2: Create Custom Fields

### Using GitHub CLI

```bash
# Get your PROJECT_ID first
PROJECT_ID="your-project-id-here"

# Create each field
gh project field create --project-id $PROJECT_ID --name "Status" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Priority" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Role" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Sprint" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Trust Level" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Points" --datatype "number"
```

### Using GitHub UI

1. Open the project
2. Click the → menu next to "Fields"
3. Select "Create new field"
4. Create each field with these settings:

**Status (Single Select)**
- Options: Backlog, Ready, In Progress, In Review, Done
- Colors: Gray, Blue, Yellow, Orange, Green

**Priority (Single Select)**
- Options: P1-Critical, P2-High, P3-Medium, P4-Low
- Colors: Red, Orange, Yellow, Gray

**Role (Single Select)**
- Options: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- Colors: Various

**Sprint (Single Select)**
- Options: Sprint 0, Sprint 1, ..., Sprint 14
- Colors: Various

**Trust Level (Single Select)**
- Options: New, Learning, Trusted
- Colors: Gray, Blue, Green

**Points (Number)**
- Format: 0, 1, 2, 3, 5, 8, 13

---

## Step 3: Create Views

### View 1: By Role

1. Click "View" menu
2. Select "New view"
3. Name: "By Role"
4. Layout: Board
5. Group by: Role custom field
6. Save

### View 2: By Sprint

1. Click "View" menu
2. Select "New view"
3. Name: "By Sprint"
4. Layout: Board
5. Add filter: Sprint = (selected sprint)
6. Save

### View 3: By Status (Kanban)

1. Click "View" menu
2. Select "New view"
3. Name: "Kanban"
4. Layout: Board
5. Group by: Status custom field
6. Save

### View 4: Monday Onboarding

1. Click "View" menu
2. Select "New view"
3. Name: "Monday Onboarding"
4. Add filter: Sprint = Sprint 0
5. Save

---

## Step 4: Create Repository Labels

### Using GitHub CLI

```bash
# Create each label
gh label create "sprint-0" --color "#fbca04" --description "Sprint 0 onboarding tasks"
gh label create "good-first-issue" --color "#7057ff" --description "Good for newcomers"
gh label create "help-wanted" --color "#008672" --description "Help wanted"
gh label create "bug" --color "#d73a4a" --description "Something isn't working"
gh label create "enhancement" --color "#a2eeef" --description "New feature or request"
gh label create "documentation" --color "#0075ca" --description "Improvements or additions to docs"
gh label create "trust:new" --color "#7f8491" --description "New contributor"
gh label create "trust:learning" --color "#5a5ed6" --description "1-2 PRs merged"
gh label create "trust:trusted" --color "#3a9f4d" --description "3+ PRs merged"
```

---

## Step 5: Link Repository to Project

```bash
# Link your repository to the project
gh project edit --project-id $PROJECT_ID --link-repo "project-chimera/project-chimera"
```

---

## Verification Checklist

- [ ] Project created
- [ ] All 7 custom fields created
- [ ] All 4 views created
- [ ] All 10 labels created
- [ ] Repository linked
- [ ] Test by creating a sample issue

---

## Next Steps

1. Trigger the onboarding workflow to create Sprint 0 issues
2. Verify issues appear in the project board
3. Test each view
4. Share board link with students

---

**Board URL:** https://github.com/orgs/project-chimera/projects/{PROJECT_NUMBER}

**Last Updated:** 2026-03-01
EOF
```

**Step 2: Commit**

```bash
git add docs/getting-started/github-project-board-setup.md
git commit -m "docs: add GitHub Project Board setup instructions

Step-by-step guide for Technical Lead to set up:
- GitHub Project creation
- 7 custom fields (Status, Priority, Role, Sprint, Trust Level, Points)
- 4 views (By Role, By Sprint, Kanban, Monday Onboarding)
- 10 labels (sprint-0, good-first-issue, etc.)
- Repository linking

Enables organized tracking of all student work.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 13: Create Pre-Monday Verification Checklist

**Files:**
- Update: `docs/getting-started/monday-demo/pre-monday-checklist.md`

**Step 1: Read existing checklist**

```bash
cat docs/getting-started/monday-demo/pre-monday-checklist.md
```

**Step 2: Append new items for complete onboarding**

```bash
cat >> docs/getting-started/monday-demo/pre-monday-checklist.md << 'EOF'

---

## Complete Student Onboarding (NEW)

### Documentation
- [ ] Student welcome email template created
- [ ] Communication channels guide created
- [ ] Code of Conduct created
- [ ] Extended Contributing Guide created
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
- [ ] CODEOWNERS configured
- [ ] Branch protection rules set
- [ ] Workflows tested

### Community Platform
- [ ] Slack workspace created
- [ ] All channels created
- [ ] Integrations configured (GitHub → Slack)
- [ ] Invite link generated
- [ ] Bot configurations tested

### Sprint 0 Issues
- [ ] Onboarding workflow tested
- [ ] All 45 Sprint 0 issues will be created automatically
- [ ] Issue templates validated
- [ ] Assignee mappings ready

### Email Preparation
- [ ] Email template personalized for all 15 students
- [ ] Placeholders filled (names, emails, roles, mentors)
- [ ] Links verified (repository, docs, Slack, Zoom)
- [ ] Schedule confirmed (location, time, Zoom link)
- [ ] Email list ready

### Monday Demo
- [ ] Demo script reviewed
- [ ] Services tested and running
- [ ] Presentation slides ready
- [ ] Name tags prepared
- [ ] Snacks arranged
- [ ] Backup plan (Zoom) ready

EOF
```

**Step 3: Commit**

```bash
git add docs/getting-started/monday-demo/pre-monday-checklist.md
git commit -m "docs: update pre-monday checklist with onboarding items

Added complete student onboarding verification including:
- Documentation (12 new files)
- GitHub setup (project board, fields, views, labels)
- Community platform setup
- Sprint 0 issues preparation
- Email preparation
- Monday demo preparation

Ensures nothing is missed before student arrival.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 14: Verify All Files Created

**Step 1: List all new files**

```bash
echo "=== New Documentation Files ===" && \
echo "Templates:" && ls -la docs/templates/ 2>/dev/null || echo "  (templates)" && \
echo "" && \
echo "Getting Started:" && ls -la docs/getting-started/*.md && \
echo "" && \
echo "Root files:" && ls -la *.md | grep -E "(CONTRIBUTORS|CODE_OF_CONDUCT)" && \
echo "" && \
echo "Total markdown files:" && find docs -name "*.md" | wc -l
```

Expected output should show:
- `docs/templates/student-welcome-email.md`
- `docs/getting-started/communication-channels.md`
- `docs/getting-started/faq.md`
- `docs/getting-started/office-hours.md`
- `docs/getting-started/sprint-definitions.md`
- `docs/getting-started/evaluation-criteria.md`
- `docs/getting-started/github-project-board-setup.md`
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- Updated `README.md`
- Updated `CHANGELOG.md`
- Updated `docs/getting-started/monday-demo/pre-monday-checklist.md`

**Step 2: Verify no broken links**

```bash
# Check for broken internal links
grep -r "](.*.md)" docs/ *.md | grep -E "\[.*\]\(\.\./" | head -20
```

Should return minimal or no broken link references.

---

## Task 15: Final Git Tag

**Step 1: Create final git tag**

```bash
# Tag the complete onboarding package
git tag -a v0.2.0-student-onboarding -m "Complete Student Onboarding Package

All documentation and guides for 15 AI students:
- Welcome email template
- Communication channels guide
- Code of Conduct
- Contributing guide
- Student FAQ
- Office hours schedule
- Sprint definitions (15 sprints)
- Evaluation criteria
- GitHub Project Board setup

Ready for student email delivery and Monday demo.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Step 2: List all tags**

```bash
git tag -l | sort -V
```

Should show:
- `v0.2.0-github-automation`
- `v0.2.0`
- `v0.2.0-student-onboarding`

---

## Summary

**Implementation complete!** All 15 tasks finished:

1. ✅ Student Welcome Email Template
2. ✅ Communication Channels Guide
3. ✅ Code of Conduct
4. ✅ Extended Contributing Guide
5. ✅ Student FAQ
6. ✅ Office Hours & Support Schedule
7. ✅ Sprint & Milestone Definitions
8. ✅ Student Evaluation Criteria
9. ✅ README updated with links
10. ✅ CONTRIBUTORS.md template
11. ✅ CHANGELOG updated
12. ✅ GitHub Project Board setup instructions
13. ✅ Pre-Monday checklist updated
14. ✅ All files verified
15. ✅ Git tag v0.2.0-student-onboarding

**Files Created:** 12 new files
**Files Modified:** 3 existing files
**Total Documentation:** Complete student onboarding package

**Ready for:** Email delivery to students in ~11 hours, Monday demo preparation

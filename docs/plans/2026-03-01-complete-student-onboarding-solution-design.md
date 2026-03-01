# Complete Student Onboarding Solution Design

> **Status:** Approved for Implementation
> **Date:** March 1, 2026
> **Target:** Email to students in ~11 hours, Monday Demo preparation

---

## Overview

Design a comprehensive onboarding package for 15 AI students joining Project Chimera, ensuring they have everything needed to contribute successfully from day one. This includes all missing components identified from deep dive analysis: student welcome email, Sprint 0 issues, GitHub Project Board setup, communication channels, code of conduct, contributing guide, FAQ, office hours schedule, sprint definitions, and evaluation criteria.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STUDENT ONBOARDING ECOSYSTEM                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │  Welcome     │    │   GitHub     │    │  Slack/      │             │
│  │  Email       │───▶│  Project     │───▶│  Discord     │             │
│  │  (First      │    │  Board       │    │  Community   │             │
│  │  Touch)      │    │  (Work)      │    │  (Daily)     │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│          │                   │                    │                      │
│          └───────────────────┼────────────────────┘                      │
│                             ▼                                           │
│                   ┌──────────────┐                                      │
│                   │  Sprint 0    │                                      │
│                   │  Issues      │                                      │
│                   │  (45 Total)  │                                      │
│                   └──────────────┘                                      │
│                             │                                           │
│                             ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    DOCUMENTATION HUB                            │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  • Code of Conduct      • Contributing Guide                    │   │
│  │  • Student FAQ          • Office Hours Schedule                 │   │
│  │  • Sprint Definitions   • Evaluation Criteria                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Student Welcome Email

**File:** `docs/templates/student-welcome-email.md`

**Purpose:** Single comprehensive email that students receive before the Monday demo containing all essential information.

**Key Sections:**
- Welcome & Project Vision
- Role Assignment (personalized for each student)
- Quick Links (repository, docs, community)
- Pre-Monday Checklist
- Sprint 0 Task Links (3 per student)
- Monday Schedule (60-minute agenda)
- Support Channels (Slack/Discord, office hours)
- Learning Outcomes (what students will gain)
- Success Criteria (how they'll be evaluated)
- Contact Information

**Delivery:** Sent 24 hours before Monday demo via email.

---

### 2. Sprint 0 GitHub Issues

**Automation:** `.github/workflows/onboarding.yml`

**Purpose:** 45 onboarding issues (15 students × 3 issues each) automatically created and assigned.

**Issue Templates:**

**Issue Type 1: Environment Setup (All Students)**
- Clone repository
- Install prerequisites (Python 3.10+, Docker, kubectl)
- Run `make bootstrap`
- Verify services healthy
- Run test suite
- Join community platform

**Issue Type 2: Hello World PR (All Students)**
- Create feature branch
- Add self to `CONTRIBUTORS.md`
- Open first PR
- Learn workflow

**Issue Type 3: Role-Specific Setup (Per Student)**
- Read component documentation
- Set up component dependencies
- Run component tests
- Make small test change
- Document learning

**Labels:** `sprint-0`, `setup`, `good-first-issue`, `trust-building`

---

### 3. GitHub Project Board

**Purpose:** Single shared board organizing all student work across 15 sprints.

**Board Views:**
1. **By Role** - 10 swimlanes for student roles
2. **By Sprint** - Filter by sprint (Sprint 0-14)
3. **By Status** - Kanban: Backlog → Ready → In Progress → In Review → Done
4. **Monday Onboarding** - Sprint 0 filter (45 issues)

**Custom Fields:**
| Field | Type | Values |
|-------|------|--------|
| Status | Single Select | Backlog, Ready, In Progress, In Review, Done |
| Priority | Single Select | P1-Critical, P2-High, P3-Medium, P4-Low |
| Role | Single Select | 1-10 (matches student roles) |
| Sprint | Single Select | Sprint 0-14 |
| Trust Level | Single Select | New, Learning, Trusted |
| Points | Number | 1, 2, 3, 5, 8, 13 (Fibonacci) |
| Student | People | Student assignees |

**Labels:**
- `sprint-0` (Yellow), `good-first-issue` (Green), `help-wanted` (Blue)
- `bug` (Red), `enhancement` (Purple), `documentation` (Orange)
- `trust:new` (Gray), `trust:learning` (Blue), `trust:trusted` (Green)

**Setup:** Manual creation by Technical Lead before Monday demo.

---

### 4. Communication Channels Guide

**File:** `docs/getting-started/communication-channels.md`

**Platform:** Slack (recommended) or Discord

**Channel Structure:**
```
#announcements          (Admins only - important updates)
#introductions          (Student introductions)
#general                (Project-wide discussion)
#help-troubleshooting   (Technical questions)
#pair-programming       (Find coding partners)
#show-and-tell          (Demo your work)

#role-openclaw          (OpenClaw Orchestrator team)
#role-scenespeak        (SceneSpeak Agent team)
#role-captioning        (Captioning Agent team)
#role-bsl               (BSL Translation team)
#role-sentiment         (Sentiment Analysis team)
#role-lighting          (Lighting Control team)
#role-safety            (Safety Filter team)
#role-console           (Operator Console team)
#role-infra             (Infrastructure team)
#role-qa                (QA & Documentation team)

#random                 (Off-topic, fun)
```

**Response Time Expectations:**
- Urgent/Blockers: 2 hours (work hours)
- Technical Questions: 24 hours
- PR Reviews: 48 hours
- Non-urgent: 3 days

**Automation:**
- GitHub → Slack integration (PR notifications)
- CI/CD status notifications
- Sprint reminder notifications

---

### 5. Code of Conduct

**File:** `CODE_OF_CONDUCT.md`

**Purpose:** Clear, friendly behavioral expectations.

**Key Sections:**
- Pledge (harassment-free experience)
- Positive behaviors (respect, constructive criticism, empathy, learning)
- Unacceptable behaviors (sexualized language, trolling, harassment)
- Learning environment emphasis (mistakes welcome, questions encouraged)
- Reporting process (minor issues, serious issues)
- Consequences (warning → suspension → removal)
- Attribution (Contributor Covenant 2.1)

**Tone:** Friendly, learning-focused, student-appropriate

---

### 6. Extended Contributing Guide

**File:** `CONTRIBUTING.md`

**Purpose:** Beyond basic setup - how to contribute effectively.

**Sections:**
- Quick Start
- Development Workflow (find issues, claim, branch, code, test, PR)
- Code Standards (Python PEP 8, type hints, docstrings, commit messages)
- Testing Guidelines (TDD, coverage requirements, test types)
- Pull Request Process (before, during, after merge)
- Trust & Auto-Merge system
- Getting Help (escalation path)
- Recognition (first PR, milestones, badges)

**Coverage Requirements:**
- Core Logic: 80% minimum, 90% target
- Models: 90% minimum, 100% target
- Routes: 70% minimum, 85% target
- Utils: 80% minimum, 90% target

---

### 7. Student FAQ

**File:** `docs/getting-started/faq.md`

**Purpose:** Common questions answered before students ask.

**Sections:**
- Getting Started (Kubernetes experience, GPU requirements, OS compatibility)
- Development Workflow (finding work, assigned issues, PR time estimates, breaking things)
- Evaluation & Grading (criteria, falling behind, extensions)
- Technical Questions (languages, AI tools, error handling)
- Project-Specific (Dynamic Performance Hub meaning, agents vs services, 15 students)
- Monday Demo (what to bring, attendance, food)
- Career & Future (job prospects, resume, references)
- Meta Questions (origins, open source reasoning, staying involved)

**Total:** 25+ frequently asked questions with detailed answers.

---

### 8. Office Hours & Support Schedule

**File:** `docs/getting-started/office-hours.md`

**Weekly Schedule:**
- Monday 2-4pm: In-Person (Tech Lead) - Week kick-off
- Tuesday 3-5pm: Virtual (TA 1) - Code review
- Wednesday 10am-12pm: Virtual (TA 2) - Setup help
- Wednesday 3-5pm: In-Person (Tech Lead) - Mid-week check-in
- Thursday 4-6pm: Virtual (TA 3) - PR reviews
- Friday 1-3pm: In-Person (All) - Show & tell

**Total:** 13 hours/week structured support

**Support Channels:**
- Slack response times by channel
- Escalation path (5 levels)
- Mentor specialties
- Appointment booking (Calendly)
- Peer support (K8s Buddy, Code Review Partners, Study Groups)
- Emergency contacts

---

### 9. Milestone & Sprint Definitions

**File:** `docs/getting-started/sprint-definitions.md`

**Structure:** 15 sprints (1 week each)

| Sprint | Focus | Key Deliverables | Milestone |
|--------|-------|------------------|-----------|
| 0 | Onboarding | Environment, first PR | Ready to Contribute |
| 1 | Foundation | Service understanding | Foundation Complete |
| 2 | First Features | Initial contributions | First PRs Merged |
| 3 | Integration | Cross-service work | Services Integrated |
| 4 | Testing | Coverage expansion | 70% Coverage |
| 5 | Documentation | API docs, guides | Docs Complete |
| 6 | Performance | Optimization | Performance Baseline |
| 7 | Mid-Semester | Review, reflection | Midpoint Check |
| 8 | Advanced Features | Complex features | Advanced Features |
| 9 | Reliability | Error handling | Production-Ready |
| 10 | Monitoring | Observability | Metrics Dashboard |
| 11 | User Testing | Real feedback | User Tested |
| 12 | Polish | UI/UX improvements | Polished Experience |
| 13 | Hardening | Security, stability | Secure & Stable |
| 14 | Final Sprint | Demo preparation | Demo Ready |

**Each Sprint Includes:**
- Goal description
- All student tasks
- Role-specific tasks
- Deliverables

**15 Milestones:** Clear criteria for each phase completion.

---

### 10. Student Evaluation Criteria

**File:** `docs/getting-started/evaluation-criteria.md`

**Grading Components:**

| Component | Weight | Description |
|-----------|--------|-------------|
| Code Quality | 30% | Clean, tested, documented code |
| PR Contributions | 25% | Quantity & quality of merged PRs |
| Peer Reviews | 15% | Reviewing others' code effectively |
| Sprint Completion | 15% | Meeting sprint goals consistently |
| Communication | 15% | Participation, collaboration, docs |

**PR Expectations:**
- 15+ merged PRs = A
- 12-14 merged PRs = B
- 10-11 merged PRs = C (minimum passing)
- Quality multipliers (Exceptional 1.5×, Solid 1.0×, Basic 0.75×)

**Trust Bonus:**
- 3-5 merged PRs: +2% to final grade
- 6-9 merged PRs: +3% to final grade
- 10+ merged PRs: +5% to final grade

**Grade Scale:**
- A: 93-100% (Exceptional)
- B: 83-92% (Good)
- C: 73-82% (Acceptable)
- D: 63-72% (Poor)
- F: 0-62% (Failing)

**Feedback Schedule:**
- Weekly updates (Fridays)
- Mid-semester review (Week 8)
- Final evaluation (Week 15)

**Extra Credit:** Up to +5% for going above and beyond.

---

## File Structure

```
docs/
├── templates/
│   └── student-welcome-email.md          # Email template
├── getting-started/
│   ├── quick-start.md                    # Already exists
│   ├── roles.md                          # Already exists
│   ├── communication-channels.md         # NEW
│   ├── office-hours.md                   # NEW
│   ├── faq.md                            # NEW
│   ├── sprint-definitions.md             # NEW
│   ├── evaluation-criteria.md            # NEW
│   └── monday-demo/
│       ├── README.md                     # Already exists
│       ├── demo-script.md                # Already exists
│       ├── github-setup-guide.md         # Already exists
│       └── pre-monday-checklist.md       # Already exists
├── guides/
│   └── github-workflow.md                # Already exists
CODE_OF_CONDUCT.md                         # NEW
CONTRIBUTING.md                            # NEW (extended)
.github/
└── workflows/
    └── onboarding.yml                     # Already exists
```

---

## Data Flow

### Student Onboarding Flow

```
┌─────────────────┐
│  Email Sent     │
│  (24h before)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Student Reads  │
│  Email          │
└────────┬────────┘
         │
         ├──► Joins Community Platform
         ├──► Reads Quick Start
         ├──► Sets up Environment
         └──► Attends Monday Demo
                  │
                  ▼
         ┌─────────────────┐
         │  GitHub Issues  │
         │  Assigned (S0)  │
         └────────┬────────┘
                  │
                  ├──► Issue 1: Environment Setup
                  ├──► Issue 2: Hello World PR
                  └──► Issue 3: Role-Specific Setup
```

### Ongoing Development Flow

```
┌─────────────────┐
│  Find Work      │
│  (Project Board)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Claim Issue    │
│  (Comment)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Create Branch  │
│  & Code         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tests & Docs   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Open PR        │
└────────┬────────┘
         │
         ├──► CI Checks
         ├──► Coverage Report
         ├──► Trust Score Check
         └──► Peer Review
                  │
                  ▼
         ┌─────────────────┐
         │  Merge          │
         │  (Manual/Auto)  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Update Trust   │
         │  & Celebrate!   │
         └─────────────────┘
```

---

## Security & Safety

### Content Moderation
- CODEOWNERS ensures appropriate review
- Safety Filter service for user-generated content
- Human oversight via Operator Console

### Student Safety
- University email required (@edu)
- 2FA encouraged
- Private mentoring available
- Emergency contacts documented

### Code Safety
- Branch protection rules enforced
- Required status checks
- CODEOWNERS approval required
- Auto-merge only for trusted contributors

---

## Implementation Plan

### Pre-Email Tasks (Complete Now)

| Task | File | Status |
|------|------|--------|
| Create student welcome email template | docs/templates/student-welcome-email.md | Pending |
| Create communication channels guide | docs/getting-started/communication-channels.md | Pending |
| Create CODE_OF_CONDUCT.md | CODE_OF_CONDUCT.md | Pending |
| Extend CONTRIBUTING.md | CONTRIBUTING.md | Pending |
| Create student FAQ | docs/getting-started/faq.md | Pending |
| Create office hours schedule | docs/getting-started/office-hours.md | Pending |
| Create sprint definitions | docs/getting-started/sprint-definitions.md | Pending |
| Create evaluation criteria | docs/getting-started/evaluation-criteria.md | Pending |

### Pre-Monday Tasks (Technical Lead)

| Task | Action | Time |
|------|--------|------|
| Create GitHub Project Board | gh project create | 15 min |
| Configure custom fields | UI setup | 10 min |
| Create views | UI setup | 10 min |
| Create Slack workspace | slack.com/create | 20 min |
| Set up channels | Channel setup | 15 min |
| Configure integrations | GitHub/Slack app | 15 min |
| Create labels | Project labels | 10 min |
| Test onboarding workflow | Trigger manually | 10 min |

**Total:** ~2 hours

### Monday Demo Tasks

- Present demo script (already created)
- Verify all 45 Sprint 0 issues created
- Welcome students to community platform
- Assign roles (if not done in email)
- Kick off Sprint 0

---

## Success Criteria

### Immediate (After Email Sent)
- ✅ All 10 documentation files created
- ✅ Email template ready for personalization
- ✅ GitHub Project Board configured
- ✅ Community platform created

### Short-term (After Monday Demo)
- ✅ All 15 students joined community platform
- ✅ All 45 Sprint 0 issues assigned
- ✅ All students have environment setup
- ✅ First 15 PRs opened (Hello World)

### Long-term (After Sprint 0)
- ✅ All 45 Sprint 0 issues completed
- ✅ All 15 students made trusted contributor
- ✅ 45+ PRs merged
- ✅ Team rhythm established

---

## Rollback Plan

If something goes wrong:

1. **Email Issues:** Send correction email immediately
2. **GitHub Issues:** Bulk close/delete via CLI
3. **Project Board:** Delete and recreate
4. **Community Platform:** Archive channels, start fresh

**Communication is key:** If something breaks, tell students immediately and transparently.

---

## Sources

- [Contributor Covenant - Code of Conduct](https://www.contributor-covenant.org/)
- [nayavia Contributing Template](https://github.com/nayafia/contributing-template)
- [GitHub Auto-Merge Documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-feedback-from pull-request-reviews/about-pull-request-auto-merge)
- [GitHub Education Student Developer Pack](https://education.github.com/pack)
- [Good First Issue Finder](https://github.com/munci/good-first-issue-finder)
- [Academic Sprint Evaluation](https://arxiv.org/abs/xxxx) - ANU Software Engineering Project
- [Slack for Education](https://slack.com/education)

---

**Next Step:** Invoke writing-plans skill to create detailed implementation plan with bite-sized tasks.

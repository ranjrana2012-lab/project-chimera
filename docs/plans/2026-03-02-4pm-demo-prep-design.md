# 4pm Demo Preparation Package - Design Document

**Date:** 2026-03-02
**Author:** Project Chimera Team
**Status:** Approved

---

## Overview

Create a complete demo package for the 4pm student onboarding call, including live demo preparation, handouts, email templates, and GitHub self-service portal.

---

## Components

### 1. Demo Preparation (Before 4pm)

**Purpose:** Ensure all services are running and demo is ready

**Deliverables:**
- Service Status Check Script
- Service Startup Script
- Demo Commands Cheat Sheet
- Port-Forward Setup Instructions

---

### 2. One-Page Handout

**Location:** `docs/getting-started/monday-demo/student-handout.md`

**Purpose:** Physical handout for students during/after call

**Front Side Content:**
- Project Chimera overview (3 sentences)
- Architecture diagram (simplified)
- Key links (GitHub, Docs, Slack)
- Quick contact info

**Back Side Content:**
- Role assignment (fill-in during call)
- First 3 steps to get started
- Support channels
- Office hours schedule

---

### 3. Personalized Email Package

**Location:** `scripts/send-welcome-emails.py`

**Purpose:** Send personalized welcome emails after call

**Features:**
- Reads student data from CSV
- Uses `student-welcome-email.md` template
- Substitutes: name, preferred name, email, role, mentor
- Sends via SMTP or GitHub CLI

---

### 4. GitHub Self-Service Portal

**Purpose:** Students can find their tasks and track progress

**Deliverables:**
- Sprint 0 issues created (15 issues, 3 per student)
- Role assignment workflow
- Project board views configured

---

### 5. Updated Demo Script

**Location:** `docs/getting-started/monday-demo/4pm-demo-script.md`

**Purpose:** Guide the 60-minute demo call

**Sections:**
1. Welcome & Overview (10 min)
2. Architecture Walkthrough (10 min)
3. Live Demo: All Services (20 min)
4. Role Assignments (10 min)
5. Contribution Workflow (5 min)
6. Q&A (5 min)

---

## Data Flow

```
Student List (CSV) → Email Script → Personalized Emails
                    ↓
              During Call → Role Assignments → GitHub Issues
                    ↓
              After Call → Send Emails + Update GitHub
```

---

## File Structure

```
Project_Chimera/
├── docs/getting-started/monday-demo/
│   ├── 4pm-demo-script.md          # Updated demo script
│   ├── student-handout.md          # One-page handout
│   └── demo-commands-cheat-sheet.md # Quick commands reference
├── scripts/
│   ├── demo-prep.sh                # Service check and startup
│   └── send-welcome-emails.py      # Personalized email script
├── data/
│   └── students.csv                # Student data (names, emails)
└── .github/
    └── workflows/
        └── assign-roles.yml        # Workflow to update issues with roles
```

---

## Success Criteria

### Before 4pm:
- ✅ All 8 services running and accessible
- ✅ Demo commands cheat sheet ready
- ✅ Student handout ready to print
- ✅ Demo script reviewed

### During 4pm Call:
- ✅ Full system demo shows all services
- ✅ Architecture walkthrough complete
- ✅ Roles assigned and documented
- ✅ Students know their first tasks

### After 4pm Call:
- ✅ Personalized emails sent
- ✅ GitHub issues updated
- ✅ Students can self-service

---

## Student Data

| # | Name | Preferred | Email |
|---|------|-----------|-------|
| 1 | Mahdi Hussain | Mahdi | mahdi.hussain@mail.bcu.ac.uk |
| 2 | Kumba Kuyateh | Kumba | kumba.kuyateh@mail.bcu.ac.uk |
| 3 | Zina Samha | Zina | zina.samha@mail.bcu.ac.uk |
| 4 | Arashdip Singh | Arashdip | arashdip.singh@mail.bcu.ac.uk |
| 5 | Onaopemiposi Adeyeye | Debby | onaopemiposi.adeyeye@mail.bcu.ac.uk |
| 6 | Mohammad Ahmadzai | Mohammad | mohammad.ahmadzai@mail.bcu.ac.uk |
| 7 | Jennifer Ansah | Jennifer | jennifer.ansah@mail.bcu.ac.uk |
| 8 | Fatmazahra Kawan | Fatma | fatmazahra.kawan@mail.bcu.ac.uk |
| 9 | Wasiq Ali | Wasiq | wasiq.ali@mail.bcu.ac.uk |
| 10 | Anzil Mohammed Nahas | Anzil | anzil.nahas@mail.bcu.ac.uk |

---

## Role Assignments (To be filled at 4pm)

| Role | Component | Student |
|------|-----------|---------|
| 1 | OpenClaw Orchestrator | TBD |
| 2 | SceneSpeak Agent | TBD |
| 3 | Captioning Agent | TBD |
| 4 | BSL Translation Agent | TBD |
| 5 | Sentiment Agent | TBD |
| 6 | Lighting Control | TBD |
| 7 | Safety Filter | TBD |
| 8 | Operator Console | TBD |
| 9 | Infrastructure | TBD |
| 10 | QA & Documentation | TBD |

---

**Next Step:** Implementation Plan

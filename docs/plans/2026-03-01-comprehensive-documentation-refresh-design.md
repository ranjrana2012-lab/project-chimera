# Comprehensive Documentation Refresh Design

> **Status:** Approved for Implementation
> **Date:** March 1, 2026
> **Purpose:** Update all documentation to reflect Music Platform, GitHub automation, and v0.2.0 release

---

## Overview

Comprehensive refresh of all Project Chimera documentation to reflect:
- Music Generation Platform (newly implemented)
- GitHub Student Contribution Automation (newly implemented)
- Version update v0.1.0 → v0.2.0
- Improved organization and navigation
- All audiences (students, developers, operators, external users)

---

## Documentation Structure

### Current Structure

```
docs/
├── monday-demo/          # Monday demo docs
├── music-platform/       # Music generation
├── quality-platform/      # Quality platform
├── plans/                 # Design docs
├── runbooks/              # Operational docs
├── architecture/          # Architecture decisions
├── api/                   # API docs
└── standards/             # Style guides
```

### Proposed Structure

```
docs/
├── README.md                      # Main docs index
├── getting-started/               # Consolidated onboarding
│   ├── quick-start.md             # From Student_Quick_Start.md
│   ├── installation.md            # Installation guide
│   ├── first-steps.md             # Tutorial for first contribution
│   ├── monday-demo/               # Monday demo docs
│   │   ├── README.md
│   │   ├── demo-script.md
│   │   ├── github-setup-guide.md
│   │   └── pre-monday-checklist.md
│   └── roles.md                   # From docs/STUDENT_ROLES.md
├── services/                      # Service documentation
│   ├── core-services.md           # 8 AI agents overview
│   ├── music-generation.md        # Music platform (music-generation + music-orchestration)
│   └── quality-platform.md        # Quality platform
├── guides/                        # How-to guides
│   ├── contributing.md            # Contribution workflow
│   ├── github-workflow.md         # GitHub automation guide
│   └── testing.md                 # Testing guide
├── reference/                     # Technical reference
│   ├── architecture.md            # System architecture
│   ├── api.md                     # API documentation
│   └── runbooks/                  # Operational docs
│       ├── monitoring.md
│       ├── incident-response.md
│       ├── deployment.md
│       └── alerts.md
├── plans/                         # Design and implementation docs
├── api/                           # Detailed API docs (service-specific)
├── architecture/                  # Architecture decision records
└── standards/                     # Style guides
```

### Key Changes

1. **Create `getting-started/`** - Consolidate all new user documentation
2. **Create `services/`** - Service-specific documentation
3. **Create `guides/`** - How-to guides for common tasks
4. **Create `reference/`** - Technical reference material
5. **Move `monday-demo/`** - Under `getting-started/`
6. **Move `runbooks/`** - Under `reference/`

---

## Content Updates

### 1. README.md

**Changes:**
- Update version badge: `v0.1.0` → `v0.2.0`
- Add Music Generation Platform to Key Components
- Add GitHub Student Automation to Key Components
- Update Technology Stack
- Update Quick Start section
- Update Documentation links
- Update Roadmap

**New Content to Add:**

```markdown
### Music Generation Platform

- **Music Generation Service** - AI-powered music generation (Meta MusicGen, ACE-Step)
- **Music Orchestration Service** - Caching, approval, and progress streaming

### Student Contribution Automation

- **Trust-Based Auto-Merge** - Students earn trust through quality PRs
- **4 GitHub Actions Workflows** - PR validation, trust checking, auto-merge, onboarding
- **Issue & PR Templates** - Standardized templates for contributors
```

### 2. CHANGELOG.md (Create New)

**Content:**

```markdown
# Changelog

All notable changes to Project Chimera will be documented in this file.

## [0.2.0] - 2026-03-01

### Added
- **Music Generation Platform** - AI-powered local music generation
  - Music Generation Service (port 8011) - Meta MusicGen & ACE-Step models
  - Music Orchestration Service (port 8012) - Caching, approval, WebSocket streaming
  - Support for marketing (auto-approve) and show (manual approval) use cases
- **GitHub Student Contribution Automation** - Complete workflow for 15 AI students
  - Trust-based auto-merge system (3+ merged PRs = trusted contributor)
  - 4 GitHub Actions workflows (validation, trust-check, auto-merge, onboarding)
  - Issue templates (feature, bug, documentation)
  - Pull request template
  - CODEOWNERS for role-based review routing
  - Branch protection with required status checks
- **Monday Demo Documentation** - Complete onboarding package for students

### Changed
- Updated documentation structure for better navigation
- Improved student onboarding experience
- Enhanced GitHub contribution workflow

### Services Status
- OpenClaw Orchestrator: ✅ Production Ready
- SceneSpeak Agent: ✅ Production Ready
- Captioning Agent: ⚠️ Partial (needs minor fixes)
- BSL Translation Agent: ⚠️ Partial (needs minor fixes)
- Sentiment Agent: ⚠️ Partial (needs minor fixes)
- Lighting Control: ✅ Production Ready
- Safety Filter: ⚠️ Partial (needs minor fixes)
- Operator Console: ✅ Production Ready
- Music Generation: ✅ Production Ready (NEW)
- Music Orchestration: ✅ Production Ready (NEW)

## [0.1.0] - 2026-02-28

### Added
- **Initial Scaffold** - 8 AI microservices implemented
  - OpenClaw Orchestrator (port 8000)
  - SceneSpeak Agent (port 8001)
  - Captioning Agent (port 8002)
  - BSL-Text2Gloss Agent (port 8003)
  - Sentiment Agent (port 8004)
  - Lighting Control (port 8005)
  - Safety Filter (port 8006)
  - Operator Console (port 8007)
- **Quality Platform** - Testing and quality infrastructure
  - Test Orchestrator (port 8008)
  - Dashboard Service (port 8009)
  - CI/CD Gateway (port 8010)
- **Bootstrap Setup** - Automated k3s cluster setup
- **Monitoring Stack** - Prometheus, Grafana, Jaeger
- **Documentation** - Initial documentation set

[Full changelog format follows Keep a Changelog](https://keepachangelog.com/)
```

### 3. docs/README.md (Documentation Index)

**Create main documentation hub:**

```markdown
# Project Chimera Documentation

Welcome to the Project Chimera documentation. Use this hub to find what you need.

## Quick Links

| I want to... | Go to |
|--------------|-------|
| Get started with Project Chimera | [Getting Started](getting-started/) |
| Set up my development environment | [Quick Start](getting-started/quick-start.md) |
| Learn about the services | [Services Overview](services/) |
| Contribute code | [Contributing Guide](guides/contributing.md) |
| Understand the GitHub workflow | [GitHub Workflow](guides/github-workflow.md) |
| Read the API docs | [API Reference](reference/api.md) |
| Deploy to production | [Deployment Runbook](reference/runbooks/deployment.md) |

## By Audience

### Students
- [Quick Start Guide](getting-started/quick-start.md)
- [Your Role](getting-started/roles.md)
- [First Steps](getting-started/first-steps.md)
- [Monday Demo](getting-started/monday-demo/)

### Developers
- [Development Guide](DEVELOPMENT.md)
- [Contributing Guide](guides/contributing.md)
- [GitHub Workflow](guides/github-workflow.md)
- [API Reference](reference/api.md)

### Operators
- [Deployment Guide](reference/runbooks/deployment.md)
- [Monitoring](reference/runbooks/monitoring.md)
- [Incident Response](reference/runbooks/incident-response.md)

## Documentation Index

### Getting Started
- [Quick Start](getting-started/quick-start.md) - Set up your environment
- [Installation](getting-started/installation.md) - Detailed installation
- [First Steps](getting-started/first-steps.md) - Your first contribution
- [Roles](getting-started/roles.md) - Student role assignments
- [Monday Demo](getting-started/monday-demo/) - Demo documentation

### Services
- [Core Services](services/core-services.md) - 8 AI agents overview
- [Music Generation](services/music-generation.md) - Music platform
- [Quality Platform](services/quality-platform.md) - Testing infrastructure

### Guides
- [Contributing](guides/contributing.md) - How to contribute
- [GitHub Workflow](guides/github-workflow.md) - GitHub automation
- [Testing](guides/testing.md) - Testing guide

### Reference
- [Architecture](reference/architecture.md) - System architecture
- [API](reference/api.md) - API documentation
- [Runbooks](reference/runbooks/) - Operational docs

### Plans
- Design and implementation documents

---

**Need help?** [Open an issue](https://github.com/project-chimera/project-chimera/issues) or [start a discussion](https://github.com/project-chimera/project-chimera/discussions).
```

### 4. File Moves and Renames

| Old Path | New Path |
|----------|----------|
| `Student_Quick_Start.md` | `docs/getting-started/quick-start.md` |
| `docs/STUDENT_ROLES.md` | `docs/getting-started/roles.md` |
| `docs/monday-demo/README.md` | `docs/getting-started/monday-demo/README.md` |
| `docs/monday-demo/github-setup-guide.md` | `docs/getting-started/monday-demo/github-setup-guide.md` |
| `docs/monday-demo/demo-script.md` | `docs/getting-started/monday-demo/demo-script.md` |
| `docs/monday-demo/pre-monday-checklist.md` | `docs/getting-started/monday-demo/pre-monday-checklist.md` |
| `docs/ARCHITECTURE.md` | `docs/reference/architecture.md` |
| `docs/API.md` | `docs/reference/api.md` |
| `docs/DEPLOYMENT.md` | `docs/reference/runbooks/deployment.md` |
| `docs/runbooks/` | `docs/reference/runbooks/` |

### 5. docs/getting-started/github-workflow.md (Create New)

**Combine content from github-setup-guide.md:**

```markdown
# GitHub Workflow Guide

Complete guide to GitHub automation for Project Chimera contributors.

## Overview

Project Chimera uses automated GitHub workflows to streamline contributions from students and contributors.

## Trust Score System

Your trust level determines whether your PRs can be auto-merged:

| Merged PRs | Trust Level | Label | Auto-Merge? |
|------------|-------------|-------|-------------|
| 0 | New | `trust:new` | Manual review required |
| 1-2 | Learning | `trust:learning` | Manual review required |
| 3+ | Trusted | `trust:trusted` | **Auto-merge eligible** |

## How It Works

### 1. Create an Issue

Use one of the templates:
- **Feature Request** - Propose new features
- **Bug Report** - Report defects
- **Documentation** - Improve docs

### 2. Create a Pull Request

1. Create a feature branch
2. Make your changes
3. Run tests locally
4. Push and create PR

### 3. Automatic Checks

GitHub Actions will automatically:
- Run linting (ruff)
- Run unit tests
- Calculate coverage
- Check your trust score
- Post comments with results

### 4. Merge Decision

**If Trusted (3+ PRs):**
- All checks pass → Auto-merge enabled
- Coverage maintained or increased → Merged automatically
- Coverage decreased → Manual review required

**If New/Learning:**
- Manual review required
- Request review from CODEOWNERS
- After merge, trust score increases

### 5. Earn Trust

Each merged PR increases your trust score:
- 1st PR: New → Learning
- 2nd PR: Learning → Learning
- 3rd PR: Learning → **Trusted** (auto-merge eligible!)

## Protected Files

These files always require manual review:
- `.github/workflows/` - GitHub Actions workflows
- `infrastructure/` - Infrastructure configuration
- `kubernetes/` - Kubernetes manifests
- `secrets/` - Sensitive configuration
- `Dockerfile` - Container definitions

## Quick Commands

```bash
# Trigger onboarding workflow
gh workflow run onboarding.yml -f create_issues=true

# Check workflow status
gh workflow list
gh run list --workflow=pr-validation.yml

# View your PRs
gh pr list

# Create PR from issue
gh pr create --body "Closes #123"
```

## Issue Templates

### Feature Request
```
Title: [FEATURE] Brief description
Labels: type:feature
Sections: Description, Acceptance Criteria, Component
```

### Bug Report
```
Title: [BUG] Brief description
Labels: type:bugfix, priority:high
Sections: Description, Steps to Reproduce, Expected Behavior
```

### Documentation
```
Title: [DOCS] Brief description
Labels: type:docs
Sections: Documentation Change, Files to Update
```

## Project Board

The GitHub Project board organizes work by:
- **Role** - Which component/service
- **Sprint** - Which sprint (0-14)
- **Status** - Backlog, In Progress, Review, Done

Views:
- **By Role** - Swimlane by component
- **By Sprint** - Filter by sprint
- **Monday Onboarding** - Sprint 0 tasks

## Tips for Success

1. **Write good commit messages** - Follow conventional commits
2. **Include tests** - Maintain or increase coverage
3. **Start small** - Your first PR should be manageable
4. **Ask for help** - Use GitHub discussions for questions
5. **Be patient** - Reviewers are volunteers

## Need Help?

- Check [Contributing Guide](../guides/contributing.md)
- [Start a Discussion](https://github.com/project-chimera/project-chimera/discussions)
- Tag `@technical-lead` for urgent issues
```

### 6. docs/services/core-services.md (Create New)

**Document the 8 core AI services:**

```markdown
# Core AI Services

Overview of the 8 AI agents that power Project Chimera.

## Services Overview

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| OpenClaw Orchestrator | 8000 | ✅ Production Ready | Central control plane |
| SceneSpeak Agent | 8001 | ✅ Production Ready | Dialogue generation |
| Captioning Agent | 8002 | ⚠️ Partial | Speech-to-text |
| BSL Translation Agent | 8003 | ⚠️ Partial | BSL gloss translation |
| Sentiment Agent | 8004 | ⚠️ Partial | Audience sentiment |
| Lighting Control | 8005 | ✅ Production Ready | DMX/sACN control |
| Safety Filter | 8006 | ⚠️ Partial | Content moderation |
| Operator Console | 8007 | ✅ Production Ready | Human oversight |

## Service Details

### OpenClaw Orchestrator (Port 8000)

**Purpose:** Central control plane coordinating all agents

**Key Features:**
- Skill routing and execution
- Agent coordination
- GPU resource scheduling
- Policy engine
- Kafka event streaming

**Health Check:**
```bash
curl http://localhost:8000/health/live
```

### SceneSpeak Agent (Port 8001)

**Purpose:** Real-time dialogue generation using local LLMs

**Key Features:**
- LLaMA-based dialogue generation
- LoRA adapter support
- Sentiment-aware generation
- Response caching

**Health Check:**
```bash
curl http://localhost:8001/health/live
```

### Captioning Agent (Port 8002)

**Purpose:** Live speech-to-text with accessibility

**Key Features:**
- OpenAI Whisper transcription
- WebSocket streaming
- Word-level timestamps
- Language auto-detection

**Status:** ⚠️ Partial - Needs minor fixes to response model

### BSL Translation Agent (Port 8003)

**Purpose:** British Sign Language gloss translation

**Key Features:**
- Text-to-gloss translation
- Non-manual marker annotation
- Gloss formatting standards

**Status:** ⚠️ Partial - Needs minor fixes to response model

### Sentiment Agent (Port 8004)

**Purpose:** Audience sentiment analysis from social media

**Key Features:**
- DistilBERT SST-2 model
- Batch text processing
- Trend analysis
- Emotion detection

**Status:** ⚠️ Partial - Needs minor fixes to response model

### Lighting Control (Port 8005)

**Purpose:** DMX/sACN stage automation

**Key Features:**
- DMX/sACN protocol support
- OSC message handling
- Scene preset management
- Fade time control

**Health Check:**
```bash
curl http://localhost:8005/health/live
```

### Safety Filter (Port 8006)

**Purpose:** Multi-layer content moderation

**Key Features:**
- Word-based filtering
- ML-based classification
- Multi-category filtering
- Audit logging

**Status:** ⚠️ Partial - Needs minor fixes to response model

### Operator Console (Port 8007)

**Purpose:** Human oversight interface

**Key Features:**
- Real-time WebSocket updates
- Alert management
- Approval workflow
- Dashboard UI

**Health Check:**
```bash
curl http://localhost:8007/health/live
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                    (Human Oversight)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  OpenClaw Orchestrator                      │
│              (Central Control Plane)                        │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┘
      │       │       │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼       ▼       ▼
  SceneSpeak Captioning  BSL  Sentiment Lighting Safety  Operator
    Agent     Agent    Agent   Agent  Control Filter  Console
```

## Related Documentation

- [Architecture](../reference/architecture.md) - System architecture
- [API Reference](../reference/api.md) - Complete API docs
- [Quality Platform](quality-platform.md) - Testing infrastructure
```

### 7. docs/services/music-generation.md (Create New)

```markdown
# Music Generation Platform

AI-powered local music generation for social media and live shows.

## Overview

The Music Generation Platform enables on-demand music generation using local AI models:
- **Meta MusicGen-Small** - Lightweight model (~2GB VRAM)
- **ACE-Step** - Advanced model (<4GB VRAM)

## Services

### Music Generation Service (Port 8011)

**Purpose:** Direct AI music generation

**Endpoints:**
- `POST /api/v1/music/generate` - Generate music
- `GET /api/v1/music/{id}` - Check status

**Features:**
- Multi-model pool management
- Async generation with cancellation
- VRAM-aware model loading

### Music Orchestration Service (Port 8012)

**Purpose:** Caching, approval, and progress streaming

**Endpoints:**
- `POST /api/v1/music/generate` - Generate with caching
- `GET /api/v1/music/{id}` - Get music status
- `WebSocket /ws/music/{id}` - Real-time progress

**Features:**
- Redis caching with 7-day TTL
- Staged approval (marketing=auto, show=manual)
- WebSocket progress streaming
- MinIO storage integration

## Use Cases

### Marketing (Auto-Approved)
- Social media content
- Promotional materials
- Preview generation

### Show (Manual Approval)
- Live underscore music
- Scene transitions
- Performance audio

## Quick Start

```bash
# Generate music (marketing)
curl -X POST http://localhost:8012/api/v1/music/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "upbeat electronic", "use_case": "marketing", "duration_seconds": 30}'

# Check status
curl http://localhost:8012/api/v1/music/{music_id}
```

## Architecture

```
┌─────────────────┐      ┌──────────────────┐
│   Music Gen     │──────│   Music Orch     │
│   Service       │      │   Service        │
│   (Port 8011)   │      │   (Port 8012)   │
└────────┬────────┘      └────────┬─────────┘
         │                       │
         ▼                       ▼
    ┌─────────┐            ┌──────────┐
    │ Models  │            │  Cache   │
    │MusicGen │            │  Redis   │
    │ACE-Step │            └──────────┘
    └─────────┘                 │
                                ▼
                          ┌──────────┐
                          │  MinIO   │
                          │ Storage  │
                          └──────────┘
```

## Related Documentation

- [Architecture Design](../plans/2026-03-01-music-generation-platform-design.md)
- [API Reference](../reference/api.md#music-generation)
```

---

## Cross-Reference Updates

### README.md Links to Update

| Old Link | New Link |
|----------|----------|
| `Student_Quick_Start.md` | `docs/getting-started/quick-start.md` |
| `docs/STUDENT_ROLES.md` | `docs/getting-started/roles.md` |
| N/A | `docs/services/music-generation.md` |
| N/A | `docs/guides/github-workflow.md` |

### docs/ARCHITECTURE.md Updates

- Add Music Generation Platform services
- Add GitHub automation workflows
- Update service count: 8 → 10

### docs/API.md Updates

- Add Music Generation API endpoints (port 8011)
- Add Music Orchestration API endpoints (port 8012)
- Update service port table

### docs/DEPLOYMENT.md Updates

- Add Music Generation deployment
- Add GitHub automation setup

### docs/DEVELOPMENT.md Updates

- Add GitHub workflow section
- Update PR process with trust system

---

## Metadata and Frontmatter

### Standard Frontmatter Template

```yaml
---
title: "Page Title"
description: "Brief description for SEO and search"
last_updated: "2026-03-01"
tags: [tag1, tag2]
audience: student|developer|operator|all
related:
  - path/to/related/doc.md
---
```

### Tags Taxonomy

- `getting-started` - Onboarding and setup
- `services` - Service-specific docs
- `guides` - How-to guides
- `api` - API documentation
- `deployment` - Deployment and ops
- `architecture` - System design
- `workflow` - GitHub/contribution workflow

### Audience Values

- `student` - Students joining project
- `developer` - Contributors and developers
- `operator` - System operators
- `all` - General audience

---

## Validation and Testing

### 1. Link Validation

```bash
# Check for broken internal links
find docs/ -name "*.md" -exec grep -H "\[.*\](" {} \;

# Verify old references are updated
grep -r "Student_Quick_Start.md" docs/
grep -r "monday-demo/" docs/
```

### 2. Content Completeness

- [ ] All 10 services documented
- [ ] GitHub workflow explained
- [ ] Trust system documented
- [ ] Installation guide complete
- [ ] API docs up to date
- [ ] All badges have correct versions

### 3. Version Consistency

- All `v0.1.0` references updated appropriately
- New `v0.2.0` features documented
- Roadmap reflects delivered work

### 4. Navigation Test

Simulate user journeys:
- New student: README → quick-start → first contribution
- Developer: README → contributing → GitHub workflow
- Operator: README → deployment → monitoring

---

## Implementation Summary

**Files to Create:** ~10 files
- `CHANGELOG.md`
- `docs/README.md`
- `docs/getting-started/github-workflow.md`
- `docs/getting-started/first-steps.md`
- `docs/getting-started/installation.md`
- `docs/services/core-services.md`
- `docs/services/music-generation.md`
- `docs/guides/contributing.md`
- `docs/guides/testing.md`
- `docs/SITEMAP.md`

**Files to Update:** ~15 files
- `README.md`
- All files in `docs/monday-demo/` (moves)
- `Student_Quick_Start.md` (move)
- `docs/STUDENT_ROLES.md` (move)
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/DEPLOYMENT.md`
- `docs/DEVELOPMENT.md`

**Total:** ~25 files to create/update/move

---

**Target:** Complete documentation refresh ready for Monday demo and v0.2.0 release.

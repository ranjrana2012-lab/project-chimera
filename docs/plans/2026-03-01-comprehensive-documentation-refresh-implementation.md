# Comprehensive Documentation Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update all Project Chimera documentation to reflect Music Generation Platform, GitHub Student Contribution Automation, and v0.2.0 release.

**Architecture:** Reorganize docs/ folder into logical hierarchy (getting-started/, services/, guides/, reference/), update main README.md with v0.2.0 features, create CHANGELOG.md, update all cross-references.

**Tech Stack:** Markdown, Git, GitHub CLI (gh)

---

## Task 1: Update README.md with Version and New Features

**Files:**
- Modify: `README.md:1-260`

**Step 1: Update version badge**

Change line 5 from:
```markdown
![Version](https://img.shields.io/badge/version-0.1.0-blue)
```

To:
```markdown
![Version](https://img.shields.io/badge/version-0.2.0-blue)
```

**Step 2: Add Music Generation Platform to Key Components section**

After line 33 (Operator Console), add:
```markdown
### Music Generation Platform

- **Music Generation Service** - AI-powered music generation using Meta MusicGen and ACE-Step models
- **Music Orchestration Service** - Caching, approval workflow, and WebSocket progress streaming
```

**Step 3: Add GitHub Student Automation to Key Components section**

After Music Generation Platform section, add:
```markdown
### Student Contribution Automation

- **Trust-Based Auto-Merge** - Students earn trust through quality PRs (3+ merged = trusted)
- **GitHub Actions Workflows** - PR validation, trust checking, auto-merge, and onboarding automation
- **Issue & PR Templates** - Standardized templates for contributors
```

**Step 4: Update Technology Stack section**

After line 50, add:
```markdown
- **AI/ML:** PyTorch, Transformers, OpenAI Whisper, Meta MusicGen
```

**Step 5: Update Documentation links section**

Replace lines 92-118 with:
```markdown
## Documentation

### For Students and Developers

- [Quick Start Guide](docs/getting-started/quick-start.md) - Set up your development environment
- [Student Roles](docs/getting-started/roles.md) - Component ownership details
- [GitHub Workflow](docs/docs/contributing/github-workflow.md) - GitHub automation and trust system
- [Contributing Guidelines](docs/guides/contributing.md) - How to contribute
- [Development Guide](docs/DEVELOPMENT.md) - Development workflow and coding standards

### Technical Documentation

- [Architecture Overview](docs/docs/reference/architecture.md) - System architecture and design
- [API Documentation](docs/api/README.md) - Complete API reference for all services
- [Deployment Guide](docs/reference/runbooks/deployment.md) - Deployment scenarios and procedures

### Services Documentation

- [Core Services](docs/services/core-services.md) - 8 AI agents overview
- [Music Generation Platform](docs/services/music-generation.md) - Music generation services
- [Quality Platform](docs/services/quality-platform.md) - Testing infrastructure

### Operational Documentation

- [Monitoring Runbook](docs/reference/runbooks/monitoring.md) - Monitoring and alerting setup
- [Incident Response](docs/reference/runbooks/incident-response.md) - Handling incidents
```

**Step 6: Update Roadmap section**

Replace lines 237-253 with:
```markdown
## Roadmap

### v0.2.0 (Current - March 2026)

✅ Music Generation Platform implemented
✅ GitHub Student Contribution Automation implemented
✅ Monday demo documentation complete

### v0.3.0 (Planned)

- Complete service fixes (Captioning, BSL, Sentiment, Safety)
- Multi-scene support
- Enhanced accessibility features

### v1.0.0 (Future)

- Production-ready deployment
- Cloud deployment guides
- Public performances
```

**Step 7: Verify changes**

Run: `head -50 README.md`
Expected: Updated version badge, new sections visible

**Step 8: Commit**

```bash
git add README.md
git commit -m "docs: update README for v0.2.0 with Music Platform and GitHub automation"
```

---

## Task 2: Create CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Create CHANGELOG.md with full content**

Create `CHANGELOG.md`:
```markdown
# Changelog

All notable changes to Project Chimera will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-01

### Added
- **Music Generation Platform** - AI-powered local music generation for social media and live shows
  - Music Generation Service (port 8011) with Meta MusicGen & ACE-Step models
  - Music Orchestration Service (port 8012) with caching, approval, and WebSocket streaming
  - Support for marketing use case (auto-approve) and show use case (manual approval)
  - MinIO storage integration for audio files
- **GitHub Student Contribution Automation** - Complete workflow for 15 AI students
  - Trust-based auto-merge system (3+ merged PRs = trusted contributor)
  - 4 GitHub Actions workflows: validation, trust-check, auto-merge, onboarding
  - Issue templates: feature request, bug report, documentation
  - Pull request template with testing checklist
  - CODEOWNERS file for role-based review routing
  - Branch protection rules with required status checks
  - 15 Sprint 0 onboarding issues for Monday demo
- **Monday Demo Documentation** - Complete onboarding package for students
  - 60-minute demo script with talking points
  - Pre-Monday verification checklist
  - GitHub setup guide for students

### Changed
- Updated documentation structure for better navigation
- Reorganized docs/ into getting-started/, services/, guides/, reference/
- Improved student onboarding experience
- Enhanced GitHub contribution workflow with automation

### Services Status
- OpenClaw Orchestrator: ✅ Production Ready
- SceneSpeak Agent: ✅ Production Ready
- Captioning Agent: ⚠️ Partial (needs minor fixes to response model)
- BSL Translation Agent: ⚠️ Partial (needs minor fixes to response model)
- Sentiment Agent: ⚠️ Partial (needs minor fixes to response model)
- Lighting Control: ✅ Production Ready
- Safety Filter: ⚠️ Partial (needs minor fixes to response model)
- Operator Console: ✅ Production Ready
- Music Generation: ✅ Production Ready (NEW)
- Music Orchestration: ✅ Production Ready (NEW)

### Documentation
- Added comprehensive documentation refresh
- Created getting-started guides for students
- Added service-specific documentation
- Added GitHub workflow guides

## [0.1.0] - 2026-02-28

### Added
- **Initial Scaffold** - 8 AI microservices implemented
  - OpenClaw Orchestrator (port 8000) - Central control plane
  - SceneSpeak Agent (port 8001) - Dialogue generation
  - Captioning Agent (port 8002) - Speech-to-text
  - BSL-Text2Gloss Agent (port 8003) - BSL translation
  - Sentiment Agent (port 8004) - Sentiment analysis
  - Lighting Control (port 8005) - DMX/sACN control
  - Safety Filter (port 8006) - Content moderation
  - Operator Console (port 8007) - Human oversight
- **Quality Platform** - Testing and quality infrastructure
  - Test Orchestrator (port 8008) - Test discovery and execution
  - Dashboard Service (port 8009) - Quality visualization
  - CI/CD Gateway (port 8010) - GitHub/GitLab integration
- **Bootstrap Setup** - Automated k3s cluster setup (make bootstrap)
- **Monitoring Stack** - Prometheus, Grafana, Jaeger
- **Initial Documentation** - Architecture, API, deployment, development guides

### Infrastructure
- k3s cluster configuration
- Redis for caching and pub/sub
- Kafka for event streaming
- Milvus vector database
- MinIO for object storage

[0.2.0]: https://github.com/project-chimera/project-chimera/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/project-chimera/project-chimera/releases/tag/v0.1.0
```

**Step 2: Verify file created**

Run: `cat CHANGELOG.md | head -20`
Expected: CHANGELOG content displayed

**Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG for v0.2.0 release"
```

---

## Task 3: Create docs/getting-started Directory Structure

**Files:**
- Create: `docs/getting-started/`
- Create: `docs/getting-started/monday-demo/`

**Step 1: Create directories**

Run:
```bash
mkdir -p docs/getting-started/monday-demo
```

Expected: Directories created silently

**Step 2: Verify directories created**

Run: `ls -la docs/getting-started/`
Expected: monday-demo subdirectory listed

**Step 3: No commit yet**

(Directories will be populated in subsequent tasks)

---

## Task 4: Move getting-started/quick-start.md to docs/getting-started/quick-start.md

**Files:**
- Move: `getting-started/quick-start.md` → `docs/getting-started/quick-start.md`

**Step 1: Move file**

Run:
```bash
git mv getting-started/quick-start.md docs/getting-started/quick-start.md
```

Expected: File moved silently

**Step 2: Update internal links in moved file**

Run:
```bash
sed -i 's|docs/STUDENT_ROLES.md|getting-started/roles.md|g' docs/getting-started/quick-start.md
sed -i 's|reference/runbooks/bootstrap-setup.md|reference/runbooks/bootstrap-setup.md|g' docs/getting-started/quick-start.md
```

Expected: Files modified silently

**Step 3: Verify file moved**

Run: `ls docs/getting-started/quick-start.md`
Expected: File listed

**Step 4: Commit**

```bash
git add docs/getting-started/quick-start.md
git commit -m "docs: move getting-started/quick-start.md to docs/getting-started/quick-start.md"
```

---

## Task 5: Move docs/STUDENT_ROLES.md to docs/getting-started/roles.md

**Files:**
- Move: `docs/STUDENT_ROLES.md` → `docs/getting-started/roles.md`

**Step 1: Move file**

Run:
```bash
git mv docs/STUDENT_ROLES.md docs/getting-started/roles.md
```

Expected: File moved silently

**Step 2: Update internal links**

Run:
```bash
sed -i 's|getting-started/quick-start.md|getting-started/quick-start.md|g' docs/getting-started/roles.md
```

Expected: File modified silently

**Step 3: Verify file moved**

Run: `ls docs/getting-started/roles.md`
Expected: File listed

**Step 4: Commit**

```bash
git add docs/getting-started/roles.md
git commit -m "docs: move STUDENT_ROLES.md to docs/getting-started/roles.md"
```

---

## Task 6: Move monday-demo Documentation

**Files:**
- Move: `getting-started/monday-demo/*` → `docs/getting-started/monday-demo/`

**Step 1: Move all monday-demo files**

Run:
```bash
git mv getting-started/monday-demo/README.md docs/getting-started/monday-demo/README.md
git mv getting-started/monday-demo/github-setup-guide.md docs/getting-started/monday-demo/github-setup-guide.md
git mv getting-started/monday-demo/demo-script.md docs/getting-started/monday-demo/demo-script.md
git mv getting-started/monday-demo/pre-monday-checklist.md docs/getting-started/monday-demo/pre-monday-checklist.md
```

Expected: Files moved silently

**Step 2: Update internal links in moved files**

Run:
```bash
sed -i 's|getting-started/monday-demo/|getting-started/monday-demo/|g' docs/getting-started/monday-demo/*.md
```

Expected: Files modified silently

**Step 3: Verify files moved**

Run: `ls docs/getting-started/monday-demo/`
Expected: 4 files listed

**Step 4: Commit**

```bash
git add docs/getting-started/monday-demo/
git commit -m "docs: move monday-demo docs to docs/getting-started/monday-demo/"
```

---

## Task 7: Update Links in README.md for Moved Files

**Files:**
- Modify: `README.md`

**Step 1: Update Student_Quick_Start link**

Run:
```bash
sed -i 's|\[Student Quick Start Guide\](getting-started/quick-start.md)|[Student Quick Start Guide](docs/getting-started/quick-start.md)|g' README.md
```

Expected: File modified silently

**Step 2: Update STUDENT_ROLES link**

Run:
```bash
sed -i 's|\[Student Role Assignments\](docs/STUDENT_ROLES.md)|[Student Role Assignments](docs/getting-started/roles.md)|g' README.md
```

Expected: File modified silently

**Step 3: Update documentation links section**

Run:
```bash
sed -i 's|\[Development Guide\](docs/DEVELOPMENT.md)|[Development Guide](docs/DEVELOPMENT.md)|g' README.md
sed -i 's|\[Architecture Overview\](docs/reference/architecture.md)|[Architecture Overview](docs/docs/reference/architecture.md)|g' README.md
sed -i 's|\[API Documentation\](reference/api.md)|[API Documentation](docs/api/README.md)|g' README.md
sed -i 's|\[Deployment Guide\](reference/runbooks/deployment.md)|[Deployment Guide](docs/reference/runbooks/deployment.md)|g' README.md
sed -i 's|\[Monitoring Runbook\](reference/runbooks/monitoring.md)|[Monitoring Runbook](docs/reference/runbooks/monitoring.md)|g' README.md
sed -i 's|\[Incident Response\](reference/runbooks/incident-response.md)|[Incident Response](docs/reference/runbooks/incident-response.md)|g' README.md
sed -i 's|\[Deployment Runbook\](reference/runbooks/deployment.md)|[Deployment Runbook](docs/reference/runbooks/deployment.md)|g' README.md
```

Expected: File modified silently

**Step 4: Verify changes**

Run: `grep -n "docs/" README.md | head -10`
Expected: All links updated

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update README.md links for moved documentation files"
```

---

## Task 8: Create docs/services Directory and Core Services Documentation

**Files:**
- Create: `docs/services/`
- Create: `docs/services/core-services.md`

**Step 1: Create services directory**

Run:
```bash
mkdir -p docs/services
```

Expected: Directory created silently

**Step 2: Create core-services.md**

Create `docs/services/core-services.md`:
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

\`\`\`
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
\`\`\`

## Related Documentation

- [Architecture](../docs/reference/architecture.md) - System architecture
- [API Reference](../reference/api.md) - Complete API docs
- [Quality Platform](quality-platform.md) - Testing infrastructure
```

**Step 3: Verify file created**

Run: `cat docs/services/core-services.md | head -20`
Expected: File content displayed

**Step 4: Commit**

```bash
git add docs/services/
git commit -m "docs: add core services documentation"
```

---

## Task 9: Create docs/services/music-generation.md

**Files:**
- Create: `docs/services/music-generation.md`

**Step 1: Create music-generation.md**

Create `docs/services/music-generation.md`:
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

\`\`\`bash
# Generate music (marketing)
curl -X POST http://localhost:8012/api/v1/music/generate \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "upbeat electronic", "use_case": "marketing", "duration_seconds": 30}'

# Check status
curl http://localhost:8012/api/v1/music/{music_id}
\`\`\`

## Architecture

\`\`\`
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
\`\`\`

## Related Documentation

- [Architecture Design](../plans/2026-03-01-music-generation-platform-design.md)
- [Implementation Plan](../plans/2026-03-01-music-generation-platform-implementation.md)
- [API Reference](../reference/api.md#music-generation)
```

**Step 2: Verify file created**

Run: `cat docs/services/music-generation.md | head -20`
Expected: File content displayed

**Step 3: Commit**

```bash
git add docs/services/music-generation.md
git commit -m "docs: add music generation platform documentation"
```

---

## Task 10: Create docs/guides Directory and Files

**Files:**
- Create: `docs/guides/`
- Create: `docs/docs/contributing/github-workflow.md`

**Step 1: Create guides directory**

Run:
```bash
mkdir -p docs/guides
```

Expected: Directory created silently

**Step 2: Create github-workflow.md**

Create `docs/docs/contributing/github-workflow.md`:
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

\`\`\`bash
# Trigger onboarding workflow
gh workflow run onboarding.yml -f create_issues=true

# Check workflow status
gh workflow list
gh run list --workflow=pr-validation.yml

# View your PRs
gh pr list

# Create PR from issue
gh pr create --body "Closes #123"
\`\`\`

## Issue Templates

### Feature Request
\`\`\`
Title: [FEATURE] Brief description
Labels: type:feature
Sections: Description, Acceptance Criteria, Component
\`\`\`

### Bug Report
\`\`\`
Title: [BUG] Brief description
Labels: type:bugfix, priority:high
Sections: Description, Steps to Reproduce, Expected Behavior
\`\`\`

### Documentation
\`\`\`
Title: [DOCS] Brief description
Labels: type:docs
Sections: Documentation Change, Files to Update
\`\`\`

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

- [Contributing Guide](contributing.md)
- [Quick Start](../getting-started/quick-start.md)
- [Start a Discussion](https://github.com/project-chimera/project-chimera/discussions)
```

**Step 3: Verify file created**

Run: `cat docs/docs/contributing/github-workflow.md | head -30`
Expected: File content displayed

**Step 4: Commit**

```bash
git add docs/guides/
git commit -m "docs: add GitHub workflow guide"
```

---

## Task 11: Create docs/README.md Documentation Index

**Files:**
- Create: `docs/README.md`

**Step 1: Create docs index**

Create `docs/README.md`:
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
| Understand the GitHub workflow | [GitHub Workflow](docs/contributing/github-workflow.md) |
| Read the API docs | [API Reference](reference/api.md) |
| Deploy to production | [Deployment Runbook](reference/runbooks/deployment.md) |

## By Audience

### Students
- [Quick Start Guide](getting-started/quick-start.md)
- [Your Role](getting-started/roles.md)
- [First Steps](getting-started/first-steps.md)
- [Monday Demo](getting-started/monday-demo/)

### Developers
- [Development Guide](../DEVELOPMENT.md)
- [Contributing Guide](guides/contributing.md)
- [GitHub Workflow](docs/contributing/github-workflow.md)
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
- [GitHub Workflow](docs/contributing/github-workflow.md) - GitHub automation
- [Testing](guides/testing.md) - Testing guide

### Reference
- [Architecture](docs/reference/architecture.md) - System architecture
- [API](reference/api.md) - API documentation
- [Runbooks](reference/runbooks/) - Operational docs

### Plans
- Design and implementation documents

---

**Need help?** [Open an issue](https://github.com/project-chimera/project-chimera/issues) or [start a discussion](https://github.com/project-chimera/project-chimera/discussions).
```

**Step 2: Verify file created**

Run: `cat docs/README.md | head -40`
Expected: File content displayed

**Step 3: Commit**

```bash
git add docs/README.md
git commit -m "docs: add documentation index and hub"
```

---

## Task 12: Update docs/reference/architecture.md with New Services

**Files:**
- Modify: `docs/reference/architecture.md`

**Step 1: Backup and move architecture doc**

Run:
```bash
mkdir -p docs/reference
git mv docs/reference/architecture.md docs/docs/reference/architecture.md
```

Expected: File moved silently

**Step 2: Add Music Generation Platform to architecture**

After the "Quality Platform" section, add:
```markdown
### Music Generation Platform

- **Music Generation Service** (port 8011)
  - AI music generation using Meta MusicGen and ACE-Step models
  - Model pool management with VRAM-aware loading
  - Async generation with cancellation support
- **Music Orchestration Service** (port 8012)
  - Request routing with cache-first approach
  - Redis caching with 7-day TTL
  - Staged approval pipeline (marketing=auto, show=manual)
  - WebSocket progress streaming
  - MinIO storage for audio files
```

**Step 3: Add GitHub Automation section**

After Music Generation Platform, add:
```markdown
### GitHub Student Automation

- **Trust-Based Auto-Merge** - Students earn trust (3+ PRs = trusted)
- **GitHub Actions Workflows**
  - PR Validation (lint, test, coverage)
  - Trust Check (query merged PRs)
  - Auto-Merge (trusted contributors)
  - Onboarding (Sprint 0 issues)
- **CODEOWNERS** - Role-based review routing
- **Branch Protection** - Required status checks and reviews
```

**Step 4: Update service counts throughout**

Find all occurrences of "8 services" or "8 agents" and update to "10 services" or "10 agents" where appropriate.

**Step 5: Commit**

```bash
git add docs/docs/reference/architecture.md
git commit -m "docs: move and update ARCHITECTURE.md with Music Platform and GitHub automation"
```

---

## Task 13: Update reference/api.md with New Endpoints

**Files:**
- Modify: `reference/api.md`

**Step 1: Move API docs to reference folder**

Run:
```bash
git mv reference/api.md docs/api/README.md
```

Expected: File moved silently

**Step 2: Add Music Generation endpoints**

After existing service endpoints, add:
```markdown
## Music Generation Service (Port 8011)

### Generate Music

**POST** `/api/v1/music/generate`

Generate music using AI models.

**Request:**
\`\`\`json
{
  "prompt": "upbeat electronic music",
  "use_case": "marketing",
  "duration_seconds": 30,
  "format": "mp3"
}
\`\`\`

**Response:**
\`\`\`json
{
  "request_id": "uuid",
  "music_id": "uuid",
  "status": "generating",
  "audio_url": null
}
\`\`\`

### Get Music Status

**GET** `/api/v1/music/{music_id}`

Get generation status and download URL.

**Response:**
\`\`\`json
{
  "music_id": "uuid",
  "status": "completed",
  "audio_url": "https://...",
  "duration_seconds": 30,
  "format": "mp3"
}
\`\`\`

## Music Orchestration Service (Port 8012)

### Generate Music (with caching)

**POST** `/api/v1/music/generate`

Generate music with caching and approval workflow.

**Request:**
\`\`\`json
{
  "prompt": "dramatic underscore",
  "use_case": "show",
  "duration_seconds": 60,
  "format": "wav"
}
\`\`\`

**Response:**
\`\`\`json
{
  "request_id": "uuid",
  "music_id": "uuid",
  "status": "generating",
  "audio_url": null,
  "was_cache_hit": false
}
\`\`\`

### WebSocket Progress Streaming

**WebSocket** `/ws/music/{request_id}`

Real-time progress updates during generation.

**Message:**
\`\`\`json
{
  "request_id": "uuid",
  "type": "progress",
  "progress": 45,
  "stage": "generating",
  "eta_seconds": 30
}
\`\`\`
```

**Step 3: Update service port table**

Add to the ports table:
| Service | Port |
|---------|------|
| Music Generation | 8011 |
| Music Orchestration | 8012 |

**Step 4: Commit**

```bash
git add docs/api/README.md
git commit -m "docs: move and update API.md with Music Platform endpoints"
```

---

## Task 14: Update Reference Links Throughout Documentation

**Files:**
- Modify: Multiple documentation files

**Step 1: Update all references to moved files**

Run:
```bash
# Find and replace old paths
find docs/ -name "*.md" -type f -exec sed -i 's|docs/reference/architecture.md|docs/reference/architecture.md|g' {} \;
find docs/ -name "*.md" -type f -exec sed -i 's|reference/api.md|reference/api.md|g' {} \;
find docs/ -name "*.md" -type f -exec sed -i 's|reference/runbooks/deployment.md|reference/runbooks/deployment.md|g' {} \;
find docs/ -name "*.md" -type f -exec sed -i 's|reference/runbooks/|reference/runbooks/|g' {} \;
```

Expected: Files modified silently

**Step 2: Update Master Documentation Monday link**

Run:
```bash
sed -i 's|MASTER_DOCUMENTATION_MONDAY.md|getting-started/monday-demo/README.md|g' README.md
```

Expected: File modified silently

**Step 3: Verify no broken links remain**

Run:
```bash
grep -r "Student_Quick_Start" docs/ 2>/dev/null || echo "No old references found"
grep -r "docs/monday-demo" docs/ 2>/dev/null | grep -v "getting-started/monday-demo" || echo "No old monday-demo references found"
```

Expected: No old references found (or minimal)

**Step 4: Commit**

```bash
git add docs/
git commit -m "docs: update cross-references after documentation restructure"
```

---

## Task 15: Create Git Tag for v0.2.0

**Files:**
- None (tagging existing commits)

**Step 1: Create annotated tag**

Run:
```bash
git tag -a v0.2.0 -m "Project Chimera v0.2.0

Major update adding Music Generation Platform and GitHub Student Contribution Automation.

Features:
- Music Generation Platform (services on ports 8011, 8012)
- GitHub Student Contribution Automation (trust-based auto-merge)
- Comprehensive documentation refresh
- 15 Sprint 0 onboarding issues for students

Services: 10 total (8 core + 2 music platform)
Status: 6 Production Ready, 4 Partial (need minor fixes)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

Expected: Tag created silently

**Step 2: Verify tag**

Run:
```bash
git tag -l "v0.2.0"
git show v0.2.0 --stat
```

Expected: Tag details displayed

**Step 3: Commit**

(Tags are created, not committed. No git commit needed.)

---

## Task 16: Final Documentation Verification

**Files:**
- None (verification only)

**Step 1: Check all new files exist**

Run:
```bash
echo "=== New Files ===" && \
echo "CHANGELOG.md:" && ls -la CHANGELOG.md && \
echo "docs/getting-started/:" && ls docs/getting-started/ && \
echo "docs/services/:" && ls docs/services/ && \
echo "docs/guides/:" && ls docs/guides/ && \
echo "docs/README.md:" && ls docs/README.md
```

Expected: All new files/directories listed

**Step 2: Verify link updates**

Run:
```bash
echo "=== Checking for old references ===" && \
echo "getting-started/quick-start.md references:" && \
grep -r "getting-started/quick-start.md" . --include="*.md" | grep -v ".git" | wc -l && \
echo "docs/STUDENT_ROLES.md references:" && \
grep -r "docs/STUDENT_ROLES.md" . --include="*.md" | grep -v ".git" | wc -l
```

Expected: 0 old references

**Step 3: Verify version consistency**

Run:
```bash
echo "=== Version consistency ===" && \
grep -r "v0.2.0" README.md CHANGELOG.md | wc -l
```

Expected: At least 2 occurrences

**Step 4: Display summary**

Run:
```bash
echo "=== Documentation Refresh Complete ===" && \
echo "" && \
echo "Files created:" && \
git log --oneline -15 | grep -c "docs:" && \
echo "" && \
echo "Git tag:" && \
git describe --tags --abbrev=0
```

Expected: Summary displayed

**Step 5: No commit**

(Verification step - no changes to commit)

---

## Summary

**Total Tasks:** 16
**Estimated Time:** 2-3 hours
**Target:** Complete documentation refresh for v0.2.0 release

### Deliverables

1. **Updated README.md** - v0.2.0 with Music Platform and GitHub automation
2. **CHANGELOG.md** - v0.1.0 and v0.2.0 release notes
3. **Reorganized docs/** - New folder structure (getting-started/, services/, guides/, reference/)
4. **Moved files** - getting-started/quick-start.md, STUDENT_ROLES.md, monday-demo/
5. **New documentation** - core-services.md, music-generation.md, github-workflow.md
6. **Updated cross-references** - All links updated to new paths
7. **Git tag v0.2.0** - Annotated tag for release

### Documentation Hierarchy After Refresh

```
docs/
├── README.md                      # Documentation hub
├── getting-started/               # Student onboarding
│   ├── quick-start.md
│   ├── roles.md
│   └── monday-demo/
├── services/                      # Service docs
│   ├── core-services.md
│   └── music-generation.md
├── guides/                        # How-to guides
│   └── github-workflow.md
├── reference/                     # Technical reference
│   ├── architecture.md
│   ├── api.md
│   └── runbooks/
└── plans/                         # Design docs
```

---

**Plan complete and saved to `docs/plans/2026-03-01-comprehensive-documentation-refresh-implementation.md`.**

# Changelog

All notable changes to Project Chimera will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-03-03

### Added
- **WorldMonitor Integration** - Global intelligence platform integration with Sentiment Agent
  - WorldMonitor sidecar service (Node.js) for news aggregation and context calculation
  - Country Instability Index (CII) scoring for sentiment context
  - Real-time context updates via WebSocket streaming
  - News sentiment analysis using aggregated news feeds
  - Sidecar deployment pattern for service integration
  - Context-aware sentiment responses with global context
  - Comprehensive test coverage (38 tests passing)

### New API Endpoints
- `GET /api/v1/context/global` - Global context with CII scores, threats, events
- `GET /api/v1/context/country/{code}` - Country-specific context
- `WebSocket /api/v1/context/stream` - Real-time context updates
- `POST /api/v1/news/sentiment` - News sentiment analysis

### Changed
- **Sentiment Agent Enhanced:** Now includes global context enrichment from WorldMonitor
- Response model extended with optional `context` field
- Configuration extended with WorldMonitor settings
- k3s deployment updated for sidecar pattern

### Services Status
- OpenClaw Orchestrator: ✅ Production Ready
- SceneSpeak Agent: ✅ Production Ready
- Captioning Agent: ⚠️ Partial (needs minor fixes to response model)
- BSL Translation Agent: ⚠️ Partial (needs minor fixes to response model)
- **Sentiment Agent: ✅ Production Ready (Enhanced with WorldMonitor)**
- Lighting, Sound & Music: ✅ Production Ready
- Safety Filter: ⚠️ Partial (needs minor fixes to response model)
- Operator Console: ✅ Production Ready
- **WorldMonitor Sidecar: ✅ Production Ready (NEW)**

## [0.5.0] - 2026-03-14

### Added
- **Production Hardening** - Kubernetes Pod Security Standards implementation
  - Pod Security Admission configuration enforcing Baseline policy
  - All 9 services updated with comprehensive security contexts
  - Non-root user enforcement (UID 1000)
  - Privilege escalation prevention
  - Seccomp profiles (RuntimeDefault)
  - All capabilities dropped
  - Automated security validation script
  - Security documentation and quick reference guides

- **Autonomous Agent Integration** - VMAO Framework implementation
  - OpenClaw client for multi-agent coordination
  - VMAO verifier: Plan-Execute-Verify-Replan cycle
  - Enhanced GSD orchestrator with verification phase
  - Parallel agent execution with dependency awareness
  - Integration tests and demo scripts
  - New API endpoints: /api/agents, /api/health/dependencies, /api/demo/multi-agent

- **Educational Platform** - AI-Powered Learning System (Port 8012)
  - Student profiles with learning styles and accessibility needs
  - Curriculum management with courses, lessons, assessments
  - BSL, captioning, and sentiment agent integration
  - Educator CLI for classroom management
  - Learning analytics and engagement tracking
  - BMet partnership ready with accessibility-first design
  - WebSocket support for real-time updates
  - OpenTelemetry distributed tracing
  - Prometheus metrics (20+ metrics)

- **Live Show Automation** - Director Agent (Port 8013)
  - Director Agent service for show orchestration
  - YAML-based show definition DSL with scenes and actions
  - Scene execution engine with multi-agent choreography
  - Safety controls: emergency stop, human approval gates, timeouts
  - WebSocket real-time show state updates
  - Audience adaptation based on sentiment analysis
  - 2 example shows: welcome_show.yaml and adaptive_show.yaml

### New Services
- **Educational Platform** (Port 8012) - AI-powered learning platform
- **Director Agent** (Port 8013) - Live show automation orchestration

### New API Endpoints

**Autonomous Agent (Port 8008):**
- `GET /api/agents` - List available agents from OpenClaw
- `GET /api/health/dependencies` - Check multi-agent health
- `POST /api/demo/multi-agent` - Demonstrate multi-agent workflow

**Educational Platform (Port 8012):**
- `POST /api/students` - Create student profile
- `GET /api/students/{id}` - Get student details
- `POST /api/courses` - Create course
- `GET /api/courses` - List all courses
- `POST /api/enrollments` - Enroll student in course
- `GET /api/learning/recommendations/{student_id}` - Get personalized recommendations
- `WebSocket /ws/students/{id}` - Real-time student updates
- `WebSocket /ws/educators` - Real-time educator dashboard

**Director Agent (Port 8013):**
- `POST /api/shows/load` - Load show from file
- `GET /api/shows` - List all shows
- `GET /api/shows/{show_id}` - Get show details
- `POST /api/shows/{show_id}/start` - Start show
- `POST /api/shows/{show_id}/pause` - Pause show
- `POST /api/shows/{show_id}/resume` - Resume show
- `POST /api/shows/{show_id}/stop` - Stop show
- `GET /api/shows/{show_id}/state` - Get current state
- `WebSocket /ws/show/{show_id}` - Real-time show updates

### Security
- All services now enforce Baseline Pod Security Standards
- Security contexts applied to all deployments
- Automated security validation via `scripts/test-security-contexts.sh`
- Security documentation in `docs/security/`

### Documentation
- 15+ new comprehensive guides created
- Educational Platform API documentation
- Director Agent show creators guide
- Live Show Automation guide
- Security hardening guides
- Autonomous Agent Integration documentation

### Files Created
- 46 new files
- 25,000+ lines of code
- Kubernetes manifests for 2 new services

### Services Status
- OpenClaw Orchestrator: ✅ Production Ready
- SceneSpeak Agent: ✅ Production Ready
- Captioning Agent: ✅ Production Ready
- BSL Agent: ✅ Production Ready
- Sentiment Agent: ✅ Production Ready
- Lighting, Sound & Music: ✅ Production Ready
- Safety Filter: ✅ Production Ready
- Operator Console: ✅ Production Ready
- Autonomous Agent: ✅ Production Ready (Enhanced with VMAO)
- **Educational Platform: ✅ Production Ready (NEW)**
- **Director Agent: ✅ Production Ready (NEW)**

### Migration Notes
- No breaking changes to existing services
- All new services are opt-in
- Security contexts are backward compatible
- See individual service documentation for setup instructions

## [Unreleased]

### Added
- **Visual Services Layer** - New video intelligence capability
  - Visual Core service (port 8014) - LTX-2 integration hub
  - Sentiment Agent enhanced with video briefing endpoints
  - First Visual Intelligence Report demo
  - End-to-end video generation pipeline from sentiment analysis
  - Prompt engineering templates for corporate, documentary, social media styles
  - FFmpeg video processing pipeline for ARM64 (DGX Spark optimized)
  - Kubernetes deployment with security contexts and autoscaling (2-8 replicas)

### Planned
- Additional service enhancements
- Performance optimizations
- Documentation improvements

## [0.3.0] - 2026-03-02

### Added
- **Lighting, Sound & Music (LSM)** - Unified audio-visual control service (port 8005)
  - Consolidated Lighting Control, Music Generation, and Music Orchestration into single service
  - Integrated ACE-Step-1.5 models (base, sft, turbo, mlx) for AI music generation
  - Coordinated cues module for synchronized multi-media scenes
  - Sound effects library with playback and mixing capabilities
  - Flat API structure: `/lighting/*`, `/sound/*`, `/music/*`, `/cues/*`
  - WebSocket support for real-time generation and execution updates
  - Kubernetes deployment manifests with PVCs for models and audio
  - Comprehensive configuration management (config.yaml + env vars)

### Changed
- **8 Core Pillars Updated:** Lighting Control (port 8005) → Lighting, Sound & Music
- Simplified student onboarding with single audio-visual component instead of three
- Improved API consistency with flat route structure across all modules

### Deprecated
- `services/lighting-control` - Merged into LSM service
- `services/music-generation` - Merged into LSM service
- `services/music-orchestration` - Merged into LSM service

### Migration Notes
- All lighting functionality preserved: `/v1/lighting/*` → `/lighting/*`
- All music generation preserved with ACE-Step-1.5: `/generate` → `/music/generate`
- All orchestration preserved in cues module: `/cues/*`

### Services Status
- OpenClaw Orchestrator: ✅ Production Ready
- SceneSpeak Agent: ✅ Production Ready
- Captioning Agent: ⚠️ Partial (needs minor fixes to response model)
- BSL Translation Agent: ⚠️ Partial (needs minor fixes to response model)
- Sentiment Agent: ⚠️ Partial (needs minor fixes to response model)
- **Lighting, Sound & Music: ✅ Production Ready (NEW - replaces 3 services)**
- Safety Filter: ⚠️ Partial (needs minor fixes to response model)
- Operator Console: ✅ Production Ready

---

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
  - GitHub Project Board setup instructions

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

[0.4.0]: https://github.com/project-chimera/project-chimera/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/project-chimera/project-chimera/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/project-chimera/project-chimera/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/project-chimera/project-chimera/releases/tag/v0.1.0

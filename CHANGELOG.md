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

[0.2.0]: https://github.com/project-chimera/project-chimera/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/project-chimera/project-chimera/releases/tag/v0.1.0

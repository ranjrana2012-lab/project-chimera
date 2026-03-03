# Project Chimera - Student Handout
## Monday Demo Session

---

## Project Overview

Project Chimera is an innovative, full-stack application designed to demonstrate modern software development practices. This project integrates cutting-edge technologies to build a scalable, maintainable, and efficient system that serves as a comprehensive learning platform for advanced development concepts.

**Key Features:**
- Microservices architecture with container orchestration
- Real-time data processing and analytics
- Modern frontend with responsive design
- Comprehensive testing and CI/CD pipeline
- Cloud-native deployment strategies

---

## Essential Links

| Resource | URL | Purpose |
|----------|-----|---------|
| **Main Repository** | [github.com/your-org/project-chimera](https://github.com/your-org/project-chimera) | Source code & collaboration |
| **Documentation** | [docs.project-chimera.dev](https://docs.project-chimera.dev) | Technical documentation |
| **Demo Script** | `/docs/getting-started/monday-demo/demo-script.md` | Today's live demo guide |
| **Setup Guide** | `/docs/getting-started/monday-demo/github-setup-guide.md` | GitHub & environment setup |
| **Issue Tracker** | [github.com/your-org/project-chimera/issues](https://github.com/your-org/project-chimera/issues) | Bug reports & feature requests |
| **Slack Workspace** | [project-chimera.slack.com](https://project-chimera.slack.com) | Team communication |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Project Chimera                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Frontend   │────▶│   API Gateway│────▶│  Services    │    │
│  │   (React)    │◀────│   (Express)  │◀────│  (Node.js)   │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         │                    ▼                    ▼             │
│         │           ┌──────────────┐     ┌──────────────┐       │
│         └──────────▶│  Auth Svc    │     │  Data Svc    │       │
│                     │  (OAuth2)    │     │  (PostgreSQL)│       │
│                     └──────────────┘     └──────────────┘       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure: Docker │ K8s │ CI/CD │ Monitoring │ Logging  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Role Assignment

Fill in your team members for each role:

| Role | Name | GitHub Handle | Email |
|------|------|---------------|-------|
| **Team Lead** | __________________ | __________________ | __________________ |
| **Frontend Dev** | __________________ | __________________ | __________________ |
| **Backend Dev** | __________________ | __________________ | __________________ |
| **DevOps Eng** | __________________ | __________________ | __________________ |
| **QA Engineer** | __________________ | __________________ | __________________ |
| **Documentation** | __________________ | __________________ | __________________ |

---

## Getting Started - First 3 Steps

### Step 1: Repository Setup
```bash
# Fork the main repository to your GitHub account
# Clone your fork locally
git clone https://github.com/YOUR_USERNAME/project-chimera.git
cd project-chimera

# Add upstream remote
git remote add upstream https://github.com/your-org/project-chimera.git
```

### Step 2: Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit with your local configuration
nano .env

# Install dependencies
npm install
```

### Step 3: Launch Application
```bash
# Start development servers
npm run dev

# Access application
# Frontend: http://localhost:3000
# API: http://localhost:8080
```

---

## Support Channels

| Channel | Response Time | Best For |
|---------|---------------|----------|
| **Slack #help** | ~15 minutes | Quick questions, pair programming |
| **GitHub Issues** | 24-48 hours | Bugs, feature requests, documentation |
| **Office Hours** | Immediate | Deep dive discussions, code review |
| **Email Support** | 48-72 hours | Formal inquiries, escalation |

---

## Office Hours Schedule

| Day | Time | Location | Host |
|-----|------|----------|------|
| **Monday** | 2:00 PM - 4:00 PM | Room 301 | Prof. Smith |
| **Wednesday** | 3:00 PM - 5:00 PM | Virtual (Zoom) | TA Johnson |
| **Friday** | 10:00 AM - 12:00 PM | Room 301 | TA Williams |

**Note:** Additional sessions available by appointment. Check Slack for updates.

---

## This Week's Checklist

### Monday
- [ ] Attend demo session
- [ ] Set up development environment
- [ ] Complete GitHub setup
- [ ] Join Slack workspace

### Tuesday
- [ ] Review documentation thoroughly
- [ ] Run local development environment
- [ ] Complete first tutorial exercise
- [ ] Introduce yourself in #introductions

### Wednesday
- [ ] Attend office hours (optional)
- [ ] Submit first pull request
- [ ] Set up code review pairing
- [ ] Complete assigned role setup

### Thursday
- [ ] Review team charter
- [ ] Sprint planning session
- [ ] Set up project board
- [ ] Establish communication protocols

### Friday
- [ ] Weekly retrospective
- [ ] Submit weekly progress report
- [ ] Plan next week's tasks
- [ ] Celebrate wins!

---

## Need Help?

### Quick Help Resources
1. **Search existing issues** before creating new ones
2. **Check documentation** - your answer might be there
3. **Ask in Slack #help** for fastest response
4. **Review error messages** carefully before asking

### When to Escalate
- Blocking issues preventing progress
- Unclear requirements or expectations
- Technical difficulties beyond your expertise
- Team coordination challenges

### Emergency Contacts
- **Instructor:** instructor@project-chimera.edu
- **Lead TA:** ta-lead@project-chimera.edu
- **SysAdmin:** sysadmin@project-chimera.edu

---

## Welcome to Project Chimera!

We're excited to have you join us on this journey. This project is designed to challenge you, expand your skills, and prepare you for real-world software development. Remember:

- **Ask questions early** - curiosity is your greatest asset
- **Collaborate freely** - we learn better together
- **Embrace failure** - mistakes are valuable learning opportunities
- **Stay curious** - technology evolves, and so should you

**Let's build something amazing together!**

---

*Document Version: 1.0*
*Last Updated: March 2026*
*Session: Spring 2026*

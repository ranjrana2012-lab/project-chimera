# Project Chimera: Monday Student Onboarding Demo Script
**Duration:** 60 minutes
**Target Audience:** New students joining the project
**Facilitator:** Project Lead or Senior Developer

---

## 📋 Prerequisites Checklist

**Before Demo Start:**
- [ ] GitHub repository cloned and accessible
- [ ] Development environment set up (Node.js, git, editor)
- [ ] Project dependencies installed (`npm install`)
- [ ] Demo branch created and updated with latest code
- [ ] Sample API server running on port 3000
- [ ] Figma link shared for UI reference
- [ ] Project documentation URLs available
- [ ] Backup plan ready (can switch to slides/presentation mode)

**Required Files/Documents:**
- [ ] README.md
- [ ] TRD_Project_Chimera.md
- [ ] ARCHITECTURE.md
- [ ] Component Map
- [ ] Wireframes/Design System

---

## ⏱️ Demo Timeline

### 0:00-0:10 | Welcome & Project Overview

**Goal:** Introduce the project, purpose, and logistics

**Talking Points:**
- Welcome and introductions
- Project Chimera overview (problem we're solving)
- What students will build by the end of the semester
- Team structure and mentorship
- What to expect today

**Visual Aids:**
- Project landing page
- High-level architecture diagram
- Team page with roles

**Shell Commands:**
```bash
# Show current branch
git branch

# Show latest commit info
git log -1 --oneline

# List project structure
tree -L 2 -d
```

**Handouts:**
- Welcome email
- Project links (GitHub, Figma, docs)
- Setup guide

---

### 0:10-0:20 | GitHub Repository Tour

**Goal:** Help students navigate the repository structure

**Talking Points:**
- Understanding the repository layout
- Key directories and their purposes
- Accessing documentation
- Version control basics

**Shell Commands:**
```bash
# Show root directory structure
ls -la

# Show documentation hierarchy
tree docs -L 2

# Show GitHub statistics (if accessible)
# gh repo view --json openIssues,openPullRequests
```

**Key Locations to Highlight:**
- `/docs/` - All project documentation
- `/src/` - Main source code
- `/scripts/` - Helper scripts and bootstrap tools
- `/tests/` - Test suite
- `/packages/` - Monorepo packages

**Navigation Demo:**
```bash
# Navigate to docs
cd /home/ranj/Project_Chimera/docs

# Show project structure
find . -name "*.md" | head -10

# View main README
cat README.md | less
```

---

### 0:20-0:30 | Component Assignments

**Goal:** Explain how students get assigned to components and what they need to know

**Talking Points:**
- Component ownership model
- How to claim a component
- Component lifecycle (TODOs, PRs, merges)
- Communication channels

**Shell Commands:**
```bash
# Show current active components
grep -r "TODO" /home/ranj/Project_Chimera/src --include="*.tsx" --include="*.ts" | wc -l

# Show component directories
ls -la /home/ranj/Project_Chimera/src/components
```

**Assignments Process:**
1. Check the Component Map
2. Choose an available component
3. Comment on the component issue/Pull Request
4. Set up development environment for that component
5. Start with TODO comments in the code

**Resources:**
- Link to Component Map
- Link to Contribution Guidelines
- Example PR template

---

### 0:30-0:40 | Live Demo: Working Services

**Goal:** Demonstrate the current project state with live services

**Goal:** Show how services work and students can interact with them

**Talking Points:**
- What services are currently running
- API endpoints available
- How to test endpoints
- Database connections
- Service architecture

**Shell Commands - Start Services:**
```bash
# Navigate to project root
cd /home/ranj/Project_Chimera

# Install dependencies (if not already done)
npm install

# Start the main API server
npm start

# Server should start on port 3000
# Listen address: http://localhost:3000
```

**Testing the Service:**
```bash
# Test the health endpoint
curl http://localhost:3000/api/health

# Get all users
curl http://localhost:3000/api/users

# Get specific user
curl http://localhost:3000/api/users/1

# Post new user (example)
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo User","email":"demo@example.com"}'
```

**API Documentation:**
- Show Swagger/OpenAPI docs if available
- Point to API endpoints list
- Explain authentication (if applicable)

**Demo Services to Show:**
1. User Service - CRUD operations
2. Auth Service - Login/logout flow
3. Analytics Service - Data endpoints
4. Notification Service - Real-time updates

---

### 0:40-0:50 | Contribution Workflow Demo

**Goal:** Show how to contribute code to the project

**Talking Points:**
- Git workflow (branch, commit, push)
- Pull request process
- Code review expectations
- CI/CD pipeline
- How to run tests locally

**Shell Commands - Git Workflow:**
```bash
# Check current branch
git branch

# Create a feature branch
git checkout -b feature/new-component

# Stage changes
git add src/components/NewComponent/

# Commit changes
git commit -m "feat: add new component for user dashboard

- Create NewComponent.tsx
- Add styling
- Implement basic functionality

Closes #123"

# Push to remote
git push origin feature/new-component

# Create pull request (show in browser)
# gh pr create --title "Add new component" --body "Description..."

# View pull requests
gh pr list
```

**Code Review Process:**
- Review PR template
- Comment on PRs
- Address feedback
- Merge after approval

**Testing Locally:**
```bash
# Run all tests
npm test

# Run specific test
npm test -- User.test.ts

# Run linter
npm run lint

# Format code
npm run format
```

**CI/CD Demo:**
- Show GitHub Actions workflow
- Explain build pipeline
- Discuss deployment process

---

### 0:50-1:00 | Q&A + First Tasks

**Goal:** Answer questions and assign initial tasks

**Q&A Topics:**
- Setup issues
- Component selection
- API integration
- Development workflow
- Timeline expectations

**First Tasks for Students:**
1. Complete basic environment setup
2. Read project documentation
3. Explore repository structure
4. Choose a component to work on
5. Set up local development for that component
6. Create a small initial contribution (fix a bug or add a TODO)

**Task Assignment Script:**
```
"For your first task, I'd like you to:
1. Pick a component from the Component Map
2. Set up your environment for that component
3. Find a TODO or bug to fix
4. Make your first commit and push
5. Create a pull request

I'll be available to help with any issues you encounter.
Let me know when you've completed your first task!"
```

**Next Steps:**
- Schedule follow-up meeting
- Provide individual help for setup issues
- Guide first contribution process

---

## 🚨 Backup Plan

**If Something Goes Wrong:**
- Switch to slide-based presentation
- Pre-record demo videos
- Share screen with prepared content
- Provide step-by-step PDF guide

**Service Failure Recovery:**
```bash
# Kill any running servers
pkill -f "node.*server"
pkill -f "npm"

# Restart services
cd /home/ranj/Project_Chimera
npm install
npm start

# Check logs if needed
tail -f logs/server.log
```

**Git Issues:**
```bash
# Reset to known good state if needed
git reset --hard origin/main

# Re-clone if corrupted
git clone https://github.com/your-org/Project-Chimera.git
```

---

## 📝 Post-Demo Tasks for Students

**Immediate (Today):**
- [ ] Review project documentation
- [ ] Explore repository structure
- [ ] Complete environment setup
- [ ] Join project Slack/Discord/communication channel

**This Week:**
- [ ] Choose and claim a component
- [ ] Set up local development for component
- [ ] Find first issue or TODO
- [ ] Create first commit and PR

**This Month:**
- [ ] Complete assigned component work
- [ ] Participate in code reviews
- [ ] Contribute to project documentation
- [ ] Set up CI/CD integration for component

---

## 📞 Support Resources

**Contact Information:**
- Project Lead: [Email/Slack]
- Senior Developers: [Email/Slack]
- Documentation: [Link to docs]
- Issue Tracker: [Link to issues]

**Where to Get Help:**
- GitHub Issues for bugs
- Pull Requests for feature discussions
- Meeting notes and archives
- Community chat channels

---

## 🎯 Success Metrics

**Students Should Be Able To:**
- Navigate the GitHub repository
- Understand the project structure
- Identify available components to work on
- Run the project locally
- Create a feature branch and make a commit
- Create a pull request
- Find and use project documentation

**What We'll Verify:**
- Repository navigation (self-assessment)
- Setup completion (ask to show logs)
- First commit created (review PRs)
- Documentation access (ask to find specific file)

---

## 📚 Appendix: Useful Commands

**Project Navigation:**
```bash
# Go to project root
cd /home/ranj/Project_Chimera

# View project structure
tree -L 2 -I "node_modules|.git"

# Show file counts
find . -type f | wc -l

# Show recent changes
git log --oneline --graph --all -10
```

**Development:**
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build project
npm run build

# Run linter
npm run lint

# Format code
npm run format
```

**Git Tips:**
```bash
# Show recent commits
git log --oneline -5

# Show all branches
git branch -a

# Show branch status
git status

# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

---

**Document Version:** 1.0
**Last Updated:** 2026-03-01
**Author:** Project Lead
**Next Review:** After first demo session

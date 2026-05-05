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

- [Contributing Guide](../CONTRIBUTING.md)
- [Student / Laptop Setup](STUDENT_LAPTOP_SETUP.md)
- [Start a Discussion](https://github.com/ranjrana2012-lab/project-chimera/discussions)

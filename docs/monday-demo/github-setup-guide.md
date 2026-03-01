# GitHub Project Setup Guide

## Overview

This guide documents the GitHub automation setup for Project Chimera student contributions.

## Project Board

The GitHub Project board is configured with:
- **Single shared board** for all 15 students
- **Views:** By Role, By Sprint, By Status
- **Custom fields:** Status, Priority, Role, Sprint, Trust Level, Points

### Creating the Project Board

1. Go to repository → Projects → "New Project"
2. Template: "Team Planning"
3. Name: "Project Chimera - Student Contributions"
4. Visibility: Private

### Custom Fields

Create these single-select fields:
- **Status:** Backlog, Ready, In Progress, In Review, Done
- **Priority:** P1-Critical, P2-High, P3-Medium, P4-Low
- **Role:** 1-10, Infrastructure, QA, Floating
- **Sprint:** Sprint 0-14
- **Trust Level:** New, Learning, Trusted

### Views

1. **By Role:** Group by Role field (swimlane layout)
2. **By Sprint:** Filter by Sprint field (table layout)
3. **Monday Onboarding:** Filter by Sprint 0 (board layout)

## Issue Templates

Three templates are available:
- **Feature Request** - For new features
- **Bug Report** - For defects
- **Documentation** - For docs improvements

## Pull Request Template

All PRs should include:
- Description of changes
- Type of change
- Testing status
- Related issue number

## Workflows

### pr-validation.yml
Runs on all PRs:
- Linting check
- Unit tests
- Coverage calculation
- Posts coverage comment

### trust-check.yml
Checks author trust level:
- Queries merged PRs
- Assigns trust label (new/learning/trusted)
- Posts welcome message

### auto-merge.yml
Enables auto-merge for trusted:
- Waits for validation
- Checks trust level
- Enables auto-merge if trusted and no protected files

### onboarding.yml
Creates Sprint 0 issues:
- 15 onboarding issues
- Pre-assigned to students
- Role-specific tasks

## Trust Score System

| Merged PRs | Trust Level | Label | Auto-Merge? |
|------------|-------------|-------|-------------|
| 0 | New | trust:new | No |
| 1-2 | Learning | trust:learning | No |
| 3+ | Trusted | trust:trusted | Yes |

## Branch Protection

Applied to: main, develop, sprint-*
- Require PR reviews
- Require status checks
- Require branches up to date
- Auto-delete head branches

## CODEOWNERS

Role-based review routing:
- All components owned by @technical-lead
- Automatic review requests based on changed files

## Quick Commands

```bash
# Trigger onboarding workflow
gh workflow run onboarding.yml -f create_issues=true

# Check workflow status
gh workflow list
gh run list --workflow=pr-validation.yml

# View project board
gh project view <project-number>

# Create an issue from template
gh issue create --template "feature.md"

# Create a PR
gh pr create --template
```

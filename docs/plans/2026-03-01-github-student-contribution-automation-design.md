# GitHub Student Contribution Automation Design

> **Status:** Approved for Implementation
> **Date:** March 1, 2026
> **Target:** Monday Student Demo (March 3, 2026)

---

## Overview

Design an automated GitHub workflow for 15 AI students contributing to Project Chimera. Students will submit pull requests that are automatically validated, tested, and (once trusted) auto-merged based on code quality and coverage improvements.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Project Board                          │
│  (Shared board with views: By Role, By Sprint, By Status)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Issue/PR     │  │ CI/CD        │  │ Branch       │
│ Workflows    │  │ Pipelines    │  │ Protection   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                ┌──────────────────┐
                │ Auto-Approval    │
                │ Engine           │
                │ (Tests +         │
                │  Coverage +      │
                │  Trust Score)    │
                └──────────────────┘
```

---

## Components

### 1. GitHub Project Board

**Single shared board** with custom views:
- **By Role** - 10 swimlanes for student roles
- **By Sprint** - Sprint 0-14 filters
- **By Status** - Backlog, In Progress, Review, Done
- **Monday Onboarding** - Sprint 0 filter

**Custom Fields:**
| Field | Type | Values |
|-------|------|--------|
| Status | Single Select | Backlog, Ready, In Progress, In Review, Done |
| Priority | Single Select | P1-Critical, P2-High, P3-Medium, P4-Low |
| Role | Single Select | 1-10, Infrastructure, QA |
| Sprint | Single Select | Sprint 0-14 |
| Trust Level | Single Select | New, Learning, Trusted |
| Points | Number | 1-13 |

### 2. Issue Templates

**`.github/ISSUE_TEMPLATE/feature.md`**
```markdown
---
name: Feature Request
about: Propose a new feature or enhancement
title: '[FEATURE] '
labels: 'type:feature'
assignees: ''
---

## Feature Description
<!-- Clear description of the feature -->

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Component
<!-- Which service/component does this affect? -->
```

**`.github/ISSUE_TEMPLATE/bug.md`**
```markdown
---
name: Bug Report
about: Report a defect or issue
title: '[BUG] '
labels: 'type:bugfix,priority:high'
assignees: ''
---

## Bug Description
<!-- Clear description of the bug -->

## Steps to Reproduce
1. Step 1
2. Step 2

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->
```

**`.github/ISSUE_TEMPLATE/documentation.md`**
```markdown
---
name: Documentation
about: Improve documentation
title: '[DOCS] '
labels: 'type:docs'
assignees: ''
---

## Documentation Change
<!-- What needs to be documented or improved? -->

## Files to Update
<!-- List of files to change -->
```

### 3. PR Template

**`.github/PULL_REQUEST_TEMPLATE.md`**
```markdown
## Description
<!-- Describe your changes -->

## Type of Change
- [ ] Feature
- [ ] Bugfix
- [ ] Documentation
- [ ] Refactor
- [ ] Tests

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Coverage increased or maintained

## Related Issue
Closes #

## Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
```

### 4. Branch Protection Rules

| Rule | Setting |
|------|---------|
| Target branches | `main`, `develop`, `sprint-*` |
| Require PR reviews | Yes |
| Required reviewers | 2 (new/learning), 1 (trusted) |
| Require status checks | `validate`, `coverage-check` |
| Require up to date | Yes |
| Auto-delete head | Yes |

### 5. GitHub Actions Workflows

**`.github/workflows/pr-validation.yml`** - Runs on all PRs
- Checkout code
- Run linting (ruff)
- Run unit tests (pytest)
- Calculate coverage delta
- Post coverage comment

**`.github/workflows/trust-check.yml`** - Checks student trust level
- Query author's merged PRs
- Calculate trust score
- Add appropriate label (new/learning/trusted)

**`.github/workflows/auto-merge.yml`** - Enables auto-merge for trusted
- Wait for CI checks
- Verify trust score >= 3
- Enable auto-merge if coverage gate passed

**`.github/workflows/onboarding.yml`** - Creates Sprint 0 issues
- Create 15 onboarding issues
- Assign to students
- Add to project board

### 6. CODEOWNERS

**`.github/CODEOWNERS`**
```
# Role-based code ownership
/services/openclaw-orchestrator/ @technical-lead @student-role-1
/services/scenespeak-agent/ @technical-lead @student-role-2
/services/captioning-agent/ @technical-lead @student-role-3
/services/bsl-text2gloss-agent/ @technical-lead @student-role-4
/services/sentiment-agent/ @technical-lead @student-role-5
/services/lighting-control/ @technical-lead @student-role-6
/services/safety-filter/ @technical-lead @student-role-7
/services/operator-console/ @technical-lead @student-role-8
/services/music-generation/ @technical-lead @student-role-9
/services/music-orchestration/ @technical-lead @student-role-10
/infrastructure/ @technical-lead @student-role-infra
/tests/ @technical-lead @student-role-qa
```

---

## Data Flow

### Student Contribution Flow

```
Student Opens Issue
    ↓
Select Template (Feature/Bug/Docs)
    ↓
Fill Form (Title, Description, Acceptance Criteria)
    ↓
Assign to Self + Role Label
    ↓
Issue Added to Project Board
```

### PR Validation Flow

```
PR Created
    ↓
GitHub Actions Triggered
    ├── Run Tests (pytest)
    ├── Run Lint (ruff)
    └── Run Coverage (pytest-cov)
    ↓
Calculate Coverage Delta
    ↓
Check Trust Score (merged PRs count)
    ↓
┌───────────────┬──────────────────┐
│ Trust < 3     │   Trust >= 3     │
│ Manual Review │   Check Coverage │
└───────────────┴──────────────────┘
                    │
         ┌──────────┴──────────┐
         │ Coverage ≥ 0?       │
         ├───────┬────────────┤
       Yes       No
         │         │
    Auto-Merge  Manual Review
```

### Trust Score System

| Merged PRs | Trust Level | Label | Auto-Merge? |
|------------|-------------|-------|-------------|
| 0 | New | `trust:new` | No |
| 1-2 | Learning | `trust:learning` | No |
| 3+ | Trusted | `trust:trusted` | Yes |

---

## Auto-Approval Logic

### Decision Algorithm

```python
def should_auto_merge(pr):
    """Determine if PR should auto-merge."""

    # Check 1: All CI checks passing
    if not pr.ci_checks_passed:
        return False, "CI checks failing"

    # Check 2: Coverage gate
    if pr.coverage_delta < 0:
        # Exception: Documentation only
        if not all(f.endswith('.md') for f in pr.changed_files):
            return False, f"Coverage decreased: {pr.coverage_delta}%"

    # Check 3: Trust score
    if pr.author.merged_prs < 3:
        return False, f"Author not trusted: {pr.author.merged_prs}/3 PRs"

    # All checks passed
    return True, "Auto-merge enabled"
```

### Auto-Merge Triggers

| Condition | Action |
|-----------|--------|
| All CI checks passing ✅ | Continue |
| Coverage delta >= 0 ✅ | Continue |
| Trust score >= 3 ✅ | **Enable auto-merge** |
| Trust score < 3 | Request review |
| Coverage delta < 0 | Request review |
| Any CI failing | Block merge |

---

## Security

### Branch Protection

```yaml
branch_protection:
  require_pull_request: true
  required_approving_review_count:
    new_student: 2
    learning_student: 2
    trusted_student: 1
  require_status_checks: true
  enforce_admins: true
```

### Protected Patterns

These paths always require manual review:
- `**/secrets/**`
- `**/.github/workflows/**`
- `**/infrastructure/**`
- `**/kubernetes/**`
- `Dockerfile`
- `docker-compose.yml`

### Student Requirements

- University email (@edu)
- 2FA enabled
- Contribution agreement signed

---

## Implementation Plan

### Pre-Monday Tasks (Saturday-Sunday)

| Task | Time | Output |
|------|------|--------|
| Create GitHub Project board | 30 min | Configured board |
| Create issue templates | 20 min | 3 `.md` files |
| Create PR template | 15 min | 1 `.md` file |
| Configure CODEOWNERS | 15 min | `.github/CODEOWNERS` |
| Create PR validation workflow | 45 min | `.github/workflows/pr-validation.yml` |
| Create trust check workflow | 30 min | `.github/workflows/trust-check.yml` |
| Create auto-merge workflow | 45 min | `.github/workflows/auto-merge.yml` |
| Create onboarding workflow | 20 min | `.github/workflows/onboarding.yml` |
| Configure branch protection | 15 min | Rules applied |
| Test all workflows | 30 min | Sample PR tested |
| Create Sprint 0 issues | 30 min | 15 issues |
| Invite 15 students | 15 min | Invitations sent |
| Create demo script | 30 min | `demo-script.md` |

**Total Time:** ~5 hours

### Files to Create

```
.github/
├── ISSUE_TEMPLATE/
│   ├── feature.md
│   ├── bug.md
│   └── documentation.md
├── workflows/
│   ├── pr-validation.yml
│   ├── trust-check.yml
│   ├── auto-merge.yml
│   └── onboarding.yml
├── PULL_REQUEST_TEMPLATE.md
└── CODEOWNERS

docs/
└── monday-demo/
    ├── demo-script.md
    └── student-handbook.md
```

---

## Monday Demo Script

### 0:00-0:10 | Welcome & Project Overview
- Welcome 15 students
- Explain Project Chimera
- Show architecture diagram
- Share documentation link

### 0:10-0:20 | GitHub Repository Tour
- Show repository structure
- Demonstrate Project board
- Show issue templates
- Show PR template

### 0:20-0:30 | Component Assignments
- Announce 10 role assignments
- Explain 5 floating roles
- Show getting-started/quick-start.md
- Assign Sprint 0 issues

### 0:30-0:40 | Live Demo: Working Services
- Demo 4 fully working services:
  - OpenClaw Orchestrator (8000)
  - SceneSpeak Agent (8001)
  - Lighting Control (8005)
  - Operator Console (8007)

### 0:40-0:50 | Contribution Workflow Demo
- Create issue from template
- Create feature branch
- Make code change
- Create PR
- Watch CI run
- Show coverage comment
- Manual review process

### 0:50-1:00 | Q&A + First Tasks
- Answer questions
- Students start Sprint 0
- Technical lead circulates

---

## Validation Checklist

### GitHub Project Setup
- [ ] GitHub Project board created
- [ ] Custom fields configured
- [ ] Views created
- [ ] Labels created
- [ ] CODEOWNERS configured

### Workflows & Automation
- [ ] pr-validation.yml created
- [ ] trust-check.yml created
- [ ] auto-merge.yml created
- [ ] onboarding.yml created
- [ ] Workflows tested

### Branch Protection
- [ ] Rules configured for main
- [ ] Rules configured for develop
- [ ] Rules configured for sprint-*

### Student Onboarding
- [ ] 15 students invited
- [ ] Write permissions granted
- [ ] Sprint 0 issues created
- [ ] Demo script prepared

---

## Rollback Plan

If automation fails:

1. **Disable Workflows**
   ```bash
   gh workflow disable pr-validation
   gh workflow disable trust-check
   gh workflow disable auto-merge
   ```

2. **Fall Back to Manual**
   - All PRs require manual review
   - Use CODEOWNERS for routing

3. **Continue Demo**
   - Services still running
   - Students can contribute manually

---

**Sources:**
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [GitHub Actions](https://docs.github.com/en/actions)
- [manual-approval Action](https://github.com/trstringer/manual-approval)
- [Auto-approve Action](https://github.com/marketplace/actions/auto-approve)
- [Hackathon Demo Best Practices](https://github.com/awesome-hackathons)

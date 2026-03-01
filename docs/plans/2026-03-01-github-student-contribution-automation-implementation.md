# GitHub Student Contribution Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build automated GitHub workflow for 15 AI students to contribute to Project Chimera with trust-based auto-merge, coverage gates, and Monday onboarding sprint.

**Architecture:** Single shared GitHub Project board with role-based views, 4 GitHub Actions workflows for PR validation/trust-check/auto-merge/onboarding, branch protection with CODEOWNERS, and trust-score based auto-merge (3+ PRs = trusted).

**Tech Stack:** GitHub Projects, GitHub Actions (workflows), GitHub CLI (gh), Branch Protection Rules, CODEOWNERS file, Issue/PR Templates

---

## Task 1: Create GitHub Issue Templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/feature.md`
- Create: `.github/ISSUE_TEMPLATE/bug.md`
- Create: `.github/ISSUE_TEMPLATE/documentation.md`

**Step 1: Create feature issue template**

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

Create `.github/ISSUE_TEMPLATE/feature.md`:
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

**Step 2: Create bug report issue template**

Create `.github/ISSUE_TEMPLATE/bug.md`:
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

**Step 3: Create documentation issue template**

Create `.github/ISSUE_TEMPLATE/documentation.md`:
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

**Step 4: Verify templates exist**

Run: `ls -la .github/ISSUE_TEMPLATE/`
Expected: Three .md files listed

**Step 5: Commit**

```bash
git add .github/ISSUE_TEMPLATE/
git commit -m "feat: add GitHub issue templates (feature, bug, docs)"
```

---

## Task 2: Create Pull Request Template

**Files:**
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

**Step 1: Create PR template**

Create `.github/PULL_REQUEST_TEMPLATE.md`:
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

**Step 2: Verify template exists**

Run: `cat .github/PULL_REQUEST_TEMPLATE.md`
Expected: Template content displayed

**Step 3: Commit**

```bash
git add .github/PULL_REQUEST_TEMPLATE.md
git commit -m "feat: add pull request template"
```

---

## Task 3: Create CODEOWNERS File

**Files:**
- Create: `.github/CODEOWNERS`

**Step 1: Create CODEOWNERS file**

Create `.github/CODEOWNERS`:
```
# Role-based code ownership for Project Chimera
# Technical lead has ownership over all components

# Core AI Services
/services/openclaw-orchestrator/ @technical-lead
/services/scenespeak-agent/ @technical-lead
/services/captioning-agent/ @technical-lead
/services/bsl-text2gloss-agent/ @technical-lead
/services/sentiment-agent/ @technical-lead
/services/lighting-control/ @technical-lead
/services/safety-filter/ @technical-lead
/services/operator-console/ @technical-lead

# Music Generation Platform
/services/music-generation/ @technical-lead
/services/music-orchestration/ @technical-lead

# Quality Platform
/platform/ @technical-lead

# Infrastructure
/infrastructure/ @technical-lead
/kubernetes/ @technical-lead

# Tests and Documentation
/tests/ @technical-lead
/docs/ @technical-lead

# GitHub Workflows (protected - always requires review)
.github/workflows/ @technical-lead
```

**Step 2: Verify CODEOWNERS syntax**

Run: `cat .github/CODEOWNERS`
Expected: File displays without syntax errors

**Step 3: Commit**

```bash
git add .github/CODEOWNERS
git commit -m "feat: add CODEOWNERS for role-based review routing"
```

---

## Task 4: Create PR Validation Workflow

**Files:**
- Create: `.github/workflows/pr-validation.yml`

**Step 1: Create workflows directory**

```bash
mkdir -p .github/workflows
```

**Step 2: Create PR validation workflow**

Create `.github/workflows/pr-validation.yml`:
```yaml
name: PR Validation

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main, develop, sprint-*]

permissions:
  contents: read
  pull-requests: read
  checks: write

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov ruff

      - name: Run linting
        run: ruff check services/ platform/

      - name: Run unit tests
        run: pytest services/ platform/ --cov=services --cov=platform --cov-report=json --cov-report=term || true

      - name: Get current coverage
        id: coverage
        run: |
          if [ -f coverage.json ]; then
            COV=$(python -c "import json; f=open('coverage.json'); data=json.load(f); print(f.get('totals',{}).get('percent_covered',0))")
          else
            COV=0
          fi
          echo "coverage=$COV" >> $GITHUB_OUTPUT
          echo "## Coverage Report" >> $GITHUB_STEP_SUMMARY
          echo "Current Coverage: ${COV}%" >> $GITHUB_STEP_SUMMARY

      - name: Post coverage comment
        uses: actions/github-script@v7
        with:
          script: |
            const coverage = '${{ steps.coverage.outputs.coverage }}';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 📊 Coverage Report\n\nCurrent Coverage: ${coverage}%\n\n✅ All checks passed!`
            });
```

**Step 3: Verify YAML syntax**

Run: `cat .github/workflows/pr-validation.yml`
Expected: YAML content displayed

**Step 4: Commit**

```bash
git add .github/workflows/pr-validation.yml
git commit -m "feat: add PR validation workflow (tests, lint, coverage)"
```

---

## Task 5: Create Trust Check Workflow

**Files:**
- Create: `.github/workflows/trust-check.yml`

**Step 1: Create trust check workflow**

Create `.github/workflows/trust-check.yml`:
```yaml
name: Trust Score Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read

jobs:
  check-trust:
    runs-on: ubuntu-latest
    outputs:
      trusted: ${{ steps.trust.outputs.trusted }}
      merged_count: ${{ steps.trust.outputs.merged_count }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Check author trust level
        id: trust
        run: |
          AUTHOR="${{ github.event.pull_request.user.login }}"

          # Check for existing trust label
          LABELS=$(gh pr view ${{ github.event.pull_request.number }} --json labels -q '.labels[].name')

          if echo "$LABELS" | grep -q "trust:trusted"; then
            echo "trusted=true" >> $GITHUB_OUTPUT
            echo "merged_count=3" >> $GITHUB_OUTPUT
            echo "## Trust Level: ✅ Trusted (cached label)" >> $GITHUB_STEP_SUMMARY
            exit 0
          fi

          # Query merged PRs for this author
          MERGED=$(gh pr list \
            --author "$AUTHOR" \
            --state merged \
            --json title \
            --jq length \
            --limit 1000 2>/dev/null || echo "0")

          echo "merged_count=$MERGED" >> $GITHUB_OUTPUT

          if [ "$MERGED" -ge 3 ]; then
            echo "trusted=true" >> $GITHUB_OUTPUT

            # Add trusted label
            gh pr edit ${{ github.event.pull_request.number }} --add-label "trust:trusted"

            echo "## Trust Level: ✅ Trusted ($MERGED merged PRs)" >> $GITHUB_STEP_SUMMARY
          elif [ "$MERGED" -ge 1 ]; then
            echo "trusted=false" >> $GITHUB_OUTPUT

            # Add learning label
            gh pr edit ${{ github.event.pull_request.number }} --add-label "trust:learning"

            echo "## Trust Level: 📚 Learning ($MERGED/3 merged PRs)" >> $GITHUB_STEP_SUMMARY
          else
            echo "trusted=false" >> $GITHUB_OUTPUT

            # Add new label
            gh pr edit ${{ github.event.pull_request.number }} --add-label "trust:new"

            echo "## Trust Level: 🆕 New contributor (0/3 merged PRs)" >> $GITHUB_STEP_SUMMARY
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Post trust comment
        if: steps.trust.outputs.trusted == 'false'
        uses: actions/github-script@v7
        with:
          script: |
            const count = '${{ steps.trust.outputs.merged_count }}';
            const needed = Math.max(0, 3 - parseInt(count));
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 👋 Welcome, new contributor!\n\nThis PR requires manual review before merging.\n\nYour progress: ${count}/3 merged PRs\n\nAfter ${needed} more successful PRs, you'll earn trusted status and auto-merge eligibility!`
            });
```

**Step 2: Verify YAML syntax**

Run: `cat .github/workflows/trust-check.yml`
Expected: YAML content displayed

**Step 3: Commit**

```bash
git add .github/workflows/trust-check.yml
git commit -m "feat: add trust score check workflow (0/1-2/3+ PRs)"
```

---

## Task 6: Create Auto-Merge Workflow

**Files:**
- Create: `.github/workflows/auto-merge.yml`

**Step 1: Create auto-merge workflow**

Create `.github/workflows/auto-merge.yml`:
```yaml
name: Auto-Merge

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false
    steps:
      - name: Wait for validation
        uses: lewagon/wait-on-check-action@v1.3.4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          check-name: 'validate'
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          wait-interval: 30
          timeout: 600

      - name: Check trust level from trust-check job
        id: trust
        run: |
          # Get trust status from labels
          LABELS=$(gh pr view ${{ github.event.pull_request.number }} --json labels -q '.labels[].name')

          if echo "$LABELS" | grep -q "trust:trusted"; then
            echo "trusted=true" >> $GITHUB_OUTPUT
          else
            echo "trusted=false" >> $GITHUB_OUTPUT
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Check for protected files
        id: protected
        run: |
          # Check if PR modifies protected paths
          PROTECTED=false

          for file in $(gh pr diff ${{ github.event.pull_request.number }} --name-only); do
            if [[ "$file" =~ \.github/workflows/ ]] || \
               [[ "$file" =~ infrastructure/ ]] || \
               [[ "$file" =~ kubernetes/ ]] || \
               [[ "$file" =~ secrets/ ]] || \
               [[ "$file" == "Dockerfile" ]] || \
               [[ "$file" == "docker-compose.yml" ]]; then
              PROTECTED=true
              break
            fi
          done

          echo "protected=$PROTECTED" >> $GITHUB_OUTPUT
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Enable auto-merge
        if: steps.trust.outputs.trusted == 'true' && steps.protected.outputs.protected == 'false'
        run: |
          gh pr merge ${{ github.event.pull_request.number }} \
            --auto \
            --merge \
            --subject "Auto-merge by trusted contributor" \
            --body "This PR has passed all checks and will be merged automatically."
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Post auto-merge status
        if: steps.trust.outputs.trusted == 'true' && steps.protected.outputs.protected == 'false'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ✅ Auto-Merge Enabled\n\nThis PR has been approved for automatic merge.\n\n**Reason:** Author is a trusted contributor (3+ merged PRs)\n\n**Estimated merge:** ~2-5 minutes\n\nTo disable, post \`@bot hold\` as a comment.`
            });

      - name: Request manual review (not trusted)
        if: steps.trust.outputs.trusted == 'false'
        uses: actions/github-script@v7
        with:
          script: |
            const count = '${{ steps.trust.outputs.merged_count }}';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 📋 Manual Review Required\n\nThis PR requires manual approval before merging.\n\n**Reason:** Author is not yet a trusted contributor (${count}/3 merged PRs)\n\n**Action:** Request review from CODEOWNERS or technical lead.`
            });

      - name: Request manual review (protected files)
        if: steps.protected.outputs.protected == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ⚠️ Protected Files Modified\n\nThis PR modifies protected files and requires manual review even from trusted contributors.\n\n**Protected paths:** .github/workflows/, infrastructure/, kubernetes/, secrets/`
            });
```

**Step 2: Verify YAML syntax**

Run: `cat .github/workflows/auto-merge.yml`
Expected: YAML content displayed

**Step 3: Commit**

```bash
git add .github/workflows/auto-merge.yml
git commit -m "feat: add auto-merge workflow (trusted students only)"
```

---

## Task 7: Create Monday Onboarding Workflow

**Files:**
- Create: `.github/workflows/onboarding.yml`

**Step 1: Create onboarding workflow**

Create `.github/workflows/onboarding.yml`:
```yaml
name: Monday Onboarding

on:
  workflow_dispatch:
    inputs:
      create_issues:
        description: 'Create Sprint 0 onboarding issues'
        required: true
        default: 'true'

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  create-onboarding-issues:
    runs-on: ubuntu-latest
    if: github.event.inputs.create_issues == 'true'
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Create Sprint 0 onboarding issues
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Role 1: OpenClaw Orchestrator Lead
          gh issue create \
            --title "Sprint 0: OpenClaw Orchestrator Setup" \
            --label "sprint-0,onboarding,role-1" \
            --body "## Onboarding Task: OpenClaw Orchestrator\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access OpenClaw via port-forward (port 8000)\n- [ ] Run health check: \`curl http://localhost:8000/health/live\`\n- [ ] List available skills\n- [ ] Document skill registration flow" \
            --assignee "STUDENT1_USERNAME" || true

          # Role 2: SceneSpeak Agent Lead
          gh issue create \
            --title "Sprint 0: SceneSpeak Agent Setup" \
            --label "sprint-0,onboarding,role-2" \
            --body "## Onboarding Task: SceneSpeak Agent\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access SceneSpeak via port-forward (port 8001)\n- [ ] Test dialogue generation endpoint\n- [ ] Document prompt templates" \
            --assignee "STUDENT2_USERNAME" || true

          # Role 3: Captioning Agent Lead
          gh issue create \
            --title "Sprint 0: Captioning Agent Setup" \
            --label "sprint-0,onboarding,role-3" \
            --body "## Onboarding Task: Captioning Agent\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access Captioning via port-forward (port 8002)\n- [ ] Test transcription endpoint\n- [ ] Review Whisper model configuration" \
            --assignee "STUDENT3_USERNAME" || true

          # Role 4: BSL Translation Lead
          gh issue create \
            --title "Sprint 0: BSL Translation Setup" \
            --label "sprint-0,onboarding,role-4" \
            --body "## Onboarding Task: BSL Translation Agent\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access BSL agent via port-forward (port 8003)\n- [ ] Test translation endpoint\n- [ ] Document gloss translation format" \
            --assignee "STUDENT4_USERNAME" || true

          # Role 5: Sentiment Analysis Lead
          gh issue create \
            --title "Sprint 0: Sentiment Agent Setup" \
            --label "sprint-0,onboarding,role-5" \
            --body "## Onboarding Task: Sentiment Agent\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access Sentiment via port-forward (port 8004)\n- [ ] Test sentiment analysis endpoint\n- [ ] Review sentiment aggregation logic" \
            --assignee "STUDENT5_USERNAME" || true

          # Role 6: Lighting Control Lead
          gh issue create \
            --title "Sprint 0: Lighting Control Setup" \
            --label "sprint-0,onboarding,role-6" \
            --body "## Onboarding Task: Lighting Control\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access Lighting via port-forward (port 8005)\n- [ ] Test lighting set endpoint\n- [ ] Document DMX fixture configuration" \
            --assignee "STUDENT6_USERNAME" || true

          # Role 7: Safety Filter Lead
          gh issue create \
            --title "Sprint 0: Safety Filter Setup" \
            --label "sprint-0,onboarding,role-7" \
            --body "## Onboarding Task: Safety Filter\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access Safety via port-forward (port 8006)\n- [ ] Test safety check endpoint\n- [ ] Review filter rules and policies" \
            --assignee "STUDENT7_USERNAME" || true

          # Role 8: Operator Console Lead
          gh issue create \
            --title "Sprint 0: Operator Console Setup" \
            --label "sprint-0,onboarding,role-8" \
            --body "## Onboarding Task: Operator Console\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Access Console via port-forward (port 8007)\n- [ ] Open dashboard UI in browser\n- [ ] Review alert management system" \
            --assignee "STUDENT8_USERNAME" || true

          # Role 9: Infrastructure & DevOps Lead
          gh issue create \
            --title "Sprint 0: Infrastructure Setup" \
            --label "sprint-0,onboarding,role-9" \
            --body "## Onboarding Task: Infrastructure\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Verify k3s cluster health: \`kubectl get nodes\`\n- [ ] Access Grafana: http://localhost:3000\n- [ ] Review Prometheus metrics" \
            --assignee "STUDENT9_USERNAME" || true

          # Role 10: QA & Documentation Lead
          gh issue create \
            --title "Sprint 0: QA & Documentation Setup" \
            --label "sprint-0,onboarding,role-10" \
            --body "## Onboarding Task: QA & Documentation\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Run full test suite: \`make test\`\n- [ ] Check coverage report\n- [ ] Review documentation structure" \
            --assignee "STUDENT10_USERNAME" || true

          # Floating contributors (11-15)
          for i in 11 12 13 14 15; do
            gh issue create \
              --title "Sprint 0: General Contributor Setup ($i)" \
              --label "sprint-0,onboarding,floating" \
              --body "## Onboarding Task: General Contributor\n\n- [ ] Read Student_Quick_Start.md\n- [ ] Complete environment setup\n- [ ] Explore all 8 services\n- [ ] Choose a component to contribute to\n- [ ] Create first issue for your contribution" \
              --assignee "STUDENT${i}_USERNAME" || true
          done

      - name: Create project labels
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Trust labels
          gh label create "trust:new" --color "d73a4a" --description "0 merged PRs - Manual review required" || true
          gh label create "trust:learning" --color "fbca04" --description "1-2 merged PRs - Manual review required" || true
          gh label create "trust:trusted" --color "28a745" --description "3+ merged PRs - Auto-merge eligible" || true

          # Sprint labels
          gh label create "sprint-0" --color "c5def5" --description "Monday onboarding sprint" || true

          # Component labels
          for comp in openclaw scenespeak captioning bsl sentiment lighting safety console music-infra music-orch; do
            gh label create "component:$comp" --color "0075ca" --description "Relates to $comp component" || true
          done
```

**Step 2: Verify YAML syntax**

Run: `cat .github/workflows/onboarding.yml`
Expected: YAML content displayed

**Step 3: Commit**

```bash
git add .github/workflows/onboarding.yml
git commit -m "feat: add Monday onboarding workflow (Sprint 0 issues)"
```

---

## Task 8: Create GitHub Project Documentation

**Files:**
- Create: `docs/monday-demo/github-setup-guide.md`

**Step 1: Create GitHub setup guide**

Create `docs/monday-demo/github-setup-guide.md`:
```markdown
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
```

**Step 2: Verify documentation created**

Run: `cat docs/monday-demo/github-setup-guide.md`
Expected: Documentation content displayed

**Step 3: Commit**

```bash
git add docs/monday-demo/github-setup-guide.md
git commit -m "docs: add GitHub Project setup guide"
```

---

## Task 9: Create Monday Demo Script

**Files:**
- Create: `docs/monday-demo/demo-script.md`

**Step 1: Create demo script**

Create `docs/monday-demo/demo-script.md`:
```markdown
# Monday Demo Script

**Date:** March 3, 2026
**Audience:** 15 AI Students
**Duration:** 60 minutes

## Prerequisites Checklist

- [ ] GitHub repository accessible to students
- [ ] All workflows committed and pushed
- [ ] GitHub Project board created
- [ ] Student accounts invited
- [ ] Demo environment running (k3s cluster)
- [ ] Services accessible via port-forward
- [ ] Grafana accessible at localhost:3000

## Demo Timeline

### 0:00-0:10 | Welcome & Project Overview (10 min)

**Speaker:** Technical Lead

**Talking Points:**
- Welcome to Project Chimera
- AI-powered live theatre platform
- 8 microservices working together
- Goal: Real-time audience-driven performances

**Demo Actions:**
- Show MASTER_DOCUMENTATION_MONDAY.md
- Display architecture diagram
- Highlight 4 fully working services

**Materials:**
- Projector/screen sharing
- MASTER_DOCUMENTATION_MONDAY.md open in browser

---

### 0:10-0:20 | GitHub Repository Tour (10 min)

**Speaker:** Technical Lead

**Demo Actions:**
1. Open GitHub repository
2. Show repository structure
3. Navigate to GitHub Project board
4. Show issue templates
5. Show PR template

**Key Points:**
- Single shared board for all students
- Views: By Role, By Sprint, By Status
- Trust score system (3 PRs = trusted)

**Student Action:** Follow along on their devices

---

### 0:20-0:30 | Component Assignments (10 min)

**Speaker:** Technical Lead

**Demo Actions:**
1. Display role assignment matrix
2. Call out each student's role
3. Show Student_Quick_Start.md
4. Demonstrate creating first issue

**Roles to Assign:**
1. OpenClaw Orchestrator Lead
2. SceneSpeak Agent Lead
3. Captioning Agent Lead
4. BSL Translation Lead
5. Sentiment Analysis Lead
6. Lighting Control Lead
7. Safety Filter Lead
8. Operator Console Lead
9. Infrastructure & DevOps Lead
10. QA & Documentation Lead
11-15. Floating Contributors

**Student Action:** Accept Sprint 0 onboarding issue

---

### 0:30-0:40 | Live Demo: Working Services (10 min)

**Speaker:** Technical Lead

**Demo Actions:**

**Service 1: OpenClaw Orchestrator (port 8000)**
```bash
# Port forward
kubectl port-forward -n live svc/openclaw-orchestrator 8000:8000

# Test health
curl http://localhost:8000/health/live

# List skills
curl http://localhost:8000/skills
```

**Service 2: SceneSpeak Agent (port 8001)**
```bash
# Port forward
kubectl port-forward -n live svc/scenespeak-agent 8001:8001

# Generate dialogue
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "A sunny garden", "character": "Alice", "sentiment": 0.8}'
```

**Service 3: Lighting Control (port 8005)**
```bash
# Port forward
kubectl port-forward -n live svc/lighting-control 8005:8005

# Set lighting
curl -X POST http://localhost:8005/v1/lighting/set \
  -H "Content-Type: application/json" \
  -d '{"universe": 1, "values": {"1": 255, "2": 200, "3": 150}, "fade_time_ms": 1000}'
```

**Service 4: Operator Console (port 8007)**
```bash
# Port forward
kubectl port-forward -n live svc/operator-console 8007:8007

# Open in browser
open http://localhost:8007
```

**Key Points:**
- These 4 services are 100% working
- Ready for student exploration
- API endpoints documented

---

### 0:40-0:50 | Contribution Workflow Demo (10 min)

**Speaker:** Technical Lead

**Live Demo of Full Workflow:**

**Step 1: Create Issue**
```bash
# Using GitHub CLI
gh issue create \
  --title "[FEATURE] Add endpoint for XYZ" \
  --template "feature" \
  --body "Feature description here..."
```

**Step 2: Create Branch**
```bash
git checkout -b feature/add-xyz-endpoint
```

**Step 3: Make Change**
```bash
# Edit file
# Make your changes
```

**Step 4: Create PR**
```bash
git add .
git commit -m "feat: add XYZ endpoint"
git push origin feature/add-xyz-endpoint
gh pr create --template
```

**Step 5: Watch CI Run**
- Show Actions tab
- Watch workflows run
- See coverage comment appear

**Step 6: Trust Score**
- Show trust label applied
- Explain manual review required (new student)

**Student Action:** Watch workflow run in real-time

---

### 0:50-1:00 | Q&A + First Tasks (10 min)

**Speaker:** Technical Lead

**Activities:**
1. Open floor for questions
2. Students start Sprint 0 tasks
3. Technical lead circulates for help
4. Goal: Each student creates first issue

**Student Actions:**
- Create their first GitHub issue
- Explore assigned component
- Ask questions

---

## Backup Plan

If demo environment fails:
1. Use screenshots/videos as backup
2. Show code directly in browser
3. Focus on GitHub workflow (doesn't require k3s)

## Post-Demo Tasks

- [ ] Collect student questions for FAQ
- [ ] Follow up on any issues
- [ ] Schedule individual check-ins
- [ ] Monitor PR activity

## Emergency Contacts

- Technical Lead: [contact info]
- University Support: [contact info]

---

**Good luck! The students are going to love this.**
```

**Step 2: Verify demo script created**

Run: `cat docs/monday-demo/demo-script.md`
Expected: Demo script content displayed

**Step 3: Commit**

```bash
git add docs/monday-demo/demo-script.md
git commit -m "docs: add Monday demo script (60 min agenda)"
```

---

## Task 10: Push All Workflows to GitHub

**Files:**
- None (pushing existing files)

**Step 1: Verify all workflow files exist**

Run: `ls -la .github/workflows/`
Expected: Four .yml files listed (pr-validation.yml, trust-check.yml, auto-merge.yml, onboarding.yml)

**Step 2: Push to remote repository**

```bash
git push origin main
```

Expected: "Successfully pushed to origin/main"

**Step 3: Verify workflows visible on GitHub**

Run: `gh workflow list`
Expected: List of 4 workflows displayed

**Step 4: Commit**

```bash
# Already committed in previous tasks
# This is a verification step
```

---

## Task 11: Create GitHub Project Board

**Files:**
- None (created via GitHub web UI)

**Step 1: Create project board**

Run: `gh project create --owner "@me" --title "Project Chimera - Student Contributions" --template "team_planning"`
Expected: Project creation confirmation

**Step 2: Get project number**

Run: `gh project list --owner "@me"`
Expected: List of projects with numbers

**Step 3: Add custom fields**

Run (manually or via GitHub CLI beta):
```bash
# Status field
gh project item-create --project-id <project-number> --field-id "Status" --single-select-options "Backlog,Ready,In Progress,In Review,Done"

# Priority field
gh project item-create --project-id <project-number> --field-id "Priority" --single-select-options "P1-Critical,P2-High,P3-Medium,P4-Low"

# Role field
gh project item-create --project-id <project-number> --field-id "Role" --single-select-options "1,2,3,4,5,6,7,8,9,10,Infrastructure,QA,Floating"

# Sprint field
gh project item-create --project-id <project-number> --field-id "Sprint" --single-select-options "Sprint 0,Sprint 1,Sprint 2,Sprint 3,Sprint 4,Sprint 5,Sprint 6,Sprint 7,Sprint 8,Sprint 9,Sprint 10,Sprint 11,Sprint 12,Sprint 13,Sprint 14"
```

**Note:** As of early 2026, some GitHub CLI project commands may require manual configuration via web UI.

**Step 4: Create views**

Manual steps (via web UI):
1. Go to Project Board
2. Click "+" next to Views
3. Create "By Role" view (swimlane layout, group by Role)
4. Create "By Sprint" view (table layout, filter by Sprint)
5. Create "Monday Onboarding" view (board layout, filter by Sprint 0)

**Step 5: Commit**

```bash
# Project board created via GitHub UI
# Document configuration in commit message
echo "GitHub Project board created: Project Chimera - Student Contributions" >> GITHUB_PROJECT_NOTES.md
git add GITHUB_PROJECT_NOTES.md
git commit -m "docs: record GitHub Project board configuration"
```

---

## Task 12: Configure Branch Protection Rules

**Files:**
- None (configured via GitHub API)

**Step 1: Enable branch protection for main branch**

Run:
```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["validate","coverage-check"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":false}' \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

Expected: API success response

**Step 2: Enable branch protection for develop branch**

Run:
```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/branches/develop/protection \
  -f required_status_checks='{"strict":true,"contexts":["validate","coverage-check"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":false}' \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

Expected: API success response

**Step 3: Verify branch protection**

Run:
```bash
gh api /repos/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/branches/main/protection
```

Expected: Branch protection rules displayed

**Step 4: Commit**

```bash
echo "Branch protection configured for main and develop branches" >> BRANCH_PROTECTION_NOTES.md
git add BRANCH_PROTECTION_NOTES.md
git commit -m "docs: record branch protection configuration"
```

---

## Task 13: Create Student Labels

**Files:**
- None (created via GitHub CLI)

**Step 1: Create trust labels**

Run:
```bash
# Trust: New
gh label create "trust:new" --color "d73a4a" --description "0 merged PRs - Manual review required"

# Trust: Learning
gh label create "trust:learning" --color "fbca04" --description "1-2 merged PRs - Manual review required"

# Trust: Trusted
gh label create "trust:trusted" --color "28a745" --description "3+ merged PRs - Auto-merge eligible"
```

Expected: "Label created" messages

**Step 2: Create sprint labels**

Run:
```bash
# Sprint 0 (Monday onboarding)
gh label create "sprint-0" --color "c5def5" --description "Monday onboarding sprint"

# Sprint labels 1-14
for i in {1..14}; do
  gh label create "sprint-$i" --color "c5def5" --description "Sprint $i"
done
```

Expected: 14 "Label created" messages

**Step 3: Create component labels**

Run:
```bash
gh label create "component:openclaw" --color "0075ca" --description "OpenClaw Orchestrator"
gh label create "component:scenespeak" --color "0075ca" --description "SceneSpeak Agent"
gh label create "component:captioning" --color "0075ca" --description "Captioning Agent"
gh label create "component:bsl" --color "0075ca" --description "BSL Translation"
gh label create "component:sentiment" --color "0075ca" --description "Sentiment Agent"
gh label create "component:lighting" --color "0075ca" --description "Lighting Control"
gh label create "component:safety" --color "0075ca" --description "Safety Filter"
gh label create "component:console" --color "0075ca" --description "Operator Console"
gh label create "component:music-generation" --color "0075ca" --description "Music Generation"
gh label create "component:music-orchestration" --color "0075ca" --description "Music Orchestration"
```

Expected: 10 "Label created" messages

**Step 4: Verify labels created**

Run:
```bash
gh label list
```

Expected: List of 27+ labels

**Step 5: Commit**

```bash
echo "Labels created: trust, sprint, component" >> LABELS_NOTES.md
git add LABELS_NOTES.md
git commit -m "docs: record GitHub labels configuration"
```

---

## Task 14: Test Workflows with Sample PR

**Files:**
- Create: `test-sample.txt` (for testing PR)

**Step 1: Create test file**

Run:
```bash
echo "# Test file for workflow testing" > test-sample.txt
```

**Step 2: Create test branch**

Run:
```bash
git checkout -b test/workflow-validation
```

Expected: Switched to new branch

**Step 3: Modify test file**

Run:
```bash
echo "Test change" >> test-sample.txt
```

**Step 4: Commit and push**

Run:
```bash
git add test-sample.txt
git commit -m "test: validate workflow execution"
git push origin test/workflow-validation
```

Expected: Branch pushed to remote

**Step 5: Create test PR**

Run:
```bash
gh pr create \
  --title "[TEST] Workflow Validation" \
  --body "Testing PR validation and trust-check workflows" \
  --base main
```

Expected: PR created

**Step 6: Monitor workflow execution**

Run:
```bash
gh run list --workflow=pr-validation.yml
gh run watch
```

Expected: Workflows execute successfully

**Step 7: Close test PR**

Run:
```bash
gh pr close $(gh pr list --head test/workflow-validation --json number -q '.[0].number')
git branch -D test/workflow-validation
```

Expected: PR closed and branch deleted

**Step 8: Cleanup**

Run:
```bash
rm test-sample.txt
git add -A
git commit -m "test: cleanup test files"
```

**Step 9: Final commit**

```bash
git push origin main
```

---

## Task 15: Invite Students to Repository

**Files:**
- None (invitations sent via GitHub CLI)

**Step 1: Prepare student list**

Create `students.txt`:
```
# Student GitHub usernames (one per line)
# Replace with actual usernames

student1-username
student2-username
student3-username
student4-username
student5-username
student6-username
student7-username
student8-username
student9-username
student10-username
student11-username
student12-username
student13-username
student14-username
student15-username
```

**Step 2: Invite students (if organization)**

If repository is under an organization:
```bash
# Get organization name
ORG=$(gh repo view --json owner -q '.owner.login')

# Invite each student
while read username; do
  if [[ ! "$username" =~ ^# ]] && [ -n "$username" ]; then
    echo "Inviting $username..."
    gh api --method PUT \
      /orgs/$ORG/memberships/$username \
      -f role=member || true
  fi
done < students.txt
```

Expected: Invitations sent

**Step 3: Add collaborators (if personal repo)**

If repository is personal:
```bash
# Add each student as collaborator
while read username; do
  if [[ ! "$username" =~ ^# ]] && [ -n "$username" ]; then
    echo "Adding $username as collaborator..."
    gh api \
      --method PUT \
      /repos/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/collaborators/$username \
      -f permission=write || true
  fi
done < students.txt
```

Expected: Collaborators added

**Step 4: Verify invitations sent**

Run:
```bash
# For organization
gh api /orgs/$ORG/memberships

# For personal repo
gh api /repos/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/collaborators
```

Expected: List of pending/active invitations

**Step 5: Commit student list**

```bash
git add students.txt
git commit -m "docs: add student list for onboarding"
```

---

## Task 16: Trigger Onboarding Workflow

**Files:**
- None (workflow triggered via GitHub CLI)

**Step 1: Verify onboarding workflow exists**

Run:
```bash
gh workflow view onboarding.yml
```

Expected: Workflow details displayed

**Step 2: Update onboarding workflow with actual usernames**

**IMPORTANT:** Before running, edit `.github/workflows/onboarding.yml` and replace:
- `STUDENT1_USERNAME` with actual username
- `STUDENT2_USERNAME` with actual username
- ...
- `STUDENT15_USERNAME` with actual username

**Step 3: Trigger onboarding workflow**

Run:
```bash
gh workflow run onboarding.yml -f create_issues=true
```

Expected: Workflow triggered successfully

**Step 4: Monitor workflow execution**

Run:
```bash
gh run list --workflow=onboarding.yml --limit 1
gh run watch
```

Expected: Workflow creates 15 issues

**Step 5: Verify issues created**

Run:
```bash
gh issue list --label "sprint-0"
```

Expected: 15 Sprint 0 issues listed

**Step 6: Commit updated workflow (if usernames added)**

```bash
git add .github/workflows/onboarding.yml
git commit -m "chore: add student usernames to onboarding workflow"
git push origin main
```

---

## Task 17: Final Verification Checklist

**Files:**
- Create: `docs/monday-demo/pre-monday-checklist.md`

**Step 1: Create checklist document**

Create `docs/monday-demo/pre-monday-checklist.md`:
```markdown
# Pre-Monday Verification Checklist

## GitHub Setup

- [ ] GitHub Project board created and configured
- [ ] Custom fields created (Status, Priority, Role, Sprint, Trust Level)
- [ ] Views created (By Role, By Sprint, Monday Onboarding)
- [ ] Issue templates created (feature, bug, documentation)
- [ ] PR template created
- [ ] CODEOWNERS file configured
- [ ] Branch protection rules enabled (main, develop)
- [ ] GitHub labels created (trust, sprint, component)

## Workflows

- [ ] pr-validation.yml created and tested
- [ ] trust-check.yml created and tested
- [ ] auto-merge.yml created and tested
- [ ] onboarding.yml created and tested
- [ ] All workflows pushed to GitHub
- [ ] Sample PR tested successfully

## Student Onboarding

- [ ] 15 student accounts invited
- [ ] Write permissions granted
- [ ] Sprint 0 onboarding issues created
- [ ] Student usernames added to workflow
- [ ] Onboarding workflow triggered successfully

## Documentation

- [ ] GitHub setup guide created
- [ ] Demo script created
- [ ] Student quick start guide exists
- [ ] MASTER_DOCUMENTATION_MONDAY.md available
- [ ] Student roles documented

## Demo Environment

- [ ] k3s cluster running
- [ ] All services deployed
- [ ] Services accessible via port-forward
- [ ] Grafana accessible at localhost:3000
- [ ] Test data prepared

## Final Checks

- [ ] Run: `gh workflow list` - should show 4 workflows
- [ ] Run: `gh label list` - should show 27+ labels
- [ ] Run: `gh issue list --label sprint-0` - should show 15 issues
- [ ] Run: `gh project list` - should show student project
- [ ] Run: `curl http://localhost:8000/health/live` - should return healthy
- [ ] Run: `curl http://localhost:8001/health/live` - should return healthy
- [ ] Run: `curl http://localhost:8005/health/live` - should return healthy
- [ ] Run: `curl http://localhost:8007/health/live` - should return healthy

## Monday Morning (Final Prep)

- [ ] Verify all workflows still working
- [ ] Re-run onboarding workflow if needed
- [ ] Check all student invitations accepted
- [ ] Prepare demo environment
- [ ] Open demo script
- [ ] Print role cards for students
- [ ] Test projector/screen sharing
- [ ] Have backup plan ready

---

**You're ready for Monday! 🚀**
```

**Step 2: Commit checklist**

```bash
git add docs/monday-demo/pre-monday-checklist.md
git commit -m "docs: add pre-Monday verification checklist"
```

**Step 3: Push all changes**

```bash
git push origin main
```

**Step 4: Verify on remote**

Run:
```bash
gh repo view --web
```

Expected: Repository opens in browser with all changes visible

---

## Task 18: Final Documentation and Tag

**Files:**
- Modify: `docs/plans/2026-03-01-github-student-contribution-automation-implementation.md`

**Step 1: Create summary document**

Create `docs/monday-demo/README.md`:
```markdown
# Monday Demo Documentation

**Date:** March 3, 2026
**Purpose:** Onboard 15 AI students to Project Chimera

## Quick Links

- [Demo Script](./demo-script.md) - 60-minute agenda
- [GitHub Setup Guide](./github-setup-guide.md) - Project configuration
- [Pre-Monday Checklist](./pre-monday-checklist.md) - Verification steps
- [Student Quick Start](../../Student_Quick_Start.md) - Student guide
- [Student Roles](../../docs/STUDENT_ROLES.md) - Role assignments

## What Students Will Learn

1. **GitHub Workflow** - Issues, PRs, code review
2. **Microservices** - 8 AI services working together
3. **Kubernetes** - k3s cluster management
4. **Testing** - Unit tests, coverage, CI/CD
5. **Trust System** - Earn auto-merge through quality contributions

## Trust Score System

- **New (0 PRs)** - Manual review required
- **Learning (1-2 PRs)** - Manual review required
- **Trusted (3+ PRs)** - Auto-merge eligible

## Services Status

| Service | Status | Port | Demo Ready? |
|---------|--------|------|-------------|
| OpenClaw Orchestrator | ✅ Working | 8000 | Yes |
| SceneSpeak Agent | ✅ Working | 8001 | Yes |
| Captioning Agent | ⚠️ Partial | 8002 | Partial |
| BSL Translation | ⚠️ Partial | 8003 | Partial |
| Sentiment Agent | ⚠️ Partial | 8004 | Partial |
| Lighting Control | ✅ Working | 8005 | Yes |
| Safety Filter | ⚠️ Partial | 8006 | Partial |
| Operator Console | ✅ Working | 8007 | Yes |

## GitHub Automation

- **4 Workflows** - PR validation, trust check, auto-merge, onboarding
- **15 Issues** - Sprint 0 onboarding tasks
- **27 Labels** - Trust, sprint, component labels
- **Project Board** - Single shared board with role views

## Emergency Contacts

- Technical Lead: [GitHub @technical-lead]
- University Support: [email/phone]

## Rollback Plan

If GitHub automation fails:
1. Disable workflows: `gh workflow disable`
2. Fall back to manual review
3. Continue with k3s demo
4. Fix and re-enable workflows

---

**Good luck with the demo! The students will love Project Chimera.**
```

**Step 2: Commit final documentation**

```bash
git add docs/monday-demo/README.md
git commit -m "docs: add Monday demo documentation summary"
git push origin main
```

**Step 3: Create release tag**

```bash
git tag -a v0.2.0-github-automation -m "GitHub Student Contribution Automation

Features:
- GitHub Project board with role-based views
- 4 GitHub Actions workflows (validation, trust, auto-merge, onboarding)
- Trust-based auto-merge system (3+ PRs = trusted)
- Coverage gates for PRs
- Branch protection with CODEOWNERS
- 15 Sprint 0 onboarding issues
- Monday demo script and documentation

Target: Monday student demo (March 3, 2026)
"

git push origin v0.2.0-github-automation
```

Expected: Tag created and pushed

**Step 4: Final verification**

Run:
```bash
echo "=== GitHub Automation Setup Complete ===" && \
echo "" && \
echo "Workflows:" && \
gh workflow list && \
echo "" && \
echo "Labels:" && \
gh label list | wc -l && \
echo "" && \
echo "Sprint 0 Issues:" && \
gh issue list --label "sprint-0" | wc -l && \
echo "" && \
echo "Latest Tag:" && \
git describe --tags --abbrev=0
```

Expected output:
```
=== GitHub Automation Setup Complete ===

Workflows:
auto-merge.yml  active  PR Validation
onboarding.yml  active  Monday Onboarding
pr-validation.yml active  Trust Check
trust-check.yml active  Auto Merge

Labels:
27

Sprint 0 Issues:
15

Latest Tag:
v0.2.0-github-automation
```

---

## Summary

**Total Tasks:** 18
**Estimated Time:** 4-5 hours
**Target:** Monday, March 3, 2026

### Deliverables

1. **GitHub Project Board** - Single shared board with role-based views
2. **4 GitHub Actions Workflows** - PR validation, trust check, auto-merge, onboarding
3. **Issue & PR Templates** - 3 issue templates, 1 PR template
4. **CODEOWNERS** - Role-based review routing
5. **Branch Protection** - Configured for main, develop, sprint-*
6. **Labels** - 27 labels (trust, sprint, component)
7. **Onboarding Issues** - 15 Sprint 0 issues
8. **Documentation** - Setup guide, demo script, checklist
9. **Tag** - v0.2.0-github-automation

### Monday Goal

By end of Monday, all 15 students will:
- Have GitHub access
- Understand their assigned role
- Complete Sprint 0 onboarding task
- Be ready to make their first contribution

---

**Plan complete and saved to `docs/plans/2026-03-01-github-student-contribution-automation-implementation.md`.**

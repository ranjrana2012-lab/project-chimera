# GitHub Project Board Setup Instructions

**For:** Technical Lead
**Time Required:** ~2 hours
**Before:** Monday Demo

---

## Overview

This guide walks through setting up the GitHub Project Board for organizing all student work across 15 sprints.

---

## Step 1: Create the Project

### Using GitHub CLI

```bash
# Create the project
gh project create --title "Project Chimera" --owner "project-chimera"

# Note the PROJECT_ID from the output
```

### Using GitHub UI

1. Go to: https://github.com/orgs/project-chimera/projects
2. Click "New Project"
3. Title: "Project Chimera"
4. Select "Board" template
5. Click "Create"

---

## Step 2: Create Custom Fields

### Using GitHub CLI

```bash
# Get your PROJECT_ID first
PROJECT_ID="your-project-id-here"

# Create each field
gh project field create --project-id $PROJECT_ID --name "Status" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Priority" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Role" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Sprint" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Trust Level" --datatype "single_select"
gh project field create --project-id $PROJECT_ID --name "Points" --datatype "number"
```

### Using GitHub UI

1. Open the project
2. Click the → menu next to "Fields"
3. Select "Create new field"
4. Create each field with these settings:

**Status (Single Select)**
- Options: Backlog, Ready, In Progress, In Review, Done
- Colors: Gray, Blue, Yellow, Orange, Green

**Priority (Single Select)**
- Options: P1-Critical, P2-High, P3-Medium, P4-Low
- Colors: Red, Orange, Yellow, Gray

**Role (Single Select)**
- Options: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- Colors: Various

**Sprint (Single Select)**
- Options: Sprint 0, Sprint 1, ..., Sprint 14
- Colors: Various

**Trust Level (Single Select)**
- Options: New, Learning, Trusted
- Colors: Gray, Blue, Green

**Points (Number)**
- Format: 0, 1, 2, 3, 5, 8, 13

---

## Step 3: Create Views

### View 1: By Role

1. Click "View" menu
2. Select "New view"
3. Name: "By Role"
4. Layout: Board
5. Group by: Role custom field
6. Save

### View 2: By Sprint

1. Click "View" menu
2. Select "New view"
3. Name: "By Sprint"
4. Layout: Board
5. Add filter: Sprint = (selected sprint)
6. Save

### View 3: By Status (Kanban)

1. Click "View" menu
2. Select "New view"
3. Name: "Kanban"
4. Layout: Board
5. Group by: Status custom field
6. Save

### View 4: Monday Onboarding

1. Click "View" menu
2. Select "New view"
3. Name: "Monday Onboarding"
4. Add filter: Sprint = Sprint 0
5. Save

---

## Step 4: Create Repository Labels

### Using GitHub CLI

```bash
# Create each label
gh label create "sprint-0" --color "#fbca04" --description "Sprint 0 onboarding tasks"
gh label create "good-first-issue" --color "#7057ff" --description "Good for newcomers"
gh label create "help-wanted" --color "#008672" --description "Help wanted"
gh label create "bug" --color "#d73a4a" --description "Something isn't working"
gh label create "enhancement" --color "#a2eeef" --description "New feature or request"
gh label create "documentation" --color "#0075ca" --description "Improvements or additions to docs"
gh label create "trust:new" --color "#7f8491" --description "New contributor"
gh label create "trust:learning" --color "#5a5ed6" --description "1-2 PRs merged"
gh label create "trust:trusted" --color "#3a9f4d" --description "3+ PRs merged"
```

---

## Step 5: Link Repository to Project

```bash
# Link your repository to the project
gh project edit --project-id $PROJECT_ID --link-repo "project-chimera/project-chimera"
```

---

## Verification Checklist

- [ ] Project created
- [ ] All 7 custom fields created
- [ ] All 4 views created
- [ ] All 10 labels created
- [ ] Repository linked
- [ ] Test by creating a sample issue

---

## Next Steps

1. Trigger the onboarding workflow to create Sprint 0 issues
2. Verify issues appear in the project board
3. Test each view
4. Share board link with students

---

**Board URL:** https://github.com/orgs/project-chimera/projects/{PROJECT_NUMBER}

**Last Updated:** 2026-03-01

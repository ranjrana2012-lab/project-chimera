#!/bin/bash
# Quick GitHub Project Board Setup for Monday Demo
# Run this before Monday demo!

set -e

echo "=== GitHub Project Board Setup for Project Chimera ==="
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI not found. Installing..."
    # Method 1: Using apt repository
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh -y
    echo "GitHub CLI installed."
else
    echo "GitHub CLI already installed."
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "Not authenticated. Please run: gh auth login"
    exit 1
fi

# Get repository owner
REPO_OWNER=$(git config --get remote.origin.url | sed 's/.*:*\///' | sed 's/\.git$//')
if [ -z "$REPO_OWNER" ]; then
    REPO_OWNER="project-chimera"
fi

echo "Repository owner: $REPO_OWNER"
echo ""

# Create the project
echo "Creating GitHub Project Board..."
PROJECT_OUTPUT=$(gh project create --title "Project Chimera" --owner "$REPO_OWNER")
PROJECT_ID=$(echo "$PROJECT_OUTPUT" | grep -oP 'id: \K\w+' || echo "$PROJECT_OUTPUT" | head -1)
echo "Project created with ID: $PROJECT_ID"
echo ""

# Extract numeric project ID from output
sleep 2

# Create custom fields
echo "Creating custom fields..."
gh project field create --project-id "$PROJECT_ID" --name "Status" --datatype "single_select" --configuration options=Backlog,Ready,In\ Progress,In\ Review,Done --configuration empty=false 2>/dev/null || echo "Status field exists"
gh project field create --project-id "$PROJECT_ID" --name "Priority" --datatype "single_select" --configuration options=P1-Critical,P2-High,P3-Medium,P4-Low --configuration empty=false 2>/dev/null || echo "Priority field exists"
gh project field create --project-id "$PROJECT_ID" --name "Role" --datatype "single_select" --configuration options=1,2,3,4,5,6,7,8,9,10 --configuration empty=false 2>/dev/null || echo "Role field exists"
gh project field create --project-id "$PROJECT_ID" --name "Sprint" --datatype "single_select" --configuration options=Sprint\ 0,Sprint\ 1,Sprint\ 2,Sprint\ 3,Sprint\ 4,Sprint\ 5,Sprint\ 6,Sprint\ 7,Sprint\ 8,Sprint\ 9,Sprint\ 10,Sprint\ 11,Sprint\ 12,Sprint\ 13,Sprint\ 14 --configuration empty=false 2>/dev/null || echo "Sprint field exists"
gh project field create --project-id "$PROJECT_ID" --name "Trust Level" --datatype "single_select" --configuration options=New,Learning,Trusted --configuration empty=false 2>/dev/null || echo "Trust Level field exists"
gh project field create --project-id "$PROJECT_ID" --name "Points" --datatype "number" 2>/dev/null || echo "Points field exists"
echo "Custom fields created."
echo ""

# Create labels
echo "Creating repository labels..."
gh label create "sprint-0" --color "#fbca04" --description "Sprint 0 onboarding tasks" 2>/dev/null || echo "sprint-0 label exists"
gh label create "good-first-issue" --color "#7057ff" --description "Good for newcomers" 2>/dev/null || echo "good-first-issue label exists"
gh label create "help-wanted" --color "#008672" --description "Help wanted" 2>/dev/null || echo "help-wanted label exists"
gh label create "bug" --color "#d73a4a" --description "Something isn't working" 2>/dev/null || echo "bug label exists"
gh label create "enhancement" --color "#a2eeef" --description "New feature or request" 2>/dev/null || echo "enhancement label exists"
gh label create "documentation" --color "#0075ca" --description "Improvements or additions to docs" 2>/dev/null || echo "documentation label exists"
gh label create "trust:new" --color "#7f8491" --description "New contributor" 2>/dev/null || echo "trust:new label exists"
gh label create "trust:learning" --color "#5a5ed6" --description "1-2 PRs merged" 2>/dev/null || echo "trust:learning label exists"
gh label create "trust:trusted" --color "#3a9f4d" --description "3+ PRs merged" 2>/dev/null || echo "trust:trusted label exists"
echo "Labels created."
echo ""

# Link repository to project
echo "Linking repository to project..."
gh project edit --project-id "$PROJECT_ID" --link-repo "$REPO_OWNER/project-chimera" 2>/dev/null || echo "Repository already linked"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Create views in GitHub Project Board UI:"
echo "   - By Role (group by: Role)"
echo "   - By Sprint (group by: Sprint)"
echo "   - Kanban (group by: Status)"
echo "   - Monday Onboarding (filter: Sprint = Sprint 0)"
echo ""
echo "2. Trigger onboarding workflow:"
echo "   gh workflow run onboarding.yml -f create_issues=true"
echo ""
echo "3. Invite students to the repository."

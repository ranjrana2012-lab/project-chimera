# Simplified Onboarding Guide - Project Chimera Phase 2

**Purpose**: Quick start for new team members (students, interns, contributors)
**Time to Complete**: 30-60 minutes
**Prerequisites**: Basic computer skills, no prior coding experience required

---

## Welcome to Project Chimera!

**What We Do**: We build AI-powered live theatre that adapts to audience emotions in real-time.

**Your Role**: You'll help us make theatre more accessible and interactive using technology.

---

## Step 1: Set Up Your Tools (5 minutes)

### Required Tools

**Git** (for saving and sharing code):
- Download: https://git-scm.com/downloads
- Install with default settings
- Open "Git Bash" (Windows) or Terminal (Mac/Linux)

**Code Editor** (for writing code):
- **Recommended**: Visual Studio Code (VS Code)
- Download: https://code.visualstudio.com/
- Install with default settings

**Slack/Discord** (for communication):
- Join our workspace: [Link to be provided]
- Download app for your phone

---

## Step 2: Get the Code (5 minutes)

### Clone the Repository

**Open Git Bash/Terminal** and type:

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
```

**What This Does**:
- Downloads all project files to your computer
- Creates a folder called "project-chimera"

**Success**: You'll see "project-chimera" folder with many files inside

---

## Step 3: Understand the Project (10 minutes)

### What We're Building

**Phase 1 Complete** ✅:
- chimera_core.py: Single script that demonstrates AI adapting to emotions
- Sentiment analysis: Detects if text is happy, sad, or neutral
- Adaptive dialogue: AI changes responses based on emotion
- Demo mode: Shows how it works

**Phase 2 In Progress** 🔄:
- Live theatre performances
- BSL avatar (sign language)
- DMX lighting control
- Audio system control

### Key Files to Know

**For Learning**:
- `README.md`: Project overview
- `docs/QUICK_START.md`: How to run things
- `services/operator-console/chimera_core.py`: Main AI script

**For Phase 2**:
- `docs/PHASE_2_IMPLEMENTATION_PLAN.md`: What we're building next
- `docs/phase2/`: Planning documents

---

## Step 4: Make Your First Change (15 minutes)

### Practice Task: Fix a Typo

**1. Open VS Code**:
- Click "Open Folder"
- Select the "project-chimera" folder you cloned

**2. Find the File**:
- Look in the left sidebar for `README.md`
- Click to open it

**3. Make a Change**:
- Find any typo or grammar error
- Or add your name to the contributors list
- Make a small change (don't worry, it's practice)

**4. Save the File**:
- Press Ctrl+S (or Cmd+S on Mac)

---

## Step 5: Save Your Changes (10 minutes)

### Git Basics (3 Commands)

**Command 1: Check What Changed**
```bash
git status
```
**What This Does**: Shows which files you modified

---

**Command 2: Save Your Changes**
```bash
git add README.md
```
**What This Does**: Stages your file for saving
*(Replace README.md with your filename)*

---

**Command 3: Describe Your Change**
```bash
git commit -m "docs: fix typo in README"
```
**What This Does**: Saves your change with a message
*(Replace the message with what you actually did)*

---

## Step 6: Share Your Work (5 minutes)

### Push to GitHub

**Command 1: Send Your Changes**
```bash
git push origin main
```

**What This Does**: Sends your changes to GitHub

**Success**: You'll see "GitHub" in your web browser at the repository

---

## Git Cheat Sheet

### Common Commands

| Command | What It Does |
|---------|--------------|
| `git status` | See what files changed |
| `git add filename` | Stage a file for saving |
| `git commit -m "message"` | Save changes with a message |
| `git push` | Send changes to GitHub |
| `git pull` | Get latest changes from GitHub |

### Pro Tips

**Commit Often**: Save your work frequently (every 30 minutes or so)
**Write Clear Messages**: Describe what you changed and why
**Don't Commit Secrets**: Never commit passwords or API keys
**Ask for Help**: If you're stuck, ask your mentor or team

---

## Project Workflow

### How We Work

1. **Choose a Task**: From the task list or ask your mentor
2. **Create a Branch**: Make a copy of the code for your work
3. **Make Changes**: Write code, fix bugs, add features
4. **Test Your Changes**: Make sure it works
5. **Commit and Push**: Save and share your work
6. **Request Review**: Ask someone to check your work
7. **Merge**: Combine your changes into the main code

### Branching (Advanced)

**Create a Branch** (for new features):
```bash
git checkout -b my-feature-name
```

**Switch Between Branches**:
```bash
git checkout main
```

**Delete a Branch** (when done):
```bash
git branch -d my-feature-name
```

---

## Common Tasks

### Update Your Code

**Get Latest Changes**:
```bash
git pull origin main
```

### See What Changed

**View Recent Commits**:
```bash
git log --oneline -10
```

### Undo a Mistake

**Restore a File** (if you mess up):
```bash
git restore filename
```

**Unstage a File** (if you added by mistake):
```bash
git restore --staged filename
```

---

## Getting Help

### Where to Ask

**Quick Questions**: Slack/Discord #help channel
**Code Review**: Ask your mentor directly
**Bugs**: Create a GitHub issue
**Blocked**: Don't wait! Ask someone immediately

### Good Questions

**Instead of**: "It doesn't work"
**Try**: "I'm trying to do X, I got error Y, here's what I tried"

**Instead of**: "I'm stuck"
**Try**: "I'm working on task X, I've tried A, B, C, but D isn't working"

### Resources

**Documentation**:
- Project README: `README.md`
- Quick Start: `docs/QUICK_START.md`
- Architecture: `docs/architecture/overview.md`

**Learning Resources**:
- Git: https://git-scm.com/docs
- VS Code: https://code.visualstudio.com/docs
- Python: https://docs.python.org/3/tutorial/

---

## First Week Checklist

### Day 1: Setup ✅
- [ ] Install Git
- [ ] Install VS Code
- [ ] Join Slack/Discord
- [ ] Clone repository
- [ ] Introduce yourself to the team

### Day 2: Learning ✅
- [ ] Read README.md
- [ ] Read QUICK_START.md
- [ ] Try running chimera_core.py
- [ ] Explore the codebase
- [ ] Ask questions

### Day 3: Practice ✅
- [ ] Make a small documentation change
- [ ] Commit your change
- [ ] Push to GitHub
- [ ] Celebrate! 🎉

### Week 1 Goals
- [ ] Complete 3 small tasks
- [ ] Get comfortable with Git
- [ ] Learn the code structure
- [ ] Meet your mentor

---

## Success Criteria

### You're Doing Great If:

- ✅ You can clone and update the repository
- ✅ You can make and commit changes
- ✅ You ask questions when stuck
- ✅ You review your team's code
- ✅ You communicate blockers early

### Red Flags (Ask for Help If):

- ❌ You're stuck for more than 1 hour
- ❌ You're afraid to break something
- ❌ You don't understand the task
- ❌ You haven't committed in a week
- ❌ You're overwhelmed

---

## Phase 2 Specifics

### What You'll Work On

**Frontend Developers**:
- Caption overlay for live performances
- Operator dashboard
- User interface improvements

**Backend Developers**:
- API endpoints for hardware control
- Service integration
- Testing and bug fixes

**BSL Researchers**:
- Gesture library research
- Translation accuracy testing
- Cultural validation

**QA Testers**:
- Testing all components
- Documenting bugs
- Verifying fixes

**Documentation**:
- User guides
- API documentation
- Tutorials and examples

---

## Quick Reference

### Essential Commands

```bash
# Start working
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

# Update regularly
git pull origin main

# Save your work
git add .
git commit -m "describe your changes"
git push origin main
```

### Important Links

- **GitHub**: https://github.com/ranjrana2012-lab/project-chimera
- **Documentation**: `docs/`
- **Issues**: https://github.com/ranjrana2012-lab/project-chimera/issues
- **Discord/Slack**: [Link to be provided]

---

## Welcome Aboard!

**We're Excited to Have You** 🎉

Project Chimera is an innovative project at the intersection of AI and live theatre. We're building something that hasn't been done before, and we need your help.

**Your Contribution Matters**:
- Every commit helps
- Every question teaches us something
- Every perspective makes us better

**Let's Build Something Amazing Together** 🚀

---

## Appendix: Troubleshooting

### Problem: Git Commands Don't Work

**Solution**:
1. Make sure Git is installed: `git --version`
2. Check you're in the right folder: `pwd`
3. Try the full path: `cd /path/to/project-chimera`

### Problem: Can't Push to GitHub

**Solution**:
1. Check you're on the right branch: `git branch`
2. Pull first: `git pull origin main`
3. Check for errors: `git status`

### Problem: Code Won't Run

**Solution**:
1. Check requirements are installed: `pip install -r requirements.txt`
2. Check Python version: `python --version` (need 3.10+)
3. Read the error message carefully
4. Ask for help with the error message

### Problem: Don't Understand the Code

**Solution**:
1. Start with README.md and QUICK_START.md
2. Read the comments in the code
3. Look at similar examples
4. Ask your mentor to explain

---

**Simplified Onboarding Guide Version: 1.0**
**For: Project Chimera Phase 2**
**Date: April 9, 2026**
**Questions?** Contact your mentor or ask in #help channel

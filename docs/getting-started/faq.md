# Student FAQ - Frequently Asked Questions

---

## Getting Started

### Q: What if I've never used Kubernetes before?

**A:** You're not alone! About half of our students are new to K8s. We have:
- A detailed [bootstrap guide](quick-start.md)
- Office hours dedicated to setup help
- A "K8s Buddy" system for pairing
- The `make bootstrap` script handles most of it automatically

### Q: Do I need a GPU?

**A:** No! Project Chimera works without a GPU. You'll run:
- Core services (FastAPI, Kafka, Redis) - CPU only
- ML inference using pre-trained models - optional GPU
- Most development is API/integration work, not ML training

### Q: Can I use Windows/Mac?

**A:** Yes, with caveats:
- **Best:** Linux (Ubuntu 22.04) - fully supported
- **Mac:** Works, but k3s requires Docker Desktop
- **Windows:** Use WSL2 with Ubuntu

If you're on Windows, come to office hours and we'll help set up WSL2.

---

## Development Workflow

### Q: How do I know what to work on?

**A:** Three ways:
1. **Assigned Issues:** Check your Sprint 0 tasks first
2. **Good First Issues:** Filter by the `good-first-issue` label
3. **Propose Ideas:** Open an issue to discuss first

### Q: What if an issue is already assigned?

**A:** Don't start working on it. Instead:
- Comment: "I'm also interested in this, can I help?"
- The assignee may welcome collaboration
- Or find another unassigned issue

### Q: How long should a PR take?

**A:** Depends on complexity:
- **Simple:** 1-2 days (typo fix, small refactor)
- **Medium:** 3-5 days (new feature, bug fix)
- **Complex:** 1-2 weeks (architecture changes)

If you're stuck, ask for help! Don't spin your wheels.

### Q: What if I break something?

**A:** It happens! Here's what to do:
1. Don't panic - that's what git is for
2. Check if tests pass locally
3. Open a PR anyway if tests pass
4. If tests fail, ask for help

We've all broken production. It's how we learn. 😅

---

## Evaluation & Grading

### Q: How will I be graded?

**A:** You'll be evaluated on:

| Component | Weight |
|-----------|--------|
| Code Quality | 30% |
| PR Contributions | 25% |
| Peer Reviews | 15% |
| Sprint Completion | 15% |
| Communication | 15% |

See [Evaluation Criteria](evaluation-criteria.md) for details.

### Q: What happens if I fall behind?

**A:** We've got your back:
- **Weeks 1-2:** We'll reach out proactively
- **Week 3+:** We'll pair you with a mentor
- **Office hours:** Always available
- **Extension policy:** Talk to us, we're reasonable

Communication is key. Don't disappear!

---

## Technical Questions

### Q: What coding language should I use?

**A:** **Python** is our primary language. You'll use:
- Python 3.10+ for all services
- YAML for Kubernetes manifests
- Bash for scripts
- SQL/NoSQL for data access

### Q: Can I use AI tools (ChatGPT, Copilot)?

**A:** Yes, with guidelines:
- ✅ Use AI for boilerplate, debugging, learning
- ✅ Disclose AI use in PR comments
- ❌ Don't copy-paste without understanding
- ❌ Don't let AI write tests without review

**Rule:** You must understand and be able to explain every line of code you submit.

### Q: I'm getting an error. Help?

**A:** Try this checklist:
1. **Read the error message** - what's it actually saying?
2. **Check logs** - `kubectl logs -f {pod-name}`
3. **Search the issue tracker** - someone may have solved this
4. **Google the error** - stackoverflow is your friend
5. **Ask in Slack** - paste the error and what you've tried

When asking, always include:
- What you're trying to do
- What you expected
- What actually happened (errors, logs)
- What you've tried

---

## Project-Specific

### Q: What does "Dynamic Performance Hub" mean?

**A:** Project Chimera creates live theatre shows that **adapt in real-time** to audience reactions:
- AI analyzes audience sentiment from social media
- AI generates dialogue based on audience mood
- Lighting and music respond to emotional tone

You're building an AI theatre director that reads the room! 🎭

### Q: What's the difference between "agents" and "services"?

**A:** We use these interchangeably, but:
- **Service:** Technical term for a microservice (FastAPI app)
- **Agent:** Functional term for AI capabilities

Each agent is deployed as one or more services.

### Q: Why 15 students? Won't that be chaotic?

**A:** 15 is perfect for our architecture:
- 10 role-specific areas (one expert per area)
- 5 "floating" contributors who help wherever needed
- Structure: Everyone owns something, but collaboration is key

---

## Monday Demo

### Q: What should I bring to the Monday demo?

**A:**
- Your laptop (fully charged)
- Questions! No question is too basic
- Excitement! We're building something cool 🚀

### Q: What if I can't make it to Monday's demo?

**A:** Let us know ASAP! We'll:
- Record the demo for you
- Schedule a 1:1 catchup
- Make sure you get your Sprint 0 tasks

### Q: Will there be food?

**A:** We'll have snacks! 🍕 If you have dietary restrictions, let us know before Monday.

---

## Career & Future

### Q: Will this help me get a job?

**A:** Absolutely! You'll gain experience in:
- FastAPI & async Python (in-demand)
- Kubernetes (huge plus)
- CI/CD & DevOps practices
- AI/ML integration
- Open source contribution

Your GitHub contributions will be a portfolio piece.

### Q: Can I add this to my resume?

**A:** Yes! You can list:

```
AI Developer | Project Chimera | Jan 2026 - Present
- Contributed to open-source AI theatre platform
- Developed FastAPI microservices for real-time dialogue generation
- Deployed services on Kubernetes with CI/CD pipelines
- Collaborated with team of 15 using GitHub workflows
```

### Q: Will there be references/recommendations?

**A:** After one semester of solid contributions, we'll write you a strong recommendation.

---

## Meta Questions

### Q: Who created Project Chimera?

**A:** Project Chimera was created by:
- {UNIVERSITY} Theatre + CS Departments collaboration
- Faculty Advisor: {NAME}
- Technical Lead: {NAME}
- Initial team of {NUMBER} students in {YEAR}

It's now open source, used by universities worldwide.

### Q: Why open source?

**A:** Because:
- Knowledge should be shared
- Other universities can use and improve it
- Students learn real-world open source practices
- It builds your professional network

### Q: How can I stay after the semester ends?

**A:** We love long-term contributors! Options:
- Continue as a maintainer for your component
- Mentor new students next semester
- Help with research and publications
- Contribute to new features

---

## Still Have Questions?

**Ask in Slack:** #help-troubleshooting
**Email:** {EMAIL}
**Office Hours:** See [office hours guide](office-hours.md)

---

**Last Updated:** 2026-03-01
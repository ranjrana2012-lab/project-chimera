# Environment Setup Tutorial

**Type:** Video Script / Screencast Tutorial
**Duration:** 15-20 minutes
**Target Audience:** New students joining Project Chimera
**Prerequisites:** Git, Docker, kubectl installed

---

## Script Outline

### Part 1: Introduction (0:00-1:30)

**Visual:** Title card with Project Chimera logo

**Speaker:** "Welcome to Project Chimera! In this tutorial, you'll learn how to set up your complete development environment so you can start contributing to our AI-powered live theatre platform."

**Visual:** Screen recording showing:
- GitHub repository page
- Project architecture diagram
- Key components (agents, platform, operator console)

**Speaker:** "By the end of this tutorial, you'll have:
- A working k3s Kubernetes cluster
- All Project Chimera services running
- Development tools installed
- Your first contribution ready"

---

### Part 2: Prerequisites Check (1:30-3:00)

**Visual:** Checklist on screen with checkmarks

**Speaker:** "Before we begin, let's verify you have everything you need. Open your terminal and run these commands:"

**Visual:** Terminal commands with green checkmarks for passing

```bash
# Check Python version
python3 --version
# Expected: Python 3.10 or higher

# Check Docker
docker --version
# Expected: Docker 20.10 or higher

# Check kubectl
kubectl version --client
# Expected: kubectl 1.25 or higher

# Check Git
git --version
# Expected: git 2.0 or higher
```

**Speaker:** "If any of these are missing or show older versions, check the Quick Start Guide for installation instructions. Links are in the description below."

**Visual:** Code block in description:
```bash
# Install Python 3.10
sudo apt update && sudo apt install python3.10 python3-pip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Git
sudo apt install git
```

---

### Part 3: Clone Repository (3:00-5:00)

**Visual:** Terminal window

**Speaker:** "First, let's clone the Project Chimera repository. Run:"

```bash
git clone https://github.com/project-chimera/project-chimera.git
cd project-chimera
```

**Visual:** Git clone progress bar, then listing files

```bash
ls -la
```

**Speaker:** "Great! You should see the project structure with services, platform, docs, and more. Take a moment to explore the README.md file to understand the project better."

**Visual:** README.md displayed with key sections highlighted

---

### Part 4: Automated Bootstrap (5:00-10:00)

**Speaker:** "Project Chimera includes an automated bootstrap script that will install k3s, set up the local registry, build all service images, and deploy everything. This takes about 15-20 minutes."

**Visual:** Terminal showing bootstrap process

```bash
make bootstrap
```

**Speaker (voiceover during progress):** "The bootstrap script is now:
1. Installing k3s (lightweight Kubernetes)
2. Setting up local container registry
3. Building all 8 service Docker images
4. Deploying infrastructure (Redis, Kafka, Milvus)
5. Deploying monitoring (Prometheus, Grafana, Jaeger, AlertManager)
6. Deploying all AI agents"

**Visual:** Progress indicators for each step

**Speaker:** "Let's verify k3s is installed:"

```bash
kubectl get nodes
```

**Expected output:**
```
NAME                      STATUS   ROLES                  AGE   VERSION
chimera-control-plane     Ready    control-plane,master   5m    v1.27.1+k3s2
```

---

### Part 5: Verify Deployment (10:00-12:00)

**Speaker:** "Now let's verify all services are running correctly:"

```bash
make bootstrap-status
```

**Visual:** Status output showing all services

**Speaker:** "You should see all services marked as Running or Ready. Let's check the pods:"

```bash
kubectl get pods -n live
```

**Expected output:**
```
NAME                                   READY   STATUS    RESTARTS   AGE
openclaw-orchestrator-xxx-yyy         1/1     Running   0          5m
scenespeak-agent-xxx-yyy              1/1     Running   0          5m
captioning-agent-xxx-yyy              1/1     Running   0          5m
bsl-agent-xxx-yyy                     1/1     Running   0          5m
sentiment-agent-xxx-yyy              1/1     Running   0          5m
lighting-service-xxx-yyy              1/1     Running   0          5m
safety-filter-xxx-yyy                 1/1     Running   0          5m
operator-console-xxx-yyy              1/1     Running   0          5m
```

---

### Part 6: Access Services (12:00-14:00)

**Speaker:** "Great! All services are running. Let's access them:"

```bash
# Health check all services
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -s http://localhost:$port/health/live && echo " : Port $port OK"
done
```

**Visual:** Each service returning OK

**Speaker:** "Now let's access the Operator Console in your browser:"

**Visual:** Browser opening to http://localhost:8007

**Speaker:** "The Operator Console shows:
- Real-time service status
- Active show information
- Alert notifications
- Approval workflows"

**Speaker:** "Let's also check the Grafana dashboards:"

**Visual:** Browser opening to http://localhost:3000

```bash
# Grafana credentials
Username: admin
Password: admin
```

**Speaker:** "You'll see dashboards for:
- Show Overview
- Dialogue Quality
- Audience Engagement"

---

### Part 7: Run Tests (14:00-16:00)

**Speaker:** "Before making changes, let's verify everything works by running tests:"

```bash
# Run all tests
make test

# Or run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
```

**Visual:** Test output with green passing tests

**Speaker:** "All tests should pass. If you see any failures, check the Testing Guide for troubleshooting tips."

---

### Part 8: Development Tools (16:00-18:00)

**Speaker:** "Let's set up your development environment:"

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

**Speaker:** "Pre-commit hooks will automatically:
- Check code style with black and ruff
- Run linters before each commit
- Catch issues early"

**Speaker:** "Recommended IDE setup:
- VS Code with Python extension
- Pylance for IntelliSense
- Docker extension for container support"

---

### Part 9: Your First Contribution (18:00-20:00)

**Speaker:** "You're ready to contribute! Here's your workflow:"

```bash
# Create a feature branch
git checkout -b feature/my-first-contribution

# Make your changes
# ... edit files ...

# Test your changes
make test
make lint

# Commit your changes
git add .
git commit -m "feat: add my feature"

# Push to GitHub
git push origin feature/my-first-contribution
```

**Visual:** Pull request creation on GitHub

**Speaker:** "Create a Pull Request on GitHub. Add:
- Clear title describing your change
- Description of what you did and why
- Link to related issue (if applicable)

**Speaker:** "Your PR will automatically run tests. If everything passes, you'll get merged!"

---

## Summary

**Visual:** Checklist with all items checked

- ✅ Prerequisites verified
- ✅ Repository cloned
- ✅ k3s installed
- ✅ Services deployed
- ✅ Services verified
- ✅ Tests passing
- ✅ Development tools ready
- ✅ First contribution workflow learned

**Speaker:** "Congratulations! You now have a complete Project Chimera development environment. Check out the other tutorials in this series for:

- Testing Guide: Learn how to write and run tests
- Debugging Guide: Troubleshooting common issues
- API Documentation: Understanding service APIs
- Deployment Guide: Deploying to production

**Speaker:** "Happy contributing, and welcome to Project Chimera!"

---

## Resources

**Documentation:**
- [Quick Start Guide](../quick-start.md)
- [Student FAQ](../faq.md)
- [Troubleshooting](../../demo/troubleshooting.md)
- [Office Hours](../office-hours.md)

**GitHub:**
- Repository: https://github.com/project-chimera/project-chimera
- Issues: https://github.com/project-chimera/project-chimera/issues
- Discussions: https://github.com/project-chimera/project-chimera/discussions

**Community:**
- Slack: #project-chimera-students
- Email: chimera-help@example.com

---

**Next Tutorial:** [Testing Guide](02-testing-guide.md) - Learn how to write and run tests for Project Chimera.

---

*Environment Setup Tutorial - Project Chimera v0.4.0 - March 2026*

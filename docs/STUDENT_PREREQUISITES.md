# Project Chimera - Student Prerequisites

This guide lists all required tools, software, and setup steps before starting development on Project Chimera.

## Last Updated

April 17, 2026

## Overview

Project Chimera is a FastAPI-based microservices application using Docker for containerization. Before contributing, ensure your development environment meets these requirements.

---

## Hardware Requirements

### Minimum Requirements
- **CPU:** 4 cores (Intel i5 or equivalent)
- **RAM:** 8GB (16GB recommended for smooth development)
- **Disk Space:** 20GB free space (for Docker images, models, and code)

### Recommended Specifications
- **CPU:** 8 cores
- **RAM:** 16GB or more
- **Disk Space:** 50GB SSD (for better performance)
- **Network:** Stable internet connection (for API calls and Docker image pulls)

---

## Software Requirements

### Essential Tools

#### 1. Docker and Docker Compose
**Required:** Yes
**Purpose:** Container orchestration for running all 8 MVP services

**Installation:**
- **Docker:** Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Version:** Docker Engine 20.10+ or Docker Desktop 4.15+
- **Docker Compose:** V2.0+ (included with Docker Desktop)

**Verification:**
```bash
docker --version
docker-compose --version
```

**Expected Output:**
```
Docker version 24.0.0 or higher
Docker Compose version v2.20.0 or higher
```

---

#### 2. Python
**Required:** Yes (for local development and testing)
**Purpose:** Running services locally, running tests, development scripts

**Installation:**
- **Version:** Python 3.10 or higher (3.12+ recommended)
- **Package Manager:** pip (included with Python)

**Installation Links:**
- [python.org](https://www.python.org/downloads/)
- Or use pyenv: `brew install pyenv` (macOS/Linux)
- Or use Windows Store (Windows)

**Verification:**
```bash
python --version
pip --version
```

**Expected Output:**
```
Python 3.10.0 or higher
pip 23.0 or higher
```

---

#### 3. Git
**Required:** Yes
**Purpose:** Version control for source code

**Installation:**
- Download from [git-scm.com](https://git-scm.com/downloads)
- Or use package manager: `brew install git` (macOS), `sudo apt install git` (Linux)

**Verification:**
```bash
git --version
```

**Expected Output:**
```
git version 2.40.0 or higher
```

---

#### 4. Code Editor / IDE
**Required:** Yes
**Purpose:** Writing and editing code

**Recommended Options:**
- **VS Code** (Free, cross-platform) - [code.visualstudio.com](https://code.visualstudio.com/)
- **PyCharm Community** (Free, Python-focused) - [jetbrains.com/pycharm](https://www.jetbrains.com/pycharm/)
- **Sublime Text** (Paid, fast)

**VS Code Extensions (if using VS Code):**
- Python
- Docker
- YAML
- GitLens
- Pylance

---

#### 5. Command Line Tools
**Required:** Yes
**Purpose:** Running commands, managing Docker, testing

**For Windows Users:**
- Windows Terminal (recommended) or PowerShell
- Git Bash (included with Git)

**For macOS Users:**
- Terminal (built-in) or iTerm2

**For Linux Users:**
- Any terminal emulator (gnome-terminal, konsole, etc.)

---

### Optional but Recommended Tools

#### curl
**Purpose:** Testing API endpoints and health checks
**Installation:**
- macOS: `brew install curl` (usually pre-installed)
- Linux: `sudo apt install curl`
- Windows: Included with Git Bash

**Verification:**
```bash
curl --version
```

#### jq
**Purpose:** Parsing JSON output from APIs
**Installation:**
- macOS: `brew install jq`
- Linux: `sudo apt install jq`
- Windows: Download from [stedolan.github.io/jq](https://stedolan.github.io/jq/)

**Verification:**
```bash
jq --version
```

#### Postman or Insomnia
**Purpose:** API testing and exploration
**Download:**
- [Postman](https://www.postman.com/downloads/)
- [Insomnia](https://insomnia.rest/download/)

---

## Environment Configuration

### Operating System Support

| OS | Support Level | Notes |
|----|---------------|-------|
| **macOS** | ✅ Full Support | Tested on macOS 13+ (Ventura, Sonoma) |
| **Linux** | ✅ Full Support | Tested on Ubuntu 22.04, Debian 12 |
| **Windows** | ✅ Full Support | Requires WSL2 for best experience |

#### Windows Users: WSL2 Recommended
For Windows development, we recommend using WSL2 (Windows Subsystem for Linux 2):
- Install WSL2 following [Microsoft's guide](https://learn.microsoft.com/en-us/windows/wsl/install)
- Install Ubuntu 22.04 LTS
- Run Docker Desktop inside WSL2

---

## Network Requirements

### Internet Access
Required for:
- Pulling Docker images (first-time setup: ~5GB download)
- API calls to external services (GLM API for LLM)
- Git operations (cloning, pushing)

### Firewall Configuration
Ensure these ports are available locally (no conflicts):
- **8000-8008:** Core application services
- **6379:** Redis database

If you have other services using these ports, you may need to stop them or reconfigure.

---

## Account Requirements

### Git Repository Access
- **GitHub Account:** Required for cloning and contributing
- **SSH Key:** Recommended for secure Git operations

### API Keys (Optional)
- **GLM API Key:** Required for SceneSpeak Agent LLM functionality
  - Get from [open.bigmodel.cn](https://open.bigmodel.cn/)
  - Set as `GLM_API_KEY` in `.env` file

---

## Verification Checklist

Before starting development, verify your setup:

- [ ] Docker installed and running (`docker --version`)
- [ ] Docker Compose working (`docker-compose --version`)
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Git installed and configured (`git --version`)
- [ ] Code editor installed (VS Code, PyCharm, etc.)
- [ ] Can run terminal commands
- [ ] Have 20GB+ free disk space
- [ ] Internet connection working
- [ ] Ports 8000-8008 and 6379 available
- [ ] Can clone Git repository

---

## Next Steps

Once prerequisites are verified:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_ORG/Project_Chimera.git
   cd Project_Chimera
   ```

2. **Continue with setup guide:**
   - Read [STUDENT_SETUP.md](STUDENT_SETUP.md)
   - Run the first-run script
   - Start all services

---

## Troubleshooting

### Docker won't start
- **Windows:** Ensure WSL2 is enabled
- **macOS:** Ensure Docker Desktop is running
- **Linux:** Ensure your user is in the `docker` group

### Python version too old
- Install Python 3.12+ from python.org
- Or use pyenv to manage multiple Python versions

### Out of memory errors
- Close other applications
- Increase Docker memory limit (Docker Desktop → Settings → Resources)
- Minimum recommended: 4GB for Docker

### Port already in use
- Check what's using the port: `lsof -i :8000` (macOS/Linux)
- Stop conflicting services
- Or reconfigure ports in docker-compose.mvp.yml

---

## Getting Help

If you encounter issues with prerequisites:

1. Check the [troubleshooting guide](STUDENT_TROUBLESHOOTING.md)
2. Ask in the project Discord/Slack
3. Create an issue on GitHub
4. Contact your technical lead

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Python Documentation](https://docs.python.org/3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Git Documentation](https://git-scm.com/doc)

---

*Last Updated: April 17, 2026*
*For questions, contact: Project Chimera Technical Lead*

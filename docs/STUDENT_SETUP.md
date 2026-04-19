# Student Setup Guide - Project Chimera

This guide walks you through setting up your Project Chimera development environment from scratch. Follow these steps to get all services running on your local machine.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Cloning the Repository](#cloning-the-repository)
3. [Configuring Environment Variables](#configuring-environment-variables)
4. [Creating Your .env File](#creating-your-env-file)
5. [Starting All Services](#starting-all-services)
6. [Verifying Services Are Running](#verifying-services-are-running)
7. [Accessing the Operator Console](#accessing-the-operator-console)
8. [Stopping Services](#stopping-services)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

- **Docker**: Version 20.10 or higher
  - Download from: https://docs.docker.com/get-docker/
  - Verify installation: `docker --version`

- **Docker Compose**: Version 2.0 or higher
  - Usually included with Docker Desktop
  - Verify installation: `docker compose version`

- **Git**: For cloning the repository
  - Download from: https://git-scm.com/downloads
  - Verify installation: `git --version`

- **Python 3.10+**: For running tests locally (optional)
  - Download from: https://www.python.org/downloads/

- **At least 8GB RAM**: Docker containers require significant memory
- **At least 20GB free disk space**: For Docker images and models

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Processor**: x86_64 or ARM64 (Apple Silicon)
- **Network**: Stable internet connection for downloading Docker images

## Cloning the Repository

### Step 1: Navigate to Your Workspace

Open a terminal and navigate to where you want to keep the project:

```bash
cd ~/projects  # or any directory you prefer
```

### Step 2: Clone the Repository

Clone the Project Chimera repository:

```bash
git clone https://github.com/your-org/project-chimera.git
cd project-chimera
```

### Step 3: Verify the Clone

Ensure you have the necessary files:

```bash
ls -la
```

You should see:
- `docker-compose.mvp.yml` - MVP Docker Compose configuration
- `.env.example` - Environment variable template
- `services/` - Directory containing all microservices
- `docs/` - Documentation directory

## Configuring Environment Variables

### Understanding the Configuration

Project Chimera uses environment variables to configure services. The MVP deployment uses a simplified Docker Compose setup that requires minimal configuration.

### Required Variables for MVP

The MVP deployment (`docker-compose.mvp.yml`) requires only one external API key:

- **GLM_API_KEY**: Z.ai GLM 4.7 API key (primary LLM service)

### Optional: Local LLM Configuration

If you have access to a local Nemotron LLM server, the system can fall back to it automatically. No configuration is needed if the local LLM is running on `http://host.docker.internal:8012`.

## Creating Your .env File

### Step 1: Copy the Example File

```bash
cp .env.example .env
```

### Step 2: Edit the .env File

Open `.env` in your preferred text editor:

```bash
nano .env
# or
code .env
# or
vim .env
```

### Step 3: Add Your API Key

Find the `GLM_API_KEY` line and add your actual API key:

```bash
# SceneSpeak Agent Configuration
SCENESPEAK_GLM_API_KEY=your_actual_api_key_here
```

Save and close the file.

### Step 4: Verify Your Configuration

```bash
cat .env | grep GLM_API_KEY
```

You should see your API key (not the placeholder).

## Starting All Services

### Step 1: Ensure Docker is Running

Verify Docker is running:

```bash
docker ps
```

If you see an error, start Docker Desktop or the Docker daemon.

### Step 2: Navigate to Project Directory

```bash
cd ~/projects/project-chimera
```

### Step 3: Start Services with Docker Compose

Use the MVP configuration to start all services:

```bash
docker compose -f docker-compose.mvp.yml up -d
```

**What this command does:**
- `-f docker-compose.mvp.yml` - Specifies the MVP configuration file
- `up` - Creates and starts containers
- `-d` - Runs containers in detached mode (background)

### Step 4: Watch the Startup Process

To see logs and monitor startup:

```bash
docker compose -f docker-compose.mvp.yml logs -f
```

Press `Ctrl+C` to stop following logs (containers keep running).

### Step 5: Wait for Services to Be Ready

Initial startup may take 2-5 minutes as Docker:
- Pulls base images
- Builds service images
- Downloads ML models for sentiment analysis
- Initializes Redis

You'll know services are ready when logs show:
```
openclaw-orchestrator  | Application startup complete
scenespeak-agent       | SceneSpeak agent ready
sentiment-agent        | Sentiment analysis model loaded
safety-filter          | Safety filter initialized
operator-console       | Operator console started
redis                  | Ready to accept connections
```

## Verifying Services Are Running

### Step 1: Check Container Status

```bash
docker compose -f docker-compose.mvp.yml ps
```

All services should show "Up" status:

| Service | Status | Ports |
|---------|--------|-------|
| chimera-openclaw-orchestrator | Up | 0.0.0.0:8000->8000/tcp |
| chimera-scenespeak-agent | Up | 0.0.0.0:8001->8001/tcp |
| chimera-sentiment-agent | Up | 0.0.0.0:8004->8004/tcp |
| chimera-safety-filter | Up | 0.0.0.0:8006->8006/tcp |
| chimera-operator-console | Up | 0.0.0.0:8007->8007/tcp |
| chimera-redis | Up | 0.0.0.0:6379->6379/tcp |
| chimera-hardware-bridge | Up | 0.0.0.0:8008->8008/tcp |

### Step 2: Test Service Health

Check the orchestrator health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "scenespeak": "healthy",
    "sentiment": "healthy",
    "safety_filter": "healthy"
  }
}
```

### Step 3: Verify Individual Services

```bash
# SceneSpeak Agent
curl http://localhost:8001/health

# Sentiment Agent
curl http://localhost:8004/health

# Safety Filter
curl http://localhost:8006/health

# Operator Console
curl http://localhost:8007/health
```

All should return `{"status": "healthy"}` or similar.

### Step 4: Check Resource Usage

```bash
docker stats
```

This shows CPU and memory usage for each container. Ensure no container is using excessive resources.

## Accessing the Operator Console

The Operator Console is your main interface for interacting with Project Chimera.

### Step 1: Open in Browser

Navigate to:
```
http://localhost:8007
```

### Step 2: Explore the Console

The console provides:
- **Dashboard**: Overview of all services and their status
- **Live Monitoring**: Real-time sentiment analysis results
- **Manual Input**: Test dialogue and sentiment processing
- **Service Control**: Start/stop individual services

### Step 3: Test a Simple Interaction

1. Click "Manual Input" in the console
2. Enter a test phrase like: "Hello, how are you today?"
3. Submit and observe the sentiment analysis
4. Check the logs to see the processing flow

### Step 4: View Live Logs

Watch real-time processing:

```bash
docker compose -f docker-compose.mvp.yml logs -f openclaw-orchestrator
```

## Stopping Services

### Graceful Shutdown

To stop all services gracefully:

```bash
docker compose -f docker-compose.mvp.yml down
```

This:
- Stops all containers
- Removes containers
- Preserves volumes (Redis data, model caches)

### Stop and Remove Everything

To stop services and remove all data:

```bash
docker compose -f docker-compose.mvp.yml down -v
```

**Warning**: This deletes all Redis data and downloaded models. Use only if you want a completely fresh start.

### Stop Individual Services

To stop a specific service:

```bash
docker compose -f docker-compose.mvp.yml stop sentiment-agent
```

To restart it:

```bash
docker compose -f docker-compose.mvp.yml start sentiment-agent
```

## Troubleshooting

### Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find what's using the port
sudo lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop the conflicting service or change the port in docker-compose.mvp.yml
```

### Out of Memory

**Error**: Container exits with OOM (Out of Memory)

**Solution**:
1. Increase Docker memory limit in Docker Desktop settings
2. Stop unused containers: `docker container prune`
3. Reduce model sizes in configuration

### Permission Denied

**Error**: `permission denied while trying to connect to the Docker daemon`

**Solution**:
```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Services Not Starting

**Symptoms**: Containers exit immediately

**Solution**:
```bash
# Check service logs
docker compose -f docker-compose.mvp.yml logs [service-name]

# Check configuration
docker compose -f docker-compose.mvp.yml config

# Rebuild containers
docker compose -f docker-compose.mvp.yml up -d --build
```

### Network Issues

**Error**: Services cannot communicate

**Solution**:
```bash
# Check Docker network
docker network ls
docker network inspect chimera-backend

# Recreate network
docker compose -f docker-compose.mvp.yml down
docker compose -f docker-compose.mvp.yml up -d
```

### API Key Issues

**Error**: GLM API authentication failed

**Solution**:
1. Verify your API key is correct in `.env`
2. Check API key hasn't expired
3. Ensure you have API credits available
4. The system will fall back to local LLM if configured

### Viewing Logs for Debugging

```bash
# All services
docker compose -f docker-compose.mvp.yml logs

# Specific service
docker compose -f docker-compose.mvp.yml logs scenespeak-agent

# Last 100 lines
docker compose -f docker-compose.mvp.yml logs --tail=100

# Follow logs in real-time
docker compose -f docker-compose.mvp.yml logs -f
```

## Next Steps

After successful setup:

1. **Read the API Documentation**: `docs/api/` directory
2. **Explore the Console**: Test different inputs and features
3. **Review Architecture**: `docs/architecture/` for system design
4. **Check Testing Guide**: `docs/testing/` for running tests
5. **Join Development**: See `CONTRIBUTING.md` for contribution guidelines

## Getting Help

If you encounter issues:

1. Check `docs/TROUBLESHOOTING.md` for detailed troubleshooting
2. Review `docs/FAQ.md` for common questions
3. Check GitHub Issues: https://github.com/your-org/project-chimera/issues
4. Contact the development team

## Summary

You've successfully:
- Cloned the Project Chimera repository
- Configured environment variables
- Started all services using Docker Compose
- Verified services are running correctly
- Accessed the Operator Console
- Learned how to stop and restart services

You're now ready to explore and develop with Project Chimera!

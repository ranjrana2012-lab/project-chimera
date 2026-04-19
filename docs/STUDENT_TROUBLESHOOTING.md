# Student Troubleshooting Guide - Project Chimera

**Version:** 1.0.0
**Last Updated:** April 15, 2026
**Target Audience:** Students, Learners, New Contributors

---

## Quick Reference

| Issue | Quick Fix | Section |
|-------|-----------|---------|
| Port already in use | `lsof -ti:8000 \| xargs kill -9` | [Port Conflicts](#port-already-in-use) |
| Docker won't start | `docker-compose down -v` then up | [Docker Issues](#docker-issues) |
| Out of memory | Reduce memory limits in .env | [Memory Issues](#out-of-memory-errors) |
| Git conflicts | `git merge --abort` then rebase | [Git Conflicts](#git-conflicts) |
| Service won't start | Check logs: `docker-compose logs service-name` | [Services Not Starting](#services-not-starting) |

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Port Already in Use](#port-already-in-use)
3. [Services Not Starting](#services-not-starting)
4. [Out of Memory Errors](#out-of-memory-errors)
5. [Permission Errors](#permission-errors)
6. [Git Conflicts](#git-conflicts)
7. [Docker Issues](#docker-issues)
8. [Network Problems](#network-problems)
9. [Environment Setup Issues](#environment-setup-issues)
10. [Common Error Messages](#common-error-messages)
11. [Getting Help](#getting-help)

---

## Getting Started

### Before You Begin

Make sure you've completed the prerequisites:

```bash
# Check Docker is installed
docker --version
docker-compose --version

# Check Git is installed
git --version

# Verify you're in the project directory
pwd  # Should show: /home/ranj/Project_Chimera
```

### Initial Setup

If you haven't set up the environment yet:

```bash
# Copy environment variables
cp .env.example .env

# Edit .env if needed (usually defaults work for development)
nano .env

# Start infrastructure services first
docker-compose up -d redis kafka zookeeper

# Wait 30 seconds for infrastructure to be ready
sleep 30

# Start all services
docker-compose up -d
```

---

## Port Already in Use

### Symptoms

- Error: "Bind for 0.0.0.0:8000 failed: port is already allocated"
- Service won't start because port is taken
- Multiple instances of same service running

### Diagnosis

```bash
# Check what's using the port
lsof -i :8000
# or
netstat -tulpn | grep 8000
# or
ss -tulpn | grep 8000
```

### Solutions

#### Option 1: Kill the Process Using the Port

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

#### Option 2: Stop Docker Containers

```bash
# Stop all Chimera containers
docker-compose down

# Stop specific container
docker stop chimera-orchestrator
```

#### Option 3: Change Port in .env

```bash
# Edit .env file
nano .env

# Change the port (example for orchestrator)
OPENCLAW_ORCHESTRATOR_PORT=8000  # Change to 8100

# Restart services
docker-compose up -d
```

### Common Port Conflicts

| Service | Default Port | Alternative |
|---------|-------------|-------------|
| Orchestrator | 8000 | 8100 |
| SceneSpeak Agent | 8001 | 8101 |
| Sentiment Agent | 8004 | 8104 |
| Safety Filter | 8006 | 8106 |
| Music Generation | 8011 | 8111 |
| Dashboard | 8013 | 8113 |

---

## Services Not Starting

### Symptoms

- Container exits immediately
- Service shows as "Restarting" repeatedly
- Health check fails

### Diagnosis

```bash
# Check container status
docker-compose ps

# Check service logs
docker-compose logs <service-name>

# Check last 50 lines of logs
docker-compose logs --tail=50 <service-name>

# Follow logs in real-time
docker-compose logs -f <service-name>
```

### Common Causes and Solutions

#### 1. Missing Environment Variables

**Error:** `KeyError: 'REDIS_URL'` or similar

**Solution:**
```bash
# Ensure .env file exists
ls -la .env

# If missing, copy from example
cp .env.example .env

# Restart services
docker-compose down
docker-compose up -d
```

#### 2. Dependencies Not Ready

**Error:** `Connection refused` to redis/kafka

**Solution:**
```bash
# Start infrastructure first
docker-compose up -d redis kafka zookeeper etcd minio

# Wait for them to be healthy
docker-compose ps

# Then start dependent services
docker-compose up -d openclaw-orchestrator scenespeak-agent
```

#### 3. Missing Configuration Files

**Error:** `FileNotFoundError: config.yml`

**Solution:**
```bash
# Check if config exists
ls -la config/

# Create from example if available
cp config/example.yml config/config.yml
```

#### 4. Build Failures

**Error:** `docker build failed`

**Solution:**
```bash
# Rebuild the service
docker-compose build --no-cache <service-name>

# Rebuild all services
docker-compose build --no-cache

# Check Dockerfile exists
ls -la services/<service-name>/Dockerfile
```

### Service-Specific Issues

#### SceneSpeak Agent Won't Start

```bash
# Check if Ollama is accessible
docker-compose exec scenespeak-agent curl http://ollama:11434/api/tags

# If using external LLM, check API key
docker-compose exec scenespeak-agent env | grep GLM_API_KEY

# Restart with increased memory
docker-compose restart scenespeak-agent
```

#### Music Generation Service Fails

```bash
# Check GPU availability (if using CUDA)
docker-compose exec music-generation nvidia-smi

# If no GPU, set CPU mode in .env
MUSIC_DEVICE=cpu

# Reduce memory usage
MUSIC_MEMORY_LIMIT=1G
MUSIC_MAX_VRAM_MB=4096
```

---

## Out of Memory Errors

### Symptoms

- Container killed with OOM (Out of Memory)
- System becomes slow
- Services crash randomly

### Diagnosis

```bash
# Check container resource usage
docker stats

# Check system memory
free -h

# Check Docker memory limits
docker inspect <container-name> | grep -A 10 Memory
```

### Solutions

#### 1. Reduce Service Memory Limits

Edit `.env` file:

```bash
# Reduce memory limits for services
SCENESPEAK_MEMORY_LIMIT=512M  # Was 1G
MUSIC_MEMORY_LIMIT=1G         # Was 2G
SAFETY_MEMORY_LIMIT=512M      # Was 1G
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

#### 2. Disable Memory-Intensive Services

```bash
# Edit docker-compose.yml to comment out heavy services
# Or use selective startup:

# Start only essential services
docker-compose up -d \
  redis \
  kafka \
  zookeeper \
  openclaw-orchestrator \
  scenespeak-agent \
  sentiment-agent

# Skip music-generation if not needed
```

#### 3. Free Up System Memory

```bash
# Remove unused Docker resources
docker system prune -a

# Remove old volumes (WARNING: deletes data)
docker volume prune

# Clear build cache
docker builder prune
```

#### 4. Use CPU Instead of GPU

Edit `.env`:

```bash
# Use CPU for ML services
MUSIC_DEVICE=cpu
CAPTIONING_DEVICE=cpu
SCENESPEAK_LOCAL_LLM_ENABLED=false
```

### Resource-Light Development Setup

For limited resources (8GB RAM or less):

```bash
# In .env, set these values:
REDIS_MEMORY_LIMIT=128M
KAFKA_MEMORY_LIMIT=512M
OPENCLAW_MEMORY_LIMIT=256M
SCENESPEAK_MEMORY_LIMIT=512M
SENTIMENT_MEMORY_LIMIT=256M
SAFETY_MEMORY_LIMIT=256M
MUSIC_MEMORY_LIMIT=1G

# Disable GPU
GPU_COUNT=0
```

---

## Permission Errors

### Symptoms

- `Permission denied` when accessing files
- `EACCES: permission denied`
- Cannot write to volumes

### Common Permission Issues

#### 1. Docker Socket Permission

**Error:** `Got permission denied while trying to connect to the Docker daemon`

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker

# Verify
groups
```

#### 2. Volume Permission Errors

**Error:** `Cannot write to /app/cache`

**Solution:**
```bash
# Fix volume permissions
docker-compose down

# Remove volumes
docker-compose down -v

# Recreate with correct permissions
docker-compose up -d
```

#### 3. File Permission Errors

**Error:** `Permission denied: './config/file.yml'`

**Solution:**
```bash
# Fix file permissions
chmod 644 config/file.yml

# Fix directory permissions
chmod 755 config/

# Make script executable
chmod +x scripts/*.sh
```

#### 4. USB Device Permissions (DMX/Audio)

**Error:** `Cannot open /dev/ttyUSB0`

**Solution:**
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Fix device permissions
sudo chmod 666 /dev/ttyUSB0

# Add to audio group for sound devices
sudo usermod -aG audio $USER
```

### Preventing Permission Issues

Create a `.gitignore` entry for sensitive permissions:

```bash
# Add to .gitignore
.env.local
*.log
.DS_Store
```

Always use Docker volumes instead of bind mounts for development:

```yaml
# In docker-compose.yml
volumes:
  - chimera-cache:/app/cache  # Good
  # - ./local/cache:/app/cache  # Can cause permission issues
```

---

## Git Conflicts

### Symptoms

- `CONFLICT (content): Merge conflict in file.py`
- Cannot pull or push
- `Automatic merge failed`

### Diagnosis

```bash
# Check git status
git status

# See conflicted files
git diff --name-only --diff-filter=U
```

### Solutions

#### Option 1: Resolve Conflicts Manually

```bash
# See the conflicts
git status

# Open conflicted file
nano <conflicted-file>

# Look for conflict markers:
<<<<<<< HEAD
Your changes
=======
Their changes
>>>>>>> main

# Edit to keep what you want, then save

# Mark as resolved
git add <conflicted-file>

# Continue merge
git commit
```

#### Option 2: Accept Their Changes

```bash
# Accept all incoming changes
git checkout --theirs <conflicted-file>
git add <conflicted-file>
git commit
```

#### Option 3: Accept Your Changes

```bash
# Keep all your changes
git checkout --ours <conflicted-file>
git add <conflicted-file>
git commit
```

#### Option 4: Abort and Try Again

```bash
# Cancel the merge
git merge --abort

# Or cancel rebase
git rebase --abort

# Pull with rebase instead
git pull --rebase
```

### Preventing Git Conflicts

```bash
# Always pull before pushing
git pull --rebase origin main

# Commit frequently
git add .
git commit -m "Work in progress"

# Use branches for features
git checkout -b feature/my-feature
```

### Common Git Issues

#### "Detached HEAD" State

```bash
# You're in detached HEAD state
git checkout main

# Or create a branch from current state
git checkout -b new-branch
```

#### "Push Rejected"

```bash
# Pull first, then push
git pull --rebase
git push

# Or force push (USE WITH CAUTION)
git push --force-with-lease
```

---

## Docker Issues

### Common Docker Problems

#### 1. Docker Daemon Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:**
```bash
# Start Docker
sudo systemctl start docker

# Or on macOS/Windows
# Start Docker Desktop

# Enable on boot
sudo systemctl enable docker

# Verify
docker ps
```

#### 2. Container Won't Stop

**Error:** Container keeps restarting

**Solution:**
```bash
# Force stop
docker kill <container-name>

# Remove container
docker rm -f <container-name>

# Remove all stopped containers
docker container prune -f
```

#### 3. Old Images Taking Space

**Solution:**
```bash
# Remove unused images
docker image prune -a

# Remove specific image
docker rmi <image-id>

# Remove all
docker system prune -a --volumes
```

#### 4. Network Issues

**Error:** Services cannot communicate

**Solution:**
```bash
# List networks
docker network ls

# Inspect network
docker network inspect chimera-backend

# Remove and recreate network
docker network rm chimera-backend
docker-compose up -d
```

### Docker Compose Issues

#### "Service not found"

```bash
# Check if service name is correct
docker-compose ps

# Use full service name from docker-compose.yml
docker-compose logs openclaw-orchestrator
```

#### "Volume not found"

```bash
# Create volume
docker volume create chimera-redis-data

# Or remove reference from docker-compose.yml
# Or use: docker-compose up -d --remove-orphans
```

#### Build Context Issues

```bash
# Check Dockerfile context
# Ensure build: context: . is correct

# Rebuild with no cache
docker-compose build --no-cache --pull
```

---

## Network Problems

### Symptoms

- Services cannot reach each other
- Connection timeouts
- DNS resolution failures

### Diagnosis

```bash
# Test DNS from within container
docker-compose exec openclaw-orchestrator ping redis

# Test HTTP connection
docker-compose exec openclaw-orchestrator curl http://redis:6379

# Check network
docker network inspect chimera-backend
```

### Solutions

#### 1. Services on Different Networks

**Problem:** Service A cannot reach Service B

**Solution:**
```yaml
# In docker-compose.yml, ensure services share network
services:
  service-a:
    networks:
      - chimera-backend

  service-b:
    networks:
      - chimera-backend
```

#### 2. Firewall Blocking Ports

```bash
# Check firewall status
sudo ufw status

# Allow Docker ports
sudo ufw allow 2375/tcp
sudo ufw allow 7946/tcp
sudo ufw allow 7946/udp
sudo ufw allow 4789/udp

# Or disable firewall for development (not recommended for production)
sudo ufw disable
```

#### 3. DNS Resolution Issues

```bash
# Restart Docker DNS
docker-compose down
sudo systemctl restart docker
docker-compose up -d

# Use explicit IPs in .env (not recommended)
REDIS_URL=redis://172.18.0.2:6379
```

#### 4. Proxy Issues

```bash
# Configure Docker proxy
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo nano /etc/systemd/system/docker.service.d/http-proxy.conf

# Add:
[Service]
Environment="HTTP_PROXY=http://proxy.example.com:8080"
Environment="HTTPS_PROXY=http://proxy.example.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## Environment Setup Issues

### Python/Virtual Environment Issues

#### Module Not Found

```bash
# Rebuild container with fresh dependencies
docker-compose build --no-cache <service-name>

# Or install manually
docker-compose exec <service-name> pip install <module>
```

#### Wrong Python Version

```bash
# Check Python version in container
docker-compose exec <service-name> python --version

# Update Dockerfile if needed
# FROM python:3.11-slim
```

### Node.js Issues (if applicable)

#### npm Install Fails

```bash
# Clear npm cache
docker-compose exec <service> npm cache clean --force

# Delete node_modules and reinstall
docker-compose exec <service> rm -rf node_modules
docker-compose exec <service> npm install
```

### Environment Variable Issues

#### Variables Not Loading

```bash
# Verify .env file exists
ls -la .env

# Check for syntax errors (no spaces around =)
# WRONG: KEY = value
# RIGHT: KEY=value

# Test variable loading
docker-compose config
```

---

## Common Error Messages

### "Bind for 0.0.0.0:8000 failed: port is already allocated"

**Meaning:** Port 8000 is already in use

**Fix:** See [Port Already in Use](#port-already-in-use)

### "Cannot connect to the Docker daemon"

**Meaning:** Docker is not running

**Fix:** Start Docker daemon
```bash
sudo systemctl start docker
```

### "ERROR: for service  Cannot start service service: OCI runtime create failed"

**Meaning:** Container creation failed

**Fix:** Check logs and rebuild
```bash
docker-compose logs <service>
docker-compose build --no-cache <service>
```

### "Connection refused"

**Meaning:** Service is not accessible

**Fix:** Check if service is running
```bash
docker-compose ps
docker-compose logs <service>
```

### "Health check failed"

**Meaning:** Service health endpoint returned error

**Fix:** Check service logs and dependencies
```bash
docker-compose logs --tail=50 <service>
curl http://localhost:<port>/health
```

### "OutOfMemoryError: CUDA out of memory"

**Meaning:** GPU memory exhausted

**Fix:** Reduce batch size or use CPU
```bash
# In .env
MUSIC_DEVICE=cpu
MUSIC_MAX_VRAM_MB=4096
```

### "ModuleNotFoundError: No module named 'xxx'"

**Meaning:** Python dependency missing

**Fix:** Rebuild container
```bash
docker-compose build --no-cache <service>
```

---

## Getting Help

### Diagnostic Steps

Before asking for help, run these diagnostics:

```bash
# 1. Check all services
docker-compose ps

# 2. Check logs for errors
docker-compose logs --tail=50

# 3. Check system resources
free -h
df -h
docker stats

# 4. Check network connectivity
docker-compose exec openclaw-orchestrator ping redis

# 5. Verify environment
docker-compose config
```

### What to Include When Asking for Help

1. **Error message**: Full error output
2. **Service affected**: Which service is failing
3. **Steps to reproduce**: What you did before the error
4. **Environment**: OS, Docker version, RAM/CPU
5. **Logs**: Relevant log output
6. **What you tried**: Solutions you already attempted

### Useful Commands for Debugging

```bash
# Get container IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>

# Execute shell in container
docker-compose exec <service> /bin/sh

# View container environment
docker-compose exec <service> env

# Check port bindings
docker port <container>

# View container details
docker inspect <container>
```

### Resources

- **Main Documentation**: `/home/ranj/Project_Chimera/docs/`
- **API Examples**: `/home/ranj/Project_Chimera/docs/PHASE2_API_EXAMPLES.md`
- **Developer Guide**: `/home/ranj/Project_Chimera/docs/DEVELOPER_ONBOARDING_GUIDE.md`
- **Deployment Guide**: `/home/ranj/Project_Chimera/docs/DEPLOYMENT.md`

### Quick Health Check Script

Save this as `quick-check.sh`:

```bash
#!/bin/bash
echo "=== Project Chimera Quick Health Check ==="
echo ""
echo "Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h | grep -E '^/dev/'
echo ""
echo "Service Health:"
for service in openclaw-orchestrator scenespeak-agent sentiment-agent safety-filter; do
  echo -n "$service: "
  curl -s http://localhost:8000/health && echo "OK" || echo "FAIL"
done
echo ""
echo "Recent Errors:"
docker-compose logs --tail=5 | grep -i error || echo "No recent errors"
```

Run it:
```bash
chmod +x quick-check.sh
./quick-check.sh
```

---

## Emergency Recovery

### Full Reset

If everything is broken:

```bash
# Stop everything
docker-compose down -v

# Remove all Chimera containers
docker rm -f $(docker ps -aq --filter name=chimera)

# Remove all Chimera volumes
docker volume rm $(docker volume ls -q --filter name=chimera)

# Remove all Chimera networks
docker network rm $(docker network ls -q --filter name=chimera)

# Start fresh
docker-compose up -d
```

**WARNING:** This deletes all data! Use only as last resort.

### Selective Reset

```bash
# Reset specific service
docker-compose stop <service>
docker-compose rm -f <service>
docker-compose up -d <service>
```

---

## Prevention Tips

1. **Always pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Keep Docker updated**
   ```bash
   # Check version
   docker --version

   # Update (method varies by OS)
   ```

3. **Monitor resources**
   ```bash
   # Run in separate terminal
   watch -n 5 'docker stats --no-stream'
   ```

4. **Clean up regularly**
   ```bash
   # Weekly cleanup
   docker system prune -a
   ```

5. **Backup important data**
   ```bash
   # Backup volumes
   docker run --rm -v chimera-redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data
   ```

---

**Document Version:** 1.0.0
**Last Updated:** April 15, 2026

For advanced troubleshooting, see:
- [TROUBLESHOOTING_GUIDE.md](/home/ranj/Project_Chimera/docs/TROUBLESHOOTING_GUIDE.md)
- [DEPLOYMENT.md](/home/ranj/Project_Chimera/docs/DEPLOYMENT.md)
- [DEVELOPER_ONBOARDING_GUIDE.md](/home/ranj/Project_Chimera/docs/DEVELOPER_ONBOARDING_GUIDE.md)

# Docker Troubleshooting Guide

**Version:** 1.0.0
**Last Updated:** March 2026
**Purpose:** Common Docker and Docker Compose issues and solutions

---

## Table of Contents

1. [Container Issues](#container-issues)
2. [Build Failures](#build-failures)
3. [Volume Issues](#volume-issues)
4. [Network Issues](#network-issues)
5. [Resource Issues](#resource-issues)
6. [Performance Issues](#performance-issues)

---

## Container Issues

### Container Exits Immediately

**Symptom:** Container starts then immediately stops

```bash
# Check logs
docker-compose logs [service]

# Check exit code
docker-compose ps

# Inspect container
docker inspect [container-id]
```

**Common Causes:**

#### 1. Command Failed

```bash
# Check the command in docker-compose.yml
# Test command manually
docker-compose run --rm [service] /bin/sh -c "your-command"

# Fix: Use correct command or fix entrypoint script
```

#### 2. Port Already in Use

```bash
# Find what's using the port
lsof -i :8000
netstat -tulpn | grep 8000

# Kill the process
kill -9 [PID]

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

#### 3. Missing Environment Variables

```bash
# Check .env file
cat .env

# Verify required variables
docker-compose config

# Fix: Add missing variables to .env
echo "REQUIRED_VAR=value" >> .env
```

#### 4. Failed Health Check

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' [container-id]

# Test health check manually
docker-compose exec [service] curl -f http://localhost:8000/health || exit 1

# Fix: Adjust health check or increase timeout
healthcheck:
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Container Keeps Restarting

**Symptom:** Container in restart loop

```bash
# Check restart count
docker-compose ps

# View logs across restarts
docker-compose logs --tail=100 [service]

# Check previous container logs
docker logs [container-id] 2>&1 | tail -50
```

**Solutions:**

```bash
# Stop the service
docker-compose stop [service]

# Check and fix the issue
# Then start again
docker-compose start [service]

# Or disable auto-restart temporarily
# In docker-compose.yml:
restart: "no"
```

---

## Build Failures

### Build Cache Issues

**Symptom:** Build fails with cached layers

```bash
# Clear build cache
docker builder prune

# Build without cache
docker-compose build --no-cache [service]

# Force pull fresh base images
docker-compose build --pull --no-cache [service]
```

### Out of Disk Space

**Symptom:** Build fails due to no space

```bash
# Check disk usage
df -h

# Clean Docker system
docker system prune -a --volumes

# Check space savings
docker system df

# Remove specific images
docker rmi [image-id]
```

### Network Issues During Build

**Symptom:** Can't download packages

```bash
# Use build arguments for proxy
docker-compose build --build-arg http_proxy=http://proxy:8080 \
                     --build-arg https_proxy=http://proxy:8080

# Or configure in Dockerfile
ARG http_proxy
ARG https_proxy
ENV http_proxy=$http_proxy
ENV https_proxy=$https_proxy
```

### ARM64 Architecture Issues

**Symptom:** Build fails on Apple Silicon

```bash
# Check architecture
uname -m

# Build for specific platform
docker-compose build --platform linux/amd64 [service]

# Add to docker-compose.yml
services:
  [service]:
    platform: linux/amd64
```

### Dependency Installation Fails

**Symptom:** pip/apt install fails

```bash
# For Python packages:
# Update pip first
RUN pip install --upgrade pip

# Use specific version
RUN pip install package==1.2.3

# For system packages:
# Update package list
RUN apt-get update

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

---

## Volume Issues

### Volume Permission Denied

**Symptom:** Can't write to mounted volume

```bash
# Check volume permissions
ls -la /path/to/volume

# Fix permissions on host
sudo chmod -R 777 /path/to/volume

# Or run container as specific user
user: "1000:1000"

# Or use named volumes (Docker manages permissions)
volumes:
  data-volume:
```

### Volume Data Lost

**Symptom:** Data disappears after container restart

```bash
# Use named volumes instead of bind mounts
volumes:
  data:
    driver: local

# Or ensure bind mount path is correct
volumes:
  - ./data:/app/data  # Ensure ./data exists
```

### Volume Not Mounting

**Symptom:** Container can't see mounted files

```bash
# Check volume mounts
docker inspect [container-id] | grep -A 10 Mounts

# Verify path exists on host
ls -la /path/to/mount

# Use absolute paths
volumes:
  - /absolute/path:/container/path
```

### Reset Volumes

**Symptom:** Need to start fresh with volumes

```bash
# Stop and remove volumes
docker-compose down -v

# Remove specific volume
docker volume rm project-chimera_volume-name

# Start fresh
docker-compose up -d
```

---

## Network Issues

### Containers Can't Communicate

**Symptom:** Services can't reach each other

```bash
# Check container network
docker network inspect project-chimera_default

# Test connectivity
docker-compose exec service1 ping service2

# Use service names, not localhost
# Correct: http://service2:8000
# Wrong: http://localhost:8000
```

### DNS Resolution Fails

**Symptom:** Can't resolve service names

```bash
# Check DNS in container
docker-compose exec service cat /etc/resolv.conf

# Test DNS
docker-compose exec service nslookup service2

# Use custom DNS
# In docker-compose.yml:
dns:
  - 8.8.8.8
  - 8.8.4.4
```

### Port Mapping Issues

**Symptom:** Can't access service from host

```bash
# Check port mapping
docker port [container-id]

# Ensure correct format
ports:
  - "HOST_PORT:CONTAINER_PORT"

# Bind to all interfaces
ports:
  - "0.0.0.0:8000:8000"

# Check firewall
sudo ufw allow 8000
```

### Network Performance Issues

**Symptom:** Slow communication between containers

```bash
# Use host network (Linux only)
network_mode: host

# Or optimize MTU
# Create network with custom MTU
docker network create --driver bridge --opt com.docker.network.driver.mtu=1450 custom-network
```

---

## Resource Issues

### Out of Memory

**Symptom:** OOM killer kills container

```bash
# Check container stats
docker stats

# Set memory limits
# In docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G

# Check system memory
free -h

# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### CPU Throttling

**Symptom:** Container slow due to CPU limits

```bash
# Check CPU usage
docker stats --no-stream

# Set CPU limits
deploy:
  resources:
    limits:
      cpus: '2.0'
    reservations:
      cpus: '1.0'

# Or use all CPUs
deploy:
  resources:
    limits:
      cpus: '4.0'  # Adjust based on your system
```

### Disk IO Issues

**Symptom:** Slow disk performance

```bash
# Check disk usage
df -h

# Monitor disk IO
iotop

# Use tmpfs for temporary data
tmpfs:
  - /tmp

# Or use volume drivers with better performance
volumes:
  data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /fast/ssd/path
```

---

## Performance Issues

### Slow Container Startup

**Symptom:** Containers take long to start

```bash
# Check startup time
docker-compose up -d && time docker-compose ps

# Optimize Dockerfile
# Use multi-stage builds
FROM builder AS build
...

FROM runtime
COPY --from=build /app /app

# Minimize layers
RUN apt-get update && apt-get install -y package1 package2 && rm -rf /var/lib/apt/lists/*

# Use .dockerignore
echo "node_modules
.git
*.log" > .dockerignore
```

### High Memory Usage

**Symptom:** Container using too much memory

```bash
# Profile memory usage
docker stats [container-id]

# Reduce layers in image
# Use alpine-based images
FROM python:3.11-slim

# Clean up package manager cache
RUN apt-get update && apt-get install -y package && rm -rf /var/lib/apt/lists/*

# Limit Python memory
export PYTHONMALLOC=malloc
```

### Large Image Size

**Symptom:** Docker images too large

```bash
# Check image size
docker images

# Use multi-stage builds
# Copy only what's needed
COPY --from=builder /app/dist /app/dist

# Don't install dev dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use .dockerignore to exclude files
echo "*.pyc
__pycache__
.git
tests" > .dockerignore
```

---

## Useful Commands

### Container Management

```bash
# List all containers (including stopped)
docker ps -a

# Remove all stopped containers
docker container prune

# Stop all running containers
docker stop $(docker ps -q)

# Remove all containers
docker rm -f $(docker ps -aq)
```

### Image Management

```bash
# List all images
docker images

# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a

# Export/import image
docker save -o image.tar image:tag
docker load -i image.tar
```

### System Cleanup

```bash
# Remove all unused data
docker system prune -a --volumes

# Check Docker disk usage
docker system df

# View detailed usage
docker system df -v
```

### Debugging

```bash
# Run container interactively
docker-compose run --rm [service] /bin/sh

# Attach to running container
docker attach [container-id]

# Execute command in container
docker-compose exec [service] /bin/sh

# Copy files from container
docker cp [container-id]:/path/to/file ./local-file

# View container logs
docker logs -f [container-id]
```

---

## Getting Help

If you encounter Docker issues not covered here:

1. **Check Docker logs:** `docker logs [container-id]`
2. **Verify Docker version:** `docker --version && docker-compose --version`
3. **Check system resources:** `docker system df` and `docker stats`
4. **Review Docker documentation:** [Docker Documentation](https://docs.docker.com/)
5. **Create issue:** Include Docker version, OS, and error logs

---

**Related Documentation:**
- [Main Troubleshooting Guide](./troubleshooting.md)
- [Deployment Guide](../DEPLOYMENT.md)
- [Development Guide](../DEVELOPMENT.md)

# Project Chimera Troubleshooting Runbook

**Version:** 1.0.0
**Last Updated:** March 2026
**Purpose:** Common issues and solutions for Project Chimera services

---

## Table of Contents

1. [Service Won't Start](#service-wont-start)
2. [GPU Not Available](#gpu-not-available)
3. [Model Download Failed](#model-download-failed)
4. [Docker Build Fails](#docker-build-fails)
5. [Service Health Check Failures](#service-health-check-failures)
6. [Memory Issues](#memory-issues)
7. [Network Connectivity Problems](#network-connectivity-problems)
8. [Performance Issues](#performance-issues)

---

## Service Won't Start

**Symptom:** Service exits immediately after starting

### Diagnosis Steps

```bash
# Check if service is running
docker-compose ps

# Check service logs
docker-compose logs [service-name]

# Check for port conflicts
lsof -i :8000-8011
```

### Common Solutions

#### 1. Port Conflicts

**Problem:** Another process is using the required port

**Solution:**
```bash
# Find process using the port
lsof -i :8000

# Kill the process (replace PID with actual process ID)
kill -9 PID

# Or change the port in docker-compose.yml
```

#### 2. Missing Environment Configuration

**Problem:** `.env` file doesn't exist or is incomplete

**Solution:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit with your configuration
nano .env

# Verify file exists
ls -la .env
```

#### 3. Failed Health Check

**Problem:** Service starts but health check fails

**Solution:**
```bash
# Check service health directly
curl http://localhost:8000/health

# Review health check configuration
grep -A 10 "healthcheck" docker-compose.yml

# Increase health check timeout if needed
# Edit docker-compose.yml healthcheck section
```

#### 4. Missing Dependencies

**Problem:** Required services not running

**Solution:**
```bash
# Start all dependencies
docker-compose up -d

# Check dependency status
docker-compose ps

# Start in correct order (orchestrator last)
docker-compose up -d kafka redis milvus
docker-compose up -d orchestrator
```

---

## GPU Not Available

**Symptom:** CUDA errors, slow inference, or service falls back to CPU

### Diagnosis Steps

```bash
# Check GPU availability
nvidia-smi

# Check CUDA version
nvcc --version

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Common Solutions

#### 1. NVIDIA Driver Not Installed

**Problem:** No NVIDIA drivers on host system

**Solution:**
```bash
# Install NVIDIA drivers (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y nvidia-driver-535

# Reboot system
sudo reboot
```

#### 2. CUDA Runtime Mismatch

**Problem:** CUDA version in container doesn't match host

**Solution:**
```bash
# Check host CUDA version
nvidia-smi

# Update Dockerfile to match CUDA version
# Edit FROM line in Dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
```

#### 3. Docker GPU Passthrough Not Configured

**Problem:** Docker not configured for GPU access

**Solution:**
```bash
# Install nvidia-container-toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### 4. Fallback to CPU

**Problem:** No GPU available, need to use CPU

**Solution:**
```bash
# Set environment variable
echo "DEVICE=cpu" >> .env

# Or set per service
docker-compose up -d --env-file .env
```

---

## Model Download Failed

**Symptom:** Service fails on first start with model-related errors

### Diagnosis Steps

```bash
# Check service logs for model errors
docker-compose logs scenespeak-agent | grep -i model

# Check model cache directory
ls -la ~/.cache/huggingface/
```

### Common Solutions

#### 1. Internet Connectivity Issues

**Problem:** Container can't download models

**Solution:**
```bash
# Check internet from container
docker-compose run --rm scenespeak-agent ping -c 3 huggingface.co

# If blocked, configure proxy in Dockerfile
ENV http_proxy=http://proxy.example.com:8080
ENV https_proxy=http://proxy.example.com:8080
```

#### 2. Insufficient Disk Space

**Problem:** No space for model download

**Solution:**
```bash
# Check disk space
df -h

# Clean Docker cache
docker system prune -a

# Or specify alternative cache location
echo "TRANSFORMERS_CACHE=/path/to/cache" >> .env
```

#### 3. Cache Permissions

**Problem:** Container can't write to cache directory

**Solution:**
```bash
# Fix cache directory permissions
chmod -R 777 ~/.cache/huggingface/

# Or use volume mount in docker-compose.yml
volumes:
  - ~/.cache/huggingface:/root/.cache/huggingface
```

#### 4. Manual Model Download

**Problem:** Automatic download fails

**Solution:**
```bash
# Use manual download script
python scripts/download-models.sh

# Or download with Python
python -c "from transformers import AutoModel; AutoModel.from_pretrained('gpt-2')"

# Verify download
ls -la ~/.cache/huggingface/hub/
```

---

## Docker Build Fails

**Symptom:** `docker-compose build` errors

### Diagnosis Steps

```bash
# Check build logs
docker-compose build --no-cache [service-name]

# Check disk space
df -h

# Check Docker version
docker --version
docker-compose --version
```

### Common Solutions

#### 1. Out of Disk Space

**Problem:** No space for build artifacts

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Clean build cache only
docker builder prune

# Check space after cleanup
df -h
```

#### 2. Architecture Mismatch

**Problem:** Building on ARM64 (Apple Silicon) without proper base image

**Solution:**
```bash
# Check architecture
uname -m

# Use platform-specific build
docker-compose build --platform linux/amd64 [service-name]

# Or add to docker-compose.yml
platform: linux/amd64
```

#### 3. Network Issues During Build

**Problem:** Can't download packages during build

**Solution:**
```bash
# Use build arguments for proxy
docker-compose build --build-arg http_proxy=http://proxy:8080

# Or pre-download requirements
pip download -r requirements.txt -d packages/
```

#### 4. Dependency Conflicts

**Problem:** Python package conflicts

**Solution:**
```bash
# Rebuild from scratch
docker-compose build --no-cache --pull [service-name]

# Check requirements.txt for conflicts
pip-check -r requirements.txt

# Update problematic packages
pip install --upgrade package-name
```

---

## Service Health Check Failures

**Symptom:** Service runs but health check returns unhealthy

### Diagnosis Steps

```bash
# Check health status
docker-compose ps

# Manual health check
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8004/health

# Check service logs
docker-compose logs -f [service-name]
```

### Common Solutions

#### 1. Slow Startup

**Problem:** Service needs more time to initialize

**Solution:**
```bash
# Edit docker-compose.yml healthcheck
healthcheck:
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

#### 2. Dependency Not Ready

**Problem:** Service starts before dependencies are ready

**Solution:**
```bash
# Add depends_on with condition
depends_on:
  kafka:
    condition: service_healthy
  redis:
    condition: service_started
```

#### 3. Incorrect Health Check Endpoint

**Problem:** Health check URL is wrong

**Solution:**
```bash
# Verify correct endpoint
curl http://localhost:8000/docs

# Update healthcheck in docker-compose.yml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

---

## Memory Issues

**Symptom:** OOM errors, slow performance, services crashing

### Diagnosis Steps

```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Check OOM events
dmesg | grep -i oom
```

### Common Solutions

#### 1. Increase Memory Limits

**Problem:** Container hitting memory limit

**Solution:**
```bash
# Edit docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
    reservations:
      memory: 2G
```

#### 2. Reduce Model Memory Usage

**Problem:** Large models consuming too much memory

**Solution:**
```bash
# Use quantization
echo "QUANTIZE=true" >> .env

# Or use smaller model
echo "MODEL_NAME=distilgpt2" >> .env

# Reduce batch size
echo "BATCH_SIZE=8" >> .env
```

#### 3. Enable Memory Swapping

**Problem:** System running out of RAM

**Solution:**
```bash
# Check swap space
swapon --show

# Add swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Network Connectivity Problems

**Symptom:** Services can't communicate with each other

### Diagnosis Steps

```bash
# Check container network
docker network ls
docker network inspect project-chimera_default

# Test connectivity between containers
docker-compose exec orchestrator ping scenespeak-agent
docker-compose exec orchestrator curl http://scenespeak-agent:8001/health
```

### Common Solutions

#### 1. DNS Resolution Issues

**Problem:** Containers can't resolve each other

**Solution:**
```bash
# Check Docker DNS
docker-compose exec orchestrator cat /etc/resolv.conf

# Use container names (not localhost)
# In code: http://scenespeak-agent:8001
# Not: http://localhost:8001
```

#### 2. Firewall Blocking

**Problem:** Firewall blocking container communication

**Solution:**
```bash
# Check firewall rules
sudo iptables -L -n

# Allow Docker traffic
sudo iptables -A INPUT -i docker0 -j ACCEPT
sudo iptables -A OUTPUT -o docker0 -j ACCEPT
```

#### 3. Bridge Network Issues

**Problem:** Default bridge network not working

**Solution:**
```bash
# Create custom network
docker network create chimera-network

# Update docker-compose.yml
networks:
  default:
    external: true
    name: chimera-network
```

---

## Performance Issues

**Symptom:** Slow response times, high latency

### Diagnosis Steps

```bash
# Check CPU usage
docker stats --no-stream

# Check service response time
time curl http://localhost:8000/health

# Check logs for slow operations
docker-compose logs | grep -i "slow\|timeout"
```

### Common Solutions

#### 1. CPU Bottleneck

**Problem:** CPU limited

**Solution:**
```bash
# Increase CPU limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
```

#### 2. Inefficient Queries

**Problem:** Database or cache queries slow

**Solution:**
```bash
# Check Redis performance
docker-compose exec redis redis-cli info stats

# Add indexes to database
# Enable query logging
```

#### 3. Network Latency

**Problem:** High latency between services

**Solution:**
```bash
# Use service mesh for optimization
# Enable connection pooling
# Add caching layer
```

---

## Getting Help

If you can't resolve the issue:

1. **Check logs:** `docker-compose logs -f [service]`
2. **Review documentation:** [Project Chimera Docs](../README.md)
3. **Check GitHub Issues:** [Project Chimera Issues](https://github.com/your-org/project-chimera/issues)
4. **Contact support:** Create a GitHub issue with:
   - Service name and version
   - Full error logs
   - System information (OS, Docker version)
   - Steps to reproduce

---

**Related Documentation:**
- [Docker Troubleshooting](./docker-troubleshooting.md)
- [Deployment Guide](../DEPLOYMENT.md)
- [Service Documentation](../services/)

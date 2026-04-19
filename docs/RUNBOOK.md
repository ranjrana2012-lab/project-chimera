# Project Chimera - Operations Runbook

## Purpose

This runbook provides step-by-step procedures for common operational tasks, troubleshooting issues, and handling incidents for Project Chimera.

## Quick Reference

| Task | Command |
|------|---------|
| Check all services | `./scripts/verify-stack-health.sh` |
| Restart services | `docker compose -f docker-compose.mvp.yml restart` |
| View logs | `docker compose -f docker-compose.mvp.yml logs -f [service]` |
| Run tests | `pytest tests/integration/mvp/ -v` |
| Stop all | `docker compose -f docker-compose.mvp.yml down` |

## Service Health Checks

### All Services

```bash
# Comprehensive health check
./scripts/verify-stack-health.sh

# Expected output:
# ✓ openclaw-orchestrator (port 8000)... ✓ HEALTHY
# ✓ scenespeak-agent (port 8001)... ✓ HEALTHY
# ✓ translation-agent (port 8002)... ✓ HEALTHY
# ✓ sentiment-agent (port 8004)... ✓ HEALTHY
# ✓ safety-filter (port 8006)... ✓ HEALTHY
# ✓ operator-console (port 8007)... ✓ HEALTHY
# ✓ hardware-bridge (port 8008)... ✓ HEALTHY
# ✓ redis (port 6379)... ✓ HEALTHY
```

### Individual Services

```bash
# Orchestrator
curl http://localhost:8000/health

# SceneSpeak
curl http://localhost:8001/health

# Sentiment
curl http://localhost:8004/health

# Safety Filter
curl http://localhost:8006/health/live

# Console
curl http://localhost:8007/health
```

### Docker Status

```bash
# Container status
docker compose -f docker-compose.mvp.yml ps

# Resource usage
docker stats

# Network connections
docker network inspect chimera-backend
```

## Common Issues & Solutions

### Issue 1: Services Not Starting

**Symptoms:**
- Docker compose up fails
- Services exit immediately
- Port conflicts

**Diagnosis:**
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8001
lsof -i :8004
lsof -i :8006
lsof -i :8007

# Check Docker daemon
docker info

# Check compose file syntax
docker compose -f docker-compose.mvp.yml config
```

**Solutions:**
```bash
# Kill conflicting processes
kill -9 <PID>

# Restart Docker daemon
sudo systemctl restart docker

# Clean rebuild
docker compose -f docker-compose.mvp.yml down
docker compose -f docker-compose.mvp.yml build --no-cache
docker compose -f docker-compose.mvp.yml up -d
```

### Issue 2: Service Cannot Reach Another Service

**Symptoms:**
- Connection refused errors
- Timeout errors
- "Name or service not known"

**Diagnosis:**
```bash
# Check if target service is running
docker compose -f docker-compose.mvp.yml ps scenespeak-agent

# Check network connectivity
docker exec chimera-openclaw-orchestrator ping scenespeak-agent

# Check DNS resolution
docker exec chimera-openclaw-orchestrator nslookup scenespeak-agent

# Check if on same network
docker network inspect chimera-backend
```

**Solutions:**
```bash
# Restart both services
docker compose -f docker-compose.mvp.yml restart openclaw-orchestrator scenespeak-agent

# Recreate network
docker compose -f docker-compose.mvp.yml down
docker network prune -f
docker compose -f docker-compose.mvp.yml up -d
```

### Issue 3: ML Model Not Loading

**Symptoms:**
- Sentiment agent returns "model not loaded"
- Slow first responses
- High memory usage

**Diagnosis:**
```bash
# Check model status
docker exec chimera-sentiment-agent curl http://localhost:8004/health

# Expected: {"model_loaded": true, ...}

# Check model cache
docker exec chimera-sentiment-agent ls -la /app/models_cache

# Check disk space
df -h

# Check service logs
docker logs chimera-sentiment-agent --tail 100
```

**Solutions:**
```bash
# Restart sentiment agent (triggers model reload)
docker compose -f docker-compose.mvp.yml restart sentiment-agent

# Wait for model to load (30-60 seconds)
watch -n 5 'docker exec chimera-sentiment-agent curl http://localhost:8004/health'

# If model cache is corrupted, clear it
docker exec chimera-sentiment-agent rm -rf /app/models_cache/*
docker compose -f docker-compose.mvp.yml restart sentiment-agent
```

### Issue 4: High Memory Usage

**Symptoms:**
- Services getting OOMKilled
- System slows down
- Docker errors

**Diagnosis:**
```bash
# Check memory usage
docker stats --no-stream

# Check system memory
free -h

# Check OOMKilled containers
docker compose -f docker-compose.mvp.yml ps -a | grep OOM
```

**Solutions:**
```bash
# Restart specific service
docker compose -f docker-compose.mvp.yml restart sentiment-agent

# Increase memory limit in docker-compose.yml
# Edit and add:
# mem_limit: 2G
# mem_reservation: 1G

# Clean up unused resources
docker system prune -a
```

### Issue 5: GLM API Connection Failed

**Symptoms:**
- SceneSpeak agent can't generate dialogue
- API timeout errors
- Authentication errors

**Diagnosis:**
```bash
# Check if API key is set
docker compose -f docker-compose.mvp.yml logs scenespeak-agent | grep GLM

# Check API key format (should be 48 characters)
echo $GLM_API_KEY | wc -c

# Test API directly
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4", "messages": [{"role": "user", "content": "Hi"}]}'
```

**Solutions:**
```bash
# Update API key in .env
nano .env

# Restart scenespeak agent
docker compose -f docker-compose.mvp.yml up -d --force-recreate scenespeak-agent

# If local LLM is enabled, check Ollama
curl http://localhost:11434/api/tags
```

### Issue 6: Redis Connection Issues

**Symptoms:**
- Services can't store/retrieve data
- Connection refused errors
- Slow responses

**Diagnosis:**
```bash
# Check Redis container
docker ps | grep redis

# Test Redis connection
docker exec chimera-redis redis-cli ping

# Check Redis logs
docker logs chimera-redis --tail 50

# Check Redis memory usage
docker exec chimera-redis redis-cli INFO memory
```

**Solutions:**
```bash
# Restart Redis
docker compose -f docker-compose.mvp.yml restart redis

# Clear Redis cache (use carefully!)
docker exec chimera-redis redis-cli FLUSHALL

# If Redis data is corrupted
docker compose -f docker-compose.mvp.yml down
docker volume rm chimera-redis-data
docker compose -f docker-compose.mvp.yml up -d
```

## Performance Issues

### Slow Response Times

**Diagnosis:**
```bash
# Check response times
time curl http://localhost:8000/health

# Check resource usage
docker stats

# Check for errors
docker compose -f docker-compose.mvp.yml logs --tail 100 | grep -i error
```

**Solutions:**
```bash
# Restart slow service
docker compose -f docker-compose.mvp.yml restart [service-name]

# Check if ML models are loaded (causes first-request slowdown)
docker exec chimera-sentiment-agent curl http://localhost:8004/health

# Scale if needed (for k8s)
kubectl scale deployment/sentiment-agent --replicas=2 -n live
```

### High CPU Usage

**Diagnosis:**
```bash
# Check CPU usage
docker stats --no-stream

# Check processes inside container
docker exec chimera-openclaw-orchestrator top

# Check for infinite loops
docker logs chimera-openclaw-orchestrator --tail 100
```

**Solutions:**
```bash
# Restart affected service
docker compose -f docker-compose.mvp.yml restart [service-name]

# Limit CPU in docker-compose.yml
# cpu_count: 1
# cpu_percent: 50.0

# Check for memory leaks
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Data Issues

### Redis Data Loss

**Symptoms:**
- Data not persisting
- Empty results from queries

**Diagnosis:**
```bash
# Check Redis volume
docker volume ls | grep redis

# Check Redis persistence
docker exec chimera-redis redis-cli CONFIG GET save
docker exec chimera-redis redis-cli CONFIG GET appendonly

# Check data exists
docker exec chimera-redis redis-cli DBSIZE
```

**Solutions:**
```bash
# Restore from backup
./scripts/restore.sh /backup/chimera/[date]

# Or reset Redis (loses data)
docker compose -f docker-compose.mvp.yml down
docker volume rm chimera-redis-data
docker compose -f docker-compose.mvp.yml up -d
```

### Configuration Drift

**Symptoms:**
- Services using old configuration
- Environment variables not applied

**Diagnosis:**
```bash
# Check current environment
docker exec chimera-openclaw-orchestrator env | grep LOG_LEVEL

# Compare with .env
grep LOG_LEVEL .env
```

**Solutions:**
```bash
# Force recreate services
docker compose -f docker-compose.mvp.yml up -d --force-recreate

# Or recreate specific service
docker compose -f docker-compose.mvp.yml up -d --force-recreate openclaw-orchestrator
```

## Incident Response

### Severity Levels

| Level | Response Time | Examples |
|-------|--------------|----------|
| P1 - Critical | 15 minutes | All services down |
| P2 - High | 1 hour | Major service degraded |
| P3 - Medium | 4 hours | Minor feature broken |
| P4 - Low | 1 day | Documentation issue |

### Incident Procedure

1. **Identify**: What is broken and who is affected
2. **Assess**: Severity level and business impact
3. **Communicate**: Notify stakeholders if P1/P2
4. **Contain**: Prevent further damage
5. **Fix**: Implement solution
6. **Verify**: Confirm fix works
7. **Post-Mortem**: Document root cause

### Rollback Procedure

```bash
# 1. Identify last known good version
git log --oneline -10

# 2. Rollback code
git checkout <previous-commit>

# 3. Redeploy
docker compose -f docker-compose.mvp.yml down
docker compose -f docker-compose.mvp.yml build --no-cache
docker compose -f docker-compose.mvp.yml up -d

# 4. Verify
./scripts/verify-stack-health.sh

# 5. Monitor
docker compose -f docker-compose.mvp.yml logs -f
```

## Maintenance Tasks

### Daily Tasks

- [ ] Check service health
- [ ] Review error logs
- [ ] Verify backup completion

### Weekly Tasks

- [ ] Review resource usage
- [ ] Check for updates
- [ ] Clean up old logs
- [ ] Test backup restore

### Monthly Tasks

- [ ] Security updates
- [ ] Performance review
- [ ] Capacity planning
- [ ] Documentation review

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Lead Developer | | |
| DevOps Engineer | | |
| System Administrator | | |

## Escalation Matrix

| Issue Type | First Response | Escalation |
|------------|---------------|-------------|
| Application bug | Developer | Lead Developer |
| Infrastructure | DevOps | System Admin |
| Security | Security Team | CISO |
| Performance | Developer | DevOps |

## Useful Commands Reference

### Docker Commands

```bash
# Container operations
docker ps                          # List running containers
docker stats                       # Resource usage
docker logs <container>            # View logs
docker exec -it <container> bash   # Shell access
docker top <container>             # Container processes

# Compose operations
docker compose ps                  # Service status
docker compose logs                # All logs
docker compose restart <service>    # Restart service
docker compose down                # Stop all
```

### Network Debugging

```bash
# Test connectivity
docker exec chimera-openclaw-orchestrator ping scenespeak-agent

# Test HTTP
docker exec chimera-openclaw-orchestrator curl http://scenespeak-agent:8001/health

# Test DNS
docker exec chimera-openclaw-orchestrator nslookup scenespeak-agent

# Trace route
docker exec chimera-openclaw-orchestrator traceroute scenespeak-agent
```

### System Monitoring

```bash
# System resources
htop                              # Interactive process viewer
iotop                             # I/O monitoring
nethogs                           # Network monitoring

# Docker monitoring
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Service-specific
curl http://localhost:8000/health   # Health check
curl http://localhost:8000/metrics  # Metrics
```

---

**Related Documentation:**
- `docs/CONFIGURATION.md` - Configuration guide
- `docs/DEPLOYMENT.md` - Deployment procedures
- `docs/DEVELOPER_SETUP.md` - Developer guide

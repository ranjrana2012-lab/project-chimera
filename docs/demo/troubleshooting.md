# Project Chimera Demo Troubleshooting Guide

This guide covers common issues that may occur during the demo and their solutions.

## Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| Service not responding | `docker-compose restart <service>` |
| All services down | `./scripts/demo-start.sh` |
| Can't access UI | Check browser, check port, restart service |
| Slow response | Check CPU/memory, restart if needed |
| Error in logs | Check logs section below |
| Port conflict | `lsof -i :<port>` and kill conflicting process |

---

## Emergency Procedures

### All Services Down

```bash
# 1. Check Docker status
docker ps

# 2. Check if Docker Compose is running
docker-compose ps

# 3. Restart everything
docker-compose down
./scripts/demo-start.sh

# 4. Verify status
./scripts/demo-status.sh
```

### One Service Down

```bash
# 1. Identify which service
docker-compose ps

# 2. Check logs for errors
docker-compose logs <service-name>

# 3. Restart the service
docker-compose restart <service-name>

# 4. Verify health
curl http://localhost:<port>/health/live
```

### Demo Time Crisis (5 minutes or less)

**Skip to backup plan:**

1. Use terminal-only demo (no UI)
2. Show pre-cached responses
3. Focus on architecture explanation
4. Do live coding/requests only if time permits

---

## Common Issues and Solutions

### Issue: Docker Container Won't Start

**Symptoms:**
```
ERROR: for chimera-orchestrator  Cannot start service orchestrator: ...
```

**Diagnosis:**
```bash
# Check if port is already in use
lsof -i :8000

# Check Docker logs
docker logs chimera-orchestrator
```

**Solutions:**
1. **Port conflict:**
   ```bash
   # Find and kill the process using the port
   sudo lsof -ti:8000 | xargs kill -9
   docker-compose up -d orchestrator
   ```

2. **Out of memory:**
   ```bash
   # Check system memory
   free -h

   # Close other applications
   # Or increase Docker memory limit
   ```

3. **Image not found:**
   ```bash
   # Rebuild images
   docker-compose build
   docker-compose up -d
   ```

### Issue: Service Not Responding (Timeout)

**Symptoms:**
```bash
$ curl http://localhost:8000/health/live
# Hangs or times out
```

**Diagnosis:**
```bash
# Check if service is running
docker-compose ps

# Check service logs
docker-compose logs -f orchestrator

# Check service health from inside container
docker exec chimera-orchestrator curl localhost:8000/health/live
```

**Solutions:**
1. **Service is running but not responding:**
   ```bash
   # Restart the specific service
   docker-compose restart orchestrator

   # If that doesn't work, recreate it
   docker-compose up -d --force-recreate orchestrator
   ```

2. **Network issue:**
   ```bash
   # Check Docker network
   docker network ls
   docker network inspect chimera_default

   # Recreate network
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

3. **Dependency issue:**
   ```bash
   # Check if NATS is running
   docker-compose ps | grep nats

   # Restart dependencies
   docker-compose restart nats
   docker-compose restart orchestrator
   ```

### Issue: High CPU/Memory Usage

**Symptoms:**
- System running slow
- Docker Desktop showing high resource usage
- Services timing out

**Diagnosis:**
```bash
# Check container stats
docker stats

# Check system resources
htop
# or
top
```

**Solutions:**
1. **Restart bloated services:**
   ```bash
   docker-compose restart scenespeak  # Usually the culprit
   ```

2. **Limit resources:**
   ```bash
   # In docker-compose.yml, add:
   services:
     scenespeak:
       deploy:
         resources:
           limits:
             memory: 1G
   ```

3. **Close unnecessary applications:**
   - Close browser tabs
   - Stop other Docker containers
   - Close IDE if not needed

### Issue: Can't Access Web UIs

**Symptoms:**
- Browser shows "Connection refused"
- "This site can't be reached"

**Diagnosis:**
```bash
# Check if service is running
docker-compose ps | grep console

# Check if port is exposed
docker-compose port console 8007

# Check firewall
sudo ufw status
```

**Solutions:**
1. **Service not running:**
   ```bash
   docker-compose up -d console
   ```

2. **Wrong port:**
   ```bash
   # Check correct port
   docker-compose ps
   # Use correct port in browser
   ```

3. **Browser cache:**
   - Hard refresh: Ctrl+Shift+R (Linux) or Cmd+Shift+R (Mac)
   - Try incognito/private window
   - Clear browser cache

4. **Firewall blocking:**
   ```bash
   # Temporarily allow port
   sudo ufw allow 8007/tcp
   ```

### Issue: Grafana Dashboards Not Loading

**Symptoms:**
- Grafana opens but shows "Dashboard not found"
- No data in graphs
- "Datasource not found" errors

**Diagnosis:**
```bash
# Check Grafana logs
docker-compose logs grafana

# Check Prometheus connection
curl http://localhost:9090/api/v1/targets
```

**Solutions:**
1. **Prometheus not running:**
   ```bash
   docker-compose restart prometheus
   ```

2. **Datasource not configured:**
   ```bash
   # Access Grafana UI
   # Go to Configuration -> Data Sources
   # Add Prometheus: http://prometheus:9090
   # Save & Test
   ```

3. **Dashboard not imported:**
   ```bash
   # Import dashboards from provisioning
   docker-compose restart grafana
   ```

### Issue: Jaeger Not Showing Traces

**Symptoms:**
- Jaeger UI opens but no services listed
- Search returns no results
- "No traces found"

**Diagnosis:**
```bash
# Check Jaeger status
docker-compose ps | grep jaeger

# Check if traces are being sent
docker-compose logs orchestrator | grep jaeger
```

**Solutions:**
1. **Jaeger agent not receiving:**
   ```bash
   docker-compose restart jaeger
   ```

2. **Services not configured to send traces:**
   ```bash
   # Check environment variables
   docker exec chimera-orchestrator env | grep JAEGER
   ```

3. **Make a test request:**
   ```bash
   curl -X POST http://localhost:8000/v1/orchestrate \
     -H "Content-Type: application/json" \
     -d '{"skill": "dialogue_generator", "input": {"prompt": "test"}}'

   # Wait 5 seconds, then search Jaeger
   ```

### Issue: API Returns Errors

**Symptoms:**
```bash
$ curl http://localhost:8000/v1/orchestrate ...
{"error": "internal server error"}
```

**Diagnosis:**
```bash
# Check service logs
docker-compose logs -f orchestrator

# Look for error messages
docker-compose logs orchestrator | grep -i error
```

**Solutions:**
1. **NATS connection error:**
   ```bash
   docker-compose restart nats
   docker-compose restart orchestrator
   ```

2. **AI model not loaded:**
   ```bash
   docker-compose restart scenespeak
   # Wait for model to load (check logs)
   docker-compose logs -f scenespeak
   ```

3. **Invalid request format:**
   ```bash
   # Verify request format
   cat examples/demo-scenario.json

   # Use sample request
   python examples/sample-request.py
   ```

### Issue: Audio Not Working (Captioning Demo)

**Symptoms:**
- Captioning service returns empty transcription
- Audio not being captured

**Diagnosis:**
```bash
# Check if audio device is available
arecord -l

# Test audio recording
arecord -d 3 test.wav
```

**Solutions:**
1. **No microphone:**
   - Skip live audio demo
   - Use pre-recorded audio file
   - Use text input instead

2. **Permission denied:**
   ```bash
   # Add user to audio group
   sudo usermod -aG audio $USER

   # Log out and back in
   ```

3. **Fallback demo:**
   ```bash
   # Use text-to-speech instead
   curl -X POST http://localhost:8002/v1/transcribe \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, this is a test transcription"}'
   ```

---

## Log Analysis

### Reading Service Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs orchestrator

# Follow logs in real-time
docker-compose logs -f scenespeak

# Last 100 lines
docker-compose logs --tail=100 sentiment

# Logs with timestamps
docker-compose logs -t orchestrator
```

### Common Log Patterns

**Normal startup:**
```
INFO: Starting orchestrator on port 8000
INFO: Connected to NATS at nats://nats:4222
INFO: All skills registered
INFO: Server ready
```

**Error patterns to look for:**
```
ERROR: Connection refused
ERROR: Failed to connect to NATS
ERROR: Model loading failed
ERROR: Out of memory
ERROR: Permission denied
```

**Warning patterns:**
```
WARN: High memory usage
WARN: Slow response time
WARN: Rate limit approaching
```

---

## Performance Issues

### Slow Response Times

**Diagnosis:**
```bash
# Check system load
uptime

# Check container stats
docker stats

# Check response times
time curl http://localhost:8000/health/live
```

**Solutions:**
1. **Reduce load:**
   - Close other applications
   - Stop unnecessary containers

2. **Restart services:**
   ```bash
   docker-compose restart scenespeak
   ```

3. **Check for bottlenecks:**
   - Open Jaeger: http://localhost:16686
   - Find slow traces
   - Identify slow service

4. **Scale services:**
   ```bash
   docker-compose up -d --scale scenespeak=2
   ```

### Memory Leaks

**Symptoms:**
- Memory usage steadily increasing
- Services getting slower over time
- OOM (Out of Memory) kills

**Diagnosis:**
```bash
# Watch memory usage
watch -n 5 'docker stats --no-stream'

# Check for memory leaks in logs
docker-compose logs orchestrator | grep -i memory
```

**Solutions:**
1. **Restart affected service:**
   ```bash
   docker-compose restart <service-name>
   ```

2. **Reboot if severe:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Network Issues

### Services Can't Communicate

**Diagnosis:**
```bash
# Check network
docker network inspect chimera_default

# Test connectivity
docker exec chimera-orchestrator ping chimera-scenespeak
```

**Solutions:**
1. **Recreate network:**
   ```bash
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

2. **Check DNS:**
   ```bash
   # From inside container
   docker exec chimera-orchestrator cat /etc/resolv.conf
   docker exec chimera-orchestrator nslookup chimera-scenespeak
   ```

### Port Forwarding Not Working

**Diagnosis:**
```bash
# Check port mapping
docker-compose port orchestrator 8000

# Check if port is listening
netstat -tulpn | grep 8000
```

**Solutions:**
1. **Restart with proper port mapping:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Check docker-compose.yml:**
   ```yaml
   ports:
     - "8000:8000"  # Correct format
   ```

---

## Demo-Specific Issues

### Sample Request Fails

**Problem:**
```bash
$ curl -X POST http://localhost:8000/v1/orchestrate ...
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Solution:**
1. Check if orchestrator is running: `docker-compose ps`
2. Restart: `docker-compose restart orchestrator`
3. Wait 5 seconds and retry

### Demo Script Command Fails

**Problem:**
Command from demo script doesn't work as shown

**Solution:**
1. **Copy exact command** from demo-script.md
2. **Check for line breaks** in copied text
3. **Use alternative:**
   ```bash
   python examples/sample-request.py
   ```

### Time Running Out

**Problem:**
Demo is taking too long, won't finish in 30 minutes

**Solution:**
1. **Skip observability section** (can show quickly at end)
2. **Combine AI demos** into one flow
3. **Pre-load requests** in terminals before demo
4. **Have backup slides** ready to show instead of live demos

---

## Getting Help

### Diagnostic Information Collection

If you need to ask for help, collect this information:

```bash
# Save to file for support
{
  echo "=== Docker Status ==="
  docker-compose ps

  echo "=== System Resources ==="
  free -h
  df -h
  uptime

  echo "=== Service Health ==="
  for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "Port $port:"
    curl -s http://localhost:$port/health/live || echo "Failed"
  done

  echo "=== Recent Logs ==="
  docker-compose logs --tail=50

  echo "=== Network Status ==="
  docker network ls
  docker network inspect chimera_default
} > demo-diagnostics.txt
```

### Emergency Contacts

- **Technical Support**: [Add contact]
- **Demo Lead**: [Add contact]
- **Backup Presenter**: [Add contact]

---

## Prevention: Pre-Demo Checklist

Run this 30 minutes before demo:

```bash
#!/bin/bash
echo "=== Pre-Demo System Check ==="

# 1. All services running
echo "Checking services..."
docker-compose ps | grep -q "Exit" && echo "ERROR: Some services not running" || echo "OK: All services running"

# 2. Health checks
echo "Checking health endpoints..."
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  curl -sf http://localhost:$port/health/live > /dev/null || echo "ERROR: Port $port not responding"
done

# 3. UI access
echo "Checking UIs..."
curl -sf http://localhost:8007 > /dev/null || echo "ERROR: Console not accessible"
curl -sf http://localhost:3000 > /dev/null || echo "ERROR: Grafana not accessible"

# 4. Make test request
echo "Testing API..."
curl -sf -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"skill": "dialogue_generator", "input": {"prompt": "test"}}' \
  > /dev/null && echo "OK: API working" || echo "ERROR: API test failed"

# 5. Check resources
echo "Checking resources..."
MEMORY=$(free | grep Mem | awk '{printf("%.0f"), $3/$2 * 100.0}')
if [ $MEMORY -gt 80 ]; then
  echo "WARNING: Memory usage at $MEMORY%"
else
  echo "OK: Memory usage at $MEMORY%"
fi

echo "=== Check Complete ==="
```

---

**Troubleshooting Guide Version:** 1.0
**Last Updated:** 2026-03-06
**Next Review:** After each demo, add any new issues encountered

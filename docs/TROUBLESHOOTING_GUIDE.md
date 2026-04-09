# Project Chimera Phase 2 - Troubleshooting and Diagnostics Guide

**Version:** 1.0.0
**Last Updated:** April 9, 2026
**Target Audience:** Operators, Developers, System Administrators

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Service-Specific Issues](#service-specific-issues)
3. [Integration Problems](#integration-problems)
4. [Performance Issues](#performance-issues)
5. [Network Issues](#network-issues)
6. [Hardware Issues](#hardware-issues)
7. [Emergency Procedures](#emergency-procedures)
8. [Diagnostic Tools](#diagnostic-tools)
9. [Common Error Messages](#common-error-messages)
10. [Recovery Procedures](#recovery-procedures)

---

## Quick Diagnostics

### Health Check Script

The fastest way to diagnose issues is to run the health check script:

```bash
./scripts/health-check.sh --service all
```

This will report the health status of all Phase 2 services.

### Manual Health Checks

```bash
# DMX Controller
curl http://localhost:8001/health

# Audio Controller
curl http://localhost:8002/health

# BSL Avatar Service
curl http://localhost:8003/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "<service-name>",
  "timestamp": "2026-04-09T12:00:00Z"
}
```

### Service Status Dashboard

```bash
./scripts/dev-tools.sh --action status
```

### Docker Container Status

```bash
docker-compose -f services/docker-compose.phase2.yml ps
```

---

## Service-Specific Issues

### DMX Controller

#### Issue: Fixtures Not Responding

**Symptoms:**
- Commands sent but no visible change
- Fixtures remain in previous state
- Inconsistent behavior

**Diagnosis:**
```bash
# Check service health
curl http://localhost:8001/health

# Check logs
docker-compose -f services/docker-compose.phase2.yml logs dmx-controller

# Check DMX interface
ls -l /dev/ttyUSB*

# Verify fixture configuration
curl http://localhost:8001/api/fixtures
```

**Solutions:**

1. **Check DMX Interface Connection**
```bash
# Verify interface is accessible
sudo chmod 666 /dev/ttyUSB0

# Test direct communication
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 250000)
ser.write(b'\x00')  # DMX break
ser.write(b'\x00')  # DMX start code
print('DMX interface accessible')
"
```

2. **Verify Fixture Addressing**
```bash
# Check fixture start addresses
curl http://localhost:8001/api/fixtures | jq '.fixtures[] | .start_address'

# Ensure no address conflicts
```

3. **Check for DMX Terminator**
- Ensure DMX terminator is installed at end of chain
- Verify terminator is properly connected

4. **Restart Service**
```bash
./scripts/dev-tools.sh --action restart --service dmx
```

#### Issue: Emergency Stop Won't Reset

**Symptoms:**
- Commands blocked after emergency stop
- Service won't accept new commands
- "Emergency stop active" message persists

**Diagnosis:**
```bash
# Check controller state
curl http://localhost:8001/api/status

# Look for emergency stop count
curl http://localhost:8001/api/status | jq '.emergency_stop_count'
```

**Solutions:**

1. **Explicit Reset**
```bash
curl -X POST http://localhost:8001/api/reset_emergency
```

2. **Verify Reset**
```bash
curl http://localhost:8001/api/status | jq '.state'
```

3. **If Reset Fails:**
```bash
# Restart service
./scripts/dev-tools.sh --action restart --service dmx

# Last resort: full redeployment
./scripts/deploy.sh --env production --service dmx --force
```

#### Issue: Scene Transition Not Working

**Symptoms:**
- Scene activation fails
- Fixtures don't transition
- Abrupt changes instead of smooth transitions

**Diagnosis:**
```bash
# Check scene configuration
curl http://localhost:8001/api/scenes/<scene_name>

# Verify transition_time_ms value
curl http://localhost:8001/api/scenes/<scene_name> | jq '.transition_time_ms'
```

**Solutions:**

1. **Increase Transition Time**
```bash
curl -X POST http://localhost:8001/api/scenes/<scene_name> \
  -H "Content-Type: application/json" \
  -d '{
    "transition_time_ms": 5000
  }'
```

2. **Check Fixture Values**
```bash
# Verify all fixture values are valid (0-255)
curl http://localhost:8001/api/scenes/<scene_name> | jq '.fixture_values'
```

### Audio Controller

#### Issue: No Sound Output

**Symptoms:**
- Tracks show as playing but no sound
- Volume controls appear to work
- No audio output from system

**Diagnosis:**
```bash
# Check service health
curl http://localhost:8002/health

# Check track status
curl http://localhost:8002/api/tracks

# Check volume levels
curl http://localhost:8002/api/volume/master

# Check system audio
aplay -l
```

**Solutions:**

1. **Verify Audio Device**
```bash
# List audio devices
docker-compose -f services/docker-compose.phase2.yml exec audio-controller aplay -l

# Check device permissions
docker-compose -f services/docker-compose.phase2.yml exec audio-controller ls -l /dev/snd
```

2. **Check Audio Files**
```bash
# Verify audio files exist
ls -la services/assets/audio/

# Check file permissions
chmod 644 services/assets/audio/*.wav
```

3. **Test Direct Playback**
```bash
# Test audio playback directly
aplay services/assets/audio/test.wav
```

4. **Check Volume Levels**
```bash
# Ensure volume is not muted
curl http://localhost:8002/api/tracks | jq '.tracks[] | select(.is_muted)'

# Unmute if needed
curl -X POST http://localhost:8002/api/tracks/<track_id>/unmute
```

#### Issue: Emergency Mute Not Working

**Symptoms:**
- Emergency mute command fails
- Audio continues playing
- No response to mute command

**Diagnosis:**
```bash
# Check service status
curl http://localhost:8002/api/status

# Check for errors
docker-compose -f services/docker-compose.phase2.yml logs --tail=50 audio-controller
```

**Solutions:**

1. **Verify Emergency Endpoint**
```bash
# Test emergency endpoint
curl -X POST http://localhost:8002/api/emergency_mute -v
```

2. **Check Audio Device Control**
```bash
# Verify audio device is controllable
docker-compose -f services/docker-compose.phase2.yml exec audio-controller amixer set Master mute
```

3. **Restart Service**
```bash
./scripts/dev-tools.sh --action restart --service audio
```

### BSL Avatar Service

#### Issue: Translation Not Working

**Symptoms:**
- Translation requests fail
- Empty translation results
- Gesture library errors

**Diagnosis:**
```bash
# Check service health
curl http://localhost:8003/health

# Check gesture library
curl http://localhost:8003/api/gestures

# Check library size
curl http://localhost:8003/api/status | jq '.gesture_library_size'
```

**Solutions:**

1. **Verify Gesture Library**
```bash
# Check if gesture library exists
ls -la services/bsl-avatar-service/data/gestures.json

# Verify library format
cat services/bsl-avatar-service/data/gestures.json | jq empty
```

2. **Test Simple Translation**
```bash
# Test with simple word
curl -X POST http://localhost:8003/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}'
```

3. **Check Fingerspelling Fallback**
```bash
# Verify fingerspelling works for unknown words
curl -X POST http://localhost:8003/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "xyzxyz"}'
```

#### Issue: Avatar Rendering Slow

**Symptoms:**
- Long wait times for avatar rendering
- Timeout errors
- Poor performance

**Diagnosis:**
```bash
# Check service status
curl http://localhost:8003/api/status

# Check translation stats
curl http://localhost:8003/api/stats

# Monitor resource usage
docker stats chimera-bsl-avatar
```

**Solutions:**

1. **Optimize Rendering Options**
```bash
# Use lower quality rendering
curl -X POST http://localhost:8003/api/render \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello",
    "render_options": {
      "quality": "low",
      "include_non_manual": false
    }
  }'
```

2. **Check Resource Usage**
```bash
# Monitor memory and CPU
docker stats chimera-bsl-avatar --no-stream

# Increase resources if needed
docker update chimera-bsl-avatar --memory="2g"
```

3. **Use Caching**
```bash
# Pre-render common phrases
# (Implementation depends on service capabilities)
```

---

## Integration Problems

### Issue: Services Not Communicating

**Symptoms:**
- Service-to-service calls fail
- Timeouts between services
- Orchestration failures

**Diagnosis:**
```bash
# Check all services are healthy
./scripts/health-check.sh --service all

# Check network connectivity
docker network inspect chimera-network

# Check service logs
docker-compose -f services/docker-compose.phase2.yml logs
```

**Solutions:**

1. **Verify Network Configuration**
```bash
# Check if services are on same network
docker network inspect chimera-network | jq '.[0].Containers'

# All services should be listed
```

2. **Check DNS Resolution**
```bash
# Test service name resolution
docker-compose -f services/docker-compose.phase2.yml exec dmx-controller ping audio-controller
docker-compose -f services/docker-compose.phase2.yml exec dmx-controller ping bsl-avatar-service
```

3. **Verify Service Discovery**
```bash
# Check if services can reach each other
curl http://dmx-controller:8001/health
curl http://audio-controller:8002/health
curl http://bsl-avatar-service:8003/health
```

### Issue: Coordinated Scene Changes Failing

**Symptoms:**
- Partial scene activation
- Some services don't respond
- Inconsistent state across services

**Diagnosis:**
```bash
# Check orchestrator logs
tail -50 services/operator-console/logs/chimera.log

# Check individual service logs
docker-compose -f services/docker-compose.phase2.yml logs --tail=100
```

**Solutions:**

1. **Implement Transaction Safety**
```python
# Use two-phase commit pattern
responses = []
for service in services:
    response = service.prepare_scene_change(scene_data)
    responses.append(response)

# Verify all prepared successfully
if all(r.success for r in responses):
    for service in services:
        service.commit_scene_change()
else:
    # Rollback
    for service in services:
        service.rollback_scene_change()
```

2. **Add Timeout Handling**
```python
import asyncio

async def coordinated_change():
    tasks = [
        asyncio.create_task(service.change_scene(scene))
        for service in services
    ]

    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)
    except asyncio.TimeoutError:
        # Handle timeout
        for task in tasks:
            task.cancel()
```

---

## Performance Issues

### Issue: High Response Times

**Symptoms:**
- Slow API responses
- Laggy scene changes
- Poor interactive performance

**Diagnosis:**
```bash
# Run performance benchmarks
python tests/performance/benchmark_phase2.py --service all

# Check resource usage
docker stats

# Profile service
docker-compose -f services/docker-compose.phase2.yml exec dmx-controller python -m cProfile
```

**Solutions:**

1. **Optimize Database Queries**
```python
# Use connection pooling
# Add indexes to frequently queried fields
# Use select_related/prefetch for related objects
```

2. **Implement Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_scene_data(scene_name: str):
    # Cache frequently accessed data
    pass
```

3. **Use Async Operations**
```python
import asyncio

async def handle_request():
    # Use async for I/O operations
    result = await async_operation()
    return result
```

### Issue: High Memory Usage

**Symptoms:**
- Services getting OOM killed
- Increasing memory consumption over time
- Memory leaks

**Diagnosis:**
```bash
# Check memory usage
docker stats chimera-dmx-controller chimera-audio-controller chimera-bsl-avatar

# Check for memory leaks
docker-compose -f services/docker-compose.phase2.yml exec dmx-controller python -m memory_profiler
```

**Solutions:**

1. **Identify Memory Leaks**
```python
import tracemalloc

tracemalloc.start()
# ... run code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

2. **Optimize Data Structures**
```python
# Use generators instead of lists for large datasets
def process_items():
    for item in large_dataset:  # Generator
        yield process(item)
```

3. **Implement Resource Limits**
```yaml
# In docker-compose.yml
services:
  dmx-controller:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

---

## Network Issues

### Issue: Services Not Accessible

**Symptoms:**
- Connection refused errors
- Services unreachable from host
- Intermittent connectivity

**Diagnosis:**
```bash
# Check if ports are listening
sudo netstat -tulpn | grep -E '8001|8002|8003'

# Check firewall rules
sudo ufw status

# Check service logs
docker-compose -f services/docker-compose.phase2.yml logs
```

**Solutions:**

1. **Verify Port Mappings**
```bash
# Check docker-compose port mappings
grep -A 5 "ports:" services/docker-compose.phase2.yml
```

2. **Check Firewall Rules**
```bash
# Ensure ports are allowed
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 8003/tcp
```

3. **Verify Service Binding**
```bash
# Services should bind to 0.0.0.0, not 127.0.0.1
# Check in service configuration
```

---

## Hardware Issues

### Issue: DMX Interface Not Detected

**Symptoms:**
- DMX controller can't find interface
- "Device not found" errors
- No communication with fixtures

**Diagnosis:**
```bash
# List USB devices
lsusb

# Check for tty devices
ls -l /dev/ttyUSB*

# Check dmesg for USB errors
dmesg | grep -i usb
```

**Solutions:**

1. **Check USB Permissions**
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Fix device permissions
sudo chmod 666 /dev/ttyUSB0
```

2. **Install DMX Drivers**
```bash
# Install FTDI drivers if needed
sudo apt-get install libftdi1

# Load kernel modules
sudo modprobe ftdi_sio
sudo modprobe usbserial
```

3. **Create udev Rule**
```bash
# Create udev rule for DMX interface
sudo nano /etc/udev/rules.d/99-dmx.rules
```

Add:
```
# DMX USB Interface
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666"
```

### Issue: Audio Device Not Accessible

**Symptoms:**
- Audio controller can't access device
- Permission denied errors
- No sound output

**Diagnosis:**
```bash
# Check audio devices
aplay -l

# Check device permissions
ls -l /dev/snd/*

# Check group membership
groups
```

**Solutions:**

1. **Add User to Audio Group**
```bash
sudo usermod -aG audio $USER
```

2. **Fix Device Permissions**
```bash
sudo chmod 666 /dev/snd/*
```

3. **Configure Docker Device Access**
```yaml
# In docker-compose.yml
services:
  audio-controller:
    devices:
      - "/dev/snd:/dev/snd"
    group_add:
      - "audio"
```

---

## Emergency Procedures

### Emergency Stop (All Services)

```bash
# Emergency stop all services
curl -X POST http://localhost:8001/api/emergency_stop
curl -X POST http://localhost:8002/api/emergency_mute

# Or use orchestrator
python examples/integration/integration_examples.py --example emergency
```

### Full System Reset

```bash
# Stop all services
docker-compose -f services/docker-compose.phase2.yml down

# Reset all emergency states
curl -X POST http://localhost:8001/api/reset_emergency
curl -X POST http://localhost:8002/api/reset_emergency

# Restart services
docker-compose -f services/docker-compose.phase2.yml up -d
```

### Rollback to Previous Version

```bash
# List backups
./scripts/backup.sh --list

# Restore from backup
./scripts/backup.sh --restore backup_YYYYMMDD_HHMMSS
```

---

## Diagnostic Tools

### System Diagnostics Script

```bash
# Run comprehensive diagnostics
./scripts/diagnose.sh
```

### Performance Profiling

```bash
# Run performance benchmarks
python tests/performance/benchmark_phase2.py --service all

# Generate performance report
python tests/performance/benchmark_phase2.py --service all --verbose
```

### Security Scanning

```bash
# Run security audit
./scripts/security-harden.sh --action audit --service all

# Check compliance
./scripts/security-harden.sh --action compliance
```

### Log Analysis

```bash
# View recent logs
docker-compose -f services/docker-compose.phase2.yml logs --tail=100

# Follow logs in real-time
docker-compose -f services/docker-compose.phase2.yml logs -f

# View specific service logs
docker-compose -f services/docker-compose.phase2.yml logs -f dmx-controller
```

---

## Common Error Messages

### "Connection refused"

**Meaning:** Service is not running or not accessible

**Solutions:**
1. Check if service is running: `docker ps | grep chimera`
2. Check service logs for errors
3. Verify port is correct
4. Check firewall rules

### "Container exited with code 1"

**Meaning:** Service crashed during startup

**Solutions:**
1. Check service logs: `docker logs <container_name>`
2. Verify configuration files
3. Check for missing dependencies
4. Verify environment variables

### "Health check failed"

**Meaning:** Service health endpoint returned error

**Solutions:**
1. Check service logs for errors
2. Verify all dependencies are available
3. Check resource availability
4. Restart service if needed

### "Emergency stop active"

**Meaning:** Service is in emergency stop state

**Solutions:**
1. Reset from emergency: `curl -X POST http://localhost:800X/api/reset_emergency`
2. Verify reset was successful
3. Check service state

### "DMX interface not found"

**Meaning:** DMX USB interface not detected

**Solutions:**
1. Check USB connection
2. Verify interface is powered
3. Check device permissions
4. Install/reinstall drivers

---

## Recovery Procedures

### Service Recovery

```bash
# 1. Identify failed service
./scripts/health-check.sh --service all

# 2. Check service logs
docker-compose -f services/docker-compose.phase2.yml logs <service>

# 3. Restart failed service
./scripts/dev-tools.sh --action restart --service <service>

# 4. Verify recovery
./scripts/health-check.sh --service <service>
```

### Complete System Recovery

```bash
# 1. Stop all services
docker-compose -f services/docker-compose.phase2.yml down

# 2. Restore from backup
./scripts/backup.sh --restore <latest_backup>

# 3. Restart services
docker-compose -f services/docker-compose.phase2.yml up -d

# 4. Verify all services
./scripts/health-check.sh --service all
```

### Disaster Recovery

```bash
# 1. Assess damage
./scripts/health-check.sh --service all
docker-compose -f services/docker-compose.phase2.yml ps

# 2. Check for data corruption
# (Depends on your data integrity checks)

# 3. Restore from off-site backup
# (If local backup is also affected)

# 4. Verify system integrity
./scripts/security-harden.sh --action audit

# 5. Document incident
# Create incident report with timeline and actions taken
```

---

## Prevention and Monitoring

### Proactive Monitoring

```bash
# Enable continuous monitoring
./scripts/health-check.sh --service all --watch
```

### Regular Maintenance

- **Daily:** Review logs for errors
- **Weekly:** Run security scans
- **Monthly:** Review performance reports
- **Quarterly:** Test disaster recovery procedures

### Automated Alerts

Set up alerts for:
- Service health failures
- High error rates
- Performance degradation
- Security vulnerabilities
- Resource exhaustion

---

**Document Version:** 1.0.0
**Last Updated:** April 9, 2026

For additional help, see:
- Developer onboarding guide: `docs/DEVELOPER_ONBOARDING_GUIDE.md`
- API examples: `docs/PHASE2_API_EXAMPLES.md`
- Deployment guide: `docs/DEPLOYMENT_AND_OPERATIONS_GUIDE.md`
- Security documentation: `docs/SECURITY_DOCUMENTATION.md`

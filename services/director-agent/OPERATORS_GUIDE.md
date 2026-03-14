# Operator's Guide

Guide for operators managing live shows with Project Chimera's Director Agent.

## Table of Contents

1. [Overview](#overview)
2. [Pre-Show Checklist](#pre-show-checklist)
3. [Show Control](#show-control)
4. [Emergency Procedures](#emergency-procedures)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Overview

As an operator, you're responsible for managing automated shows, ensuring safety, and handling any issues that arise during performance.

### Your Responsibilities

- Monitor show execution in real-time
- Grant approval for scene transitions (if required)
- Handle emergency stops
- Troubleshoot issues as they arise
- Ensure smooth show progression

### Key Concepts

- **Show**: A complete theatrical production with multiple scenes
- **Scene**: A segment of the show with specific actions
- **Action**: A single operation performed by an agent
- **Approval Gate**: Point requiring operator approval before proceeding
- **Emergency Stop**: Immediate halt of all show activity

## Pre-Show Checklist

### 1. System Health Check

Verify all services are running:

```bash
# Director Agent
curl http://localhost:8013/health

# All specialized agents
curl http://localhost:8001/health  # SceneSpeak
curl http://localhost:8002/health  # Captioning
curl http://localhost:8003/health  # BSL
curl http://localhost:8004/health  # Sentiment
curl http://localhost:8005/health  # Lighting/Sound
```

Expected response:
```json
{
  "status": "healthy",
  "service": "director-agent",
  "shows_loaded": 2
}
```

### 2. Show Validation

Verify show is loaded and valid:

```bash
# List available shows
curl http://localhost:8013/api/shows

# Check specific show details
curl http://localhost:8013/api/shows/welcome_show
```

### 3. Configuration Check

Review show safety settings:

```bash
# Get show details
curl http://localhost:8013/api/shows/welcome_show | jq '.metadata'
```

Verify:
- `require_human_approval`: true (recommended)
- `emergency_stop_enabled`: true
- `max_scene_duration_ms`: reasonable value

### 4. Agent Connectivity

Test agent communication:

```bash
# Test lighting agent
curl -X POST http://localhost:8005/api/lighting \
  -H "Content-Type: application/json" \
  -d '{"scene": "test", "mood": "calm"}'

# Test dialogue generation
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test message"}'
```

### 5. WebSocket Connection

Establish WebSocket connection for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8013/ws/show/welcome_show');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

### 6. Emergency Stop Test

Verify emergency stop functionality:

```bash
# Start a test show
curl -X POST http://localhost:8013/api/shows/test/start

# Immediately stop
curl -X POST http://localhost:8013/api/shows/test/stop

# Verify stopped
curl http://localhost:8013/api/shows/test/state
```

## Show Control

### Starting a Show

#### Option 1: Start from Beginning

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_scene": 0,
    "require_approval": true
  }'
```

#### Option 2: Start from Specific Scene

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_scene": 2,
    "require_approval": true
  }'
```

#### Option 3: Start without Approval (Auto-play)

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/start \
  -H "Content-Type: application/json" \
  -d '{
    "require_approval": false
  }'
```

### Monitoring Show Progress

#### Get Current State

```bash
curl http://localhost:8013/api/shows/welcome_show/state
```

Response:
```json
{
  "show_id": "welcome_show",
  "state": "running",
  "current_scene_index": 2,
  "engine_state": {
    "state": "running",
    "current_scene": {
      "id": "scene_3",
      "title": "Audience Engagement"
    },
    "awaiting_approval": false
  }
}
```

#### Monitor via WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8013/ws/show/welcome_show');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'initial_state':
      console.log('Show state:', data.state);
      break;

    case 'show_state_update':
      console.log('Scene:', data.state.current_scene);
      console.log('Status:', data.state.state);

      if (data.state.engine_state.awaiting_approval) {
        console.log('APPROVAL REQUIRED');
      }
      break;
  }
};
```

### Granting Scene Approval

When `awaiting_approval` is true:

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/approve
```

### Pausing a Show

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/pause
```

The show will pause at the next action boundary.

### Resuming a Paused Show

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/resume
```

### Stopping a Show

#### Normal Stop

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/stop
```

The show will stop at the next scene boundary.

#### Emergency Stop

Same command, but immediate effect:

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/stop
```

## Emergency Procedures

### Emergency Stop Triggers

Consider emergency stop when:
- Agent failure causes safety concerns
- Show behavior is unexpected or dangerous
- Technical issues risk audience safety
- Physical emergency in venue

### Emergency Stop Procedure

1. **IMMEDIATE ACTION**: Stop the show

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/stop
```

2. **ASSESS**: Check show state

```bash
curl http://localhost:8013/api/shows/welcome_show/state
```

3. **SECURE**: Ensure all agents stopped

```bash
# Check agent states
curl http://localhost:8005/api/lighting/state  # Lighting
curl http://localhost:8005/v1/audio/stop       # Audio
```

4. **DOCUMENT**: Record incident details

5. **NOTIFY**: Inform relevant parties

### Recovery After Emergency

1. **Investigate**: Review logs to identify cause

```bash
# Check director logs
tail -f /var/log/director-agent.log

# Check agent logs
tail -f /var/log/scenespeak-agent.log
tail -f /var/log/lighting-sound-music.log
```

2. **Resolve**: Fix underlying issue

3. **Test**: Verify fix with test show

4. **Restart**: Begin show from appropriate scene

```bash
# Restart from scene 3
curl -X POST http://localhost:8013/api/shows/welcome_show/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_scene": 2,
    "require_approval": true
  }'
```

## Monitoring

### Key Metrics to Monitor

1. **Show State**: Current scene and status
2. **Agent Health**: All agents responding
3. **Action Duration**: Actions completing within timeout
4. **WebSocket Connection**: Real-time updates flowing
5. **System Resources**: CPU, memory, network

### Monitoring Dashboard

Create a simple monitoring dashboard:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Show Monitor</title>
  <script>
    const ws = new WebSocket('ws://localhost:8013/ws/show/welcome_show');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateDashboard(data);
    };

    function updateDashboard(data) {
      if (data.type === 'show_state_update') {
        document.getElementById('state').textContent = data.state.state;
        document.getElementById('scene').textContent =
          data.state.engine_state.current_scene?.title || 'N/A';
        document.getElementById('approval').textContent =
          data.state.engine_state.awaiting_approval ? 'YES' : 'NO';
      }
    }

    function approve() {
      fetch('/api/shows/welcome_show/approve', {method: 'POST'});
    }

    function emergencyStop() {
      if (confirm('EMERGENCY STOP?')) {
        fetch('/api/shows/welcome_show/stop', {method: 'POST'});
      }
    }
  </script>
</head>
<body>
  <h1>Show Monitor</h1>
  <div>State: <span id="state">Unknown</span></div>
  <div>Scene: <span id="scene">Unknown</span></div>
  <div>Needs Approval: <span id="approval">NO</span></div>
  <button onclick="approve()">Approve</button>
  <button onclick="emergencyStop()">EMERGENCY STOP</button>
</body>
</html>
```

### Log Monitoring

```bash
# Follow director agent logs
tail -f /var/log/director-agent.log

# Search for errors
grep "ERROR" /var/log/director-agent.log

# Search for specific show
grep "welcome_show" /var/log/director-agent.log
```

## Troubleshooting

### Show Won't Start

**Symptoms**: Show returns error or doesn't change state

**Diagnosis**:
```bash
# Check show state
curl http://localhost:8013/api/shows/welcome_show/state

# Check director health
curl http://localhost:8013/health
```

**Solutions**:
1. Verify show is loaded
2. Check all agents are healthy
3. Review show definition for errors
4. Check network connectivity

### Scene Not Advancing

**Symptoms**: Show stuck on same scene

**Diagnosis**:
```bash
# Check if awaiting approval
curl http://localhost:8013/api/shows/welcome_show/state | jq '.engine_state.awaiting_approval'
```

**Solutions**:
1. Grant approval if required
2. Check for agent timeouts
3. Review action execution logs
4. Consider pausing and investigating

### Agent Failure

**Symptoms**: Actions failing for specific agent

**Diagnosis**:
```bash
# Check agent health
curl http://localhost:8003/health  # BSL example

# Check agent logs
tail -f /var/log/bsl-agent.log
```

**Solutions**:
1. Restart failed agent
2. Check agent configuration
3. Verify agent connectivity
4. Use `continue_on_failure` in show definition

### WebSocket Disconnection

**Symptoms**: No real-time updates

**Diagnosis**:
```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8013/ws/show/welcome_show
```

**Solutions**:
1. Reconnect WebSocket
2. Check network stability
3. Fall back to polling API state endpoint
4. Restart director agent if needed

### Show Running Too Fast/Slow

**Symptoms**: Actions not timing correctly

**Solutions**:
1. Adjust `wait` action durations
2. Review action timeout values
3. Check agent response times
4. Consider adding more wait actions

## Best Practices

### 1. Always Use Approval Gates

For live shows, always enable approval:

```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/start \
  -H "Content-Type: application/json" \
  -d '{"require_approval": true}'
```

### 2. Monitor Continuously

Never leave an unattended show running without:
- WebSocket connection active
- Monitoring dashboard visible
- Log monitoring in place
- Emergency access available

### 3. Test Before Live

Always run full rehearsal:
```bash
# Load test show
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{"show_id": "rehearsal", "file_path": "./shows/production_show.yaml"}'

# Run with approval
curl -X POST http://localhost:8013/api/shows/rehearsal/start \
  -H "Content-Type: application/json" \
  -d '{"require_approval": true}'
```

### 4. Document Incidents

Record all incidents:

```markdown
## Incident Log

### 2026-03-14 15:30
- **Issue**: Scene 3 failed to advance
- **Cause**: BSL agent timeout
- **Resolution**: Restarted BSL agent, approved scene
- **Impact**: 30 second delay
```

### 5. Have Backup Plans

Know your alternatives:
- Manual show control
- Reduced agent set
- Emergency procedures
- Contact information

### 6. Regular Health Checks

Schedule periodic checks:
```bash
# Every 5 minutes during show
while true; do
  curl http://localhost:8013/health
  curl http://localhost:8013/api/shows/welcome_show/state
  sleep 300
done
```

## Quick Reference

### Essential Commands

```bash
# Health check
curl http://localhost:8013/health

# List shows
curl http://localhost:8013/api/shows

# Start show
curl -X POST http://localhost:8013/api/shows/SHOW_ID/start \
  -H "Content-Type: application/json" \
  -d '{"require_approval": true}'

# Get state
curl http://localhost:8013/api/shows/SHOW_ID/state

# Approve
curl -X POST http://localhost:8013/api/shows/SHOW_ID/approve

# Pause
curl -X POST http://localhost:8013/api/shows/SHOW_ID/pause

# Resume
curl -X POST http://localhost:8013/api/shows/SHOW_ID/resume

# STOP
curl -X POST http://localhost:8013/api/shows/SHOW_ID/stop
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8013/ws/show/SHOW_ID');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### Emergency Stop

```bash
curl -X POST http://localhost:8013/api/shows/SHOW_ID/stop
```

## Support

### Contact Information

- Technical Support: [support@projectchimera.org](mailto:support@projectchimera.org)
- Emergency Contact: [emergency@projectchimera.org](mailto:emergency@projectchimera.org)
- Documentation: [Project Chimera Wiki](https://github.com/your-org/project-chimera/wiki)

### Resources

- [Director Agent README](README.md)
- [Show Creator's Guide](SHOW_CREATORS_GUIDE.md)
- [API Documentation](http://localhost:8013/docs)
- [Example Shows](shows/)

---

**Remember**: Safety first. When in doubt, stop the show and assess.

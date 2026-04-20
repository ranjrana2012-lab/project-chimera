# Live Show Automation System

Comprehensive guide to Project Chimera's automated theatrical production system.

## Overview

The Live Show Automation System enables end-to-end automated theatrical productions by coordinating multiple specialized AI agents through a central Director Agent.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Operator Console                         │
│                      (Port 8007)                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Director Agent                           │
│                    (Port 8013)                              │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Show Parser  │  │ Exec Engine   │  │ Safety Ctrl   │   │
│  └──────────────┘  └───────────────┘  └───────────────┘   │
└───┬───────────┬────────┬──────────┬──────────┬─────────────┘
    │           │        │          │          │
    ▼           ▼        ▼          ▼          ▼
┌────────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌─────────┐
│ BSL    │  │ Cap  │  │ Light│  │Sound │  │Sentiment│
│ 8003   │  │ 8002 │  │ 8005 │  │ 8005 │  │  8004   │
└────────┘  └──────┘  └──────┘  └──────┘  └─────────┘
     │
     ▼
┌─────────┐
│SceneSpk │
│  8001   │
└─────────┘
```

## Components

### 1. Director Agent (Port 8013)

**Purpose**: Central orchestrator for automated shows

**Key Features**:
- Show definition parsing (YAML DSL)
- Multi-agent coordination
- Scene execution engine
- Safety controls & emergency stop
- Real-time WebSocket updates
- Audience adaptation

**Documentation**: [Director Agent README](services/director-agent/README.md)

### 2. Specialized Agents

| Agent | Port | Purpose |
|-------|------|---------|
| SceneSpeak | 8001 | Generate dialogue & content |
| Captioning | 8002 | Real-time transcription |
| BSL | 8003 | Sign language translation |
| Sentiment | 8004 | Audience mood analysis |
| Lighting/Sound | 8005 | Environmental control |

### 3. Operator Console (Port 8007)

**Purpose**: Human oversight and manual control

**Key Features**:
- Real-time show monitoring
- Manual approval interface
- Emergency stop controls
- Agent health dashboard
- Execution logs

## Quick Start

### 1. Start All Services

```bash
# From Project_Chimera root

# Start specialized agents
cd services/scenespeak-agent && python main.py &
cd services/captioning-agent && python main.py &
cd services/bsl-agent && python -m api.main &
cd services/sentiment-agent && python main.py &
cd services/lighting-sound-music && python main.py &

# Start director agent
cd services/director-agent && python main.py &

# Start operator console (optional)
cd services/operator-console && python main.py &
```

### 2. Verify Services

```bash
# Check all agents are healthy
curl http://localhost:8001/health  # SceneSpeak
curl http://localhost:8002/health  # Captioning
curl http://localhost:8003/health  # BSL
curl http://localhost:8004/health  # Sentiment
curl http://localhost:8005/health  # Lighting/Sound
curl http://localhost:8013/health  # Director
```

### 3. Run Example Show

```bash
# List available shows
curl http://localhost:8013/api/shows

# Start welcome show
curl -X POST http://localhost:8013/api/shows/welcome_show/start \
  -H "Content-Type: application/json" \
  -d '{
    "require_approval": true
  }'

# Monitor via WebSocket
wscat -c ws://localhost:8013/ws/show/welcome_show
```

## Creating Your Own Show

### Step 1: Write Show Definition

Create a YAML file (e.g., `my_show.yaml`):

```yaml
metadata:
  title: "My Show"
  version: "1.0"
  require_human_approval: true
  emergency_stop_enabled: true

scenes:
  - id: "scene_1"
    title: "Opening"
    actions:
      - agent: "lighting"
        action: "set_lighting"
        parameters:
          mood: "calm"

      - agent: "scenespeak"
        action: "generate_dialogue"
        parameters:
          prompt: "Welcome to our show!"

      - action: "wait"
        duration_ms: 3000
```

### Step 2: Load Show

```bash
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{
    "show_id": "my_show",
    "file_path": "/path/to/my_show.yaml"
  }'
```

### Step 3: Test Show

```bash
# Start with approval
curl -X POST http://localhost:8013/api/shows/my_show/start \
  -H "Content-Type: application/json" \
  -d '{"require_approval": true}'

# Approve scenes as needed
curl -X POST http://localhost:8013/api/shows/my_show/approve
```

## Documentation

### For Show Creators

- [Show Creator's Guide](services/director-agent/SHOW_CREATORS_GUIDE.md)
  - Show definition syntax
  - Working with agents
  - Creating scenes
  - Advanced features
  - Best practices

### For Operators

- [Operator's Guide](services/director-agent/OPERATORS_GUIDE.md)
  - Pre-show checklist
  - Show control procedures
  - Emergency protocols
  - Troubleshooting

### For Developers

- [Director Agent README](services/director-agent/README.md)
  - Architecture details
  - API documentation
  - Development setup
  - Testing guide

## Example Shows

### 1. Welcome Show

**File**: `services/director-agent/shows/welcome_show.yaml`

**Description**: Simple demonstration of multi-agent coordination

**Features**:
- 4 scenes, 30 seconds
- Basic agent coordination
- Accessibility features (BSL, captioning)
- Mood-based lighting

**Run**:
```bash
curl -X POST http://localhost:8013/api/shows/welcome_show/start
```

### 2. Adaptive Show

**File**: `services/director-agent/shows/adaptive_show.yaml`

**Description**: Advanced show with audience adaptation

**Features**:
- Sentiment-based branching
- Conditional actions
- Parallel execution
- Real-time adaptation

**Run**:
```bash
curl -X POST http://localhost:8013/api/shows/adaptive_show/start
```

## Safety Features

### 1. Human Approval Gates

Require operator approval between scenes:

```yaml
metadata:
  require_human_approval: true
```

### 2. Emergency Stop

Immediately stop all show activity:

```bash
curl -X POST http://localhost:8013/api/shows/SHOW_ID/stop
```

### 3. Scene Timeouts

Prevent runaway scenes:

```yaml
metadata:
  max_scene_duration_ms: 300000  # 5 minutes max
```

### 4. Action Timeouts

Prevent hanging actions:

```yaml
- agent: "scenespeak"
  action: "generate_dialogue"
  timeout_ms: 8000
```

### 5. Graceful Failure

Continue on non-critical failures:

```yaml
- agent: "bsl"
  action: "translate"
  continue_on_failure: true
```

## Monitoring

### Health Checks

```bash
# All services
for port in 8001 8002 8003 8004 8005 8013; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq .
done
```

### Show State

```bash
# Current state
curl http://localhost:8013/api/shows/welcome_show/state | jq .
```

### WebSocket Updates

```javascript
const ws = new WebSocket('ws://localhost:8013/ws/show/welcome_show');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('State:', data.state);
};
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8013/metrics
```

## Testing

### Automated Tests

```bash
cd services/director-agent
python test_director.py
```

### Manual Testing

```bash
# 1. Load show
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{"show_id": "test", "file_path": "./shows/welcome_show.yaml"}'

# 2. Start show
curl -X POST http://localhost:8013/api/shows/test/start \
  -H "Content-Type: application/json" \
  -d '{"require_approval": true}'

# 3. Monitor
curl http://localhost:8013/api/shows/test/state

# 4. Approve scenes
curl -X POST http://localhost:8013/api/shows/test/approve

# 5. Stop show
curl -X POST http://localhost:8013/api/shows/test/stop
```

## Troubleshooting

### Show Won't Start

**Symptoms**: API returns error

**Solutions**:
1. Check director agent is running: `curl http://localhost:8013/health`
2. Verify show is loaded: `curl http://localhost:8013/api/shows`
3. Check agent health
4. Review show definition syntax

### Actions Failing

**Symptoms**: Actions timeout or return errors

**Solutions**:
1. Check agent logs
2. Increase action timeout
3. Set `continue_on_failure: true` for non-critical actions
4. Verify agent endpoints

### Show Stuck

**Symptoms**: Show not advancing

**Solutions**:
1. Check if awaiting approval: `curl http://localhost:8013/api/shows/SHOW_ID/state`
2. Grant approval if needed
3. Use pause/resume to reset
4. Emergency stop if necessary

### WebSocket Issues

**Symptoms**: No real-time updates

**Solutions**:
1. Verify WebSocket endpoint
2. Check network connectivity
3. Fall back to polling state endpoint
4. Restart director agent

## Performance Considerations

### 1. Action Parallelization

Use parallel actions for independent operations:

```yaml
- action: "parallel"
  actions:
    - agent: "lighting"
      action: "set_lighting"
    - agent: "sound"
      action: "play_audio"
```

### 2. Timeout Optimization

Set appropriate timeouts:

- Fast operations (lighting): 2-3 seconds
- Medium operations (BSL): 3-5 seconds
- Slow operations (dialogue): 5-10 seconds

### 3. Caching

Reuse generated content where possible:

```yaml
- agent: "scenespeak"
  action: "generate_dialogue"
  parameters:
    prompt: "Welcome!"  # Reusable content
```

### 4. Resource Management

Monitor resource usage:

```bash
# Check memory/CPU
top -p $(pgrep -f "director-agent")

# Check connections
netstat -an | grep 8013
```

## Best Practices

### For Show Creators

1. **Start Simple**: Begin with basic shows
2. **Test Thoroughly**: Test each scene independently
3. **Use Timeouts**: Set appropriate timeouts for all actions
4. **Handle Failures**: Use `continue_on_failure` wisely
5. **Add Comments**: Document complex scenes
6. **Version Control**: Track show definitions in git

### For Operators

1. **Pre-Show Checks**: Verify all services before starting
2. **Monitor Continuously**: Never leave unattended shows
3. **Have Backup Plans**: Know manual procedures
4. **Document Incidents**: Record all issues
5. **Test Emergency Stops**: Verify before live show
6. **Stay Alert**: Keep monitoring dashboard visible

### For Developers

1. **Follow Patterns**: Use existing show examples
2. **Validate Inputs**: Check all parameters
3. **Handle Errors**: Graceful error handling
4. **Log Events**: Comprehensive logging
5. **Test Changes**: Automated testing
6. **Document Code**: Clear comments

## Advanced Features

### Audience Adaptation

Enable sentiment-based adaptations:

```yaml
metadata:
  enable_sentiment_adaptation: true
  sentiment_check_interval_ms: 3000

scenes:
  - id: "scene_1"
    adapt_to_sentiment: true
    sentiment_thresholds:
      positive: 0.7
      negative: 0.3
```

### Conditional Branching

Branch based on audience mood:

```yaml
- action: "conditional"
  condition:
    type: "sentiment"
    operator: ">"
    threshold: 0.6
  then_actions:
    # Positive path
  else_actions:
    # Negative path
```

### Context Variables

Pass data between actions:

```yaml
- agent: "scenespeak"
  action: "generate_dialogue"
  parameters:
    prompt: "Hello!"

- agent: "bsl"
  action: "translate"
  parameters:
    text: "${dialogue_text}"  # References previous result
```

## Contributing

To contribute to the Live Show Automation system:

1. Read the documentation
2. Study example shows
3. Test your changes
4. Submit pull requests
5. Participate in discussions

## Support

- **Documentation**: [Project Chimera Wiki](https://github.com/your-org/project-chimera/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/project-chimera/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/project-chimera/discussions)
- **Email**: support@projectchimera.org

## License

Part of Project Chimera. See main project LICENSE file.

---

**Remember**: This is a live performance system. Always prioritize safety, test thoroughly, and have backup plans ready.

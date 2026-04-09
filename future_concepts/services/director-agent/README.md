# Director Agent

Automated show director service for Project Chimera. Parses show definitions, coordinates multiple agents, and manages live show execution with real-time audience adaptation.

## Overview

The Director Agent is the central orchestrator for automated theatrical productions. It executes show definitions written in YAML, coordinating all specialized agents (BSL, captioning, lighting, sound, sentiment, SceneSpeak) to create synchronized, adaptive performances.

## Features

- **Show Definition DSL**: YAML-based format for defining shows, scenes, and actions
- **Multi-Agent Coordination**: Orchestrates 6+ specialized agents in real-time
- **Scene Execution Engine**: Sequential and parallel action execution
- **Audience Adaptation**: Real-time sentiment-based content branching
- **Safety Controls**: Emergency stop, manual override, human approval gates
- **Real-time Updates**: WebSocket streaming of show state
- **Show Management**: Load, validate, and manage multiple shows
- **Metrics & Monitoring**: Prometheus metrics for observability

## Architecture

```
Director Agent (port 8013)
├── Show Definition Parser
│   └── YAML DSL → Pydantic models
├── Execution Engine
│   ├── Scene scheduler
│   ├── Action executor
│   ├── Agent client pool
│   └── Context manager
├── Safety Controls
│   ├── Emergency stop
│   ├── Human approval gates
│   └── Pause/Resume
└── WebSocket Broadcaster
    └── Real-time state updates
```

## Installation

```bash
cd services/director-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key settings:
- `PORT`: Service port (default: 8013)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `REQUIRE_HUMAN_APPROVAL`: Require approval between scenes
- `EMERGENCY_STOP_ENABLED`: Enable emergency stop functionality
- `SHOWS_DIR`: Directory containing show definition YAML files

## Running the Service

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8013 --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8013/docs
- ReDoc: http://localhost:8013/redoc

## Show Definition Format

Shows are defined in YAML with the following structure:

### Basic Structure

```yaml
metadata:
  title: "Show Title"
  author: "Author Name"
  version: "1.0"
  description: "Show description"
  estimated_duration_ms: 60000
  tags:
    - demo
    - accessible

  # Safety settings
  require_human_approval: true
  emergency_stop_enabled: true
  max_scene_duration_ms: 300000

  # Audience adaptation
  enable_sentiment_adaptation: false
  sentiment_check_interval_ms: 5000

scenes:
  - id: "scene_1"
    title: "First Scene"
    description: "Scene description"
    duration_ms: 10000

    actions:
      # Scene actions here

    transition:
      type: "fade"
      duration_ms: 1000
```

### Action Types

#### 1. Agent Actions

```yaml
- agent: "lighting"
  action: "set_lighting"
  description: "Set scene lighting"
  parameters:
    scene: "dramatic"
    mood: "dramatic"
  timeout_ms: 3000
  continue_on_failure: false
  retry_count: 2
```

Available agents:
- `bsl`: Sign language translation
- `captioning`: Real-time transcription
- `lighting`: DMX lighting control
- `sound`: Audio playback
- `music`: Background music
- `sentiment`: Audience analysis
- `scenespeak`: Dialogue generation

#### 2. Wait Action

```yaml
- action: "wait"
  duration_ms: 3000
  description: "Pause for delivery"
```

#### 3. Parallel Actions

```yaml
- action: "parallel"
  description: "Execute multiple actions simultaneously"
  wait_for_all: true
  actions:
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        scene: "dramatic"
    - agent: "scenespeak"
      action: "generate_dialogue"
      parameters:
        prompt: "Welcome to the show!"
```

#### 4. Conditional Actions

```yaml
- action: "conditional"
  description: "Branch based on audience sentiment"
  condition:
    type: "sentiment"
    operator: ">"
    threshold: 0.6
  then_actions:
    # Actions if condition is true
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        mood: "joyful"
  else_actions:
    # Actions if condition is false
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        mood: "calm"
```

### Scene Transitions

```yaml
transition:
  type: "fade"  # cut, fade, dissolve
  duration_ms: 1000
  lighting_transition:
    from_color: "#FFFFFF"
    to_color: "#000000"
  audio_fade: true
```

### Audience Adaptation

```yaml
scenes:
  - id: "scene_1"
    # ... scene definition ...

    adapt_to_sentiment: true
    sentiment_thresholds:
      positive: 0.7
      negative: 0.3
```

## Usage Examples

### 1. Load a Show

```bash
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{
    "show_id": "my_show",
    "file_path": "/path/to/show.yaml"
  }'
```

### 2. List Available Shows

```bash
curl http://localhost:8013/api/shows
```

### 3. Start Show Execution

```bash
curl -X POST http://localhost:8013/api/shows/my_show/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_scene": 0,
    "require_approval": true
  }'
```

### 4. Pause Show

```bash
curl -X POST http://localhost:8013/api/shows/my_show/pause
```

### 5. Resume Show

```bash
curl -X POST http://localhost:8013/api/shows/my_show/resume
```

### 6. Emergency Stop

```bash
curl -X POST http://localhost:8013/api/shows/my_show/stop
```

### 7. Grant Approval

```bash
curl -X POST http://localhost:8013/api/shows/my_show/approve
```

### 8. Get Show State

```bash
curl http://localhost:8013/api/shows/my_show/state
```

## WebSocket Integration

Connect to real-time show updates:

```javascript
const ws = new WebSocket('ws://localhost:8013/ws/show/my_show');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'show_state_update') {
    console.log('State:', data.state);
    console.log('Scene:', data.state.current_scene);
    console.log('Status:', data.state.state);
  }
};

// Send ping to keep connection alive
ws.send('ping');
```

## Creating Custom Shows

### Step 1: Create YAML File

```bash
cd shows/
vim my_custom_show.yaml
```

### Step 2: Define Show Structure

```yaml
metadata:
  title: "My Custom Show"
  author: "Your Name"
  version: "1.0"
  description: "A description of my show"

  require_human_approval: true
  emergency_stop_enabled: true

scenes:
  - id: "scene_1"
    title: "Opening"
    actions:
      # Add your actions here
```

### Step 3: Test Show Definition

```bash
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{
    "show_id": "test_show",
    "file_path": "/path/to/shows/my_custom_show.yaml"
  }'
```

### Step 4: Execute Show

```bash
curl -X POST http://localhost:8013/api/shows/test_show/start
```

## Safety Best Practices

1. **Always Test First**: Test shows in a safe environment before live performance
2. **Human Approval**: Enable `require_human_approval` for critical scenes
3. **Emergency Stop**: Know how to trigger emergency stop
4. **Timeouts**: Set appropriate timeouts for all agent actions
5. **Failure Handling**: Use `continue_on_failure` for non-critical actions
6. **Scene Duration**: Set `max_scene_duration_ms` to prevent runaway scenes
7. **Backup Plans**: Have contingency plans for agent failures

## Monitoring

### Metrics

Prometheus metrics are available at `/metrics`:

- `director_agent_show_starts_total`: Total shows started
- `director_agent_scene_executions_total`: Total scenes executed
- `director_agent_action_executions_total`: Total actions executed
- `director_agent_execution_duration_seconds`: Execution duration histogram

### Health Checks

- Liveness: `/health/live`
- Readiness: `/health/ready`
- Full health: `/health`

## Troubleshooting

### Show Won't Load

- Check YAML syntax
- Verify all required fields are present
- Check agent endpoint URLs in `.env`

### Actions Failing

- Check agent logs
- Verify agents are running on correct ports
- Check network connectivity between services
- Review timeout settings

### Show Stuck

- Use `/api/shows/{show_id}/stop` for emergency stop
- Check agent health endpoints
- Review execution logs

## Example Shows

Two example shows are included:

1. **Welcome Show** (`shows/welcome_show.yaml`):
   - Simple demonstration
   - 4 scenes, 30 seconds
   - Shows basic agent coordination

2. **Adaptive Show** (`shows/adaptive_show.yaml`):
   - Advanced demonstration
   - Audience sentiment adaptation
   - Conditional branching
   - Parallel action execution

## Integration with Operator Console

The Director Agent integrates with the Operator Console (port 8007) for oversight:

- Real-time show state monitoring
- Manual approval interface
- Emergency stop controls
- Execution logs and metrics

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

```
director-agent/
├── main.py                  # FastAPI application
├── show_definition.py       # Pydantic models for show DSL
├── execution_engine.py      # Scene execution engine
├── shows/                   # Show definition files
│   ├── welcome_show.yaml
│   └── adaptive_show.yaml
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── .env.example            # Environment configuration
└── README.md               # This file
```

## License

Part of Project Chimera. See main project LICENSE file.

## Support

For issues and questions:
- GitHub Issues: [Project Chimera Issues](https://github.com/your-org/project-chimera/issues)
- Documentation: [Project Chimera Wiki](https://github.com/your-org/project-chimera/wiki)

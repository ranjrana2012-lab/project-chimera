# Show Creator's Guide

A comprehensive guide for creating theatrical shows using Project Chimera's Director Agent.

## Table of Contents

1. [Introduction](#introduction)
2. [Show Definition Basics](#show-definition-basics)
3. [Working with Agents](#working-with-agents)
4. [Creating Scenes](#creating-scenes)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Testing & Debugging](#testing--debugging)

## Introduction

Project Chimera's Director Agent allows you to create automated theatrical productions that coordinate multiple AI agents. This guide will teach you how to:

- Write show definitions in YAML
- Coordinate lighting, sound, BSL, captioning, and dialogue generation
- Create adaptive experiences based on audience sentiment
- Ensure safety and reliability in live performance

## Show Definition Basics

### Minimal Show Structure

Every show must have:

```yaml
metadata:
  title: "My Show"
  version: "1.0"

  # Safety
  require_human_approval: true
  emergency_stop_enabled: true

scenes:
  - id: "scene_1"
    title: "First Scene"
    actions:
      # At least one action required
```

### Complete Show Structure

```yaml
metadata:
  # Required
  title: "My Show Title"
  version: "1.0"

  # Optional but recommended
  author: "Your Name"
  description: "A compelling description"
  estimated_duration_ms: 120000  # 2 minutes
  tags:
    - drama
    - accessible
    - interactive

  # Safety Configuration
  require_human_approval: true      # Human approval between scenes
  emergency_stop_enabled: true      # Allow emergency stop
  max_scene_duration_ms: 300000    # Max 5 minutes per scene

  # Audience Adaptation
  enable_sentiment_adaptation: false
  sentiment_check_interval_ms: 5000

scenes:
  - id: "unique_scene_id"
    title: "Scene Title"
    description: "What happens in this scene"
    duration_ms: 30000  # Expected duration (optional)

    actions:
      # Scene actions go here

    transition:
      type: "fade"
      duration_ms: 1000
```

## Working with Agents

### Available Agents

| Agent | Port | Purpose | Endpoints |
|-------|------|---------|-----------|
| BSL | 8003 | Sign language translation | translate |
| Captioning | 8002 | Real-time transcription | transcribe |
| Lighting | 8005 | DMX lighting control | set_lighting |
| Sound | 8005 | Audio playback | play_audio |
| Music | 8005 | Background music | play_music |
| Sentiment | 8004 | Audience analysis | analyze_sentiment |
| SceneSpeak | 8001 | Dialogue generation | generate_dialogue |

### Agent Action Syntax

```yaml
- agent: "agent_name"
  action: "action_name"
  description: "Human-readable description"
  parameters:
    # Action-specific parameters
  timeout_ms: 5000
  retry_count: 2
  continue_on_failure: false
```

### Lighting Agent

Set lighting scenes and moods:

```yaml
- agent: "lighting"
  action: "set_lighting"
  description: "Create dramatic atmosphere"
  parameters:
    scene: "dramatic_scene"
    mood: "dramatic"
  timeout_ms: 3000
```

Available moods:
- `dramatic`: High contrast, focused lighting
- `calm`: Soft, even illumination
- `tense`: Stark shadows, cool tones
- `joyful`: Bright, warm colors
- `mysterious`: Dim, colored lighting
- `romantic`: Soft, warm glow

Advanced lighting control:

```yaml
- agent: "lighting"
  action: "set_lighting"
  parameters:
    color: "#FF5733"      # Hex color
    intensity: 0.8        # 0.0 to 1.0
    zone: "stage_center"  # Specific zone
    effect: "fade"        # Lighting effect
```

### Sound Agent

Play audio cues:

```yaml
- agent: "sound"
  action: "play_audio"
  description: "Play thunder sound effect"
  parameters:
    file_path: "/sounds/thunder.wav"
    volume: 0.8
    loop: false
  timeout_ms: 5000
```

### SceneSpeak Agent

Generate dialogue:

```yaml
- agent: "scenespeak"
  action: "generate_dialogue"
  description: "Generate hero's opening line"
  parameters:
    prompt: "The hero enters the room and says: Welcome, brave adventurers!"
    context:
      show_id: "my_show"
      scene_number: 1
      character: "hero"
      tone: "heroic"
    max_tokens: 150
    temperature: 0.7  # 0.0 = focused, 1.0 = creative
  timeout_ms: 5000
```

### BSL Agent

Translate to sign language:

```yaml
- agent: "bsl"
  action: "translate"
  description: "Translate dialogue to BSL"
  parameters:
    text: "${dialogue_text}"  # Use variable from context
    language: "en"
    gloss_format: "singspell"
    region: "northern"
  timeout_ms: 3000
  continue_on_failure: true
```

### Captioning Agent

Generate captions:

```yaml
- agent: "captioning"
  action: "transcribe"
  description: "Create captions for audio"
  parameters:
    audio: "base64_encoded_audio"
    language: "en"
    timestamps: true
  timeout_ms: 5000
  continue_on_failure: true
```

### Sentiment Agent

Analyze audience reaction:

```yaml
- agent: "sentiment"
  action: "analyze_sentiment"
  description: "Check audience mood"
  parameters:
    text: "audience_reaction_sample"
    detect_language: false
  timeout_ms: 2000
  continue_on_failure: true
```

## Creating Scenes

### Scene Structure

```yaml
- id: "scene_1_act1"
  title: "The Discovery"
  description: "Hero discovers the ancient artifact"
  duration_ms: 45000

  actions:
    # Sequential actions

  transition:
    type: "fade"
    duration_ms: 1500
    lighting_transition:
      from_color: "#000000"
      to_color: "#FFFFFF"
```

### Sequential Actions

Actions execute one after another:

```yaml
actions:
  # Step 1: Set lighting
  - agent: "lighting"
    action: "set_lighting"
    parameters:
      mood: "dramatic"

  # Step 2: Generate dialogue
  - agent: "scenespeak"
    action: "generate_dialogue"
    parameters:
      prompt: "What's this strange glow?"

  # Step 3: Pause for delivery
  - action: "wait"
    duration_ms: 3000

  # Step 4: Analyze audience
  - agent: "sentiment"
    action: "analyze_sentiment"
    parameters:
      text: "audience_reaction"
```

### Parallel Actions

Execute multiple actions simultaneously:

```yaml
actions:
  - action: "parallel"
    description: "Launch atmosphere and dialogue together"
    wait_for_all: true  # Wait for all to complete
    actions:
      - agent: "lighting"
        action: "set_lighting"
        parameters:
          mood: "mysterious"

      - agent: "sound"
        action: "play_audio"
        parameters:
          file_path: "/sounds/ambience.wav"

      - agent: "scenespeak"
        action: "generate_dialogue"
        parameters:
          prompt: "Something feels different here..."
```

### Conditional Actions

Branch based on audience sentiment:

```yaml
actions:
  - action: "conditional"
    description: "Adapt based on audience mood"
    condition:
      type: "sentiment"
      operator: ">"  # >, <, >=, <=, ==
      threshold: 0.6
    then_actions:
      # Audience is positive
      - agent: "lighting"
        action: "set_lighting"
        parameters:
          mood: "joyful"

      - agent: "scenespeak"
        action: "generate_dialogue"
        parameters:
          prompt: "Your excitement fills the air!"

    else_actions:
      # Audience needs more engagement
      - agent: "lighting"
        action: "set_lighting"
        parameters:
          mood: "dramatic"

      - agent: "scenespeak"
        action: "generate_dialogue"
        parameters:
          prompt: "Let us draw you deeper into the mystery..."
```

## Advanced Features

### Context Variables

Pass data between actions:

```yaml
actions:
  # Generate dialogue and store result
  - agent: "scenespeak"
    action: "generate_dialogue"
    parameters:
      prompt: "Welcome to our show!"

  # Use generated dialogue in BSL translation
  - agent: "bsl"
    action: "translate"
    parameters:
      text: "${dialogue_text}"  # References previous result
```

### Audience Adaptation

Enable scene-level adaptation:

```yaml
- id: "scene_2"
  title: "Adaptive Scene"
  adapt_to_sentiment: true
  sentiment_thresholds:
    positive: 0.7
    negative: 0.3

  actions:
    # Scene will check sentiment periodically
    # and can adapt content accordingly
```

### Scene Transitions

Create smooth transitions:

```yaml
transition:
  type: "fade"  # cut, fade, dissolve
  duration_ms: 2000
  lighting_transition:
    from_color: "#FFFFFF"
    to_color: "#000000"
    from_intensity: 1.0
    to_intensity: 0.3
  audio_fade: true
```

### Error Handling

Control failure behavior:

```yaml
- agent: "lighting"
  action: "set_lighting"
  parameters:
    mood: "dramatic"
  timeout_ms: 5000
  retry_count: 3
  continue_on_failure: true  # Don't stop show if this fails
```

## Best Practices

### 1. Start Simple

Begin with basic shows before adding complexity:

```yaml
# Simple first show
metadata:
  title: "My First Show"
  require_human_approval: true

scenes:
  - id: "scene_1"
    title: "Welcome"
    actions:
      - agent: "lighting"
        action: "set_lighting"
        parameters:
          mood: "calm"

      - agent: "scenespeak"
        action: "generate_dialogue"
        parameters:
          prompt: "Welcome everyone!"
```

### 2. Use Timeouts Wisely

Set appropriate timeouts:

```yaml
# Fast operations
- agent: "lighting"
  timeout_ms: 2000

# Slower operations
- agent: "scenespeak"
  timeout_ms: 8000

# Very slow operations
- agent: "captioning"
  timeout_ms: 12000
```

### 3. Handle Failures Gracefully

```yaml
# Critical action - stop on failure
- agent: "scenespeak"
  action: "generate_dialogue"
  parameters:
    prompt: "Critical plot point"
  continue_on_failure: false

# Nice-to-have action - continue on failure
- agent: "bsl"
  action: "translate"
  parameters:
    text: "Optional translation"
  continue_on_failure: true
```

### 4. Test Thoroughly

```bash
# Load show to validate syntax
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{
    "show_id": "test",
    "file_path": "/path/to/show.yaml"
  }'

# Run with approval required
curl -X POST http://localhost:8013/api/shows/test/start \
  -H "Content-Type: application/json" \
  -d '{
    "require_approval": true
  }'
```

### 5. Add Descriptive Comments

```yaml
scenes:
  - id: "scene_1"
    title: "Opening"
    description: |
      This is the opening scene where we establish the atmosphere.
      We start with mysterious lighting and ambient sound to build tension.
    actions:
      # Step 1: Create mysterious atmosphere
      - agent: "lighting"
        action: "set_lighting"
        description: "Dim, cool-toned lighting for mystery"
        parameters:
          mood: "mysterious"

      # Step 2: Add ambient sound
      - agent: "sound"
        action: "play_audio"
        description: "Low, rumbling ambience"
        parameters:
          file_path: "/sounds/mystery_ambience.wav"
```

### 6. Use Parallel Execution Appropriately

```yaml
# GOOD: Parallel independent actions
- action: "parallel"
  actions:
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        mood: "dramatic"
    - agent: "sound"
      action: "play_audio"
      parameters:
        file_path: "/sounds/thunder.wav"

# BAD: Parallel dependent actions
- action: "parallel"
  actions:
    - agent: "scenespeak"
      action: "generate_dialogue"
      parameters:
        prompt: "Hello"
    - agent: "bsl"
      action: "translate"
      parameters:
        text: "${dialogue_text}"  # Won't work in parallel!
```

## Examples

### Example 1: Monologue Scene

```yaml
- id: "monologue_scene"
  title: "Hero's Soliloquy"
  duration_ms: 60000

  actions:
    # Set intimate lighting
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        mood: "romantic"
        intensity: 0.7

    # Generate monologue
    - agent: "scenespeak"
      action: "generate_dialogue"
      parameters:
        prompt: |
          To be, or not to be, that is the question:
          Whether 'tis nobler in the mind to suffer
          The slings and arrows of outrageous fortune,
          Or to take arms against a sea of troubles
        context:
          scene_number: 3
          character: "hamlet"
          tone: "contemplative"
        max_tokens: 200
        temperature: 0.6

    # Provide accessibility
    - action: "parallel"
      wait_for_all: false
      actions:
        - agent: "captioning"
          action: "transcribe"
          parameters:
            audio: "${monologue_audio}"
          continue_on_failure: true

        - agent: "bsl"
          action: "translate"
          parameters:
            text: "${dialogue_text}"
          continue_on_failure: true

    # Pause for delivery
    - action: "wait"
      duration_ms: 8000
```

### Example 2: Action Sequence

```yaml
- id: "action_sequence"
  title: "The Chase"
  duration_ms: 45000

  actions:
    # Tense lighting
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        mood: "tense"

    # Start music
    - agent: "sound"
      action: "play_audio"
      parameters:
        file_path: "/music/chase.wav"
        volume: 0.9

    # Quick dialogue
    - agent: "scenespeak"
      action: "generate_dialogue"
      parameters:
        prompt: "Run! They're coming!"
        temperature: 0.9  # More urgent

    # Action sound
    - agent: "sound"
      action: "play_audio"
      parameters:
        file_path: "/sounds/explosion.wav"
        volume: 1.0

    # Dramatic lighting change
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        color: "#FF0000"
        intensity: 1.0
```

### Example 3: Interactive Scene

```yaml
- id: "interactive_scene"
  title: "Audience Choice"
  adapt_to_sentiment: true

  actions:
    # Check audience mood
    - agent: "sentiment"
      action: "analyze_sentiment"
      parameters:
        text: "audience_reaction"

    # Branch based on mood
    - action: "conditional"
      condition:
        type: "sentiment"
        operator: ">"
        threshold: 0.6
      then_actions:
        # Happy path
        - agent: "scenespeak"
          action: "generate_dialogue"
          parameters:
            prompt: "Your joy guides our story to a peaceful resolution."

      else_actions:
        # Tense path
        - agent: "scenespeak"
          action: "generate_dialogue"
          parameters:
            prompt: "The tension rises as our heroes face greater challenges."

    # Adapt lighting
    - agent: "lighting"
      action: "set_lighting"
      parameters:
        mood: "${audience_mood}"  # joyful or dramatic
```

## Testing & Debugging

### Validate Show Syntax

```bash
# Try to load show
curl -X POST http://localhost:8013/api/shows/load \
  -H "Content-Type: application/json" \
  -d '{
    "show_id": "validation_test",
    "file_path": "./shows/my_show.yaml"
  }'
```

### Test Scene Execution

```bash
# Start show with approval
curl -X POST http://localhost:8013/api/shows/test/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_scene": 0,
    "require_approval": true
  }'

# Approve each scene manually
curl -X POST http://localhost:8013/api/shows/test/approve
```

### Monitor Execution

```bash
# Get current state
curl http://localhost:8013/api/shows/test/state

# Watch via WebSocket
wscat -c ws://localhost:8013/ws/show/test
```

### Debug Tips

1. **Use descriptive action descriptions**: Helps identify issues in logs
2. **Set appropriate timeouts**: Prevents hanging actions
3. **Enable continue_on_failure**: For non-critical actions
4. **Test scenes individually**: Start from specific scene index
5. **Check agent health**: Verify all agents are running
6. **Review logs**: Check director-agent and agent logs

## Common Issues

### Issue: Action Times Out

**Solution**: Increase timeout or check agent health

```yaml
- agent: "scenespeak"
  timeout_ms: 10000  # Increase from 5000
```

### Issue: Show Won't Load

**Solution**: Check YAML syntax and required fields

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('show.yaml'))"
```

### Issue: Agents Not Responding

**Solution**: Check agent services are running

```bash
# Check health endpoints
curl http://localhost:8001/health  # SceneSpeak
curl http://localhost:8002/health  # Captioning
curl http://localhost:8003/health  # BSL
curl http://localhost:8004/health  # Sentiment
curl http://localhost:8005/health  # Lighting/Sound
```

## Resources

- [Director Agent README](README.md)
- [Example Shows](shows/)
- [API Documentation](http://localhost:8013/docs)
- [Project Chimera Wiki](https://github.com/your-org/project-chimera/wiki)

## Support

For help creating shows:
- GitHub Issues: [Project Chimera Issues](https://github.com/your-org/project-chimera/issues)
- Discussion Forum: [Project Chimera Discussions](https://github.com/your-org/project-chimera/discussions)

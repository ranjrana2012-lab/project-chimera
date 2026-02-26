# SceneSpeak Skill

Generates real-time dialogue and stage cues for live theatrical performances using local LLMs.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| current_scene | object | Yes | Current scene state |
| dialogue_context | array | Yes | Recent dialogue turns |
| sentiment_vector | object | No | Audience sentiment |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| proposed_lines | string | Generated dialogue |
| stage_cues | array | Suggested cues |
| metadata | object | Generation metadata |

## Configuration

- **Timeout:** 3000ms
- **Retry:** 2 attempts with exponential backoff
- **Caching:** Enabled (5 minute TTL)
- **Model:** local-7b-quantised (fallback: local-3b-quantised)

## Usage Example

```yaml
input:
  current_scene:
    title: "Opening Monologue"
    setting: "A dimly lit room"
    mood: "tense"
  dialogue_context: []
```

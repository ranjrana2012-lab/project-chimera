# Lighting Control Skill

Controls DMX/OSC stage lighting with human approval gates for scene changes.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| action | string | Yes | set_scene, blackout, get_status |
| name | string | No | Scene name |
| channels | object | No | DMX channel values |
| osc_address | string | No | OSC address |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Action success |
| scene | string | Applied scene name |
| action | string | Completed action |
| current_state | object | DMX state |

## Configuration

- **Timeout:** 200ms
- **Retry:** 3 attempts with exponential backoff
- **Caching:** Disabled
- **Approval Gates:** Scene changes require operator approval

## Usage Example

```yaml
input:
  action: set_scene
  name: "Scene 1 - Opening"
  channels:
    1: 255
    2: 128
    3: 64
```

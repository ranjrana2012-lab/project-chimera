# Safety Filter Skill

Multi-layer content moderation with pattern matching, ML classification, and rule engine.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | Content to filter |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| decision | string | allow, block, flag |
| category | string | safe, blocked, flagged |
| confidence | float | Decision confidence |
| details | object | Layer results |

## Configuration

- **Timeout:** 200ms
- **Retry:** 1 attempt
- **Caching:** Enabled (1 hour TTL)
- **Layers:** Pattern matcher, Classifier, Rule engine

## Usage Example

```yaml
input:
  content: "The stage lights dimmed slowly."
```

**Output:**
```yaml
output:
  decision: allow
  category: safe
  confidence: 0.95
```

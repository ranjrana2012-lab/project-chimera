# BSL Text2Gloss Skill

Translates English text to BSL gloss notation for sign language interpretation.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | English text to translate |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| gloss | string | BSL gloss notation |
| breakdown | array | Individual gloss signs |
| language | string | Target language (bsl) |
| confidence | float | Confidence score |

## Configuration

- **Timeout:** 2000ms
- **Retry:** 2 attempts with exponential backoff
- **Caching:** Enabled (5 minute TTL)

## Usage Example

```yaml
input:
  text: "Hello, my name is John"
```

**Output:**
```yaml
output:
  gloss: "HELLO MY NAME JOHN"
  breakdown: ["HELLO", "MY", "NAME", "JOHN"]
  language: "bsl"
  confidence: 0.88
```

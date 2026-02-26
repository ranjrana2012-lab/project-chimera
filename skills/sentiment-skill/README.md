# Sentiment Skill

Analyzes audience sentiment from social media and sensor data.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | No* | Single text to analyze |
| texts | array | No* | Multiple texts for batch |

*Either text or texts must be provided

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| sentiment | string | positive/negative/neutral |
| confidence | float | Confidence score |
| emotions | object | Emotion breakdown |
| intensity | float | Sentiment intensity (batch) |

## Configuration

- **Timeout:** 500ms
- **Retry:** 1 attempt
- **Caching:** Enabled (30 second TTL)
- **Model:** cardiffnlp/twitter-roberta-base-sentiment

## Usage Example

```yaml
input:
  texts:
    - "This is amazing!"
    - "Great performance!"
```

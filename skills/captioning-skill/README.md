# Captioning Skill

Converts audio to text captions with accessibility descriptions using OpenAI Whisper.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| audio_data | string | Yes | Base64-encoded audio |
| language | string | No | Language code (default: en) |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| text | string | Transcribed text |
| language | string | Detected language |
| confidence | float | Confidence score |
| timestamp | string | ISO 8601 timestamp |

## Configuration

- **Timeout:** 1500ms
- **Retry:** 1 attempt
- **Caching:** Disabled
- **Model:** Whisper (base)

## Usage Example

```yaml
input:
  audio_data: "UklGRjIAAABXQVZFZm10IBIA..."
  language: "en"
```

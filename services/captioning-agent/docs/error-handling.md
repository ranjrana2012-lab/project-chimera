# Captioning Agent - Error Handling Specification

**Version:** 1.0.0
**Date:** 2026-03-03
**Service:** Captioning Agent (Port 8002)
**Status:** Design Document

---

## Overview

This document defines all error scenarios for the Captioning Agent and specifies handling strategies for each. The Captioning Agent provides real-time speech-to-text transcription using OpenAI Whisper API with WebSocket streaming for live caption updates.

---

## Error Categories

### 1. API/Network Errors (Whisper API)

#### 1.1 Connection Timeout
**Description:** Unable to establish connection to Whisper API within timeout period.

**Detection:**
- `requests.exceptions.Timeout` or `httpx.TimeoutException`
- Connection timeout > 30 seconds

**Handling Strategy:**
- Log error with severity WARNING
- Return cached transcription if available (same audio hash)
- Return placeholder transcription: "[Transcription unavailable - connection timeout]"
- Increment metric: `captioning_timeout_total`
- **Do NOT crash** - return 200 with error flag

```python
# Response format on error
{
    "request_id": "req_123",
    "text": "[Transcription unavailable - connection timeout]",
    "language": "en",
    "duration": 0.0,
    "confidence": 0.0,
    "processing_time_ms": 30000,
    "model_version": "whisper-1",
    "error": {
        "code": "TIMEOUT",
        "message": "Connection to Whisper API timed out",
        "retryable": True
    }
}
```

#### 1.2 HTTP 500 Internal Server Error (Whisper API)
**Description:** Whisper API returns 500 error.

**Detection:**
- HTTP status code 500
- Response body indicates server error

**Handling Strategy:**
- Log error with severity ERROR
- Implement exponential backoff retry (max 3 retries):
  - Retry 1: 1 second delay
  - Retry 2: 2 seconds delay
  - Retry 3: 4 seconds delay
- If all retries fail, return cached transcription or placeholder
- Increment metric: `captioning_whisper_error_total`

#### 1.3 HTTP 429 Rate Limit Error
**Description:** Whisper API rate limit exceeded.

**Detection:**
- HTTP status code 429
- `Retry-After` header present

**Handling Strategy:**
- Log error with severity WARNING
- Extract `Retry-After` header value
- Queue request for retry after delay
- Return 202 Accepted with `Retry-After` header to client
- Increment metric: `captioning_rate_limited_total`

```python
# Response format for rate limit
{
    "request_id": "req_123",
    "status": "queued",
    "retry_after": 60,
    "message": "Request queued due to rate limit, please retry"
}
```

#### 1.4 HTTP 401 Unauthorized
**Description:** Invalid API key for Whisper.

**Detection:**
- HTTP status code 401
- Authentication error in response

**Handling Strategy:**
- Log error with severity CRITICAL
- **Immediately alert** via monitoring system
- Return 503 Service Unavailable to client
- Do NOT retry (configuration issue)
- Increment metric: `captioning_auth_error_total`

---

### 2. Audio Processing Errors

#### 2.1 Invalid Audio Format
**Description:** Uploaded audio is not supported format.

**Detection:**
- File extension not in [mp3, wav, m4a, ogg, flac]
- MIME type not audio/*
- FFmpeg probe fails

**Handling Strategy:**
- Log error with severity INFO
- Return 400 Bad Request with clear error message
- Specify supported formats in response
- Increment metric: `captioning_invalid_format_total`

```python
# Response format
{
    "error": {
        "code": "INVALID_AUDIO_FORMAT",
        "message": "Unsupported audio format. Supported: mp3, wav, m4a, ogg, flac",
        "supported_formats": ["mp3", "wav", "m4a", "ogg", "flac"]
    }
}
```

#### 2.2 Audio File Too Large
**Description:** Audio file exceeds size limit (25MB default).

**Detection:**
- Content-Length header > 25MB
- File size after upload > 25MB

**Handling Strategy:**
- Log error with severity INFO
- Return 413 Payload Too Large
- Suggest chunking or compression
- Increment metric: `captioning_file_too_large_total`

#### 2.3 Audio Duration Too Long
**Description:** Audio exceeds max duration (10 minutes default).

**Detection:**
- FFmpeg probe shows duration > 600 seconds

**Handling Strategy:**
- Log error with severity WARNING
- Return 400 Bad Request
- Suggest splitting audio into chunks
- Increment metric: `captioning_duration_exceeded_total`

#### 2.4 Corrupt Audio File
**Description:** Audio file is corrupted or unreadable.

**Detection:**
- FFmpeg fails to parse
- Wave file has invalid headers
- Duration cannot be determined

**Handling Strategy:**
- Log error with severity WARNING
- Return 422 Unprocessable Entity
- Include FFmpeg error details
- Suggest re-encoding audio
- Increment metric: `captioning_corrupt_audio_total`

---

### 3. Transcription Processing Errors

#### 3.1 Empty Transcription Result
**Description:** Whisper returns empty transcription (silence or no speech detected).

**Detection:**
- Whisper response `text` field is empty string
- All segments have low confidence

**Handling Strategy:**
- Log with severity DEBUG (not an error, just silence)
- Return empty transcription with confidence 0.0
- Include language detected
- Increment metric: `captioning_empty_result_total`

```python
# Response format
{
    "request_id": "req_123",
    "text": "",
    "language": "en",
    "duration": 5.2,
    "confidence": 0.0,
    "processing_time_ms": 1500,
    "model_version": "whisper-1",
    "warning": {
        "code": "NO_SPEECH_DETECTED",
        "message": "No speech detected in audio"
    }
}
```

#### 3.2 Low Confidence Transcription
**Description:** Transcription has low confidence score (< 0.5).

**Detection:**
- Average confidence score < 0.5
- More than 50% of segments below threshold

**Handling Strategy:**
- Log with severity INFO
- Return transcription with warning flag
- Include confidence score in response
- Increment metric: `captioning_low_confidence_total`

```python
# Response format
{
    "request_id": "req_123",
    "text": "Hello world",
    "language": "en",
    "duration": 2.5,
    "confidence": 0.35,
    "processing_time_ms": 1200,
    "model_version": "whisper-1",
    "warning": {
        "code": "LOW_CONFIDENCE",
        "message": "Transcription confidence is low (0.35), manual review recommended"
    }
}
```

#### 3.3 Language Detection Failure
**Description:** Unable to detect language from audio.

**Detection:**
- Whisper language detection fails
- Confidence for all languages < 0.3

**Handling Strategy:**
- Log with severity WARNING
- Default to English (en) with warning
- Return transcription with language_code="unknown"
- Increment metric: `captioning_language_detection_failed_total`

---

### 4. WebSocket Streaming Errors

#### 4.1 WebSocket Connection Drop
**Description:** Client disconnects during streaming.

**Detection:**
- WebSocket connection closed unexpectedly
- Heartbeat timeout

**Handling Strategy:**
- Log with severity INFO
- Clean up resources (audio buffer, partial transcription)
- Mark session as incomplete in Redis
- Increment metric: `captioning_websocket_disconnect_total`

#### 4.2 Audio Buffer Overflow
**Description:** Audio received faster than processing.

**Detection:**
- Buffer size exceeds threshold (10 seconds)
- Memory usage spike

**Handling Strategy:**
- Log with severity WARNING
- Start dropping oldest audio chunks (circular buffer)
- Send warning to client via WebSocket
- Increment metric: `captioning_buffer_overflow_total`

```python
# WebSocket warning message
{
    "type": "warning",
    "code": "BUFFER_OVERFLOW",
    "message": "Audio buffer full, dropping oldest chunks"
}
```

#### 4.3 Slow Consumer Detection
**Description:** Client not consuming WebSocket messages fast enough.

**Detection:**
- WebSocket send buffer full
- Message queue > 100 messages

**Handling Strategy:**
- Log with severity WARNING
- Send partial updates (throttle)
- Suggest client to process faster
- Increment metric: `captioning_slow_consumer_total`

---

### 5. Internal Service Errors

#### 5.1 Redis Connection Failure
**Description:** Cannot connect to Redis for caching/state.

**Detection:**
- `redis.exceptions.ConnectionError`
- Health check to Redis fails

**Handling Strategy:**
- Log with severity ERROR
- **Continue in degraded mode** (no caching)
- Return 200 but with `degraded=true` flag
- Alert operations team
- Increment metric: `captioning_redis_error_total`

```python
# Degraded mode response header
X-Service-Degraded: true
X-Disabled-Features: caching
```

#### 5.2 Out of Memory
**Description:** Service memory limit exceeded.

**Detection:**
- `MemoryError` exception
- Container OOM kill imminent

**Handling Strategy:**
- Log with severity CRITICAL
- **Immediately reject new requests** with 503
- Complete in-progress requests if possible
- Trigger container restart
- Increment metric: `captioning_oom_total`

#### 5.3 Unexpected Exception
**Description:** Any unhandled exception.

**Detection:**
- Generic `Exception` catch

**Handling Strategy:**
- Log full stack trace with severity ERROR
- Return 500 Internal Server Error
- Include safe error message (no stack trace to client)
- Increment metric: `captioning_unexpected_error_total`

```python
# Response format
{
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred. Please try again.",
        "request_id": "req_123"
    }
}
```

---

## Error Recovery Matrix

| Error Type | Retry | Cache Fallback | Return Error | Alert |
|------------|-------|----------------|--------------|-------|
| Connection Timeout | ✅ Yes (3x) | ✅ Yes | Placeholder | Warning |
| HTTP 500 | ✅ Yes (3x) | ✅ Yes | Placeholder | Warning |
| HTTP 429 | ⏳ Queued | ❌ No | 202 Queued | Info |
| HTTP 401 | ❌ No | ❌ No | 503 Unavailable | Critical |
| Invalid Format | ❌ No | ❌ No | 400 Bad Request | None |
| File Too Large | ❌ No | ❌ No | 413 Too Large | None |
| Corrupt Audio | ❌ No | ❌ No | 422 Unprocessable | None |
| Empty Result | ❌ No | N/A | Empty with warning | None |
| Low Confidence | ❌ No | N/A | Result with warning | Info |
| Redis Down | ❌ No | N/A | Degraded mode | Error |
| OOM | ❌ No | N/A | 503 Unavailable | Critical |

---

## Circuit Breaker Configuration

For cascading error scenarios (repeated Whisper API failures):

**Closed State (Normal):**
- All requests go through
- Track error rate

**Open State (Failing):**
- Triggered after 5 consecutive errors OR 50% error rate over 1 minute
- Block all new requests for 30 seconds
- Return cached results or placeholders
- Alert operations

**Half-Open State (Recovering):**
- After 30 seconds, allow 1 test request
- If successful, return to Closed
- If failed, remain Open for another 30 seconds

---

## Metrics to Track

All errors should increment Prometheus counters:

```python
from prometheus_client import Counter

captioning_errors_total = Counter(
    'captioning_errors_total',
    'Total captioning errors',
    ['error_type', 'severity']
)

captioning_timeout_total = Counter(
    'captioning_timeout_total',
    'Connection timeout errors',
    ['endpoint']
)

captioning_degraded_mode = Gauge(
    'captioning_degraded_mode',
    'Service in degraded mode (1=yes, 0=no)'
)
```

---

## Testing Requirements

Each error scenario must have:

1. **Unit Test:** Verify error detection and handling
2. **Integration Test:** Test with real Whisper API failures (mocked)
3. **Load Test:** Verify graceful degradation under load

Example test structure:
```python
def test_whisper_timeout_returns_cached_transcription():
    # Given: Whisper API times out
    with patch('captioning.core.transcription.whisper', side_effect=Timeout()):
        # When: Request is made
        response = transcribe_audio(test_audio)
        # Then: Returns cached transcription or placeholder
        assert response.status_code == 200
        assert response.json()['error']['code'] == 'TIMEOUT'
```

---

**Status:** ✅ Ready for Implementation
**Next Step:** Task 1.1.2 - Implement Whisper API failure fallback logic

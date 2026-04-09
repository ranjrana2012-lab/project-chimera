# Project Chimera Phase 2 - API Examples and Tutorials

**Version:** 1.0.0
**Last Updated:** April 9, 2026

---

## Overview

This guide provides comprehensive examples and tutorials for using all Phase 2 service APIs. Each service includes practical examples from basic operations to advanced use cases.

---

## Table of Contents

1. [DMX Controller API Examples](#dmx-controller-api-examples)
2. [Audio Controller API Examples](#audio-controller-api-examples)
3. [BSL Avatar Service API Examples](#bsl-avatar-service-api-examples)
4. [Integration Examples](#integration-examples)
5. [Best Practices](#best-practices)

---

## DMX Controller API Examples

### Getting Started

**Base URL:** `http://localhost:8001`

**Health Check:**
```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "dmx-controller",
  "universe": 1,
  "active_fixtures": 3
}
```

### Basic Operations

#### 1. Get Service Status

```bash
curl http://localhost:8001/api/status
```

**Response:**
```json
{
  "service": "dmx-controller",
  "state": "running",
  "universe": 1,
  "refresh_rate": 44,
  "fixture_count": 3,
  "scene_count": 2,
  "current_scene": null
}
```

#### 2. List All Fixtures

```bash
curl http://localhost:8001/api/fixtures
```

**Response:**
```json
{
  "fixtures": [
    {
      "id": "mh_1",
      "name": "Moving Head 1",
      "start_address": 1,
      "channel_count": 6,
      "channels": {
        "1": {"value": 128, "type": "intensity"},
        "2": {"value": 0, "type": "pan"},
        "3": {"value": 0, "type": "tilt"}
      }
    }
  ]
}
```

#### 3. Get Fixture Details

```bash
curl http://localhost:8001/api/fixtures/mh_1
```

#### 4. Set Fixture Channel

```bash
curl -X POST http://localhost:8001/api/fixtures/mh_1/channels/1 \
  -H "Content-Type: application/json" \
  -d '{"value": 255}'
```

**Response:**
```json
{
  "success": true,
  "fixture_id": "mh_1",
  "channel": 1,
  "value": 255,
  "previous_value": 128
}
```

#### 5. Set Multiple Channels

```bash
curl -X POST http://localhost:8001/api/fixtures/mh_1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channels": {
      "1": 255,
      "4": 255,
      "5": 0,
      "6": 0
    }
  }'
```

### Scene Management

#### 6. Create a Scene

```bash
curl -X POST http://localhost:8001/api/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "red_alert",
    "fixture_values": {
      "mh_1": {
        "1": 255,
        "4": 255,
        "5": 0,
        "6": 0
      },
      "mh_2": {
        "1": 200,
        "4": 255,
        "5": 50,
        "6": 0
      }
    },
    "transition_time_ms": 2000
  }'
```

**Response:**
```json
{
  "success": true,
  "scene_name": "red_alert",
  "fixtures_affected": 2,
  "transition_time_ms": 2000
}
```

#### 7. List All Scenes

```bash
curl http://localhost:8001/api/scenes
```

#### 8. Activate a Scene

```bash
curl -X POST http://localhost:8001/api/scenes/red_alert/activate
```

#### 9. Delete a Scene

```bash
curl -X DELETE http://localhost:8001/api/scenes/red_alert
```

### Emergency Procedures

#### 10. Emergency Stop (Instant Blackout)

```bash
curl -X POST http://localhost:8001/api/emergency_stop
```

**Response:**
```json
{
  "success": true,
  "action": "emergency_stop",
  "timestamp": "2026-04-09T12:00:00Z",
  "all_channels_set_to": 0
}
```

⚠️ **WARNING:** This will immediately blackout all fixtures. Use only in emergencies.

#### 11. Reset from Emergency

```bash
curl -X POST http://localhost:8001/api/reset_emergency
```

### Python Client Example

```python
import requests
from typing import Dict, Any

class DMXClient:
    """Client for DMX Controller API."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        response = requests.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()

    def set_channel(self, fixture_id: str, channel: int, value: int) -> Dict[str, Any]:
        """Set single channel value."""
        response = requests.post(
            f"{self.base_url}/api/fixtures/{fixture_id}/channels/{channel}",
            json={"value": value}
        )
        response.raise_for_status()
        return response.json()

    def create_scene(
        self,
        name: str,
        fixture_values: Dict[str, Dict[int, int]],
        transition_time_ms: int = 1000
    ) -> Dict[str, Any]:
        """Create a new scene."""
        response = requests.post(
            f"{self.base_url}/api/scenes",
            json={
                "name": name,
                "fixture_values": fixture_values,
                "transition_time_ms": transition_time_ms
            }
        )
        response.raise_for_status()
        return response.json()

    def activate_scene(self, scene_name: str) -> Dict[str, Any]:
        """Activate a scene."""
        response = requests.post(
            f"{self.base_url}/api/scenes/{scene_name}/activate"
        )
        response.raise_for_status()
        return response.json()

    def emergency_stop(self) -> Dict[str, Any]:
        """Activate emergency stop."""
        response = requests.post(f"{self.base_url}/api/emergency_stop")
        response.raise_for_status()
        return response.json()

# Usage example
client = DMXClient()

# Get status
status = client.get_status()
print(f"Service state: {status['state']}")
print(f"Fixtures: {status['fixture_count']}")

# Create a scene
client.create_scene(
    "warm_welcome",
    {
        "mh_1": {1: 200, 4: 255, 5: 200, 6: 100},
        "mh_2": {1: 180, 4: 255, 5: 180, 6: 80}
    },
    transition_time_ms=3000
)

# Activate scene
client.activate_scene("warm_welcome")
```

---

## Audio Controller API Examples

### Getting Started

**Base URL:** `http://localhost:8002`

**Health Check:**
```bash
curl http://localhost:8002/health
```

### Basic Operations

#### 1. Get Service Status

```bash
curl http://localhost:8002/api/status
```

**Response:**
```json
{
  "service": "audio-controller",
  "state": "running",
  "track_count": 5,
  "playing_tracks": 2,
  "muted_tracks": 1,
  "master_volume_db": -6.0
}
```

#### 2. List All Tracks

```bash
curl http://localhost:8002/api/tracks
```

**Response:**
```json
{
  "tracks": [
    {
      "id": "bgm_1",
      "name": "Background Music 1",
      "volume_db": -12.0,
      "is_playing": true,
      "is_muted": false
    },
    {
      "id": "sfx_1",
      "name": "Sound Effect 1",
      "volume_db": -6.0,
      "is_playing": false,
      "is_muted": false
    }
  ]
}
```

#### 3. Play a Track

```bash
curl -X POST http://localhost:8002/api/tracks/bgm_1/play
```

**Response:**
```json
{
  "success": true,
  "track_id": "bgm_1",
  "action": "play",
  "previous_state": "stopped"
}
```

#### 4. Stop a Track

```bash
curl -X POST http://localhost:8002/api/tracks/bgm_1/stop
```

#### 5. Pause a Track

```bash
curl -X POST http://localhost:8002/api/tracks/bgm_1/pause
```

### Volume Control

#### 6. Get Master Volume

```bash
curl http://localhost:8002/api/volume/master
```

**Response:**
```json
{
  "volume_db": -6.0,
  "max_volume_db": -6.0,
  "min_volume_db": -60.0
}
```

#### 7. Set Master Volume

```bash
curl -X POST http://localhost:8002/api/volume/master \
  -H "Content-Type: application/json" \
  -d '{"volume_db": -12}'
```

**Response:**
```json
{
  "success": true,
  "previous_volume_db": -6.0,
  "new_volume_db": -12.0
}
```

#### 8. Set Track Volume

```bash
curl -X POST http://localhost:8002/api/tracks/bgm_1/volume \
  -H "Content-Type: application/json" \
  -d '{"volume_db": -18}'
```

#### 9. Mute a Track

```bash
curl -X POST http://localhost:8002/api/tracks/bgm_1/mute
```

#### 10. Unmute a Track

```bash
curl -X POST http://localhost:8002/api/tracks/bgm_1/unmute
```

### Emergency Procedures

#### 11. Emergency Mute (All Audio)

```bash
curl -X POST http://localhost:8002/api/emergency_mute
```

**Response:**
```json
{
  "success": true,
  "action": "emergency_mute",
  "timestamp": "2026-04-09T12:00:00Z",
  "affected_tracks": 5
}
```

⚠️ **WARNING:** This will immediately mute all audio. Use only in emergencies.

#### 12. Reset from Emergency Mute

```bash
curl -X POST http://localhost:8002/api/reset_emergency
```

### Python Client Example

```python
import requests
from typing import Dict, Any, List

class AudioClient:
    """Client for Audio Controller API."""

    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        response = requests.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()

    def list_tracks(self) -> List[Dict[str, Any]]:
        """List all tracks."""
        response = requests.get(f"{self.base_url}/api/tracks")
        response.raise_for_status()
        return response.json()["tracks"]

    def play_track(self, track_id: str) -> Dict[str, Any]:
        """Play a track."""
        response = requests.post(f"{self.base_url}/api/tracks/{track_id}/play")
        response.raise_for_status()
        return response.json()

    def set_master_volume(self, volume_db: float) -> Dict[str, Any]:
        """Set master volume."""
        response = requests.post(
            f"{self.base_url}/api/volume/master",
            json={"volume_db": volume_db}
        )
        response.raise_for_status()
        return response.json()

    def set_track_volume(
        self,
        track_id: str,
        volume_db: float
    ) -> Dict[str, Any]:
        """Set track volume."""
        response = requests.post(
            f"{self.base_url}/api/tracks/{track_id}/volume",
            json={"volume_db": volume_db}
        )
        response.raise_for_status()
        return response.json()

    def emergency_mute(self) -> Dict[str, Any]:
        """Activate emergency mute."""
        response = requests.post(f"{self.base_url}/api/emergency_mute")
        response.raise_for_status()
        return response.json()

# Usage example
client = AudioClient()

# Get status
status = client.get_status()
print(f"Playing: {status['playing_tracks']} tracks")

# Play background music
client.play_track("bgm_1")

# Set volume
client.set_master_volume(-12.0)
client.set_track_volume("bgm_1", -18.0)

# Mute if needed
client.emergency_mute()
```

---

## BSL Avatar Service API Examples

### Getting Started

**Base URL:** `http://localhost:8003`

**Health Check:**
```bash
curl http://localhost:8003/health
```

### Basic Operations

#### 1. Get Service Status

```bash
curl http://localhost:8003/api/status
```

**Response:**
```json
{
  "service": "bsl-avatar-service",
  "state": "running",
  "gesture_library_size": 150,
  "supported_features": ["translation", "fingerspelling", "avatar_rendering"]
}
```

#### 2. List Available Gestures

```bash
curl http://localhost:8003/api/gestures
```

**Response:**
```json
{
  "gestures": [
    {
      "id": "hello",
      "name": "Hello",
      "category": "greeting",
      "complexity": "beginner"
    },
    {
      "id": "thank_you",
      "name": "Thank You",
      "category": "courtesy",
      "complexity": "beginner"
    }
  ],
  "total": 150
}
```

#### 3. Translate Text to BSL

```bash
curl -X POST http://localhost:8003/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, thank you for coming"}'
```

**Response:**
```json
{
  "success": true,
  "original_text": "Hello, thank you for coming",
  "translation": {
    "gestures": [
      {"word": "hello", "gesture_id": "hello", "from_library": true},
      {"word": "thank", "gesture_id": "thank_you", "from_library": true},
      {"word": "you", "gesture_id": "you", "from_library": true},
      {"word": "for", "gesture_id": "for", "from_library": true},
      {"word": "coming", "gesture_id": "come", "from_library": true}
    ],
    "fingerspelled": [],
    "total_gestures": 5,
    "library_hit_rate": 1.0
  },
  "rendering_time_ms": 150
}
```

#### 4. Get Gesture Details

```bash
curl http://localhost:8003/api/gestures/hello
```

**Response:**
```json
{
  "id": "hello",
  "name": "Hello",
  "category": "greeting",
  "complexity": "beginner",
  "description": "Standard BSL greeting gesture",
  "hand_shape": "open_hand",
  "movement": "wave",
  "non_manual_features": {
    "facial_expression": "smile",
    "body_language": "forward_lean"
  }
}
```

#### 5. Render Avatar Animation

```bash
curl -X POST http://localhost:8003/api/render \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello",
    "render_options": {
      "quality": "high",
      "include_non_manual": true,
      "animation_speed": 1.0
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "animation": {
    "duration_ms": 2000,
    "frames": 60,
    "format": "json",
    "data": [...]
  },
  "gestures_used": ["hello"]
}
```

### Advanced Features

#### 6. Batch Translation

```bash
curl -X POST http://localhost:8003/api/translate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Hello",
      "Thank you",
      "Goodbye"
    ]
  }'
```

#### 7. Search Gestures

```bash
curl "http://localhost:8003/api/gestures/search?category=greeting&complexity=beginner"
```

#### 8. Get Translation Statistics

```bash
curl http://localhost:8003/api/stats
```

**Response:**
```json
{
  "total_translations": 1500,
  "gestures_from_library": 1200,
  "fingerspelled_words": 300,
  "average_rendering_time_ms": 145,
  "library_hit_rate": 0.8
}
```

### Python Client Example

```python
import requests
from typing import Dict, Any, List

class BSLClient:
    """Client for BSL Avatar Service API."""

    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        response = requests.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()

    def list_gestures(self) -> List[Dict[str, Any]]:
        """List all available gestures."""
        response = requests.get(f"{self.base_url}/api/gestures")
        response.raise_for_status()
        return response.json()["gestures"]

    def translate(self, text: str) -> Dict[str, Any]:
        """Translate text to BSL gestures."""
        response = requests.post(
            f"{self.base_url}/api/translate",
            json={"text": text}
        )
        response.raise_for_status()
        return response.json()

    def render_avatar(
        self,
        text: str,
        quality: str = "high",
        include_non_manual: bool = True
    ) -> Dict[str, Any]:
        """Render avatar animation."""
        response = requests.post(
            f"{self.base_url}/api/render",
            json={
                "text": text,
                "render_options": {
                    "quality": quality,
                    "include_non_manual": include_non_manual
                }
            }
        )
        response.raise_for_status()
        return response.json()

    def get_gesture(self, gesture_id: str) -> Dict[str, Any]:
        """Get gesture details."""
        response = requests.get(f"{self.base_url}/api/gestures/{gesture_id}")
        response.raise_for_status()
        return response.json()

# Usage example
client = BSLClient()

# Get status
status = client.get_status()
print(f"Gesture library size: {status['gesture_library_size']}")

# Translate text
result = client.translate("Hello, welcome to the show")
print(f"Translation used {len(result['translation']['gestures'])} gestures")
print(f"Library hit rate: {result['translation']['library_hit_rate']}")

# Render avatar
animation = client.render_avatar("Hello")
print(f"Animation duration: {animation['animation']['duration_ms']}ms")
```

---

## Integration Examples

### Coordinated Show Control

This example shows how to coordinate all three services for a theatrical moment.

```python
import requests
import time
from typing import Dict, Any

class ShowController:
    """Coordinated control of all Phase 2 services."""

    def __init__(self):
        self.dmx_url = "http://localhost:8001"
        self.audio_url = "http://localhost:8002"
        self.bsl_url = "http://localhost:8003"

    def dramatic_entrance(self):
        """Execute a dramatic entrance sequence."""
        print("🎭 Starting dramatic entrance sequence...")

        # 1. Fade in lights (DMX)
        print("Setting lighting...")
        requests.post(
            f"{self.dmx_url}/api/scenes/dramatic_entrance/activate"
        )

        # 2. Start music (Audio)
        print("Starting audio...")
        requests.post(f"{self.audio_url}/api/tracks/dramatic_theme/play")
        requests.post(
            f"{self.audio_url}/api/volume/master",
            json={"volume_db": -12}
        )

        # 3. Display welcome message (BSL)
        print("Translating to BSL...")
        bsl_result = requests.post(
            f"{self.bsl_url}/api/translate",
            json={"text": "Welcome to our show"}
        ).json()

        print(f"✅ Sequence complete! Used {len(bsl_result['translation']['gestures'])} gestures")

    def emergency_shutdown(self):
        """Emergency shutdown of all systems."""
        print("🚨 EMERGENCY SHUTDOWN INITIATED")

        # Emergency stop all services
        requests.post(f"{self.dmx_url}/api/emergency_stop")
        requests.post(f"{self.audio_url}/api/emergency_mute")

        print("✅ All systems stopped safely")

    def create_scene(
        self,
        name: str,
        lighting: Dict[str, Dict[int, int]],
        audio_track: str,
        bsl_text: str
    ):
        """Create a complete scene with all services."""
        print(f"Creating scene: {name}")

        # Create DMX scene
        requests.post(
            f"{self.dmx_url}/api/scenes",
            json={
                "name": name,
                "fixture_values": lighting,
                "transition_time_ms": 2000
            }
        )

        # Prepare audio (don't play yet)
        requests.post(f"{self.audio_url}/api/tracks/{audio_track}/stop")

        # Pre-translate BSL
        requests.post(f"{self.bsl_url}/api/translate", json={"text": bsl_text})

        print(f"✅ Scene '{name}' ready")

# Usage
controller = ShowController()

# Create a scene
controller.create_scene(
    "opening_scene",
    lighting={
        "mh_1": {1: 200, 4: 255, 5: 200, 6: 100},
        "mh_2": {1: 180, 4: 255, 5: 180, 6: 80}
    },
    audio_track="opening_theme",
    bsl_text="Welcome to Project Chimera"
)

# Execute the scene
controller.dramatic_entrance()
```

### Async Integration Example

```python
import asyncio
import aiohttp
from typing import Dict, Any

class AsyncShowController:
    """Async controller for coordinated service operations."""

    def __init__(self):
        self.dmx_url = "http://localhost:8001"
        self.audio_url = "http://localhost:8002"
        self.bsl_url = "http://localhost:8003"

    async def coordinated_scene_change(
        self,
        scene_name: str,
        audio_track: str,
        bsl_message: str
    ):
        """Change all services simultaneously."""
        async with aiohttp.ClientSession() as session:
            # Execute all changes in parallel
            tasks = [
                self._activate_dmx_scene(session, scene_name),
                self._play_audio_track(session, audio_track),
                self._translate_bsl(session, bsl_message)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ Task {i} failed: {result}")
                else:
                    print(f"✅ Task {i} succeeded")

    async def _activate_dmx_scene(self, session, scene_name: str):
        """Activate DMX scene."""
        url = f"{self.dmx_url}/api/scenes/{scene_name}/activate"
        async with session.post(url) as response:
            return await response.json()

    async def _play_audio_track(self, session, track_id: str):
        """Play audio track."""
        url = f"{self.audio_url}/api/tracks/{track_id}/play"
        async with session.post(url) as response:
            return await response.json()

    async def _translate_bsl(self, session, text: str):
        """Translate text to BSL."""
        url = f"{self.bsl_url}/api/translate"
        async with session.post(url, json={"text": text}) as response:
            return await response.json()

# Usage
async def main():
    controller = AsyncShowController()
    await controller.coordinated_scene_change(
        "scene_1",
        "background_music",
        "Hello and welcome"
    )

asyncio.run(main())
```

---

## Best Practices

### 1. Error Handling

Always handle API errors gracefully:

```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post(
        "http://localhost:8001/api/scenes",
        json={"name": "test", "fixture_values": {}},
        timeout=5  # Always set timeout
    )
    response.raise_for_status()
    result = response.json()
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.ConnectionError:
    print("Connection failed")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except RequestException as e:
    print(f"Request failed: {e}")
```

### 2. Retry Logic

Implement retry logic for transient failures:

```python
import time
from typing import Callable

def retry_request(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 0.5
):
    """Retry request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor * (2 ** attempt)
            print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)

# Usage
response = retry_request(
    lambda: requests.post("http://localhost:8001/api/scenes", json={...})
)
```

### 3. Rate Limiting

Respect rate limits:

```python
import time
from typing import List

def batch_requests(urls: List[str], delay: float = 0.1):
    """Send requests with delay between each."""
    results = []
    for url in urls:
        response = requests.get(url)
        results.append(response)
        time.sleep(delay)  # Delay between requests
    return results
```

### 4. Health Checks

Always check service health before operations:

```python
def check_service_health(base_url: str) -> bool:
    """Check if service is healthy."""
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        return response.status_code == 200
    except RequestException:
        return False

# Usage
if check_service_health("http://localhost:8001"):
    # Service is healthy, proceed
    pass
else:
    # Service is down, handle error
    print("DMX Controller is not healthy!")
```

### 5. Monitoring Response Times

Track API performance:

```python
import time
from functools import wraps

def timed_request(func):
    """Decorator to time API requests."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper

@timed_request
def activate_scene(scene_name: str):
    return requests.post(f"http://localhost:8001/api/scenes/{scene_name}/activate")
```

---

## Troubleshooting

### Common Issues

**1. Connection Refused**
```bash
# Check if service is running
curl http://localhost:8001/health

# Start service if needed
docker-compose -f services/docker-compose.phase2.yml up -d
```

**2. Timeout Errors**
```bash
# Increase timeout
curl --max-time 30 http://localhost:8001/api/status
```

**3. Invalid JSON**
```bash
# Validate JSON before sending
echo '{"name": "test"}' | jq .
```

**4. Emergency Stop Active**
```bash
# Reset from emergency state
curl -X POST http://localhost:8001/api/reset_emergency
```

---

**Document Version:** 1.0.0
**Last Updated:** April 9, 2026

For more information, see:
- Service-specific READMEs in `services/*/README.md`
- Security documentation: `docs/SECURITY_DOCUMENTATION.md`
- Deployment guide: `docs/DEPLOYMENT_AND_OPERATIONS_GUIDE.md`

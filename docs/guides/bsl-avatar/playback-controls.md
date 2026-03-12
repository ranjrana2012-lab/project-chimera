# BSL Avatar Playback Controls

Learn how to control BSL avatar playback using the enhanced avatar viewer.

## Accessing the Avatar Viewer

Navigate to:
- **Production**: `http://localhost:8007/static/avatar-enhanced.html`
- **Development**: `http://localhost:8003/static/avatar-enhanced.html`

The enhanced viewer provides full playback controls for the BSL avatar.

## Basic Playback Controls

### Play

- **Button**: Play button (▶ icon) or press **Spacebar**
- **API**: `POST /api/avatar/play` with animation data
- **JavaScript**: `avatarViewer.playAnimation('animation_name')`

**Example:**
```javascript
// Play a specific animation
avatarViewer.playAnimation('phrase_hello');
```

### Pause

- **Button**: Pause button (⏸ icon) or press **Spacebar**
- **JavaScript**: `avatarViewer.pauseAnimation()`

Pause temporarily stops the animation at the current frame.

### Stop

- **Button**: Stop button (⏹ icon) or press **Esc**
- **JavaScript**: `avatarViewer.stopAnimation()`

Stop resets the animation to the beginning and clears the current action.

## Playback Speed

Control playback speed using speed buttons or slider:

| Speed | Description | Use Case |
|-------|-------------|----------|
| 0.25x | Quarter speed | Detailed observation of handshapes |
| 0.5x | Half speed | Learning specific gestures |
| 1x | Normal speed | Standard playback |
| 1.5x | 1.5x speed | Faster review |
| 2x | Double speed | Quick preview |

**API:** Set `speed` parameter in request body

**JavaScript:**
```javascript
avatarViewer.setPlaybackSpeed(1.5); // 1.5x speed
avatarViewer.setPlaybackSpeed(0.5); // Half speed
```

## Frame-by-Frame Navigation

### Step Forward

Moves forward one frame (at 30 FPS, that's ~33ms).

- **Button**: Step forward button (⏭)
- **Keyboard**: → (right arrow)
- **JavaScript**: `avatarViewer.stepForward()`

### Step Backward

Moves backward one frame.

- **Button**: Step backward button (⏮)
- **Keyboard**: ← (left arrow)
- **JavaScript**: `avatarViewer.stepBackward()`

Frame-by-frame navigation is useful for:
- Analyzing specific handshapes
- Checking transition smoothness
- Learning BSL finger spelling

## Timeline Scrubbing

Drag the timeline scrubber to jump to any point in the animation.

- **UI**: Click and drag on timeline bar
- **API**: `POST /api/avatar/seek` with `time` parameter
- **JavaScript**: `avatarViewer.seek(2.5)` // Jump to 2.5 seconds

**Example:**
```javascript
// Jump to specific time
avatarViewer.seek(1.5); // 1.5 seconds into animation

// Get current time
const currentTime = avatarViewer.getCurrentTime();

// Get total duration
const totalDuration = avatarViewer.getTotalDuration();
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ← | Step backward one frame |
| → | Step forward one frame |
| Esc | Stop animation |
| F | Toggle full-screen |
| ↑ | Increase playback speed |
| ↓ | Decrease playback speed |

## Expression Controls

The avatar viewer also supports facial expressions:

```javascript
// Set facial expression
avatarViewer.setExpression('happy');
avatarViewer.setExpression('sad');
avatarViewer.setExpression('surprised');
avatarViewer.setExpression('neutral');

// Available expressions:
// - happy, sad, angry, surprised, confused
// - excited, bored, worried, proud, embarrassed
```

## API Endpoints

### Play Animation
```http
POST /api/avatar/play
Content-Type: application/json

{
  "animation": "phrase_hello",
  "speed": 1.0,
  "loop": false
}
```

### Seek to Time
```http
POST /api/avatar/seek
Content-Type: application/json

{
  "time": 2.5
}
```

### Set Playback Speed
```http
POST /api/avatar/speed
Content-Type: application/json

{
  "speed": 1.5
}
```

### Pause/Stop
```http
POST /api/avatar/pause
POST /api/avatar/stop
```

## Advanced Features

### Animation Queue

Queue multiple animations to play in sequence:

```javascript
avatarViewer.queueAnimation('phrase_hello');
avatarViewer.queueAnimation('phrase_how_are_you');
avatarViewer.queueAnimation('phrase_thank_you');
avatarViewer.playQueue();
```

### Blend Animations

Smoothly blend between animations:

```javascript
avatarViewer.blendTo('phrase_hello', 0.5); // 0.5 second blend
```

### Event Listeners

Listen to playback events:

```javascript
canvas.addEventListener('avatar:play', (e) => {
  console.log('Animation started', e.detail);
});

canvas.addEventListener('avatar:pause', (e) => {
  console.log('Animation paused', e.detail);
});

canvas.addEventListener('avatar:complete', (e) => {
  console.log('Animation complete', e.detail);
});
```

## Troubleshooting

### Animation not playing?

1. Check browser console for errors
2. Verify the animation name is correct
3. Check that the avatar model is loaded
4. Ensure WebGL is supported

### Jerky playback?

1. Reduce playback speed
2. Close other browser tabs
3. Check GPU acceleration is enabled
4. Try a different browser

### Controls not responding?

1. Click on the canvas to focus it
2. Refresh the page
3. Check browser console for JavaScript errors

## See Also

- [Recording Guide](recording.md) - How to record avatar performances
- [Timeline Editor](timeline-editor.md) - Creating animation sequences
- [Animation Library](animation-library.md) - Available BSL animations

# BSL Avatar Recording Guide

Learn how to record BSL avatar performances as video or capture screenshots.

## Accessing Recording Features

Recording controls are available in the enhanced avatar viewer:
- **Production**: `http://localhost:8007/static/avatar-enhanced.html`
- **Development**: `http://localhost:8003/static/avatar-enhanced.html`

Look for the recording controls in the bottom toolbar.

## Recording Video

### Start Recording

1. Click the **Record** button (red circle icon)
2. Select format (WebM recommended for compatibility)
3. Perform your avatar actions
4. Click **Stop** when done

The video will automatically download to your downloads folder.

### Via UI

1. **Start Recording**: Click red circle button
2. **Select Format**: Choose WebM or GIF
3. **Perform Actions**: Play animations, change expressions
4. **Stop Recording**: Click square stop button
5. **Download**: Video downloads automatically

### Via API

```bash
# Start recording
curl -X POST http://localhost:8003/api/avatar/record/start \
  -H "Content-Type: application/json" \
  -d '{
    "format": "webm",
    "fps": 30
  }'

# Stop recording and download
curl -X POST http://localhost:8003/api/avatar/record/stop
```

### Via JavaScript

```javascript
// Start recording
await avatarViewer.startRecording('webm');

// Perform actions...
avatarViewer.playAnimation('phrase_hello');

// Stop recording
avatarViewer.stopRecording();

// The video downloads automatically
```

## Capturing Screenshots

### Single Frame

Click the **Frame** button (camera icon) to capture the current frame as a PNG image.

### Via API

```bash
curl -X POST http://localhost:8003/api/avatar/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "format": "png"
  }'
```

### Via JavaScript

```javascript
// Capture current frame
avatarViewer.captureFrame('png');

// Also supports 'jpg' or 'webp'
avatarViewer.captureFrame('jpg');
```

## Recording Formats

| Format | Description | Quality | File Size | Browser Support | Use Case |
|--------|-------------|---------|-----------|-----------------|----------|
| WebM | High quality video | Excellent | Medium | Most modern browsers | Productions, sharing |
| GIF | Animated image | Lower | Large | Universal | Quick sharing, demos |
| PNG | Single image | Excellent | Varies | Universal | Screenshots |
| JPG | Single image | Good | Smaller | Universal | Screenshots (smaller) |

**Recommendation**: Use WebM for video recordings (best quality/size ratio).

## Recording Quality Settings

### Video Quality

```javascript
// Start recording with custom settings
const options = {
  format: 'webm',
  fps: 30,           // Frames per second
  bitrate: 5000000   // 5 Mbps
};
await avatarViewer.startRecording(options);
```

### Frame Capture

```javascript
// Capture with custom format
avatarViewer.captureFrame('png', 1920, 1080);  // HD resolution
avatarViewer.captureFrame('jpg', 1280, 720);   // HD resolution (smaller)
```

## Recording Duration

Check recording duration:

```javascript
// Get current recording duration
const duration = avatarViewer.getRecordingDuration();
console.log(`Recording for ${duration} seconds`);

// Check if currently recording
if (avatarViewer.isRecordingActive()) {
  console.log('Recording in progress');
}
```

## Recording Events

Listen to recording events:

```javascript
canvas.addEventListener('avatar:recording:started', (e) => {
  console.log('Recording started', e.detail);
});

canvas.addEventListener('avatar:recording:stopped', (e) => {
  console.log('Recording stopped', e.detail);
});

canvas.addEventListener('avatar:recording:saved', (e) => {
  console.log('Recording saved', e.detail.url);
});

canvas.addEventListener('avatar:recording:frame-captured', (e) => {
  console.log('Frame captured', e.detail.format);
});
```

## Tips for Better Recordings

1. **Light backgrounds** work best for avatar visibility
2. **Smooth movements** - the avatar interpolates between keyframes
3. **Use presets** for common gestures (wave, goodbye, etc.)
4. **Check audio** if recording voice along with avatar
5. **Preview first** - test animation before recording
6. **Use appropriate speed** - 0.5x or 0.75x for learning materials
7. **Stable camera** - don't move camera during recording

## Recording Workflow

### For Learning Materials

1. Set playback speed to 0.5x or 0.75x
2. Use light background
3. Record each gesture separately
4. Add voice narration later

### For Demonstrations

1. Use normal speed (1x)
2. Practice the sequence first
3. Use smooth transitions
4. Keep recordings short (<30 seconds)

### For Social Media

1. Use GIF format for easy sharing
2. Keep under 15 seconds
3. Use bright, clear gestures
4. Add captions/subtitles

## Troubleshooting

### Recording not starting?

- Ensure services are running: `docker compose ps`
- Check browser console for errors
- Try refreshing the page
- Verify WebGL is supported: https://get.webgl.org/

### Video not downloading?

- Check browser download settings
- Try different format (WebM vs GIF)
- Ensure sufficient disk space
- Check browser popup blocker

### Poor video quality?

- Increase bitrate setting
- Use WebM format instead of GIF
- Ensure hardware acceleration is enabled
- Close other tabs to free resources

### Large file size?

- Reduce recording duration
- Use JPG instead of PNG for screenshots
- Lower bitrate for video
- Consider using GIF only for short clips

## Advanced Features

### Recording with Audio

```javascript
// Start recording with audio (if supported)
await avatarViewer.startRecording('webm', {
  audio: true,
  audioBitsPerSecond: 128000
});
```

### Custom Filename

```javascript
// The recording uses automatic naming:
// bsl-avatar-{timestamp}.{format}

// To rename, download and rename manually
```

### Batch Recording

```javascript
// Record multiple animations in sequence
const animations = ['phrase_hello', 'phrase_how_are_you', 'phrase_thank_you'];

for (const anim of animations) {
  await avatarViewer.startRecording('webm');
  avatarViewer.playAnimation(anim);
  await new Promise(r => setTimeout(r, 3000)); // Wait 3 seconds
  avatarViewer.stopRecording();
  await new Promise(r => setTimeout(r, 1000)); // Pause between recordings
}
```

## Storage Considerations

- **WebM video**: ~1-5 MB per minute at 5 Mbps
- **GIF**: ~5-20 MB per minute (larger files)
- **PNG screenshot**: ~100-500 KB each
- **JPG screenshot**: ~50-200 KB each

Plan storage accordingly for batch recordings.

## See Also

- [Playback Controls](playback-controls.md) - Basic avatar controls
- [Timeline Editor](timeline-editor.md) - Creating sequenced animations
- [Animation Library](animation-library.md) - Available BSL animations

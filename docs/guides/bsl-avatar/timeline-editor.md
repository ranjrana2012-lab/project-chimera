# BSL Avatar Timeline Editor Guide

Learn how to create sequenced avatar animations using the timeline editor.

## Accessing the Timeline Editor

The timeline editor is built into the enhanced avatar viewer:
- **Production**: `http://localhost:8007/static/avatar-enhanced.html`
- **Development**: `http://localhost:8003/static/avatar-enhanced.html`

The timeline is located at the bottom of the viewer, below the playback controls.

## Timeline Features

The timeline editor includes:

- **Timeline Track**: Visual representation of animation sequence
- **Markers**: Named points in time (e.g., "Wave hello", "Thank you")
- **Scrubber**: Drag to jump to any point in the timeline
- **Marker List**: See all markers, jump to specific points
- **Playback Controls**: Play, pause, step through marked sections

## Timeline Display

```
Timeline Track:
|----|----|----|----|----|----|----|----|----| (time in seconds)
  ↑              ↑        ↑
Marker 1      Marker 2  Marker 3
```

## Adding Timeline Markers

### Via UI

1. Play or scrub to the desired position
2. Click the **+ Marker** button in the timeline controls
3. Enter a label for the marker (e.g., "Wave hello")
4. Optionally select a color
5. Click **Add**

The marker appears at the current playback position.

### Via API

```bash
curl -X POST http://localhost:8003/api/avatar/timeline/markers \
  -H "Content-Type: application/json" \
  -d '{
    "time": 2.5,
    "label": "Wave hello",
    "color": "#4CAF50"
  }'
```

### Via JavaScript

```javascript
// Add marker at current time
const marker = avatarViewer.addTimelineMarker(
  2.5,              // time in seconds
  'Wave hello',     // label
  '#4CAF50'         // color (green)
);

// Add marker at specific time
const marker2 = avatarViewer.addTimelineMarker(
  5.0,
  'Character enters',
  '#2196F3'         // blue
);
```

**Default colors:**
- `#4CAF50` - Green (actions)
- `#2196F3` - Blue (events)
- `#FF9800` - Orange (transitions)
- `#F44336` - Red (important)
- `#9C27B0` - Purple (notes)

## Navigating Markers

### Jump to Marker

- Click **Go** button next to marker in the marker list
- Click directly on the marker in the timeline track
- Use **Previous** and **Next** buttons to navigate between markers

### Via API

```bash
# Jump to specific marker
curl -X POST http://localhost:8003/api/avatar/timeline/jump \
  -H "Content-Type: application/json" \
  -d '{"marker_id": "marker-123"}'
```

### Via JavaScript

```javascript
// Jump to marker by ID
avatarViewer.jumpToMarker('marker-123');

// Jump to nearest marker
avatarViewer.seek(2.7);  // Seek to time
const nearest = avatarViewer.getNearestMarker(2.7);
if (nearest) {
  avatarViewer.jumpToMarker(nearest.id);
}
```

## Managing Markers

### Update Marker

Change marker properties:

```javascript
avatarViewer.updateTimelineMarker('marker-123', {
  label: 'New label',
  color: '#FF9800',
  time: 3.0
});
```

### Delete Marker

- Click the **×** button next to a marker in the marker list
- Or use JavaScript:

```javascript
avatarViewer.removeTimelineMarker('marker-123');
```

### Clear All Markers

Click the **Clear All** button to remove all timeline markers.

```javascript
avatarViewer.clearTimelineMarkers();
```

## Listing Markers

### Get All Markers

```javascript
const markers = avatarViewer.getTimelineMarkers();
console.log(markers);
// Output:
// [
//   { id: 'marker-1', time: 2.5, label: 'Wave hello', color: '#4CAF50' },
//   { id: 'marker-2', time: 5.0, label: 'Character enters', color: '#2196F3' }
// ]
```

### Get Nearest Marker

```javascript
const nearest = avatarViewer.getNearestMarker(3.2);
console.log(nearest);
// Output: { id: 'marker-2', time: 5.0, label: 'Character enters', ... }
```

## Use Cases

### Creating a Performance Sequence

1. Play your avatar through the performance
2. Add markers at key moments:
   - Scene starts
   - Character entrances
   - Music cues
   - Transition points
   - Curtain calls
3. Use markers for quick navigation during rehearsals

**Example sequence:**
```javascript
// Scene 1 markers
avatarViewer.addTimelineMarker(0.0, 'Scene 1: Introduction', '#4CAF50');
avatarViewer.addTimelineMarker(2.5, 'Character enters', '#2196F3');
avatarViewer.addTimelineMarker(5.0, 'Dialogue starts', '#9C27B0');
avatarViewer.addTimelineMarker(10.0, 'Scene 1 ends', '#FF9800');

// Navigate between markers
avatarViewer.jumpToMarker('marker-2');  // Go to character entrance
```

### Annotation

Markers can include labels like:
- "Scene 1: Introduction"
- "Character enters stage left"
- "Music starts - upbeat"
- "Lighting fade in"
- "Audience interaction point"

### Rehearsal Tool

Use markers to:
- Mark rehearsal points
- Note timing adjustments
- Flag sections needing work
- Track performance timing

```javascript
// Rehearsal notes
avatarViewer.addTimelineMarker(3.5, 'TODO: Smooth transition', '#F44336');
avatarViewer.addTimelineMarker(7.2, 'CHECK: Timing with music', '#FF9800');
avatarViewer.addTimelineMarker(12.0, 'GOOD: Expression change', '#4CAF50');
```

## Saving Timeline

Timeline markers are **automatically saved** to your browser's localStorage and persist between sessions.

### Manual Save

```javascript
// Normally automatic, but you can force save:
avatarViewer.saveTimelineMarkers();
```

### Load Timeline

```javascript
// Normally automatic on page load
avatarViewer.loadTimelineMarkers();
```

### Clear Timeline

```javascript
// Remove all markers from localStorage
avatarViewer.clearTimelineMarkers();
```

## Import/Export (Coming Soon)

Future features will include:

- Export timeline as JSON
- Share timelines with other users
- Import timeline from file
- Template timelines for common sequences

```javascript
// Future API
const json = avatarViewer.exportTimeline();
avatarViewer.importTimeline(json);
```

## Timeline Events

Listen to timeline events:

```javascript
canvas.addEventListener('avatar:timeline:marker-added', (e) => {
  console.log('Marker added', e.detail);
});

canvas.addEventListener('avatar:timeline:marker-removed', (e) => {
  console.log('Marker removed', e.detail);
});

canvas.addEventListener('avatar:timeline:marker-updated', (e) => {
  console.log('Marker updated', e.detail);
});

canvas.addEventListener('avatar:timeline:marker-selected', (e) => {
  console.log('Marker selected', e.detail);
});

canvas.addEventListener('avatar:timeline:markers-cleared', (e) => {
  console.log('All markers cleared', e.detail);
});
```

## Best Practices

### Marker Labels

- **Be descriptive**: "Character waves hello" not "Wave"
- **Use categories**: Prefix with type (SCENE, ACTION, NOTE)
- **Keep it short**: Under 30 characters for display
- **Use consistent format**: "Scene 1: Introduction"

### Marker Colors

Use color coding:
- **Green** (`#4CAF50`): Actions, successful elements
- **Blue** (`#2196F3`): Events, scene changes
- **Orange** (`#FF9800`): Transitions, warnings
- **Red** (`#F44336`): Problems, important notes
- **Purple** (`#9C27B0`): Annotations, thoughts

### Marker Spacing

- Place markers at meaningful transitions
- Don't over-mark (every 5+ seconds is good)
- Use markers for sections, not every frame

## Troubleshooting

### Markers not saving?

- Check browser localStorage is enabled
- Verify browser has storage quota available
- Try clearing cache and re-adding markers

### Can't jump to marker?

- Ensure marker ID is valid
- Check marker time is within animation duration
- Try refreshing the page

### Markers lost?

- Check browser didn't clear localStorage
- Look for marker data in browser DevTools → Application → Local Storage
- Consider exporting timeline regularly (when feature available)

## Example Workflows

### Workflow 1: Creating a Rehearsal Timeline

```javascript
// 1. Clear old markers
avatarViewer.clearTimelineMarkers();

// 2. Play through performance
avatarViewer.playAnimation('phrase_hello');

// 3. Add markers during playback
// (User adds markers manually via UI at key points)

// 4. Review markers
const markers = avatarViewer.getTimelineMarkers();
markers.forEach(m => console.log(m.label, m.time));

// 5. Navigate between markers during rehearsal
avatarViewer.jumpToMarker('marker-3');
```

### Workflow 2: Analyzing Performance

```javascript
// 1. Add analysis markers
avatarViewer.addTimelineMarker(0.0, 'Start', '#4CAF50');
avatarViewer.addTimelineMarker(2.3, 'Hand transition', '#2196F3');
avatarViewer.addTimelineMarker(4.1, 'Expression change', '#9C27B0');
avatarViewer.addTimelineMarker(6.0, 'End', '#4CAF50');

// 2. Step through each section
avatarViewer.seek(2.3);
avatarViewer.stepForward();
avatarViewer.stepForward();

// 3. Adjust timing if needed
avatarViewer.updateTimelineMarker('marker-2', { time: 2.5 });
```

## See Also

- [Playback Controls](playback-controls.md) - Basic avatar controls
- [Recording Guide](recording.md) - Recording your performance
- [Animation Library](animation-library.md) - Available BSL animations

# BSL Avatar Animation Library

The BSL Agent includes 107 pre-built animations covering common phrases, alphabet, numbers, and emotions.

## Accessing Animations

### Via API

```bash
# List all animations
curl http://localhost:8003/api/avatar/library

# Get animations by category
curl http://localhost:8003/api/avatar/library/phrase
curl http://localhost:8003/api/avatar/library/letter
curl http://localhost:8003/api/avatar/library/number
curl http://localhost:8003/api/avatar/library/emotion

# Get specific animation details
curl http://localhost:8003/api/avatar/library/phrase/hello

# Play an animation
curl -X POST http://localhost:8003/api/avatar/library/phrase/hello/play \
  -H "Content-Type: application/json"
```

### Via JavaScript

```javascript
// List all animations
const animations = await fetch('/api/avatar/library').then(r => r.json());
console.log(animations);

// Get animation by ID
const animation = avatarLibrary.getAnimation('phrase_hello');
console.log(animation);

// Play a specific animation
avatarViewer.playAnimation('phrase_hello');

// Play a preset animation
avatarViewer.playPreset('greeting');
```

## Animation Categories

### Phrases (50 animations)

Common BSL phrases for everyday communication:

**Greetings:**
- `phrase_hello` - Hello
- `phrase_goodbye` - Goodbye
- `phrase_good_morning` - Good morning
- `phrase_good_night` - Good night
- `phrase_how_are_you` - How are you?

**Politeness:**
- `phrase_please` - Please
- `phrase_thank_you` - Thank you
- `phrase_sorry` - Sorry
- `phrase_welcome` - You're welcome
- `phrase_excuse_me` - Excuse me

**Questions:**
- `phrase_what` - What?
- `phrase_when` - When?
- `phrase_where` - Where?
- `phrase_who` - Who?
- `phrase_why` - Why?
- `phrase_how` - How?
- `phrase_which` - Which?

**Responses:**
- `phrase_yes` - Yes
- `phrase_no` - No
- `phrase_maybe` - Maybe
- `phrase_i_agree` - I agree
- `phrase_i_disagree` - I disagree

**Time:**
- `phrase_now` - Now
- `phrase_later` - Later
- `phrase_today` - Today
- `phrase_tomorrow` - Tomorrow
- `phrase_yesterday` - Yesterday

**People:**
- `phrase_me` - Me
- `phrase_you` - You
- `phrase_he` - He
- `phrase_she` - She
- `phrase_we` - We
- `phrase_they` - They

**Other:**
- `phrase_love` - Love
- `phrase_like` - Like
- `phrase_dont_know` - Don't know
- `phrase_understand` - Understand
- `phrase_help` - Help

### Alphabet (26 animations)

Finger spelling for each letter A-Z with proper BSL handshapes:

- `letter_A` through `letter_Z`

**Note:** BSL alphabet uses two-handed fingerspelling, distinct from ASL.

### Numbers (21 animations)

BSL number signing with counting gestures:

- `number_0` through `number_20`

**Usage:** Numbers are signed with specific handshapes and movements for 0-20.

### Emotions (10 animations)

Facial expressions and body language for emotions:

- `emotion_happy` - Happy, smiling
- `emotion_sad` - Sad, frowning
- `emotion_angry` - Angry, frustrated
- `emotion_surprised` - Surprised, shocked
- `emotion_confused` - Confused, puzzled
- `emotion_excited` - Excited, enthusiastic
- `emotion_bored` - Bored, uninterested
- `emotion_worried` - Worried, anxious
- `emotion_proud` - Proud, confident
- `emotion_embarrassed` - Embarrassed, shy

## Quick Presets

The enhanced viewer includes 8 quick preset buttons for common actions:

| Preset | Animations | Description |
|--------|-----------|-------------|
| `greeting` | phrase_hello + emotion_happy | Wave and smile |
| `goodbye` | phrase_goodbye + emotion_neutral | Wave goodbye |
| `thank-you` | phrase_thank_you + emotion_happy | Thank you gesture |
| `yes` | phrase_yes + emotion_happy | Nod yes |
| `no` | phrase_no + emotion_neutral | Shake no |
| `alphabet-a` | letter_A | Sign letter A |
| `count-1` | number_1 | Sign number 1 |
| `happy` | emotion_happy | Happy expression |

### Using Presets

```javascript
// Play a preset
avatarViewer.playPreset('greeting');

// Available presets
const presets = avatarViewer.getAvailablePresets();
console.log(presets);
// Output:
// {
//   greetings: ['greeting', 'goodbye', 'thank-you'],
//   responses: ['yes', 'no'],
//   learning: ['alphabet-a', 'count-1'],
//   emotions: ['happy', 'sad', 'surprised']
// }
```

## Searching Animations

### Via API

```bash
# Search for animations
curl "http://localhost:8003/api/avatar/library/search?q=hello"
```

### Via JavaScript

```javascript
// Search animations
const results = avatarLibrary.search('hello');
console.log(results);
// Output:
// [
//   { id: 'phrase_hello', name: 'Hello', category: 'phrase' }
// ]

// Search by category
const phrases = avatarLibrary.getByCategory('phrase');
console.log(phrases);  // All 50 phrases
```

## Building Custom Animations

### Creating NMM Animations

BSL animations use the NMM (Neural Model Format). To create custom animations:

1. **Model the animation** in Blender or similar tool
2. **Export to NMM format** with bone rotations and morph targets
3. **Add to library** in `services/bsl-agent/animations/`
4. **Register in manifest** (`animations.json`)

See the [Avatar Rendering documentation](../../../../services/bsl-agent/README.md) for details.

### Animation File Format

NMM animations include:

```javascript
{
  "format": "NMM",
  "version": "1.0",
  "fps": 30,
  "duration": 2.5,
  "bones": {
    "head": { "rotations": [...], "positions": [...] },
    "spine": { "rotations": [...], "positions": [...] },
    "left_arm": { "rotations": [...], "positions": [...] },
    "right_arm": { "rotations": [...], "positions": [...] },
    // ... more bones
  },
  "morphTargets": {
    "happy": [...],
    "sad": [...],
    // ... more expressions
  },
  "lipSync": {
    "visemes": [...]
  }
}
```

### Keyframes

Animations are stored at 30 FPS with keyframes every ~3 frames (10 keyframes per second).

## Animation Playback

### Basic Playback

```javascript
// Play single animation
avatarViewer.playAnimation('phrase_hello');

// Play with options
avatarViewer.playAnimation('phrase_hello', {
  speed: 1.0,      // Normal speed
  loop: false,     // Don't loop
  blend: 0.2       // 0.2 second blend from current
});
```

### Sequenced Playback

```javascript
// Play multiple animations in sequence
avatarViewer.playAnimationSequence([
  'phrase_hello',
  'phrase_how_are_you',
  'phrase_thank_you'
], {
  delay: 0.5,  // 0.5 second delay between animations
  blend: 0.2   // Smooth blend between animations
});
```

### Layered Animations

```javascript
// Play base animation
avatarViewer.playAnimation('phrase_hello');

// Layer expression on top
avatarViewer.setExpression('happy');

// Expression blends with base animation
```

## Lip Sync

The avatar supports lip-sync for speech:

```javascript
// Enable lip-sync
avatarViewer.enableLipSync(true);

// Provide viseme data
avatarViewer.updateLipSync([
  { viseme: 'sil', timestamp: 0.0 },
  { viseme: 'PP', timestamp: 0.1 },
  { viseme: 'AA', timestamp: 0.2 },
  { viseme: 'sil', timestamp: 0.3 }
]);
```

## Performance Considerations

### Animation Caching

Animations are automatically cached after first load:
- First play: ~50-100ms (load from disk)
- Subsequent plays: ~1-5ms (from cache)

### Memory Usage

Approximate memory per animation:
- Phrase: 10-50 KB
- Letter: 5-10 KB
- Number: 5-10 KB
- Emotion: 20-100 KB

Total library: ~5-10 MB in memory

### Streaming

Large animations (>1 MB) are streamed:
- First frame loads immediately
- Remaining frames load in background
- Playback starts without full download

## Troubleshooting

### Animation not found?

- Check the animation ID matches exactly
- Verify animation exists in library
- Check browser console for errors
- Try `curl /api/avatar/library` to see available animations

### Jerky playback?

- Check hardware acceleration is enabled
- Close other tabs to free GPU resources
- Reduce playback speed
- Check for JavaScript errors in console

### Animation not loading?

- Verify WebGL is supported
- Check network tab for failed requests
- Ensure animations directory exists
- Check file permissions

## API Reference

### List Animations

```http
GET /api/avatar/library
```

**Response:**
```json
{
  "phrase": ["phrase_hello", "phrase_goodbye", ...],
  "letter": ["letter_A", "letter_B", ...],
  "number": ["number_0", "number_1", ...],
  "emotion": ["emotion_happy", "emotion_sad", ...]
}
```

### Get Animation Details

```http
GET /api/avatar/library/{category}/{name}
```

**Response:**
```json
{
  "id": "phrase_hello",
  "name": "Hello",
  "category": "phrase",
  "duration": 2.5,
  "fps": 30,
  "keyframes": 75
}
```

### Play Animation

```http
POST /api/avatar/library/{category}/{name}/play
Content-Type: application/json

{
  "speed": 1.0,
  "loop": false
}
```

## See Also

- [Playback Controls](playback-controls.md) - How to play animations
- [Recording Guide](recording.md) - Record custom animations
- [Timeline Editor](timeline-editor.md) - Create animation sequences

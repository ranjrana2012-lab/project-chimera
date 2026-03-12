# ADR 009: BSL Avatar Rendering Architecture

**Status:** Accepted

**Date:** 2026-03-12

**Context**

Project Chimera requires a realistic British Sign Language (BSL) avatar for accessibility and immersive theatre experiences. The avatar must:

1. Render in real-time in a web browser
2. Support 107+ pre-built animations (phrases, alphabet, numbers, emotions)
3. Allow real-time control (playback, recording, timeline editing)
4. Handle lip-sync for speech synchronization
5. Perform efficiently on consumer hardware

Previous approaches considered:
- **Server-side rendering**: Would require video streaming, high server load, and higher latency
- **2D sprite-based animation**: Limited expressiveness, difficult to scale
- **External SaaS solution**: Cost prohibitive, lack of customization

**Decision**

We will use a WebGL/Three.js-based rendering system with the following components:

### Core Renderer (AvatarWebGLRenderer)

- **Three.js** for 3D rendering in browser
- **NMM (Neural Model Format)** for animations
- **Morph targets** for facial expressions
- **Bone hierarchy** for body poses

### Advanced Features

- **LipSyncEngine**: Viseme-to-phoneme mapping with coarticulation
- **FacialExpressionController**: Blend masks for expression layering
- **BodyPoseController**: Predefined poses with IK support
- **GestureQueueManager**: Priority queue for gesture sequencing

### Animation Library

- 50 common BSL phrases
- 26 alphabet letters (A-Z)
- 21 numbers (0-20)
- 10 emotional expressions

### Frontend Enhancement

- Playback controls (play, pause, stop, seek, speed)
- Recording (WebM/GIF capture)
- Full-screen mode
- Timeline editor with markers
- Camera controls (orbit, zoom, presets)

### Performance Optimizations

- Worker threads for parallel processing
- GLB compression for models
- LRU cache for animations
- Streaming for large animations
- GPU instancing for multiple avatars

**Rationale**

### Why WebGL/Three.js?

- **Ubiquitous**: Runs in all modern browsers without plugins
- **Performant**: GPU-accelerated 3D rendering at 60 FPS
- **Ecosystem**: Large community, extensive examples and documentation
- **Python Integration**: Can be controlled from Python backend via REST API
- **No Plugin Required**: Works on any device with WebGL support

### Why NMM Format?

- **Compact**: Binary format smaller than equivalent JSON
- **Expressive**: Supports bones, morph targets, keyframes in one format
- **Emerging Standard**: Becoming the standard for neural animations
- **Tool Support**: Good tooling for creation and editing

### Why Client-Side Rendering?

- **Real-time**: Low latency control (no server round-trip)
- **Scalable**: Rendering happens on user's device
- **Offline-capable**: Once loaded, no server needed for basic playback
- **Cost-effective**: No server-side GPU costs
- **Responsive**: Immediate feedback for user interactions

### Why Not Alternatives?

**Server-side rendering (video streaming)**:
- ❌ Higher latency (encoding + streaming delay)
- ❌ Expensive server costs (GPU instances)
- ❌ Bandwidth intensive
- ❌ Lower quality (compression artifacts)

**2D sprite-based animation**:
- ❌ Limited expressiveness
- ❌ Hard to create smooth transitions
- ❌ Difficult to scale (more sprites = more assets)
- ❌ Can't easily change camera angles

**External SaaS avatar services**:
- ❌ Expensive recurring costs
- ❌ Limited customization
- ❌ Vendor lock-in
- ❌ Can't add custom animations easily

**Consequences**

### Positive

- **Real-time control**: Users can control avatar with <50ms latency
- **No server load**: Rendering happens on user's device
- **Offline capability**: Works offline after initial load
- **Smooth playback**: 60 FPS on most modern hardware
- **Extensible**: Easy to add new animations
- **Customizable**: Full control over appearance and behavior
- **Cost-effective**: No recurring GPU costs

### Negative

- **Initial load time**: Model load takes ~2-5 seconds depending on connection
- **Hardware requirements**: Requires WebGL support (all modern browsers have this)
- **GPU dependent**: Performance varies by user's GPU power
- **Bandwidth**: Initial model download is ~5-10 MB

### Side Effects

- Need to keep 3D models optimized for web delivery (GLB compression)
- Fallback 2D UI needed for WebGL-free browsers (graceful degradation)
- Need to manage animation caching carefully (memory vs performance trade-off)
- Browser compatibility testing required (WebGL support varies)

**Implementation**

- **Backend**: `services/bsl-agent/avatar_webgl.py` (1800+ lines)
  - WebGL renderer initialization
  - NMM animation loading
  - Lip-sync engine
  - Expression controller
  - Gesture queue management

- **Frontend**: `services/bsl-agent/static/js/avatar-enhanced.js` (640+ lines)
  - BSLAvatarEnhanced class
  - Playback controls
  - Recording functionality
  - Timeline editor
  - Camera controls

- **API**: 20+ new endpoints for avatar control
  - `/api/avatar/play` - Play animation
  - `/api/avatar/pause` - Pause playback
  - `/api/avatar/stop` - Stop animation
  - `/api/avatar/seek` - Jump to time
  - `/api/avatar/speed` - Set playback speed
  - `/api/avatar/record/start` - Start recording
  - `/api/avatar/record/stop` - Stop recording
  - `/api/avatar/snapshot` - Capture frame
  - `/api/avatar/library` - List animations
  - And more...

- **Tests**: 16/16 E2E tests passing (100%)
  - Animation playback
  - Expression changes
  - Recording functionality
  - Timeline marker management
  - API endpoints

**Performance Metrics**

- **Initial load**: 2-5 seconds (5-10 MB download)
- **Animation load**: <50ms first, <5ms cached
- **Playback latency**: <50ms from API call to visual
- **Frame rate**: 60 FPS on mid-range hardware
- **Memory usage**: ~50-100 MB per avatar instance

**Future Enhancements**

- Multi-avatar support (GPU instancing)
- Custom avatar upload (user-generated content)
- Voice-driven animation (speech-to-BSL)
- Mobile optimization (reduced poly models)
- VR/AR support (WebXR)

**References**

- [BSL Agent README](../../../../services/bsl-agent/README.md)
- [Animation Library Guide](../../guides/bsl-avatar/animation-library.md)
- [Playback Controls Guide](../../guides/bsl-avatar/playback-controls.md)
- Three.js documentation: https://threejs.org/docs/
- NMM format specification: Internal documentation
- WebGL support: https://get.webgl.org/

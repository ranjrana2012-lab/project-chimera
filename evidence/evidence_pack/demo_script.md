# Demo Script - 3-Minute Controlled Demonstration

**Date**: April 9, 2026
**Purpose**: Week 5 - Controlled Demo Capture
**Duration**: 3 minutes (180 seconds)
**Status**: Ready for Capture

## Demo Overview

This script demonstrates the **core innovation** of Project Chimera: **adaptive AI based on real-time sentiment analysis**.

### Key Message

"Project Chimera is an AI-powered adaptive framework that detects emotional sentiment and adjusts its responses in real-time. Unlike traditional chatbots that use the same response regardless of emotional state, Chimera adapts its dialogue strategy, tone, and context based on detected sentiment."

---

## Script Timeline

### 0:00-0:20 | Introduction (20 seconds)

**Visual**: Terminal window showing chimera_core.py directory

**Narration**:
> "Welcome to Project Chimera. This is an AI-powered adaptive framework for live theatre. The core innovation is real-time sentiment analysis that drives adaptive dialogue generation. Let me show you how it works."

**Action**: Show directory listing
```bash
ls -la services/operator-console/
# Show chimera_core.py (1,077 lines)
```

---

### 0:20-0:50 | Scenario 1: Positive Sentiment (30 seconds)

**Visual**: Terminal with chimera_core.py running

**Input**: "I'm so excited about this project! It's going to be amazing!"

**Expected Output**:
```
[STEP 1] Sentiment Analysis...
  → Sentiment: POSITIVE
  → Score: +0.60
  → Confidence: 0.85

[STEP 2] Adaptive Dialogue Generation...
  → Source: API
  → Model: glm-4

[STEP 3] Adaptive Routing Rules...
  → Routing: momentum_build
  → Context: expansive
  → Tone: enthusiastic

OUTPUT:
That's wonderful to hear! Your positive energy is contagious.
Let's build on this momentum together!
```

**Narration**:
> "Watch what happens when I input positive text. The system detects positive sentiment with high confidence. Notice how it routes to a 'momentum build' strategy with an enthusiastic tone. It's building on my positive energy."

---

### 0:50-1:20 | Scenario 2: Negative Sentiment (30 seconds)

**Visual**: Terminal with chimera_core.py running

**Input**: "I'm really frustrated with how things are going."

**Expected Output**:
```
[STEP 1] Sentiment Analysis...
  → Sentiment: NEGATIVE
  → Score: -0.65
  → Confidence: 0.78

[STEP 2] Adaptive Dialogue Generation...
  → Source: API
  → Model: glm-4

[STEP 3] Adaptive Routing Rules...
  → Routing: supportive_care
  → Context: empathetic
  → Tone: reassuring

OUTPUT:
I understand things may be difficult right now.
Let's work through this together - you're not alone.
```

**Narration**:
> "Now watch with negative input. The sentiment shifts to negative. The system adapts completely—now using a 'supportive care' strategy with an empathetic tone. It acknowledges the difficulty and offers support."

---

### 1:20-1:50 | Scenario 3: Neutral Sentiment (30 seconds)

**Visual**: Terminal with chimera_core.py running

**Input**: "Can you tell me more about the system?"

**Expected Output**:
```
[STEP 1] Sentiment Analysis...
  → Sentiment: NEUTRAL
  → Score: 0.00
  → Confidence: 0.72

[STEP 2] Adaptive Dialogue Generation...
  → Source: API
  → Model: glm-4

[STEP 3] Adaptive Routing Rules...
  → Routing: standard_response
  → Context: neutral
  → Tone: professional

OUTPUT:
Thank you for your input. Let me help you with that.
```

**Narration**:
> "With neutral input, the system uses a standard response strategy. The tone is professional and the context is neutral. This three-way adaptation—positive, negative, neutral—is the core innovation."

---

### 1:50-2:20 | Comparison Mode (30 seconds)

**Visual**: Terminal showing comparison output

**Command**: `python chimera_core.py compare "I'm so excited!"`

**Expected Output**:
```
[WITH ADAPTATION]
Strategy: momentum_build
Tone: enthusiastic
Output: "That's wonderful! Your positive energy is contagious..."

[WITHOUT ADAPTATION]
Strategy: standard_response
Tone: professional
Output: "Thank you for your input. I have received your message."

KEY DIFFERENCE
The adaptive system detects POSITIVE sentiment and adjusts its
response strategy to 'momentum_build' with an 'enthusiastic' tone.

The non-adaptive system uses the same standard response regardless of
emotional state.
```

**Narration**:
> "Let me show you the difference side-by-side. On the left, adaptive mode detects positive sentiment and responds enthusiastically. On the right, non-adaptive mode gives the same standard response every time. This comparison clearly demonstrates the value of adaptive routing."

---

### 2:20-2:40 | Caption Mode (20 seconds)

**Visual**: Terminal showing caption formatting

**Command**: `python chimera_core.py caption "I'm so excited!"`

**Expected Output**:
```
┌────────────────────────────────────────┐
│              POSITIVE                  │
│                                        │
│      That's wonderful! Your           │
│      positive energy is contagious.   │
│      Let's build on this momentum!    │
└────────────────────────────────────────┘
```

**Narration**:
> "The system also includes accessibility features. Here you see caption formatting with high-contrast output and visual sentiment indicators. This ensures the adaptive AI is accessible to all users."

---

### 2:40-3:00 | Conclusion (20 seconds)

**Visual**: Terminal showing script information

**Narration**:
> "Project Chimera demonstrates that AI can adapt in real-time based on emotional sentiment. This has applications in live theatre, customer service, education, and more. The core framework is complete and ready for deployment. Thank you."

**Action**: Show final system info
```bash
python chimera_core.py --version
# Output: Chimera Core v1.0.0
```

---

## Screen Capture Plan

### Technical Setup

**Terminal**: Clear, readable terminal with good contrast
- Font: Monospace, size 14-16
- Colors: Dark background, light text
- Window size: 1280x720 minimum

**Recording Tool**: OBS Studio or similar
- Format: MP4
- Resolution: 1920x1080 or 1280x720
- Frame rate: 30 fps
- Audio: Clear voice narration

### Capture Checklist

- [ ] Terminal configured and visible
- [ ] chimera_core.py tested and working
- [ ] All three scenarios tested (positive/negative/neutral)
- [ ] Comparison mode tested
- [ ] Caption mode tested
- [ ] Recording software configured
- [ ] Quiet environment for narration
- [ ] Script practiced and timed

### Backup Plans

**If ML model fails**: Use keyword fallback (already implemented)
**If API unavailable**: Use local LLM or mock responses (already implemented)
**If demo crashes**: Have backup terminal ready with cached outputs

---

## Post-Production Notes

### Editing Requirements

1. **Trim**: Remove any mistakes or dead air
2. **Transitions**: Clean cuts between scenarios
3. **Captions**: Add captions for accessibility (meta!)
4. **Overlay**: Consider text overlays for key points
5. **Duration**: Target exactly 3 minutes

### Export Settings

- **Format**: MP4 (H.264)
- **Resolution**: 1920x1080 (downscale to 1280x720 if needed)
- **Bitrate**: 5-8 Mbps
- **Audio**: AAC, 128 kbps, 48 kHz

### Files Generated

1. `demo_final.mp4` - Final edited demo (3:00)
2. `demo_raw.mp4` - Raw capture (for reference)
3. `demo_script.md` - This script
4. `demo_screenshots/` - Key screenshots

---

## Success Criteria

The demo is successful if it demonstrates:

✅ Sentiment detection working (positive/negative/neutral)
✅ Adaptive routing based on sentiment
✅ Difference between adaptive and non-adaptive modes
✅ Accessibility features (caption formatting)
✅ Clear explanation of core innovation
✅ Professional presentation

---

## Alternative Short Version (1 Minute)

If time is limited, use this condensed version:

**0:00-0:10**: Introduction
**0:10-0:25**: Positive sentiment example
**0:25-0:40**: Negative sentiment example
**0:40-0:50**: Comparison mode
**0:50-1:00**: Conclusion

---

**Script Status**: ✅ READY FOR CAPTURE
**Date**: April 9, 2026
**Estimated Capture Time**: 30 minutes (including practice)
**Estimated Edit Time**: 1 hour
**Total Time Investment**: ~1.5 hours

# Screenshot Package - Project Chimera Demo

**Date**: April 9, 2026
**Purpose**: Week 5 - Key Screenshots for Evidence Pack
**Status**: READY FOR CAPTURE

## Overview

This package contains **5 key screenshots** from the chimera_core.py demonstration, with annotations highlighting the core adaptive AI functionality.

---

## Required Screenshots

### 1. Positive Sentiment Detection

**File**: `positive_sentiment.png`

**Command**:
```bash
cd services/operator-console
python chimera_core.py "I'm so excited about this project!"
```

**What to Capture**:
- Terminal showing full pipeline output
- Highlight "Sentiment: POSITIVE"
- Highlight "Routing: momentum_build"
- Highlight "Tone: enthusiastic"

**Annotation Points**:
- [1] Input text visible
- [2] Sentiment analysis result (POSITIVE)
- [3] Adaptive routing strategy (momentum_build)
- [4] Generated dialogue showing enthusiastic response

---

### 2. Negative Sentiment Detection

**File**: `negative_sentiment.png`

**Command**:
```bash
python chimera_core.py "I'm really frustrated with things."
```

**What to Capture**:
- Terminal showing full pipeline output
- Highlight "Sentiment: NEGATIVE"
- Highlight "Routing: supportive_care"
- Highlight "Tone: reassuring"

**Annotation Points**:
- [1] Input text visible
- [2] Sentiment analysis result (NEGATIVE)
- [3] Adaptive routing strategy (supportive_care)
- [4] Generated dialogue showing empathetic response

---

### 3. Neutral Sentiment Detection

**File**: `neutral_sentiment.png`

**Command**:
```bash
python chimera_core.py "Can you tell me more about the system?"
```

**What to Capture**:
- Terminal showing full pipeline output
- Highlight "Sentiment: NEUTRAL"
- Highlight "Routing: standard_response"
- Highlight "Tone: professional"

**Annotation Points**:
- [1] Input text visible
- [2] Sentiment analysis result (NEUTRAL)
- [3] Adaptive routing strategy (standard_response)
- [4] Generated dialogue showing professional response

---

### 4. Comparison Mode

**File**: `comparison_mode.png`

**Command**:
```bash
python chimera_core.py compare "I'm so excited!"
```

**What to Capture**:
- Terminal showing side-by-side comparison
- Highlight "WITH ADAPTATION" section
- Highlight "WITHOUT ADAPTATION" section
- Highlight "KEY DIFFERENCE" section

**Annotation Points**:
- [1] Adaptive response (enthusiastic)
- [2] Non-adaptive response (standard)
- [3] Clear difference highlighted
- [4] Sentiment detection shown

---

### 5. Caption Mode

**File**: `caption_mode.png`

**Command**:
```bash
python chimera_core.py caption "I'm so excited!"
```

**What to Capture**:
- Terminal showing formatted caption box
- Highlight "POSITIVE" label
- Highlight visual border
- Highlight readable text formatting

**Annotation Points**:
- [1] Caption box with border
- [2] Sentiment indicator (POSITIVE)
- [3] Formatted text with line breaks
- [4] High contrast formatting

---

## Capture Guidelines

### Technical Setup

**Terminal Settings**:
- Font: Monospace (size 14-16)
- Colors: Dark background, light text
- Window size: 1280x720 minimum
- Transparency: 100% opacity

**Capture Tool**:
- Linux: `gnome-screenshot` or `scrot`
- macOS: Built-in screenshot (Cmd+Shift+4)
- Windows: Snipping Tool or Win+Shift+S

**Image Specifications**:
- Format: PNG (lossless)
- Resolution: 1920x1080 or 1280x720
- Quality: Highest available
- File size: <500KB per screenshot

### Composition Tips

1. **Clear the terminal** before each capture
2. **Maximize the window** for best visibility
3. **Hide unrelated windows**
4. **Use consistent styling** across all screenshots
5. **Capture full output** including prompts

---

## Annotation Guide

### Adding Annotations

**Tool Options**:
- **Linux**: Shutter, Gwenview
- **macOS**: Preview, Skitch
- **Windows**: Paint, Snipping Tool annotation
- **Online**: Canva, Figma

**Annotation Style**:
- Color: Bright red or yellow (#FF0000 or #FFFF00)
- Font: Sans-serif (Arial, Helvetica)
- Size: 14-18pt
- Style: Clean arrows, clear text

### Annotation Template

For each screenshot, add:
1. **Title** at top (e.g., "Positive Sentiment Detection")
2. **Numbered markers** (1, 2, 3, 4) pointing to key elements
3. **Brief labels** explaining each marker
4. **Project Chimera branding** (bottom right)

---

## Automated Capture Script

An automated screenshot capture script is provided:

```bash
cd evidence/evidence_pack/screenshots
bash capture_screenshots.sh
```

This script will:
1. Launch chimera_core.py for each scene
2. Provide clear instructions for each capture
3. Ensure consistent naming with timestamps
4. Guide you through all 5 screenshots sequentially

### Manual Capture (Alternative)

If you prefer manual capture:

```bash
#!/bin/bash
# screenshot_capture.sh

cd services/operator-console

# Clear terminal
clear

# Screenshot 1: Positive Sentiment
echo "Capturing positive sentiment..."
python chimera_core.py "I'm so excited!"
# Take screenshot manually
sleep 1

# Screenshot 2: Negative Sentiment
echo "Capturing negative sentiment..."
python chimera_core.py "I'm frustrated."
# Take screenshot manually
sleep 1

# Screenshot 3: Neutral Sentiment
echo "Capturing neutral sentiment..."
python chimera_core.py "Tell me more."
# Take screenshot manually
sleep 1

# Screenshot 4: Comparison Mode
echo "Capturing comparison mode..."
python chimera_core.py compare "I'm excited!"
# Take screenshot manually
sleep 1

# Screenshot 5: Caption Mode
echo "Capturing caption mode..."
python chimera_core.py caption "I'm excited!"
# Take screenshot manually

echo "All screenshots captured!"
mv *.png ../../evidence/evidence_pack/screenshots/
```

---

## Quality Checklist

For each screenshot, verify:

- [ ] Terminal output is clearly visible
- [ ] Key elements are in focus
- [ ] No unrelated windows visible
- [ ] Consistent styling across all screenshots
- [ ] File size is reasonable (<500KB)
- [ ] Resolution is adequate (1280x720 minimum)
- [ ] Format is PNG (not JPG with artifacts)
- [ ] Annotations are clear and readable

---

## Post-Processing

### Cropping

Crop screenshots to:
- Remove terminal window borders
- Focus on actual content
- Maintain consistent aspect ratio
- Use 16:9 aspect ratio if possible

### Optimization

Optimize for web delivery:
- Use PNG optimization tool
- Target file size: 100-300KB each
- Maintain visual quality
- Test on different displays

---

## Delivery Checklist

- [ ] All 5 screenshots captured
- [ ] Each screenshot follows naming convention
- [ ] Annotations added (or planned)
- [ ] File sizes optimized
- [ ] Verified for clarity and quality
- [ ] Organized in screenshots/ directory
- [ ] Added to evidence pack index

---

## Usage in Evidence Pack

These screenshots will be used in:

1. **Grant Closeout Report**: Visual evidence of functionality
2. **Demo Video**: As alternative to video capture
3. **Presentation Materials**: For grant committee
4. **Documentation**: To illustrate key features

---

**Screenshot Package Status**: ⏳ READY FOR CAPTURE
**Time Estimate**: 30 minutes (including capture and basic annotation)
**Priority**: HIGH - Week 5 deliverable
**Dependencies**: chimera_core.py working (✅ VERIFIED)

---

**Last Updated**: April 9, 2026
**Next Action**: Execute capture or use batch script
**Review Date**: Week 6 (before final assembly)

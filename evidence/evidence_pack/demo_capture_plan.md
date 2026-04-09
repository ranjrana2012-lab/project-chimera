# Demo Capture Execution Plan

**Date**: April 9, 2026
**Purpose**: Week 5 - Screen Capture Execution
**Status**: Ready to Execute

## Pre-Capture Checklist

### Environment Setup

- [ ] **Terminal Configuration**
  - [ ] Open terminal with dark background
  - [ ] Set monospace font (size 14-16)
  - [ ] Resize window to 1280x720 minimum
  - [ ] Test readability from recording distance

- [ ] **Working Directory**
  - [ ] `cd services/operator-console`
  - [ ] Verify `chimera_core.py` exists
  - [ ] Test script runs without errors

- [ ] **Dependencies Check**
  - [ ] Python 3.12+ installed
  - [ ] Required packages available
  - [ ] Optional: GLM API key configured
  - [ ] Optional: Ollama running (if using local LLM)

### Recording Setup

- [ ] **Software**: OBS Studio (or similar)
  - [ ] Install OBS Studio
  - [ ] Configure display capture
  - [ ] Set recording area to terminal window
  - [ ] Test capture quality

- [ ] **Recording Settings**
  - [ ] Format: MP4
  - [ ] Resolution: 1920x1080 (or 1280x720)
  - [ ] Frame rate: 30 fps
  - [ ] Bitrate: 5-8 Mbps
  - [ ] Audio: Microphone configured

- [ ] **Storage**
  - [ ] 2GB free disk space minimum
  - [ ] Output directory created: `evidence/evidence_pack/demo/`

### Content Preparation

- [ ] **Script Review**
  - [ ] Read demo script (demo_script.md)
  - [ ] Practice narration timing
  - [ ] Memorize key transition points

- [ ] **Test Runs**
  - [ ] Run positive sentiment scenario
  - [ ] Run negative sentiment scenario
  - [ ] Run neutral sentiment scenario
  - [ ] Run comparison mode
  - [ ] Run caption mode

## Capture Procedure

### Step 1: Warm-up (5 minutes)

```bash
# Navigate to working directory
cd /home/ranj/Project_Chimera/services/operator-console

# Test basic functionality
python chimera_core.py "test input"
# Should see full pipeline output
```

**Verify**:
- [ ] Sentiment analysis returns result
- [ ] Dialogue generation returns result
- [ ] Adaptive rules are applied
- [ ] Output is clearly visible

### Step 2: Scene 1 - Introduction (20 sec)

**Action**:
1. Start recording in OBS
2. Clear terminal screen
3. Run: `ls -la chimera_core.py`
4. Deliver narration: "Welcome to Project Chimera..."
5. Stop recording (or mark section)

**File**: `demo_scene1_intro.mp4`

### Step 3: Scene 2 - Positive Sentiment (30 sec)

**Action**:
1. Start recording
2. Clear terminal screen
3. Run: `python chimera_core.py "I'm so excited about this project! It's going to be amazing!"`
4. Observe output
5. Deliver narration: "Watch what happens..."
6. Stop recording

**File**: `demo_scene2_positive.mp4`

**Expected Output Verification**:
- [ ] Sentiment: POSITIVE
- [ ] Score: +0.XX
- [ ] Routing: momentum_build
- [ ] Tone: enthusiastic

### Step 4: Scene 3 - Negative Sentiment (30 sec)

**Action**:
1. Start recording
2. Clear terminal screen
3. Run: `python chimera_core.py "I'm really frustrated with how things are going."`
4. Observe output
5. Deliver narration: "Now watch with negative input..."
6. Stop recording

**File**: `demo_scene3_negative.mp4`

**Expected Output Verification**:
- [ ] Sentiment: NEGATIVE
- [ ] Score: -0.XX
- [ ] Routing: supportive_care
- [ ] Tone: reassuring

### Step 5: Scene 4 - Neutral Sentiment (30 sec)

**Action**:
1. Start recording
2. Clear terminal screen
3. Run: `python chimera_core.py "Can you tell me more about the system?"`
4. Observe output
5. Deliver narration: "With neutral input..."
6. Stop recording

**File**: `demo_scene4_neutral.mp4`

**Expected Output Verification**:
- [ ] Sentiment: NEUTRAL
- [ ] Score: 0.00
- [ ] Routing: standard_response
- [ ] Tone: professional

### Step 6: Scene 5 - Comparison Mode (30 sec)

**Action**:
1. Start recording
2. Clear terminal screen
3. Run: `python chimera_core.py compare "I'm so excited!"`
4. Observe comparison output
5. Deliver narration: "Let me show you side-by-side..."
6. Stop recording

**File**: `demo_scene5_compare.mp4`

**Expected Output Verification**:
- [ ] Shows adaptive response
- [ ] Shows non-adaptive response
- [ ] Displays key difference

### Step 7: Scene 6 - Caption Mode (20 sec)

**Action**:
1. Start recording
2. Clear terminal screen
3. Run: `python chimera_core.py caption "I'm so excited!"`
4. Observe caption box
5. Deliver narration: "Accessibility features..."
6. Stop recording

**File**: `demo_scene6_caption.mp4`

**Expected Output Verification**:
- [ ] Caption box displayed
- [ ] High contrast formatting
- [ ] Sentiment indicator visible

### Step 8: Scene 7 - Conclusion (20 sec)

**Action**:
1. Start recording
2. Clear terminal screen
3. Show: `python chimera_core.py --version`
4. Deliver narration: "Project Chimera demonstrates..."
5. Stop recording

**File**: `demo_scene7_conclusion.mp4`

## Post-Capture Processing

### Immediate Tasks

1. **Verify Recordings**
   - [ ] Check all scene files exist
   - [ ] Verify each scene plays correctly
   - [ ] Check audio quality
   - [ ] Note any issues for editing

2. **Create Screenshot Package**
   - [ ] Capture 3-5 key screenshots
   - [ ] Save to `evidence/evidence_pack/screenshots/`
   - [ ] Name descriptively (e.g., `positive_sentiment.png`)

3. **Backup Raw Files**
   - [ ] Copy all scene files to backup location
   - [ ] Verify backup integrity

### Editing Tasks (Week 5-6)

1. **Rough Cut**
   - [ ] Import all scenes into video editor
   - [ ] Trim to exact timings
   - [ ] Arrange in sequence
   - [ ] Add transitions between scenes

2. **Audio Enhancement**
   - [ ] Normalize audio levels
   - [ ] Remove background noise
   - [ ] Add captions for accessibility
   - [ ] Mix background music (optional)

3. **Final Polish**
   - [ ] Add title overlay
   - [ ] Add text highlights for key points
   - [ ] Color correction if needed
   - [ ] Export final version

## Troubleshooting

### Common Issues

**Issue**: Script crashes with import error
**Solution**: 
```bash
cd services/operator-console
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python chimera_core.py "test"
```

**Issue**: ML model fails to load
**Solution**: Script automatically falls back to keyword analysis. No action needed.

**Issue**: API unavailable
**Solution**: Script automatically falls back to local LLM or mock responses. No action needed.

**Issue**: Terminal output too small
**Solution**: Increase font size or terminal window size before recording.

**Issue**: Recording audio quality poor
**Solution**: Use external microphone or record narration separately (voiceover).

## Backup Plans

### If Script Fails Completely

**Plan B**: Use cached screenshot/video from previous run
**Location**: `evidence/evidence_pack/demo/backup/`

### If Recording Fails

**Plan B**: Use screen capture images with voiceover slideshow
**Tools**: ffmpeg, simple video editor

### If Time Runs Out

**Plan B**: Use 1-minute condensed version (see demo_script.md)

## Completion Checklist

- [ ] All 7 scenes captured
- [ ] Each scene verified for quality
- [ ] Screenshots captured and saved
- [ ] Raw files backed up
- [ ] Editing timeline created
- [ ] Audio narration recorded (or live)
- [ ] Final demo exported (3:00 duration)
- [ ] Demo uploaded to evidence folder

---

**Capture Plan Status**: ✅ READY TO EXECUTE
**Estimated Time**: 2-3 hours (including setup and editing)
**Priority**: HIGH - Week 5 deliverable
**Dependencies**: None (script is self-contained)

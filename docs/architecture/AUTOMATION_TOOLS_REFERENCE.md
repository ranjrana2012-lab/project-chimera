# Automation Tools Quick Reference

**Date**: April 9, 2026
**Purpose**: Quick reference for all automation tools
**Status**: Ready for Use

---

## Overview

This document provides a **quick reference** for all automation tools created to complete the remaining 3% of the Project Chimera implementation.

---

## Tool 1: Demo Capture Automation

**File**: `evidence/evidence_pack/capture_demo.py`
**Purpose**: Automated demo scene capture
**Time Savings**: ~1 hour

### Usage

```bash
cd evidence/evidence_pack
python capture_demo.py
```

### Options

```bash
# Capture all scenes
python capture_demo.py

# Capture specific scene
python capture_demo.py --scene 2

# Custom output directory
python capture_demo.py --output ../demo_footage
```

### What It Does

- Launches chimera_core.py for each scene
- Feeds appropriate inputs automatically
- Captures terminal output to text files
- Generates summary report
- Supports batch or single-scene modes

### Output

- Scene files: `scene_01_intro_TIMESTAMP.txt`, etc.
- Summary: `capture_summary_TIMESTAMP.md`
- Location: `demo_footage/` (default)

---

## Tool 2: Screenshot Capture Automation

**File**: `evidence/evidence_pack/screenshots/capture_screenshots.sh`
**Purpose**: Interactive screenshot capture guidance
**Time Savings**: ~30 minutes

### Usage

```bash
cd evidence/evidence_pack/screenshots
bash capture_screenshots.sh
```

### What It Does

- Provides step-by-step guidance for each screenshot
- Launches chimera_core.py for each scene
- Gives clear instructions for capture timing
- Ensures consistent naming with timestamps
- Guides through all 5 required screenshots

### Screenshots Captured

1. Intro/Banner
2. Positive Sentiment
3. Negative Sentiment
4. Comparison Mode
5. Caption Mode

### Output

- Files: `01_intro_banner_TIMESTAMP.png`, etc.
- Location: `screenshots/` directory

---

## Tool 3: Budget Helper

**File**: `evidence/budget/budget_helper.py`
**Purpose**: Interactive budget tracking completion
**Time Savings**: ~45 minutes

### Usage

```bash
cd evidence/budget
python budget_helper.py --interactive
```

### What It Does

- Provides interactive interface for data entry
- Organizes expenditures by category
- Calculates totals automatically
- Generates filled budget markdown
- Ensures consistent formatting

### Categories

1. Equipment Purchases
2. Software & Services
3. Development Time
4. Miscellaneous Expenses

### Output

- Filled budget: `budget_filled.md`
- Location: `evidence/budget/`

---

## Tool 4: Final Assembly Guide

**File**: `evidence/grant_closeout/final_assembly_guide.md`
**Purpose**: Step-by-step submission package assembly
**Time Savings**: ~1 hour

### Usage

```bash
# Read the guide
cat evidence/grant_closeout/final_assembly_guide.md

# Follow the step-by-step instructions
# (manual execution of commands)
```

### What It Does

- Provides complete assembly workflow
- Includes all copy commands
- Generates audit trail
- Creates archive with checksums
- Quality control checklist

### Output

- Submission directory: `project-chimera-submission/`
- Archive: `project-chimera-submission.zip`
- Checksums: `.sha256`, `.md5`

---

## Tool 5: Final Execution Guide

**File**: `EXECUTION_GUIDE_FINAL_STEPS.md`
**Purpose**: Complete workflow for remaining 3%
**Time Savings**: ~2 hours

### Usage

```bash
# Read the guide
cat EXECUTION_GUIDE_FINAL_STEPS.md

# Follow phases 1-5 sequentially
```

### What It Does

- Complete end-to-end workflow
- All 5 phases with step-by-step instructions
- Prerequisites and verification steps
- Timeline and success criteria
- Troubleshooting guidance

---

## Execution Order

### Recommended Sequence

1. **Read** `EXECUTION_GUIDE_FINAL_STEPS.md` (5 minutes)
2. **Execute** Phase 1: Demo Video Capture (2-3 hours)
   - Use `capture_demo.py` for automation
   - Follow `demo_polish_guide.md` for editing
3. **Execute** Phase 2: Screenshot Capture (1 hour)
   - Use `capture_screenshots.sh` for automation
4. **Execute** Phase 3: Budget Finalization (1 hour)
   - Use `budget_helper.py --interactive`
5. **Execute** Phase 4: Final Assembly (1.5 hours)
   - Follow `final_assembly_guide.md`
6. **Execute** Phase 5: Final Verification (30 minutes)
   - Complete all checklists

### Total Time: 5.5-7.5 hours

---

## Quick Start Commands

```bash
# 1. Demo capture (2-3 hours)
cd evidence/evidence_pack
python capture_demo.py --output ../../demo_footage

# 2. Screenshot capture (1 hour)
cd screenshots
bash capture_screenshots.sh

# 3. Budget completion (1 hour)
cd ../../../budget
python budget_helper.py --interactive

# 4. Final assembly (1.5 hours)
cd ..
# Follow final_assembly_guide.md
```

---

## Tool Dependencies

All tools require:

- ✅ Python 3.10+
- ✅ chimera_core.py working
- ✅ Bash shell (for .sh scripts)
- ✅ Required packages installed

**No additional dependencies required**

---

## Verification

After using each tool, verify:

**Demo Capture:**
- [ ] All 7 scene files created
- [ ] Summary report generated
- [ ] Output files contain expected content

**Screenshot Capture:**
- [ ] All 5 screenshots captured
- [ ] Files named correctly
- [ ] Images are clear and readable

**Budget Helper:**
- [ ] All entries added
- [ ] Totals calculated
- [ ] Filled budget created

**Final Assembly:**
- [ ] All directories populated
- [ ] Archive created
- [ ] Checksums generated

---

## Troubleshooting

### Demo Capture Issues

**Problem**: chimera_core.py not found
**Solution**: Run from project root directory

**Problem**: Scene timing off
**Solution**: Adjust timing in demo_script.md

### Screenshot Capture Issues

**Problem**: Screenshots not capturing
**Solution**: Use system screenshot tool manually

**Problem**: Images blurry
**Solution**: Increase terminal font size

### Budget Helper Issues

**Problem**: Invalid input format
**Solution**: Use exact format specified (YYYY-MM-DD)

**Problem**: Totals incorrect
**Solution**: Verify all amounts entered correctly

---

## Support Resources

**Documentation:**
- `EXECUTION_GUIDE_FINAL_STEPS.md` - Complete workflow
- `IMPLEMENTATION_COMPLETE.md` - Status report
- `evidence/evidence_pack/demo_script.md` - Demo scenes
- `evidence/evidence_pack/demo_polish_guide.md` - Video editing

**Guides:**
- `evidence/grant_closeout/final_assembly_guide.md` - Assembly
- `evidence/grant_closeout/submission_checklist.md` - Checklist

---

## Success Criteria

Using these automation tools, the remaining 3% is complete when:

✅ Demo video captured and edited (3:00 duration)
✅ Screenshots captured (5 images)
✅ Budget tracking completed
✅ Submission package assembled
✅ Archive created and verified

---

**Automation Tools Status**: ✅ READY TO USE
**Time Estimate**: 5.5-7.5 hours (with tools)
**Without Tools**: 8-10 hours (manual)
**Time Savings**: ~2-3 hours

---

**Last Updated**: April 9, 2026
**Next Action**: Execute tools in sequence
**Completion Target**: 100% by end of session

#!/bin/bash
# Screenshot Capture Automation Script for Project Chimera
#
# This script helps capture the 5 key screenshots needed for the evidence pack.
# It provides timing prompts and ensures consistent naming.
#
# Usage: bash capture_screenshots.sh

set -e

# Configuration
SCREENSHOT_DIR="./screenshots"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CHIMERA_PATH="../../services/operator-console/chimera_core.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$SCREENSHOT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PROJECT CHIMERA - SCREENSHOT CAPTURE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Output Directory: $SCREENSHOT_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Check if chimera_core.py exists
if [ ! -f "$CHIMERA_PATH" ]; then
    echo -e "${RED}Error: chimera_core.py not found at $CHIMERA_PATH${NC}"
    echo "Please run from the correct directory."
    exit 1
fi

# Function to capture screenshot with prompt
capture_screenshot() {
    local scene_num=$1
    local scene_name=$2
    local input_text=$3
    local instructions=$4

    local filename="${SCREENSHOT_DIR}/$(printf '%02d' $scene_num)_${scene_name}_${TIMESTAMP}.png"

    echo -e "${YELLOW}========================================${NC}"
    echo -e "${GREEN}Scene $scene_num: $scene_name${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Instructions: $instructions"
    echo ""
    echo "Input to type: $input_text"
    echo ""
    echo -e "${BLUE}Press Enter when ready to capture...${NC}"
    read

    # Launch chimera_core.py in background
    cd "$(dirname "$CHIMERA_PATH")"
    python3 "$(basename "$CHIMERA_PATH")" &
    CHIMERA_PID=$!
    cd - > /dev/null

    # Give it time to start
    sleep 2

    # Provide instructions for screenshot
    echo ""
    echo -e "${GREEN}>>> chimera_core.py is running${NC}"
    echo -e "${YELLOW}>>> Type the following input: $input_text${NC}"
    echo -e "${YELLOW}>>> Wait for the response${NC}"
    echo -e "${YELLOW}>>> Take a screenshot (use your screenshot tool)${NC}"
    echo -e "${YELLOW}>>> Save as: $filename${NC}"
    echo ""
    echo -e "${BLUE}Press Enter when screenshot is captured...${NC}"
    read

    # Kill chimera_core.py
    kill $CHIMERA_PID 2>/dev/null || true
    wait $CHIMERA_PID 2>/dev/null || true

    echo -e "${GREEN}✓ Scene $scene_num captured${NC}"
    echo ""
    sleep 1
}

# Screenshot 1: Intro/Banner
capture_screenshot \
    1 \
    "intro_banner" \
    "(just view the banner)" \
    "Capture the Project Chimera banner that appears on startup. Make sure the full title and ASCII art are visible."

# Screenshot 2: Positive Sentiment
capture_screenshot \
    2 \
    "positive_sentiment" \
    "I'm so excited to be here! This is amazing!" \
    "Type the positive input and capture the response showing POSITIVE sentiment detection and momentum_build strategy."

# Screenshot 3: Negative Sentiment
capture_screenshot \
    3 \
    "negative_sentiment" \
    "I'm feeling worried about everything going wrong." \
    "Type the negative input and capture the response showing NEGATIVE sentiment detection and supportive_care strategy."

# Screenshot 4: Comparison Mode
capture_screenshot \
    4 \
    "comparison_mode" \
    "compare\nI love this performance!" \
    "Type 'compare' first, then type the positive input. Capture the side-by-side comparison showing adaptive vs non-adaptive responses."

# Screenshot 5: Caption Mode
capture_screenshot \
    5 \
    "caption_mode" \
    "caption\nThis is wonderful!" \
    "Type 'caption' first, then type the input. Capture the high-contrast caption formatting showing accessibility features."

# Final summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}SCREENSHOT CAPTURE COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Captured screenshots:"
ls -lh "$SCREENSHOT_DIR"/*.png 2>/dev/null || echo "No PNG files found"
echo ""
echo "Next steps:"
echo "1. Verify all screenshots are clear and readable"
echo "2. Rename if needed (already named correctly)"
echo "3. Add to evidence_pack/screenshots/ directory"
echo "4. Update submission_checklist.md"
echo ""
echo -e "${GREEN}Done!${NC}"

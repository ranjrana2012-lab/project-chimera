#!/bin/bash
# Print Demo Materials Preparation Script
# Prepares all necessary handouts and cheat sheets for the 4pm demo

set -e

echo "=== Project Chimera - Demo Materials Preparation ==="
echo ""

# Create output directory
OUTPUT_DIR="demo-materials-$(date +%Y-%m-%d)"
mkdir -p "$OUTPUT_DIR"

echo "📁 Created output directory: $OUTPUT_DIR"
echo ""

# Files to copy
FILES=(
    "docs/getting-started/monday-demo/student-handout.md"
    "docs/getting-started/monday-demo/demo-commands-cheat-sheet.md"
    "docs/getting-started/monday-demo/4pm-demo-script.md"
    "Student_Quick_Start.md"
)

echo "📄 Copying demo materials..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$OUTPUT_DIR/"
        echo "  ✅ Copied: $file"
    else
        echo "  ❌ Not found: $file"
    fi
done

echo ""
echo "🖨️  PRINTING INSTRUCTIONS:"
echo ""
echo "1. Student Handout (student-handout.md):"
echo "   - Copies needed: 12 (10 students + 2 spare)"
echo "   - Print: Double-sided recommended"
echo "   - This is the main handout for students"
echo ""
echo "2. Demo Commands Cheat Sheet (demo-commands-cheat-sheet.md):"
echo "   - Copies needed: 1 (for you, the presenter)"
echo "   - Print: Single-sided, keep at podium"
echo "   - Contains all commands for the live demo"
echo ""
echo "3. 4pm Demo Script (4pm-demo-script.md):"
echo "   - Copies needed: 1 (for you, the presenter)"
echo "   - Print: Single-sided, use during presentation"
echo "   - Full 60-minute demo script with timing"
echo ""
echo "4. Student Quick Start (Student_Quick_Start.md):"
echo "   - Copies needed: Optional reference during Q&A"
echo "   - Students will access this online"
echo ""
echo "=== PREPARATION COMPLETE ==="
echo ""
echo "📂 All files ready in: $OUTPUT_DIR/"
echo ""
echo "Quick print command (if you have lp):"
echo "  lpr -# 12 $OUTPUT_DIR/student-handout.md"
echo "  lpr $OUTPUT_DIR/demo-commands-cheat-sheet.md"
echo "  lpr $OUTPUT_DIR/4pm-demo-script.md"
echo ""
echo "Or open the folder:"
echo "  cd $OUTPUT_DIR && ls -la"
echo ""

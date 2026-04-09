#!/usr/bin/env python3
"""
Screen Capture Script for Chimera Core Comparison Mode

This script runs the chimera_core.py comparison mode with predefined inputs
to generate evidence of adaptive vs non-adaptive behavior.

Output: Terminal captures saved as text files for evidence documentation.
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Predefined test inputs covering all sentiment categories
TEST_INPUTS = [
    ("positive", "I'm so excited about this project! It's going to be amazing!"),
    ("negative", "I'm really frustrated and disappointed with how things are going."),
    ("neutral", "Can you tell me more about the system architecture?"),
]


async def capture_comparison(category: str, input_text: str):
    """Capture comparison output for a single input."""
    print(f"\n{'=' * 60}")
    print(f"Capturing: {category.upper()} - {input_text[:50]}...")
    print(f"{'=' * 60}\n")

    # Run chimera_core.py in comparison mode
    result = subprocess.run(
        [sys.executable, "chimera_core.py", "compare", input_text],
        capture_output=True,
        text=True,
        timeout=60
    )

    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"comparison_{category}_{timestamp}.txt")

    # Save output
    output_file.write_text(result.stdout)

    print(f"✓ Saved: {output_file}")
    print(f"  Size: {len(result.stdout)} characters")

    # Extract key metrics for summary
    lines = result.stdout.split('\n')
    for i, line in enumerate(lines):
        if "Detected Sentiment:" in line:
            print(f"  Sentiment: {lines[i].split(':')[1].strip()}")
        if "Score:" in line and "Confidence:" in lines[i+1] if i+1 < len(lines) else False:
            print(f"  Score: {line.split(':')[1].strip()}")
            print(f"  Confidence: {lines[i+1].split(':')[1].strip()}")

    return output_file


async def main():
    """Run all comparison captures."""
    print("\n" + "=" * 60)
    print(" CHIMERA CORE - Screen Capture Script")
    print(" Generating comparison evidence for all sentiment types")
    print("=" * 60)

    results = []

    for category, input_text in TEST_INPUTS:
        try:
            output_file = await capture_comparison(category, input_text)
            results.append((category, output_file))
        except Exception as e:
            print(f"✗ Error capturing {category}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(" CAPTURE SUMMARY")
    print("=" * 60)
    print(f"\nTotal captures: {len(results)}/{len(TEST_INPUTS)}")

    for category, output_file in results:
        print(f"  ✓ {category.upper()}: {output_file}")

    print("\n" + "=" * 60)
    print("Evidence files ready for grant documentation.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

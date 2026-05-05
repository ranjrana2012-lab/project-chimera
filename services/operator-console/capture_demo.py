#!/usr/bin/env python3
"""
Demo Video Capture Script for Project Chimera Phase 1

This script automates local demo scene capture for maintainer review.
It runs the chimera_core.py through all demo scenarios and saves the output.

Usage:
    python3 capture_demo.py [--output-dir DIR]
"""

import asyncio
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import argparse


async def capture_scene(scene_name: str, command: list, output_dir: Path):
    """Capture a single demo scene."""
    print(f"\n{'=' * 60}")
    print(f"Capturing Scene: {scene_name}")
    print(f"{'=' * 60}\n")

    # Run the command
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120
    )

    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"scene_{scene_name}_{timestamp}.txt"
    output_file.write_text(result.stdout)

    print(f"✓ Captured: {output_file.name}")
    print(f"  Size: {len(result.stdout)} characters")

    return output_file, result.stdout


async def main():
    """Capture all demo scenes."""
    parser = argparse.ArgumentParser(description="Capture demo scenes")
    parser.add_argument("--output-dir", default="demo_captures", help="Output directory")
    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print(" PROJECT CHIMERA - Demo Video Capture")
    print("=" * 60)
    print(f"Output Directory: {output_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    # Scene 1: Introduction (show script header)
    scene_1_file, _ = await capture_scene(
        "01_introduction",
        ["head", "-20", "chimera_core.py"],
        output_dir
    )
    results.append(("Scene 1: Introduction", scene_1_file))

    time.sleep(2)

    # Scene 2: Pipeline explanation
    pipeline_output = """=== Project Chimera Pipeline ===

1. Text Input → Sentiment Analysis (DistilBERT ML Model)
   - Detects emotional state (positive/negative/neutral)
   - 6-dimensional emotion vector (joy, surprise, neutral, sadness, anger, fear)
   - Confidence score: 0.0 to 1.0

2. Sentiment → Adaptive Dialogue Generation
   - Configured dialogue provider when available
   - Deterministic local fallback for repeatable demos

3. Sentiment → Routing Strategy Selection
   - Positive → momentum_build (enthusiastic)
   - Negative → supportive_care (empathetic)
   - Neutral → standard_response (professional)

Total Pipeline Latency: ~300-500ms (after model load)
"""
    scene_2_file = output_dir / "scene_02_pipeline.txt"
    scene_2_file.write_text(pipeline_output)
    print(f"\n✓ Created: {scene_2_file.name}")
    results.append(("Scene 2: Pipeline", scene_2_file))

    # Scene 3: Sentiment Detection (demo mode)
    print(f"\n{'=' * 60}")
    print("Capturing Scene: 03_sentiment_detection")
    print(f"{'=' * 60}\n")
    print("Running chimera_core.py demo mode...")
    print("(This may take 30-60 seconds with model loading)\n")

    result = subprocess.run(
        [sys.executable, "chimera_core.py", "demo"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path(__file__).parent
    )

    scene_3_file = output_dir / "scene_03_sentiment_detection.txt"
    scene_3_file.write_text(result.stdout)
    print(f"\n✓ Captured: {scene_3_file.name}")
    results.append(("Scene 3: Sentiment Detection", scene_3_file))

    time.sleep(2)

    # Scene 4: Adaptive Routing (comparison mode)
    # Capture positive sentiment comparison
    print(f"\n{'=' * 60}")
    print("Capturing Scene: 04_adaptive_routing_positive")
    print(f"{'=' * 60}\n")

    result = subprocess.run(
        [sys.executable, "chimera_core.py", "compare",
         "I'm so excited about this project!"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=Path(__file__).parent
    )

    scene_4a_file = output_dir / "scene_04a_adaptive_positive.txt"
    scene_4a_file.write_text(result.stdout)
    print(f"✓ Captured: {scene_4a_file.name}")
    results.append(("Scene 4a: Adaptive Routing (Positive)", scene_4a_file))

    time.sleep(2)

    # Capture negative sentiment comparison
    print(f"\n{'=' * 60}")
    print("Capturing Scene: 04_adaptive_routing_negative")
    print(f"{'=' * 60}\n")

    result = subprocess.run(
        [sys.executable, "chimera_core.py", "compare",
         "I'm really frustrated with how things are going."],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=Path(__file__).parent
    )

    scene_4b_file = output_dir / "scene_04b_adaptive_negative.txt"
    scene_4b_file.write_text(result.stdout)
    print(f"✓ Captured: {scene_4b_file.name}")
    results.append(("Scene 4b: Adaptive Routing (Negative)", scene_4b_file))

    time.sleep(2)

    # Scene 5: Accessibility Features (caption mode)
    print(f"\n{'=' * 60}")
    print("Capturing Scene: 05_accessibility")
    print(f"{'=' * 60}\n")

    result = subprocess.run(
        [sys.executable, "chimera_core.py", "caption",
         "That's wonderful to hear!"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=Path(__file__).parent
    )

    scene_5_file = output_dir / "scene_05_accessibility.txt"
    scene_5_file.write_text(result.stdout)
    print(f"✓ Captured: {scene_5_file.name}")
    results.append(("Scene 5: Accessibility", scene_5_file))

    # Scene 6: Summary
    summary_output = f"""=== Project Chimera Phase 1 - Local Demo Summary ===

Date: {datetime.now().strftime('%Y-%m-%d')}
Scope: Local maintainer evidence capture

=== Demo Behaviours ===
• CLI demo exercises positive, negative, and neutral routing
• Compare mode shows baseline and adaptive output
• Caption mode writes an SRT file in the working directory
• Web API evidence is captured separately through the Phase 1 helper

=== Verification ===
• Smoke demo
• Focused pytest contracts
• Privacy preflight
• Maintainer review before public release

=== Evidence Storage ===
• Generated logs and captures belong under internal/phase1-evidence/
• Receipts, invoices, and grant records stay private and local
• Public commits should include source, tests, and non-sensitive docs only

=== Git Repository ===
• Branch: main
• Public source set must pass the privacy preflight before commit

=== Status ===
✅ Demo capture generated locally
✅ Evidence intended for private maintainer review
✅ Public/private separation required before publishing
"""

    scene_6_file = output_dir / "scene_06_summary.txt"
    scene_6_file.write_text(summary_output)
    print(f"\n✓ Created: {scene_6_file.name}")
    results.append(("Scene 6: Summary", scene_6_file))

    # Summary
    print("\n" + "=" * 60)
    print(" CAPTURE SUMMARY")
    print("=" * 60)
    print(f"\nTotal Scenes Captured: {len(results)}")
    print(f"Output Directory: {output_dir}")

    for scene_name, output_file in results:
        print(f"  ✓ {scene_name}: {output_file.name}")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("\n1. Review captured scenes for quality")
    print("2. Record voiceover using DEMO_SCRIPT.md")
    print("3. Edit captures into final demo video")
    print("4. Add titles, transitions, and music")
    print("5. Store final recordings under internal/phase1-evidence/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

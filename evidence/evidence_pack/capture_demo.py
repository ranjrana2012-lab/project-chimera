#!/usr/bin/env python3
"""
Demo Capture Automation Script for Project Chimera

This script automates the capture of demo scenes for the grant closeout video.
It runs chimera_core.py with predefined inputs and captures terminal output.

Usage:
    python capture_demo.py [--scene SCENE_NUMBER] [--output DIR]

Examples:
    python capture_demo.py              # Capture all scenes
    python capture_demo.py --scene 2    # Capture scene 2 only
    python capture_demo.py --output ./demo_footage  # Custom output directory
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json


# Demo script configuration based on evidence/evidence_pack/demo_script.md
DEMO_SCENES = {
    1: {
        "name": "Intro",
        "duration": "0:20",
        "input": "Hello Project Chimera",
        "description": "System introduction and banner display",
        "mode": "interactive"
    },
    2: {
        "name": "Positive Sentiment",
        "duration": "0:30",
        "input": "I'm so excited to be here! This is amazing!",
        "description": "Demonstrates positive sentiment detection and momentum_build strategy",
        "mode": "interactive"
    },
    3: {
        "name": "Negative Sentiment",
        "duration": "0:30",
        "input": "I'm feeling worried about everything going wrong.",
        "description": "Demonstrates negative sentiment detection and supportive_care strategy",
        "mode": "interactive"
    },
    4: {
        "name": "Neutral Sentiment",
        "duration": "0:30",
        "input": "The weather is nice today.",
        "description": "Demonstrates neutral sentiment detection and standard_response strategy",
        "mode": "interactive"
    },
    5: {
        "name": "Comparison Mode",
        "duration": "0:30",
        "input": "I love this performance!",
        "description": "Side-by-side adaptive vs non-adaptive comparison",
        "mode": "compare"
    },
    6: {
        "name": "Caption Mode",
        "duration": "0:20",
        "input": "This is wonderful!",
        "description": "High-contrast caption formatting for accessibility",
        "mode": "caption"
    },
    7: {
        "name": "Outro",
        "duration": "0:20",
        "input": "quit",
        "description": "System exit and summary",
        "mode": "interactive"
    }
}


class DemoCapture:
    """Handles automated demo scene capture."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("./demo_footage")
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chimera_path = Path("services/operator-console/chimera_core.py")

    def capture_scene(self, scene_number: int) -> dict:
        """Capture a single demo scene.

        Args:
            scene_number: Scene number (1-7)

        Returns:
            Dictionary with capture results
        """
        if scene_number not in DEMO_SCENES:
            raise ValueError(f"Invalid scene number: {scene_number}")

        scene = DEMO_SCENES[scene_number]
        output_file = self.output_dir / f"scene_{scene_number:02d}_{scene['name'].lower().replace(' ', '_')}_{self.timestamp}.txt"

        print(f"\n{'='*60}")
        print(f"Capturing Scene {scene_number}: {scene['name']}")
        print(f"Description: {scene['description']}")
        print(f"Duration: {scene['duration']}")
        print(f"Input: {scene['input']}")
        print(f"Mode: {scene['mode']}")
        print(f"{'='*60}\n")

        # Prepare input for chimera_core.py
        if scene['mode'] == 'compare':
            full_input = f"compare\n{scene['input']}\n"
        elif scene['mode'] == 'caption':
            full_input = f"caption\n{scene['input']}\n"
        else:
            full_input = f"{scene['input']}\n"

        # Add quit for final scene
        if scene_number == 7:
            full_input = "quit\n"

        # Build command
        cmd = [sys.executable, str(self.chimera_path)]

        try:
            # Run chimera_core.py with input
            result = subprocess.run(
                cmd,
                input=full_input,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.chimera_path.parent
            )

            # Save output
            with open(output_file, 'w') as f:
                f.write(f"Scene {scene_number}: {scene['name']}\n")
                f.write(f"Input: {scene['input']}\n")
                f.write(f"Mode: {scene['mode']}\n")
                f.write(f"Timestamp: {self.timestamp}\n")
                f.write(f"\n{'='*60}\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write(f"\n{'='*60}\n")
                if result.stderr:
                    f.write("STDERR:\n")
                    f.write(result.stderr)

            print(f"✅ Scene {scene_number} captured successfully")
            print(f"   Output: {output_file}")

            return {
                "scene": scene_number,
                "name": scene['name'],
                "status": "success",
                "output_file": str(output_file),
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            print(f"⏱️  Scene {scene_number} timed out")
            return {
                "scene": scene_number,
                "name": scene['name'],
                "status": "timeout",
                "error": "Command timed out after 60 seconds"
            }
        except Exception as e:
            print(f"❌ Scene {scene_number} failed: {e}")
            return {
                "scene": scene_number,
                "name": scene['name'],
                "status": "error",
                "error": str(e)
            }

    def capture_all_scenes(self) -> list:
        """Capture all demo scenes in sequence.

        Returns:
            List of capture results
        """
        results = []

        print(f"\n{'='*60}")
        print("PROJECT CHIMERA - DEMO CAPTURE AUTOMATION")
        print(f"Output Directory: {self.output_dir}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Total Scenes: {len(DEMO_SCENES)}")
        print(f"{'='*60}\n")

        for scene_num in sorted(DEMO_SCENES.keys()):
            result = self.capture_scene(scene_num)
            results.append(result)

            # Brief pause between scenes
            if scene_num < len(DEMO_SCENES):
                print("\n⏸️  Pausing 3 seconds before next scene...\n")
                import time
                time.sleep(3)

        return results

    def generate_summary(self, results: list) -> Path:
        """Generate capture summary report.

        Args:
            results: List of capture results

        Returns:
            Path to summary file
        """
        summary_file = self.output_dir / f"capture_summary_{self.timestamp}.md"

        with open(summary_file, 'w') as f:
            f.write("# Demo Capture Summary\n\n")
            f.write(f"**Timestamp**: {self.timestamp}\n")
            f.write(f"**Total Scenes**: {len(results)}\n")
            f.write(f"**Successful**: {sum(1 for r in results if r['status'] == 'success')}\n")
            f.write(f"**Failed**: {sum(1 for r in results if r['status'] != 'success')}\n\n")

            f.write("## Scene Results\n\n")
            f.write("| Scene | Name | Status | Output File |\n")
            f.write("|-------|------|--------|-------------|\n")

            for result in results:
                status_emoji = "✅" if result['status'] == 'success' else "❌"
                output = result.get('output_file', 'N/A')
                f.write(f"| {result['scene']} | {result['name']} | {status_emoji} {result['status']} | {output} |\n")

            f.write("\n## Next Steps\n\n")
            f.write("1. Review captured output files\n")
            f.write("2. Record terminal sessions using asciinema or script\n")
            f.write("3. Follow demo_polish_guide.md for video editing\n")
            f.write("4. Create 3-minute final demo video\n")

        print(f"\n📊 Summary report: {summary_file}")
        return summary_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated demo capture for Project Chimera"
    )
    parser.add_argument(
        "--scene",
        type=int,
        choices=range(1, 8),
        help="Capture specific scene only (1-7)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./demo_footage"),
        help="Output directory for captured footage"
    )

    args = parser.parse_args()

    # Verify chimera_core.py exists
    chimera_path = Path("services/operator-console/chimera_core.py")
    if not chimra_path.exists():
        print(f"❌ Error: {chimera_path} not found")
        print("   Please run from Project Chimera root directory")
        sys.exit(1)

    # Create capture instance
    capture = DemoCapture(args.output)

    # Capture scenes
    if args.scene:
        print(f"Capturing single scene: {args.scene}")
        results = [capture.capture_scene(args.scene)]
    else:
        print("Capturing all scenes...")
        results = capture.capture_all_scenes()

    # Generate summary
    summary = capture.generate_summary(results)

    # Exit with appropriate code
    failed = sum(1 for r in results if r['status'] != 'success')
    if failed > 0:
        print(f"\n⚠️  {failed} scene(s) failed to capture")
        sys.exit(1)
    else:
        print(f"\n✅ All scenes captured successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()

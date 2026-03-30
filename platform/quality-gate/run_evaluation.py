#!/usr/bin/env python3
"""
Python runner for the anti-gaming evaluator.

This script is invoked by evaluate.sh and runs the actual evaluation,
writing results to evaluation_results.json for the shell script to parse.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the gate module to the path
gate_dir = Path(__file__).parent / "gate"
sys.path.insert(0, str(gate_dir))

from anti_gaming_evaluator import (
    AntiGamingEvaluator,
    BaselineMetrics,
    EvaluationOutcome,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the anti-gaming evaluation."""
    parser = argparse.ArgumentParser(
        description="Run anti-gaming quality evaluation for autonomous refactoring"
    )
    parser.add_argument(
        "--test-path",
        type=Path,
        default=Path("tests"),
        help="Path to test directory"
    )
    parser.add_argument(
        "--coverage-target",
        type=Path,
        default=None,
        help="Path to module for coverage measurement"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("baseline_metrics.json"),
        help="Path to baseline metrics JSON file"
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum coverage threshold"
    )
    parser.add_argument(
        "--enable-mutation",
        action="store_true",
        help="Enable mutation testing"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation_results.json"),
        help="Output path for evaluation results"
    )

    args = parser.parse_args()

    # Create evaluator
    evaluator = AntiGamingEvaluator(
        baseline_file=args.baseline,
        min_coverage=args.min_coverage,
        enable_mutation_testing=args.enable_mutation
    )

    # Run evaluation
    logger.info(f"Starting evaluation with test path: {args.test_path}")
    result = evaluator.evaluate(
        test_path=args.test_path,
        coverage_target=args.coverage_target
    )

    # Prepare output
    output_data = {
        "outcome": result.outcome.value,
        "score": result.score,
        "metrics": result.metrics,
        "violations": result.violations,
        "timestamp": result.timestamp.isoformat()
    }

    # Write results
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Evaluation complete: {result.outcome.value}")
    logger.info(f"Score: {result.score:.1f}/100")

    if result.violations:
        logger.warning("Violations found:")
        for violation in result.violations:
            logger.warning(f"  - {violation}")

    return 0 if result.is_passed() else 1


if __name__ == "__main__":
    sys.exit(main())

"""
Human Evaluation Framework for Model Outputs

Provides tools for human evaluation of generated dialogue,
stage directions, and theatrical content.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class HumanEvaluator:
    """Manages human evaluation workflow."""

    def __init__(self, output_path: str = None):
        self.output_path = output_path or "evaluation_results.json"
        self.results = []

    def create_evaluation_task(
        self,
        model_output: str,
        reference_input: Dict,
        criteria: List[str] = None,
    ) -> Dict:
        """
        Create an evaluation task.

        Args:
            model_output: The model's output to evaluate
            reference_input: The input that generated the output
            criteria: List of evaluation criteria

        Returns:
            Task dictionary
        """
        default_criteria = [
            "naturalness",  # Does the dialogue sound natural?
            "relevance",    # Is it relevant to the context?
            "character",    # Does it maintain character voice?
            "safety",       # Is the content appropriate?
            "engagement",   # Is it engaging for the audience?
        ]

        return {
            "task_id": len(self.results),
            "reference_input": reference_input,
            "model_output": model_output,
            "criteria": criteria or default_criteria,
            "timestamp": datetime.now().isoformat(),
        }

    def load_tasks(self, tasks_file: str) -> List[Dict]:
        """Load evaluation tasks from file."""
        with open(tasks_file) as f:
            return json.load(f)

    def save_results(self):
        """Save evaluation results to file."""
        with open(self.output_path, "w") as f:
            json.dump(self.results, f, indent=2)

    def record_evaluation(self, task_id: int, scores: Dict[str, int], notes: str = ""):
        """
        Record evaluation scores for a task.

        Args:
            task_id: ID of the task being evaluated
            scores: Dict mapping criterion to score (1-5)
            notes: Optional evaluator notes
        """
        evaluation = {
            "task_id": task_id,
            "scores": scores,
            "average_score": sum(scores.values()) / len(scores),
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }

        # Update or add result
        existing = next((r for r in self.results if r.get("task_id") == task_id), None)
        if existing:
            existing["evaluation"] = evaluation
        else:
            self.results.append({"task_id": task_id, "evaluation": evaluation})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["create", "evaluate", "report"], required=True)
    parser.add_argument("--tasks-file", help="File to read/write tasks")
    parser.add_argument("--output", default="evaluation_results.json")
    args = parser.parse_args()

    evaluator = HumanEvaluator(args.output)

    if args.mode == "create":
        # Create evaluation tasks from model outputs
        print("Creating evaluation tasks...")
        # This would read from a file of model outputs
        # For scaffold, we just print instructions
        print("To create tasks, provide a JSON file with model outputs")

    elif args.mode == "evaluate":
        # Interactive evaluation
        print("Interactive evaluation (for scaffold - implement UI for production)")
        print("Load tasks from:", args.tasks_file)

    elif args.mode == "report":
        # Generate evaluation report
        print("Generating evaluation report...")
        if Path(args.output).exists():
            with open(args.output) as f:
                results = json.load(f)

            # Calculate statistics
            scores = [r.get("evaluation", {}).get("average_score", 0) for r in results]

            if scores:
                print(f"Evaluation Report")
                print(f"  Total evaluations: {len(scores)}")
                print(f"  Average score: {sum(scores) / len(scores):.2f}/5.0")
                print(f"  Min score: {min(scores):.2f}")
                print(f"  Max score: {max(scores):.2f}")


if __name__ == "__main__":
    main()

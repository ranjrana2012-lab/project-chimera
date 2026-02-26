"""
Latency Evaluation for Model Inference

Measures the response time of model inference under various conditions.
"""

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Dict, List


def mock_inference(input_text: str, max_tokens: int = 100) -> str:
    """Mock inference for testing."""
    # Simulate processing time
    time.sleep(0.1 + (max_tokens / 1000) * 0.5)
    return "This is a mock response."


def evaluate_latency(
    inputs: List[str],
    inference_fn,
    num_runs: int = 10,
) -> Dict:
    """
    Evaluate inference latency.

    Args:
        inputs: List of input texts
        inference_fn: Function that takes text and returns result
        num_runs: Number of times to run each input

    Returns:
        Latency statistics
    """
    latencies = []

    for input_text in inputs:
        for _ in range(num_runs):
            start = time.time()
            result = inference_fn(input_text)
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

    return {
        "count": len(latencies),
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "p95_ms": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
        "p99_ms": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
        "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-file", required=True, help="File with test inputs")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs per input")
    args = parser.parse_args()

    # Load test inputs
    test_file = Path(args.test_file)
    if test_file.suffix == ".json":
        with open(test_file) as f:
            data = json.load(f)
        inputs = [item.get("input", item.get("text", "")) for item in data]
    else:
        inputs = test_file.read_text().split("\n")
        inputs = [i for i in inputs if i.strip()]

    print(f"Evaluating latency on {len(inputs)} inputs ({args.runs} runs each)...")

    results = evaluate_latency(inputs, mock_inference, args.runs)

    print("\nLatency Results:")
    print(f"  Mean:    {results['mean_ms']:.2f} ms")
    print(f"  Median:  {results['median_ms']:.2f} ms")
    print(f"  Min:     {results['min_ms']:.2f} ms")
    print(f"  Max:     {results['max_ms']:.2f} ms")
    print(f"  P95:     {results['p95_ms']:.2f} ms")
    print(f"  P99:     {results['p99_ms']:.2f} ms")
    print(f"  StdDev:  {results['stdev_ms']:.2f} ms")


if __name__ == "__main__":
    main()

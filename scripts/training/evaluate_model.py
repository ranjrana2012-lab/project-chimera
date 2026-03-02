#!/usr/bin/env python3
"""
Project Chimera - Model Evaluation Script

Evaluates a trained model against a test dataset.
"""

import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm


def evaluate_model(
    model_path: str,
    test_data_path: str,
    output_path: str,
):
    """Evaluate model on test data.

    Args:
        model_path: Path to trained model
        test_data_path: Path to test data
        output_path: Path to save results
    """
    print(f"Loading model from {model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    # Load test data
    print(f"Loading test data from {test_data_path}")
    with open(test_data_path) as f:
        test_data = json.load(f)

    results = []

    print("Evaluating...")
    for item in tqdm(test_data):
        input_text = item["input"]
        expected_output = item.get("expected_output", "")

        # Generate
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
            )

        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Evaluate
        result = {
            "input": input_text,
            "generated": generated_text,
            "expected": expected_output,
        }

        # TODO: Add actual evaluation metrics
        # - Perplexity
        # - BLEU score
        # - Character consistency
        # - Safety check

        results.append(result)

    # Save results
    print(f"Saving results to {output_path}")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print("Evaluation complete!")


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--model", required=True, help="Path to model")
    parser.add_argument("--test-data", required=True, help="Path to test data")
    parser.add_argument("--output", required=True, help="Path to save results")

    args = parser.parse_args()

    evaluate_model(
        model_path=args.model,
        test_data_path=args.test_data,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()

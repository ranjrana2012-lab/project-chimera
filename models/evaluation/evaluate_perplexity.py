"""
Perplexity Evaluation for Language Models

Measures how well the model predicts the test data.
Lower perplexity indicates better performance.
"""

import argparse
import math
from pathlib import Path
from typing import List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(model_path: str):
    """Load model and tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    model.eval()
    return model, tokenizer


def calculate_perplexity(model, tokenizer, texts: List[str], max_length: int = 512):
    """Calculate perplexity on given texts."""
    total_loss = 0.0
    total_tokens = 0

    for text in texts:
        encodings = tokenizer(text, return_tensors="pt", max_length=max_length, truncation=True)

        with torch.no_grad():
            outputs = model(**encodings, labels=encodings["input_ids"])
            loss = outputs.loss.item()

        total_loss += loss * encodings["input_ids"].size(1)
        total_tokens += encodings["input_ids"].size(1)

    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)
    return perplexity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model path")
    parser.add_argument("--test-file", required=True, help="Test data file")
    parser.add_argument("--max-length", type=int, default=512)
    args = parser.parse_args()

    # Load test data
    texts = Path(args.test_file).read_text().split("\n")
    texts = [t for t in texts if t.strip()]

    print(f"Loading model from {args.model}...")
    model, tokenizer = load_model(args.model)

    print(f"Evaluating on {len(texts)} samples...")
    perplexity = calculate_perplexity(model, tokenizer, texts, args.max_length)

    print(f"\nPerplexity: {perplexity:.2f}")


if __name__ == "__main__":
    main()

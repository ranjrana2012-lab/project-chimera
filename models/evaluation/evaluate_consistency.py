"""
Character Consistency Evaluation

Measures how consistently the model maintains character voice
across multiple dialogue generations.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import numpy as np


def evaluate_character_consistency(dialogues: List[Dict]) -> float:
    """
    Evaluate character consistency across dialogues.

    Args:
        dialogues: List of dialogue entries with character, text, and metadata

    Returns:
        Consistency score between 0 and 1
    """
    character_profiles = {}
    consistency_scores = []

    for dialogue in dialogues:
        character = dialogue["character"]
        text = dialogue["text"]

        # Build character profile
        if character not in character_profiles:
            character_profiles[character] = {
                "word_count": [],
                "sentence_length": [],
                "vocabulary": set(),
            }

        # Update profile
        words = text.split()
        sentences = text.split(".")

        character_profiles[character]["word_count"].append(len(words))
        character_profiles[character]["sentence_length"].append(len(sentences))
        character_profiles[character]["vocabulary"].update(words)

    # Calculate consistency for each character
    for character, profile in character_profiles.items():
        # Word count consistency (coefficient of variation)
        wc_mean = np.mean(profile["word_count"])
        wc_std = np.std(profile["word_count"])
        wc_consistency = 1 - min(wc_std / wc_mean, 1.0) if wc_mean > 0 else 0

        # Sentence length consistency
        sl_mean = np.mean(profile["sentence_length"])
        sl_std = np.std(profile["sentence_length"])
        sl_consistency = 1 - min(sl_std / sl_mean, 1.0) if sl_mean > 0 else 0

        # Overall character consistency
        character_consistency = (wc_consistency + sl_consistency) / 2
        consistency_scores.append(character_consistency)

    return np.mean(consistency_scores) if consistency_scores else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dialogue-file", required=True, help="JSON file with dialogues")
    args = parser.parse_args()

    with open(args.dialogue_file) as f:
        dialogues = json.load(f)

    consistency = evaluate_character_consistency(dialogues)
    print(f"Character Consistency: {consistency:.2f}")


if __name__ == "__main__":
    main()

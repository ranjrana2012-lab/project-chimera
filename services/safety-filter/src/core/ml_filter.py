"""ML-based content safety classification using BERT.

This module provides machine learning-based content safety classification
using a BERT model fine-tuned for safety detection.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.utils.data import Dataset, DataLoader
import numpy as np


class SafetyDataset(Dataset):
    """Dataset for safety classification."""

    def __init__(self, texts: List[str], tokenizer, max_length: int = 512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten()
        }


class MLFilter:
    """ML-based content safety filter using BERT.

    This filter uses a pre-trained BERT model to classify content
    into safety categories with probability scores.
    """

    # Default category labels
    DEFAULT_CATEGORIES = [
        "safe",
        "profanity",
        "hate_speech",
        "sexual_content",
        "violence",
        "harassment",
        "self_harm",
        "misinformation"
    ]

    def __init__(
        self,
        model_path: Optional[Path] = None,
        model_name: str = "bert-base-uncased",
        device: Optional[str] = None,
        max_length: int = 512,
        batch_size: int = 8
    ):
        """Initialize the ML filter.

        Args:
            model_path: Path to saved model (if None, uses default model)
            model_name: HuggingFace model name for base model
            device: Device to run inference on (auto-detect if None)
            max_length: Maximum sequence length
            batch_size: Batch size for inference
        """
        self.model_path = model_path
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Model components
        self.model: Optional[torch.nn.Module] = None
        self.tokenizer: Optional[Any] = None
        self.categories = self.DEFAULT_CATEGORIES.copy()

        # Model metadata
        self.model_loaded = False
        self.model_version = "bert-safety-v0.1.0"

    async def load_model(self):
        """Load the model and tokenizer.

        This loads either a fine-tuned model from model_path or
        initializes a base model for inference.
        """
        try:
            # Try to load from path if provided
            if self.model_path and self.model_path.exists():
                print(f"Loading model from {self.model_path}...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_path
                )
                self.model_version = f"custom-{self.model_path.name}"
            else:
                # Use default base model
                print(f"Loading base model {self.model_name}...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name
                )
                # For base model, we'll use a simpler approach
                # In production, you'd use a fine-tuned model

            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            print(f"Model loaded successfully on {self.device}")

        except Exception as e:
            print(f"Warning: Could not load ML model: {e}")
            print("ML filter will use rule-based fallback")
            self.model_loaded = False

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before classification.

        Args:
            text: Input text

        Returns:
            Preprocessed text
        """
        # Basic preprocessing
        text = text.strip()
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text

    async def classify(
        self,
        content: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Classify content for safety.

        Args:
            content: Text content to classify
            include_details: Whether to include detailed scores

        Returns:
            Dictionary with classification results
        """
        start_time = time.time()

        if not self.model_loaded or self.model is None:
            # Fallback to rule-based classification
            return self._rule_based_fallback(content)

        try:
            # Preprocess
            processed_content = self._preprocess_text(content)

            # Tokenize
            inputs = self.tokenizer(
                processed_content,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors='pt'
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            # Get probabilities
            probabilities = torch.softmax(logits, dim=-1)
            probs = probabilities[0].cpu().numpy()

            # Process results
            result = self._process_results(probs, content, include_details)
            result["processing_time_ms"] = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            print(f"Error during ML classification: {e}")
            return self._rule_based_fallback(content)

    async def classify_batch(
        self,
        contents: List[str],
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Classify multiple contents in batch.

        Args:
            contents: List of text contents to classify
            include_details: Whether to include detailed scores

        Returns:
            List of classification results
        """
        if not self.model_loaded or self.model is None:
            return [self._rule_based_fallback(c) for c in contents]

        try:
            # Create dataset
            dataset = SafetyDataset(contents, self.tokenizer, self.max_length)
            dataloader = DataLoader(dataset, batch_size=self.batch_size)

            all_results = []

            self.model.eval()
            with torch.no_grad():
                for batch in dataloader:
                    inputs = {
                        'input_ids': batch['input_ids'].to(self.device),
                        'attention_mask': batch['attention_mask'].to(self.device)
                    }

                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=-1)

                    for i, probs in enumerate(probabilities):
                        content = contents[len(all_results)]
                        result = self._process_results(
                            probs.cpu().numpy(),
                            content,
                            include_details
                        )
                        all_results.append(result)

            return all_results

        except Exception as e:
            print(f"Error during batch classification: {e}")
            return [self._rule_based_fallback(c) for c in contents]

    def _process_results(
        self,
        probs: np.ndarray,
        original_content: str,
        include_details: bool
    ) -> Dict[str, Any]:
        """Process model output probabilities into results.

        Args:
            probs: Probability array from model
            original_content: Original content text
            include_details: Whether to include details

        Returns:
            Processed results dictionary
        """
        # Get top prediction
        top_idx = np.argmax(probs)
        top_category = self.categories[top_idx] if top_idx < len(self.categories) else "unknown"
        top_confidence = float(probs[top_idx])

        # Calculate harm probability (1 - safe probability)
        safe_idx = 0  # Assuming "safe" is first category
        harm_probability = 1.0 - float(probs[safe_idx])

        # Build category scores
        category_scores = {}
        for i, category in enumerate(self.categories):
            if i < len(probs):
                category_scores[category] = float(probs[i])

        result = {
            "prediction": top_category,
            "confidence": top_confidence,
            "harm_probability": harm_probability,
            "safe": top_category == "safe" or harm_probability < 0.5,
            "model_version": self.model_version
        }

        if include_details:
            result["category_scores"] = category_scores
            result["all_probabilities"] = {
                cat: float(probs[i]) if i < len(probs) else 0.0
                for i, cat in enumerate(self.categories)
            }

        return result

    def _rule_based_fallback(self, content: str) -> Dict[str, Any]:
        """Rule-based fallback when model is not available.

        Args:
            content: Text content to analyze

        Returns:
            Fallback classification results
        """
        # Simple keyword-based fallback
        content_lower = content.lower()

        # Harm keywords by category
        harm_keywords = {
            "profanity": ["fuck", "shit", "damn", "hell", "ass"],
            "hate_speech": ["hate", "kill all", "inferior"],
            "sexual_content": ["naked", "nude", "explicit"],
            "violence": ["kill", "murder", "torture", "assault"],
            "harassment": ["stalker", "creep", "harass"],
            "self_harm": ["suicide", "kill myself", "end it"],
            "misinformation": ["fake news", "conspiracy", "hoax"]
        }

        category_scores = {"safe": 0.9}  # Start with high safe score

        for category, keywords in harm_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 0.15
            category_scores[category] = min(score, 1.0)
            category_scores["safe"] -= score * 0.5

        category_scores["safe"] = max(category_scores["safe"], 0.0)

        # Find highest score
        top_category = max(category_scores, key=category_scores.get)
        top_confidence = category_scores[top_category]
        harm_probability = 1.0 - category_scores["safe"]

        return {
            "prediction": top_category,
            "confidence": top_confidence,
            "harm_probability": harm_probability,
            "safe": harm_probability < 0.5,
            "category_scores": category_scores,
            "model_version": f"{self.model_version}-fallback",
            "fallback": True
        }

    async def close(self):
        """Clean up resources."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        self.model_loaded = False

        # Force garbage collection
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

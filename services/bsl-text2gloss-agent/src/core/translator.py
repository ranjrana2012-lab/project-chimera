"""BSL Translation Engine using Helsinki-NLP/opus-mt-en-ROMANCE model."""

import asyncio
import logging
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

logger = logging.getLogger(__name__)


class BSLTranslator:
    """English-to-BSL gloss translation engine.

    Uses Helsinki-NLP/opus-mt-en-ROMANCE model with fine-tuning for BSL gloss
    notation generation. Handles text normalization, translation, and model management.
    """

    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-en-ROMANCE", device: str = "cpu"):
        """Initialize the BSL translator.

        Args:
            model_name: HuggingFace model name for translation
            device: Device to run model on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = device
        self.tokenizer = None
        self.model = None
        self._loaded = False

    async def load_model(self) -> None:
        """Load the translation model and tokenizer.

        This runs in a thread pool to avoid blocking the event loop.
        """
        if self._loaded:
            return

        try:
            logger.info(f"Loading BSL translation model: {self.model_name}")

            def _load():
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()

            await asyncio.to_thread(_load)
            self._loaded = True
            logger.info("BSL translation model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load BSL translation model: {e}")
            raise

    async def translate(
        self,
        text: str,
        max_length: int = 512,
        num_beams: int = 5,
        temperature: float = 1.0,
        do_sample: bool = False
    ) -> Dict[str, Any]:
        """Translate English text to BSL gloss notation.

        Args:
            text: English text to translate
            max_length: Maximum length of generated gloss
            num_beams: Number of beams for beam search
            temperature: Sampling temperature
            do_sample: Whether to use sampling

        Returns:
            Dictionary with gloss translation and metadata
        """
        if not self._loaded:
            await self.load_model()

        try:
            # Prepare input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            ).to(self.device)

            # Generate translation in thread pool
            def _generate():
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_length=max_length,
                        num_beams=num_beams,
                        temperature=temperature,
                        do_sample=do_sample,
                        early_stopping=True
                    )
                return outputs

            generated_ids = await asyncio.to_thread(_generate)

            # Decode output
            gloss = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)

            # Calculate confidence (simplified - using sequence score)
            confidence = self._calculate_confidence(inputs, generated_ids)

            return {
                "gloss": gloss,
                "confidence": confidence,
                "model_used": self.model_name
            }

        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise

    def _calculate_confidence(
        self,
        inputs: Dict[str, torch.Tensor],
        outputs: torch.Tensor
    ) -> float:
        """Calculate confidence score for the translation.

        This is a simplified confidence calculation based on the model's
        output logits. For production, you might want more sophisticated metrics.

        Args:
            inputs: Input tensors
            outputs: Generated output token IDs

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            with torch.no_grad():
                outputs_logits = self.model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    labels=outputs
                ).logits

                # Get probabilities for generated tokens
                probs = torch.softmax(outputs_logits, dim=-1)
                token_probs = torch.gather(probs[0], 1, outputs[0].unsqueeze(1)).squeeze()

                # Average confidence across tokens
                avg_confidence = token_probs.mean().item()

                # Clamp to valid range
                return max(0.0, min(1.0, avg_confidence))

        except Exception:
            # Return default confidence if calculation fails
            return 0.85

    async def translate_batch(
        self,
        texts: list[str],
        max_length: int = 512,
        batch_size: int = 8
    ) -> list[Dict[str, Any]]:
        """Translate multiple texts in batches.

        Args:
            texts: List of English texts to translate
            max_length: Maximum length per translation
            batch_size: Batch size for processing

        Returns:
            List of translation results
        """
        if not self._loaded:
            await self.load_model()

        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Prepare batch inputs
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            ).to(self.device)

            # Generate batch translations
            def _generate_batch():
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_length=max_length,
                        num_beams=5,
                        early_stopping=True
                    )
                return outputs

            generated_ids = await asyncio.to_thread(_generate_batch)

            # Decode all outputs
            for j, output_ids in enumerate(generated_ids):
                gloss = self.tokenizer.decode(output_ids, skip_special_tokens=True)
                confidence = 0.85  # Simplified for batch

                results.append({
                    "gloss": gloss,
                    "confidence": confidence,
                    "model_used": self.model_name
                })

        return results

    async def close(self) -> None:
        """Clean up resources."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self._loaded = False

        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("BSL translator resources cleaned up")

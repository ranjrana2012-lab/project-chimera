"""Music generation inference engine."""

import asyncio
import logging
from typing import Callable, Optional
import torch
import numpy as np

from config import get_settings
from models import ModelName, GenerationRequest
from model_pool import get_model_pool

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Async music generation engine."""

    def __init__(self):
        """Initialize inference engine."""
        self.settings = get_settings()
        self.model_pool = get_model_pool()

    async def generate(self, request: GenerationRequest,
                     progress_callback: Optional[Callable] = None) -> tuple[np.ndarray, int]:
        """Generate music from prompt.

        Args:
            request: Generation request
            progress_callback: Optional progress callback

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        # Get model
        model, processor = await self.model_pool.get_model(request.model)

        # Prepare inputs
        inputs = processor(
            text=request.prompt,
            return_tensors="pt"
        ).to(self.model_pool.device)

        # Calculate max tokens based on duration
        # Rough estimate: 50 tokens per second
        max_new_tokens = int(request.duration * 50)

        logger.info(f"Generating {request.duration}s of music with {request.model}")

        # Generate
        with torch.no_grad():
            sampling_rate = model.config.audio_encoder.sampling_rate
            generate_kwargs = {
                "max_new_tokens": max_new_tokens,
                "do_sample": True,
                "temperature": 0.7,
                "top_k": 50,
            }

            if progress_callback:
                # For progress tracking, we'd need to use a streaming approach
                # For now, just call the callback at start and end
                await progress_callback(0, 100)

            outputs = model.generate(**inputs, **generate_kwargs)

            if progress_callback:
                await progress_callback(100, 100)

        # Decode audio
        audio_values = outputs[0, 0].cpu().numpy()

        # Resample if needed
        from scipy.signal import resample_poly
        if sampling_rate != request.sample_rate:
            audio_values = resample_poly(
                audio_values,
                sampling_rate,
                request.sample_rate
            )

        return audio_values, request.sample_rate

    async def generate_async_with_cancellation(self, request: GenerationRequest,
                                             cancellation_token: asyncio.CancelledError) -> tuple[np.ndarray, int]:
        """Generate with cancellation support.

        Args:
            request: Generation request
            cancellation_token: Token to check for cancellation

        Returns:
            Tuple of (audio_array, sample_rate)

        Raises:
            asyncio.CancelledError: If generation is cancelled
        """
        task = asyncio.create_task(self.generate(request))

        try:
            result = await asyncio.wait_for(
                asyncio.shield(task),
                timeout=300.0  # 5 minute timeout
            )
            return result
        except asyncio.CancelledError:
            task.cancel()
            logger.info("Generation cancelled by user")
            raise

    def estimate_vram_required(self, model: ModelName, duration: float) -> int:
        """Estimate VRAM required for generation.

        Args:
            model: Which model
            duration: Duration in seconds

        Returns:
            Estimated VRAM in MB
        """
        base_vram = self.model_pool.estimate_vram_mb(model)

        # Add overhead for longer durations
        duration_multiplier = min(2.0, duration / 5.0)

        return int(base_vram * duration_multiplier)


# Global inference engine instance
_inference_engine: Optional[InferenceEngine] = None


def get_inference_engine() -> InferenceEngine:
    """Get global inference engine instance."""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = InferenceEngine()
    return _inference_engine

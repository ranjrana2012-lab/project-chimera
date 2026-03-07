"""Model Pool Manager for Music Generation."""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
import torch
from transformers import MusicgenForConditionalGeneration, MusicgenProcessor
from transformers import AutoModel

from config import get_settings
from models import ModelName

logger = logging.getLogger(__name__)


class ModelPool:
    """Manages loading and unloading of music generation models."""

    def __init__(self) -> None:
        """Initialize model pool."""
        self.settings = get_settings()
        self.models: Dict[ModelName, Optional[torch.nn.Module]] = {
            ModelName.MUSICGEN: None,
            ModelName.ACESTEP: None,
        }
        self.processors: Dict[ModelName, Any] = {
            ModelName.MUSICGEN: None,
            ModelName.ACESTEP: None,
        }
        self.device = torch.device(self.settings.device)
        self._load_lock = asyncio.Lock()

    async def get_model(self, model_name: ModelName) -> Tuple[torch.nn.Module, Any]:
        """Get loaded model, loading if necessary.

        Args:
            model_name: Which model to get

        Returns:
            Tuple of (model, processor)
        """
        async with self._load_lock:
            if self.models[model_name] is None:
                await self._load_model(model_name)

            return self.models[model_name], self.processors[model_name]

    async def _load_model(self, model_name: ModelName) -> None:
        """Load a model into memory.

        Args:
            model_name: Which model to load
        """
        logger.info(f"Loading model: {model_name}")

        if model_name == ModelName.MUSICGEN:
            model_path = self.settings.musicgen_model_path
            model_id = "facebook/musicgen-small"
        else:  # ACESTEP
            model_path = self.settings.acestep_model_path
            model_id = "ACE-Step/ACE-Step"  # Placeholder - update with actual

        try:
            # Check if local path exists
            if Path(model_path).exists():
                logger.info(f"Loading from local path: {model_path}")
                if model_name == ModelName.MUSICGEN:
                    model = MusicgenForConditionalGeneration.from_pretrained(
                        model_path,
                        local_files_only=True,
                        torch_dtype=torch.float16,
                    )
                    processor = MusicgenProcessor.from_pretrained(
                        model_path,
                        local_files_only=True,
                    )
                else:
                    # Use AutoModel as fallback for ACE-Step
                    model = AutoModel.from_pretrained(
                        model_path,
                        local_files_only=True,
                        torch_dtype=torch.float16,
                    )
                    processor = None  # ACE-Step may not need a processor
            else:
                logger.info(f"Loading from HuggingFace: {model_id}")
                if model_name == ModelName.MUSICGEN:
                    model = MusicgenForConditionalGeneration.from_pretrained(
                        model_id,
                        torch_dtype=torch.float16,
                        cache_dir=self.settings.huggingface_cache_dir,
                    )
                    processor = MusicgenProcessor.from_pretrained(
                        model_id,
                        cache_dir=self.settings.huggingface_cache_dir,
                    )
                else:
                    # Use AutoModel as fallback for ACE-Step
                    model = AutoModel.from_pretrained(
                        model_id,
                        torch_dtype=torch.float16,
                        cache_dir=self.settings.huggingface_cache_dir,
                    )
                    processor = None  # ACE-Step may not need a processor

            model = model.to(self.device)
            model.eval()

            self.models[model_name] = model
            self.processors[model_name] = processor

            logger.info(f"Model {model_name} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    async def unload_model(self, model_name: ModelName) -> None:
        """Unload a model to free VRAM.

        Args:
            model_name: Which model to unload
        """
        async with self._load_lock:
            if self.models[model_name] is not None:
                logger.info(f"Unloading model: {model_name}")
                del self.models[model_name]
                del self.processors[model_name]
                self.models[model_name] = None
                self.processors[model_name] = None

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                logger.info(f"Model {model_name} unloaded")

    def estimate_vram_mb(self, model_name: ModelName) -> int:
        """Estimate VRAM usage for a model.

        Args:
            model_name: Which model to estimate

        Returns:
            Estimated VRAM in MB
        """
        # Rough estimates - adjust based on actual usage
        if model_name == ModelName.MUSICGEN:
            return 4096  # ~4GB for musicgen-small
        else:  # ACESTEP
            return 2048  # ~2GB

    async def switch_model(self, from_model: ModelName, to_model: ModelName) -> None:
        """Switch from one model to another.

        Args:
            from_model: Model to unload
            to_model: Model to load
        """
        await self.unload_model(from_model)
        await self._load_model(to_model)


# Global model pool instance
_model_pool: Optional[ModelPool] = None


def get_model_pool() -> ModelPool:
    """Get global model pool instance."""
    global _model_pool
    if _model_pool is None:
        _model_pool = ModelPool()
    return _model_pool

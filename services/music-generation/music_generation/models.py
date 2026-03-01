import asyncio
from typing import Dict
from music_generation.errors import InsufficientVRAMError, ModelNotFoundError


class ModelInfo:
    """Metadata about a loaded model"""
    def __init__(
        self,
        name: str,
        vram_usage_mb: int,
        sample_rate: int = 44100,
        max_duration_seconds: int = 300
    ):
        self.name = name
        self.vram_usage_mb = vram_usage_mb
        self.sample_rate = sample_rate
        self.max_duration_seconds = max_duration_seconds


class ModelPoolManager:
    """Manages multiple AI music models with lazy loading"""

    def __init__(self, vram_limit_mb: int = 16384):
        self.vram_limit_mb = vram_limit_mb
        self.loaded_models: Dict[str, any] = {}
        self.model_info: Dict[str, ModelInfo] = {}
        self._load_lock = asyncio.Lock()
        self.model_requirements = {
            "musicgen": 2048,   # ~2GB
            "acestep": 4096,    # ~4GB
        }

    async def load_model(self, model_name: str) -> ModelInfo:
        """Load model into memory"""
        async with self._load_lock:
            if model_name in self.loaded_models:
                return self.model_info[model_name]

            # Check VRAM availability
            required_vram = self.model_requirements.get(model_name, 2048)
            current_usage = sum(info.vram_usage_mb for info in self.model_info.values())

            if current_usage + required_vram > self.vram_limit_mb:
                raise InsufficientVRAMError(
                    required_mb=current_usage + required_vram,
                    available_mb=self.vram_limit_mb
                )

            # Load the model
            model = await self._load_model_from_disk(model_name)
            info = ModelInfo(
                name=model_name,
                vram_usage_mb=required_vram
            )

            self.loaded_models[model_name] = model
            self.model_info[model_name] = info

            return info

    async def unload_model(self, model_name: str) -> None:
        """Unload model from memory"""
        if model_name not in self.loaded_models:
            raise ModelNotFoundError(model_name)

        del self.loaded_models[model_name]
        del self.model_info[model_name]

    def get_model_info(self, model_name: str) -> ModelInfo | None:
        """Get model metadata"""
        return self.model_info.get(model_name)

    def estimate_vram_usage(self) -> Dict[str, int]:
        """Estimate current VRAM usage"""
        return {
            name: info.vram_usage_mb
            for name, info in self.model_info.items()
        }

    async def _load_model_from_disk(self, model_name: str):
        """Load model from disk (placeholder for actual implementation)"""
        # This will be implemented with actual model loading
        await asyncio.sleep(0.1)  # Simulate loading time
        return {"name": model_name, "loaded": True}

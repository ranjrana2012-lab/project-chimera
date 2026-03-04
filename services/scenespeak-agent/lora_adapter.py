"""
LoRA (Low-Rank Adaptation) adapter support for SceneSpeak agent.

Allows efficient fine-tuning of language models by adding small adapter layers
instead of fine-tuning the entire model.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import hashlib

logger = logging.getLogger(__name__)


class AdapterStatus(Enum):
    """LoRA adapter status."""
    LOADED = "loaded"
    LOADING = "loading"
    UNLOADED = "unloaded"
    ERROR = "error"


@dataclass
class LoRAAdapter:
    """LoRA adapter configuration."""
    name: str
    path: str
    rank: int = 8
    alpha: float = 32.0
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    description: str = ""
    is_active: bool = False
    status: AdapterStatus = AdapterStatus.UNLOADED
    loaded_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "rank": self.rank,
            "alpha": self.alpha,
            "target_modules": self.target_modules,
            "description": self.description,
            "is_active": self.is_active,
            "status": self.status.value,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "error_message": self.error_message
        }


@dataclass
class AdapterConfig:
    """LoRA adapter configuration manager."""
    adapters: Dict[str, LoRAAdapter] = field(default_factory=dict)
    base_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    default_adapter: Optional[str] = None
    max_loaded_adapters: int = 3
    enable_merging: bool = True

    def add_adapter(self, adapter: LoRAAdapter) -> bool:
        """Add an adapter to the configuration."""
        if adapter.name in self.adapters:
            logger.warning(f"Adapter {adapter.name} already exists")
            return False
        self.adapters[adapter.name] = adapter
        return True

    def get_adapter(self, name: str) -> Optional[LoRAAdapter]:
        """Get an adapter by name."""
        return self.adapters.get(name)

    def list_adapters(self) -> List[LoRAAdapter]:
        """List all adapters."""
        return list(self.adapters.values())

    def remove_adapter(self, name: str) -> bool:
        """Remove an adapter from configuration."""
        if name in self.adapters:
            del self.adapters[name]
            return True
        return False


class LoRAManager:
    """Manages LoRA adapters for SceneSpeak agent."""

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        adapters_dir: str = "/models/lora",
        device: str = "cuda"
    ):
        self.config = config or AdapterConfig()
        self.adapters_dir = Path(adapters_dir)
        self.device = device
        self.loaded_adapters: Dict[str, Any] = {}
        self._load_lock = asyncio.Lock()
        self._callbacks: List[Callable] = []

    def add_callback(self, callback: Callable[[str, AdapterStatus], None]):
        """Add a callback for adapter status changes."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, adapter_name: str, status: AdapterStatus):
        """Notify all callbacks of status change."""
        for callback in self._callbacks:
            try:
                callback(adapter_name, status)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def load_adapter(self, name: str) -> bool:
        """Load a LoRA adapter."""
        adapter = self.config.get_adapter(name)
        if not adapter:
            logger.error(f"Adapter {name} not found")
            return False

        async with self._load_lock:
            try:
                adapter.status = AdapterStatus.LOADING
                self._notify_callbacks(name, AdapterStatus.LOADING)

                # Simulate loading (in production, would use PEFT/transformers)
                await asyncio.sleep(0.5)

                # Check if adapter file exists
                adapter_path = self.adapters_dir / adapter.path
                if not adapter_path.exists():
                    raise FileNotFoundError(f"Adapter path not found: {adapter_path}")

                # Load adapter weights (simulated)
                self.loaded_adapters[name] = {
                    "adapter": adapter,
                    "weights": f"loaded_{hashlib.md5(name.encode()).hexdigest()}"
                }

                adapter.status = AdapterStatus.LOADED
                adapter.loaded_at = datetime.now(timezone.utc)
                adapter.error_message = None

                self._notify_callbacks(name, AdapterStatus.LOADED)
                logger.info(f"Loaded adapter: {name}")
                return True

            except Exception as e:
                adapter.status = AdapterStatus.ERROR
                adapter.error_message = str(e)
                self._notify_callbacks(name, AdapterStatus.ERROR)
                logger.error(f"Failed to load adapter {name}: {e}")
                return False

    async def unload_adapter(self, name: str) -> bool:
        """Unload a LoRA adapter."""
        if name not in self.loaded_adapters:
            logger.warning(f"Adapter {name} not loaded")
            return False

        adapter = self.config.get_adapter(name)
        try:
            # Unload from memory
            del self.loaded_adapters[name]

            adapter.status = AdapterStatus.UNLOADED
            adapter.loaded_at = None

            self._notify_callbacks(name, AdapterStatus.UNLOADED)
            logger.info(f"Unloaded adapter: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload adapter {name}: {e}")
            return False

    async def switch_adapter(self, from_name: Optional[str], to_name: str) -> bool:
        """Switch from one adapter to another."""
        try:
            # Unload current adapter if specified
            if from_name and from_name in self.loaded_adapters:
                await self.unload_adapter(from_name)

            # Load new adapter
            success = await self.load_adapter(to_name)
            if success:
                adapter = self.config.get_adapter(to_name)
                if adapter:
                    adapter.is_active = True

            return success

        except Exception as e:
            logger.error(f"Failed to switch adapters: {e}")
            return False

    async def merge_adapters(self, adapter_names: List[str]) -> bool:
        """Merge multiple adapters into base model."""
        if not self.config.enable_merging:
            logger.warning("Adapter merging is disabled")
            return False

        try:
            # Load all adapters first
            for name in adapter_names:
                if name not in self.loaded_adapters:
                    await self.load_adapter(name)

            # Merge adapters (simulated)
            logger.info(f"Merged adapters: {', '.join(adapter_names)}")
            return True

        except Exception as e:
            logger.error(f"Failed to merge adapters: {e}")
            return False

    def get_loaded_adapters(self) -> List[str]:
        """Get list of currently loaded adapters."""
        return list(self.loaded_adapters.keys())

    def get_adapter_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about an adapter."""
        adapter = self.config.get_adapter(name)
        if not adapter:
            return None

        info = adapter.to_dict()
        info["is_loaded"] = name in self.loaded_adapters

        return info

    async def benchmark_adapter(
        self,
        name: str,
        prompts: List[str]
    ) -> Dict[str, float]:
        """Benchmark adapter performance."""
        if name not in self.loaded_adapters:
            logger.warning(f"Adapter {name} not loaded")
            return {}

        try:
            start = datetime.now(timezone.utc)

            # Simulate benchmarking
            for prompt in prompts:
                # Simulate generation
                await asyncio.sleep(0.1)

            end = datetime.now(timezone.utc)
            duration = (end - start).total_seconds()

            return {
                "adapter": name,
                "prompts_tested": len(prompts),
                "total_duration_seconds": duration,
                "avg_duration_per_prompt": duration / len(prompts),
                "prompts_per_second": len(prompts) / duration if duration > 0 else 0
            }

        except Exception as e:
            logger.error(f"Benchmark failed for {name}: {e}")
            return {}

    def discover_adapters(self) -> List[str]:
        """Discover available adapters from filesystem."""
        try:
            if not self.adapters_dir.exists():
                return []

            discovered = []
            for path in self.adapters_dir.rglob("adapter_config.json"):
                try:
                    with open(path) as f:
                        config = json.load(f)
                        name = config.get("name", path.stem)
                        discovered.append(name)
                except Exception as e:
                    logger.warning(f"Failed to load adapter config from {path}: {e}")

            return discovered

        except Exception as e:
            logger.error(f"Failed to discover adapters: {e}")
            return []

    async def auto_load_adapters(self) -> int:
        """Auto-load default adapters."""
        count = 0
        discovered = self.discover_adapters()

        for name in discovered:
            adapter = self.config.get_adapter(name)
            if not adapter:
                continue

            # Load if it's the default adapter
            if self.config.default_adapter == name:
                if await self.load_adapter(name):
                    count += 1

        return count


class AdapterBenchmark:
    """Benchmarking utilities for LoRA adapters."""

    @staticmethod
    async def compare_adapters(
        manager: LoRAManager,
        adapter_names: List[str],
        test_prompts: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Compare multiple adapters' performance."""
        results = {}

        for name in adapter_names:
            # Load adapter
            if name not in manager.get_loaded_adapters():
                await manager.load_adapter(name)

            # Benchmark
            metrics = await manager.benchmark_adapter(name, test_prompts)
            results[name] = metrics

        return results

    @staticmethod
    def generate_report(
        comparison: Dict[str, Dict[str, float]],
        output_path: Optional[str] = None
    ) -> str:
        """Generate benchmark report."""
        lines = ["# LoRA Adapter Benchmark Report"]
        lines.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n")

        lines.append("## Performance Comparison\n")
        lines.append("| Adapter | Prompts | Total (s) | Avg (s) | Prompts/s |")
        lines.append("|--------|--------|----------|---------|-----------|")

        for name, metrics in comparison.items():
            lines.append(
                f"| {name} | {metrics.get('prompts_tested', 0)} | "
                f"{metrics.get('total_duration_seconds', 0):.2f} | "
                f"{metrics.get('avg_duration_per_prompt', 0):.3f} | "
                f"{metrics.get('prompts_per_second', 0):.1f} |"
            )

        report = "\n".join(lines)

        if output_path:
            with open(output_path, "w") as f:
                f.write(report)

        return report


# Global LoRA manager instance
lora_manager = LoRAManager()


__all__ = [
    "AdapterStatus",
    "LoRAAdapter",
    "AdapterConfig",
    "LoRAManager",
    "AdapterBenchmark",
    "lora_manager"
]

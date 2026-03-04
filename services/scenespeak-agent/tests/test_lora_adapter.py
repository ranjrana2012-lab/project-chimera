"""
Unit tests for LoRA adapter support.

Tests LoRA loading, switching, and benchmarking.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add scenespeak-agent to path
agent_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(agent_path))

from lora_adapter import (
    AdapterStatus,
    LoRAAdapter,
    AdapterConfig,
    LoRAManager,
    AdapterBenchmark,
    lora_manager
)


class TestLoRAAdapter:
    """Test LoRA adapter dataclass."""

    def test_adapter_creation(self):
        """Test creating an adapter."""
        adapter = LoRAAdapter(
            name="test_adapter",
            path="/models/test",
            rank=8,
            alpha=32.0
        )
        assert adapter.name == "test_adapter"
        assert adapter.path == "/models/test"
        assert adapter.rank == 8
        assert adapter.alpha == 32.0
        assert adapter.status == AdapterStatus.UNLOADED

    def test_adapter_to_dict(self):
        """Test converting adapter to dictionary."""
        adapter = LoRAAdapter(
            name="test_adapter",
            path="/models/test",
            description="Test adapter"
        )
        adapter.status = AdapterStatus.LOADED
        adapter.loaded_at = datetime.now(timezone.utc)

        data = adapter.to_dict()
        assert data["name"] == "test_adapter"
        assert data["status"] == "loaded"
        assert data["loaded_at"] is not None


class TestAdapterConfig:
    """Test adapter configuration manager."""

    def test_config_initialization(self):
        """Test config creation."""
        config = AdapterConfig()
        assert len(config.adapters) == 0
        assert config.base_model == "mistralai/Mistral-7B-Instruct-v0.2"
        assert config.max_loaded_adapters == 3

    def test_add_adapter(self):
        """Test adding an adapter."""
        config = AdapterConfig()
        adapter = LoRAAdapter(name="test", path="/models/test")

        result = config.add_adapter(adapter)
        assert result is True
        assert "test" in config.adapters

    def test_add_duplicate_adapter(self):
        """Test adding duplicate adapter."""
        config = AdapterConfig()
        adapter = LoRAAdapter(name="test", path="/models/test")

        config.add_adapter(adapter)
        result = config.add_adapter(adapter)
        assert result is False

    def test_get_adapter(self):
        """Test getting an adapter."""
        config = AdapterConfig()
        adapter = LoRAAdapter(name="test", path="/models/test")
        config.add_adapter(adapter)

        retrieved = config.get_adapter("test")
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_get_nonexistent_adapter(self):
        """Test getting nonexistent adapter."""
        config = AdapterConfig()
        assert config.get_adapter("nonexistent") is None

    def test_list_adapters(self):
        """Test listing all adapters."""
        config = AdapterConfig()
        config.add_adapter(LoRAAdapter(name="test1", path="/models/test1"))
        config.add_adapter(LoRAAdapter(name="test2", path="/models/test2"))

        adapters = config.list_adapters()
        assert len(adapters) == 2

    def test_remove_adapter(self):
        """Test removing an adapter."""
        config = AdapterConfig()
        adapter = LoRAAdapter(name="test", path="/models/test")
        config.add_adapter(adapter)

        result = config.remove_adapter("test")
        assert result is True
        assert "test" not in config.adapters

    def test_remove_nonexistent_adapter(self):
        """Test removing nonexistent adapter."""
        config = AdapterConfig()
        result = config.remove_adapter("nonexistent")
        assert result is False


class TestLoRAManager:
    """Test LoRA manager."""

    @pytest.fixture
    def manager(self):
        """Create a LoRA manager."""
        config = AdapterConfig()
        return LoRAManager(config=config, adapters_dir="/tmp/test_lora")

    def test_manager_initialization(self, manager):
        """Test manager creation."""
        assert manager.config is not None
        assert manager.device == "cuda"
        assert len(manager.loaded_adapters) == 0

    def test_load_adapter(self, manager):
        """Test loading an adapter."""
        adapter = LoRAAdapter(name="test", path="test_adapter")
        manager.config.add_adapter(adapter)

        async def run_test():
            # This will fail because file doesn't exist, but we can test the flow
            result = await manager.load_adapter("test")
            # Will fail due to missing file, but status tracking works
            assert adapter.status == AdapterStatus.ERROR
            return result

        asyncio.run(run_test())

    def test_unload_adapter(self, manager):
        """Test unloading an adapter."""
        adapter = LoRAAdapter(name="test", path="test_adapter")
        manager.config.add_adapter(adapter)
        manager.loaded_adapters["test"] = {"adapter": adapter, "weights": "test"}

        async def run_test():
            result = await manager.unload_adapter("test")
            assert result is True
            assert adapter.status == AdapterStatus.UNLOADED
            assert "test" not in manager.loaded_adapters

        asyncio.run(run_test())

    def test_get_loaded_adapters(self, manager):
        """Test getting loaded adapters list."""
        manager.loaded_adapters["test1"] = {}
        manager.loaded_adapters["test2"] = {}

        loaded = manager.get_loaded_adapters()
        assert "test1" in loaded
        assert "test2" in loaded
        assert len(loaded) == 2

    def test_get_adapter_info(self, manager):
        """Test getting adapter information."""
        adapter = LoRAAdapter(
            name="test",
            path="/models/test",
            description="Test adapter"
        )
        manager.config.add_adapter(adapter)

        info = manager.get_adapter_info("test")
        assert info is not None
        assert info["name"] == "test"
        assert info["is_loaded"] is False

    def test_discover_adapters(self, manager):
        """Test adapter discovery."""
        # With no adapters directory, should return empty
        discovered = manager.discover_adapters()
        assert isinstance(discovered, list)

    def test_add_callback(self, manager):
        """Test adding status change callback."""
        called = []

        def callback(name, status):
            called.append((name, status))

        manager.add_callback(callback)
        manager._notify_callbacks("test", AdapterStatus.LOADED)

        assert len(called) == 1
        assert called[0] == ("test", AdapterStatus.LOADED)


class TestAdapterBenchmark:
    """Test adapter benchmarking."""

    def test_compare_adapters(self):
        """Test comparing multiple adapters."""
        manager = LoRAManager()

        async def run_test():
            # Add mock loaded adapters
            manager.loaded_adapters["adapter1"] = {}
            manager.loaded_adapters["adapter2"] = {}

            test_prompts = ["test prompt 1", "test prompt 2"]
            results = await AdapterBenchmark.compare_adapters(
                manager,
                ["adapter1", "adapter2"],
                test_prompts
            )

            assert "adapter1" in results
            assert "adapter2" in results
            assert results["adapter1"]["prompts_tested"] == 2

        asyncio.run(run_test())

    def test_generate_report(self):
        """Test benchmark report generation."""
        comparison = {
            "adapter1": {
                "prompts_tested": 10,
                "total_duration_seconds": 5.0,
                "avg_duration_per_prompt": 0.5,
                "prompts_per_second": 2.0
            },
            "adapter2": {
                "prompts_tested": 10,
                "total_duration_seconds": 3.0,
                "avg_duration_per_prompt": 0.3,
                "prompts_per_second": 3.33
            }
        }

        report = AdapterBenchmark.generate_report(comparison)

        assert "## Performance Comparison" in report
        assert "adapter1" in report
        assert "adapter2" in report
        assert "| adapter1 |" in report


class TestGlobalLoRAManager:
    """Test global LoRA manager instance."""

    def test_global_manager(self):
        """Test global manager is accessible."""
        assert lora_manager is not None
        assert isinstance(lora_manager, LoRAManager)

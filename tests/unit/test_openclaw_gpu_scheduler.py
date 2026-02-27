# tests/unit/test_openclaw_gpu_scheduler.py

import pytest
from services.openclaw_orchestrator.src.core.gpu_scheduler import GPUScheduler, GPU_AVAILABLE, GPUAllocation

class TestGPUScheduler:
    @pytest.fixture
    def scheduler(self):
        return GPUScheduler()

    def test_scheduler_init(self, scheduler):
        assert scheduler is not None
        assert scheduler.allocations == {}
        assert isinstance(scheduler.gpu_count, int)

    @pytest.mark.asyncio
    async def test_allocate_returns_none_when_no_gpu(self, scheduler):
        if not GPU_AVAILABLE:
            result = await scheduler.allocate_gpu("test", 1000)
            assert result is None

    @pytest.mark.asyncio
    async def test_release_gpu(self, scheduler):
        # Manually add an allocation for testing
        scheduler.allocations["test_service"] = GPUAllocation(gpu_id=0, memory_mb=1000)
        assert "test_service" in scheduler.allocations

        await scheduler.release_gpu("test_service")
        assert "test_service" not in scheduler.allocations

    @pytest.mark.asyncio
    async def test_release_nonexistent_service(self, scheduler):
        # Should not raise error
        await scheduler.release_gpu("nonexistent")
        assert "nonexistent" not in scheduler.allocations

    def test_get_usage(self, scheduler):
        # Initially empty
        usage = scheduler.get_usage()
        assert usage == {}

        # Add some allocations
        scheduler.allocations["service1"] = GPUAllocation(gpu_id=0, memory_mb=1000)
        scheduler.allocations["service2"] = GPUAllocation(gpu_id=0, memory_mb=2000)

        usage = scheduler.get_usage()
        assert usage == {"service1": 1000, "service2": 2000}

    def test_gpu_allocation_class(self):
        alloc = GPUAllocation(gpu_id=0, memory_mb=1000)
        assert alloc.gpu_id == 0
        assert alloc.memory_mb == 1000
        assert alloc.allocated is False


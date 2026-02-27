"""GPU allocation and scheduling."""
import asyncio
from typing import Dict, Optional
import pynvml

try:
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False


class GPUAllocation:
    """Represents a GPU allocation."""
    def __init__(self, gpu_id: int, memory_mb: int):
        self.gpu_id = gpu_id
        self.memory_mb = memory_mb
        self.allocated = False


class GPUScheduler:
    """Manages GPU resource allocation."""

    def __init__(self):
        self.allocations: Dict[str, GPUAllocation] = {}
        self.gpu_count = 0
        self.total_memory_mb = 0

        if GPU_AVAILABLE:
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            self.total_memory_mb = mem_info.total // (1024 * 1024)

    async def allocate_gpu(
        self,
        service: str,
        memory_mb: int,
        timeout: float = 30.0
    ) -> Optional[int]:
        """Allocate GPU for a service."""
        if not GPU_AVAILABLE:
            return None

        # Check if already allocated
        if service in self.allocations:
            return self.allocations[service].gpu_id

        # Try to allocate on GPU 0
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            free_mb = mem_info.free // (1024 * 1024)

            if free_mb >= memory_mb:
                self.allocations[service] = GPUAllocation(gpu_id=0, memory_mb=memory_mb)
                return 0
        except Exception as e:
            pass

        return None

    async def release_gpu(self, service: str) -> None:
        """Release GPU allocation."""
        if service in self.allocations:
            del self.allocations[service]

    def get_usage(self) -> Dict[str, int]:
        """Get current GPU usage in MB."""
        usage = {}
        for service, alloc in self.allocations.items():
            usage[service] = alloc.memory_mb
        return usage

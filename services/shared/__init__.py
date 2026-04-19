"""
Shared utilities for Project Chimera services.

This package provides common modules used across all services.
"""

from .tracing import (
    setup_telemetry,
    instrument_fastapi,
    add_span_attributes,
    record_error
)
from .connection_pool import (
    ConnectionPoolManager,
    PoolStats,
    get_global_pool,
    close_global_pool,
)
from .cache import (
    RequestCache,
    CacheStats,
    get_global_cache,
    close_global_cache,
)

__all__ = [
    # Telemetry
    'setup_telemetry',
    'instrument_fastapi',
    'add_span_attributes',
    'record_error',
    # Connection Pool
    'ConnectionPoolManager',
    'PoolStats',
    'get_global_pool',
    'close_global_pool',
    # Request Cache
    'RequestCache',
    'CacheStats',
    'get_global_cache',
    'close_global_cache',
]

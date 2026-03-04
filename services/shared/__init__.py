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

__all__ = [
    'setup_telemetry',
    'instrument_fastapi',
    'add_span_attributes',
    'record_error',
]

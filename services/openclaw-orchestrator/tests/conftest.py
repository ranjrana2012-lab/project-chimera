"""
Pytest configuration for OpenClaw Orchestrator tests.

Sets up the Python path for proper module imports.
"""

import sys
import os

# Add orchestrator root to Python path for imports
_orchestrator_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(f"DEBUG: conftest.py adding to sys.path: {_orchestrator_root}")
if _orchestrator_root not in sys.path:
    sys.path.insert(0, _orchestrator_root)
print(f"DEBUG: sys.path includes orchestrator root: {_orchestrator_root in sys.path}")

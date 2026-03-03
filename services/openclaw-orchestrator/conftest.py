"""
Pytest configuration for OpenClaw Orchestrator tests.

Sets up the Python path for proper module imports.
"""

import sys
import os

# Add current directory to Python path for imports
_current_dir = os.path.abspath(os.path.dirname(__file__))
print(f"DEBUG root conftest: adding to sys.path: {_current_dir}")
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# Also verify transitions can be imported
try:
    from transitions import time_triggers
    print(f"DEBUG root conftest: transitions.time_triggers imported successfully")
except ImportError as e:
    print(f"DEBUG root conftest: Failed to import transitions.time_triggers: {e}")

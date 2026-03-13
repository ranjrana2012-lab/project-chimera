"""Pytest configuration for autonomous-agent tests."""

import sys
from pathlib import Path

# Add service root to Python path for imports
_service_root = Path(__file__).parent
if str(_service_root) not in sys.path:
    sys.path.insert(0, str(_service_root))

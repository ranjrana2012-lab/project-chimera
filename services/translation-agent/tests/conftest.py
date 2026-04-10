"""Pytest configuration for Translation Agent tests."""

import sys
import os

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

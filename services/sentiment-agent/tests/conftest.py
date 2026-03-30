"""
Pytest configuration for Sentiment Agent tests.

Sets up PYTHONPATH to include shared modules.
"""

import sys
import os

# Force CPU mode for tests (no CUDA available in test environment)
os.environ["CI_GPU_AVAILABLE"] = "false"

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Add shared services directory to path
shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../shared'))
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

"""
Pytest configuration for unit tests.
"""

import sys
import os

# Add project root to Python path for imports
# Force it to the beginning to ensure it takes precedence
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Remove any existing occurrence and add to the front
sys.path = [p for p in sys.path if p != _project_root]
sys.path.insert(0, _project_root)

"""
Pytest configuration for Project Chimera tests.

Sets up the Python path for proper module imports.
"""

import sys
import os

# Add project root to Python path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(f"DEBUG conftest: adding to sys.path: {_project_root}")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Add shared module to path BEFORE platform modules to avoid conflicts
_shared_dir = os.path.join(_project_root, 'shared')
if _shared_dir not in sys.path:
    sys.path.insert(0, _shared_dir)

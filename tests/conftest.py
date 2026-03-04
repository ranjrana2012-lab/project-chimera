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

# Add specific platform modules to path using import hooks
# We need to be careful not to shadow the standard library 'platform' module
# So we'll add the platform/monitoring and platform/monitoring/telemetry paths specifically
_monitoring_dir = os.path.join(_project_root, 'platform', 'monitoring')
if _monitoring_dir not in sys.path:
    sys.path.insert(0, _monitoring_dir)

_telemetry_dir = os.path.join(_monitoring_dir, 'telemetry')
if _telemetry_dir not in sys.path:
    sys.path.insert(0, _telemetry_dir)

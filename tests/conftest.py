"""
Pytest configuration for Project Chimera tests.

Sets up the Python path for proper module imports.
"""

import importlib.util
import sys
import os

# Add project root to Python path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Force the repo's shared package to win over any unrelated module/plugin
# named "shared" that may already be importable in the test environment.
_shared_dir = os.path.join(_project_root, 'shared')
_shared_init = os.path.join(_shared_dir, '__init__.py')
if os.path.exists(_shared_init):
    _shared_module = sys.modules.get('shared')
    _shared_file = getattr(_shared_module, '__file__', '') if _shared_module else ''
    if not _shared_file.startswith(_shared_dir):
        spec = importlib.util.spec_from_file_location(
            'shared',
            _shared_init,
            submodule_search_locations=[_shared_dir],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules['shared'] = module
        spec.loader.exec_module(module)

# Force the repo's services package for the same reason. Some environments have
# unrelated packages named "services", and collection order can otherwise make
# tests resolve services.dashboard or services.kimi_super_agent incorrectly.
_services_dir = os.path.join(_project_root, 'services')
_services_init = os.path.join(_services_dir, '__init__.py')
if os.path.exists(_services_init):
    _services_module = sys.modules.get('services')
    _services_file = getattr(_services_module, '__file__', '') if _services_module else ''
    if not _services_file.startswith(_services_dir):
        spec = importlib.util.spec_from_file_location(
            'services',
            _services_init,
            submodule_search_locations=[_services_dir],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules['services'] = module
        spec.loader.exec_module(module)

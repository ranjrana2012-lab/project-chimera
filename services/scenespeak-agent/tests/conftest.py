"""Pytest configuration for SceneSpeak Agent tests."""

import sys
import os

# Add src and shared modules to path for imports
service_dir = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(service_dir)
shared_path = os.path.join(service_dir, "..", "shared")

if src_path not in sys.path:
    sys.path.insert(0, src_path)
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

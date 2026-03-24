"""CI mode detection for CPU-only environments."""
import os

def is_cpu_mode():
    """Check if running in CPU-only CI mode."""
    return os.getenv("CI_GPU_AVAILABLE", "true").lower() == "false"

def get_device():
    """Get appropriate device for current environment."""
    return "cpu" if is_cpu_mode() else "cuda"

def get_model_variant():
    """Get model variant for current environment."""
    return "ci" if is_cpu_mode() else "full"

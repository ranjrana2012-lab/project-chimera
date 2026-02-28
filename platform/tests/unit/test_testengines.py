"""Test advanced test engines."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from testengines.mutmut import MutationTestRunner
from testengines.locust import PerformanceTestRunner

def test_mutation_runner_initializes():
    """Test MutationTestRunner initializes."""
    runner = MutationTestRunner()
    assert runner.baseline_branch == "main"

def test_performance_runner_initializes():
    """Test PerformanceTestRunner initializes."""
    runner = PerformanceTestRunner()
    assert runner is not None

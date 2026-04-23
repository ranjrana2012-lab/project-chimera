import subprocess
import os
import sys
import unittest

class TestChimeraSmoke(unittest.TestCase):
    def test_running_demo_from_cli(self):
        """Smoke test compiling demo output strictly using subprocess"""
        script_path = os.path.abspath("services/operator-console/chimera_core.py")
        
        # Check if venv python exists specifically for ML load test
        venv_python = os.path.abspath("services/operator-console/venv/bin/python")
        python_bin = venv_python if os.path.exists(venv_python) else sys.executable
        
        res = subprocess.run([python_bin, script_path, "demo"], capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 0)
        self.assertIn("Processing Demo Input", res.stdout)
        self.assertIn("momentum_build", res.stdout)

if __name__ == "__main__":
    unittest.main()

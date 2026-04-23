import sys
import os
import unittest
from unittest.mock import patch
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../services/operator-console')))
from chimera_core import ChimeraCore

class TestChimeraWorkflows(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input', side_effect=["This is amazing!", "compare", "This is terrible", "quit"])
    def test_interactive_loop(self, mock_input, mock_stdout):
        core = ChimeraCore()
        # Mocking to avoid loading ML for quick integration tests
        core.load_models = lambda: None
        core.sentiment_analyzer = core.heuristic_sentiment 
        
        core.run_interactive()
        
        output = mock_stdout.getvalue()
        
        # Check standard processing
        self.assertIn("momentum_build", output)
        
        # Check comparison mode
        self.assertIn("Comparison Mode", output)
        self.assertIn("supportive_care", output)
        
        # Ensure it exited
        self.assertIn("Exiting", output)

if __name__ == "__main__":
    unittest.main()

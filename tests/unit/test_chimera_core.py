import sys
import os
import unittest
from unittest.mock import patch, mock_open

# Add services/operator-console to python path to import chimera_core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../services/operator-console')))

from chimera_core import ChimeraCore

class TestChimeraCore(unittest.TestCase):
    def setUp(self):
        self.core = ChimeraCore()

    def test_heuristic_sentiment_positive(self):
        res = self.core.heuristic_sentiment("This is an amazing and wonderful experience!")
        self.assertEqual(res[0]['label'], 'POSITIVE')

    def test_heuristic_sentiment_negative(self):
        res = self.core.heuristic_sentiment("I am very worried and frustrated by this.")
        self.assertEqual(res[0]['label'], 'NEGATIVE')

    def test_heuristic_sentiment_neutral(self):
        res = self.core.heuristic_sentiment("It is a building.")
        self.assertEqual(res[0]['label'], 'NEUTRAL')

    def test_select_strategy(self):
        self.assertEqual(self.core.select_strategy({'label': 'POSITIVE'}), 'momentum_build')
        self.assertEqual(self.core.select_strategy({'label': 'NEGATIVE'}), 'supportive_care')
        self.assertEqual(self.core.select_strategy({'label': 'NEUTRAL'}), 'standard_response')

    def test_generate_response(self):
        self.assertIn("amplifying", self.core.generate_response("test", "momentum_build"))
        self.assertIn("supportive", self.core.generate_response("test", "supportive_care"))
        self.assertIn("standard", self.core.generate_response("test", "standard_response"))

    @patch("builtins.open", new_callable=mock_open)
    def test_export_json_csv(self, mock_file):
        self.core.history = [{"input": "test", "sentiment": "POSITIVE"}]
        self.core.export_json("test.json")
        self.core.export_csv("test.csv")
        self.assertTrue(mock_file.called)

if __name__ == "__main__":
    unittest.main()

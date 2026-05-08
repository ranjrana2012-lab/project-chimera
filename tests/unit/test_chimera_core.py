import unittest
from unittest.mock import patch, mock_open
import importlib.util
from pathlib import Path

chimera_core_path = (
    Path(__file__).resolve().parent.parent.parent
    / "services"
    / "operator-console"
    / "chimera_core.py"
)
spec = importlib.util.spec_from_file_location("chimera_core", chimera_core_path)
chimera_core = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(chimera_core)

ChimeraCore = chimera_core.ChimeraCore

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

    def test_select_strategy_uses_grounding_support_for_confused_overwhelmed_input(self):
        self.assertEqual(
            self.core.select_strategy(
                {'label': 'NEGATIVE'},
                "I am confused and overwhelmed",
            ),
            "grounding_support",
        )

    def test_select_strategy_uses_reflective_transition_for_intense_inspiring_input(self):
        self.assertEqual(
            self.core.select_strategy(
                {'label': 'POSITIVE'},
                "This is intense but inspiring",
            ),
            "reflective_transition",
        )

    def test_generate_response(self):
        self.assertIn("amplifying", self.core.generate_response("test", "momentum_build"))
        self.assertIn("supportive", self.core.generate_response("test", "supportive_care"))
        self.assertIn("standard", self.core.generate_response("test", "standard_response"))
        self.assertIn("ground", self.core.generate_response("test", "grounding_support").lower())
        self.assertIn("reflect", self.core.generate_response("test", "reflective_transition").lower())

    @patch("builtins.open", new_callable=mock_open)
    def test_export_json_csv(self, mock_file):
        self.core.history = [{"input": "test", "sentiment": "POSITIVE"}]
        self.core.export_json("test.json")
        self.core.export_csv("test.csv")
        self.assertTrue(mock_file.called)

if __name__ == "__main__":
    unittest.main()

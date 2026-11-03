import unittest
from remgu import SimulationResult

class TestSimulationResult(unittest.TestCase):
    def test_predictions_are_json_compatible(self):
        result = SimulationResult('demo', {}, 3, {}, {}, predictions={2: 1})
        self.assertEqual(result.to_dict()['predictions'], {'2': 1})

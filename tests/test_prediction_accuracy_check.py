import unittest
from remgu import GraphWorld, PredictionAccuracyCheck

class TestPredictionAccuracyCheck(unittest.TestCase):
    def test_reports_accuracy(self):
        world = GraphWorld({0: set()}, {0: 1}, {0: 0})
        result = PredictionAccuracyCheck().evaluate(world, {0: 1, 1: 0}, {0: 1, 1: 1})
        self.assertEqual(result['metrics']['accuracy'], 0.5)

    def test_reports_missing_prediction(self):
        world = GraphWorld({0: set()}, {0: 1}, {0: 0})
        self.assertEqual(PredictionAccuracyCheck().evaluate(world, {0: 1}, {})['status'], 'failed')

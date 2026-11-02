import unittest
from remgu import GraphReachabilityBaseline, GraphWorld

class TestGraphReachabilityBaseline(unittest.TestCase):
    def test_predicts_signal_when_reachable_and_default_when_not(self):
        world = GraphWorld({0: {1}, 1: {0}, 2: set()}, {0: 0, 1: 1, 2: 0}, {0: 0, 1: 1, 2: 0}, (0, 1))
        model = GraphReachabilityBaseline(source_node=1)
        self.assertEqual(model.predict(world, (0, 2)), {0: 1, 2: 0})

    def test_rejects_non_binary_default(self):
        with self.assertRaises(ValueError):
            GraphReachabilityBaseline(unreachable_prediction=2)

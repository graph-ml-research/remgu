import unittest
from remgu import CriticalBridgeCheck, GraphWorld, RemoveEdgeOperator

class TestCriticalBridgeCheck(unittest.TestCase):
    def test_passes_when_bridge_is_removed(self):
        world = GraphWorld({0: {1}, 1: {0}}, {0: 0, 1: 1}, {0: 0, 1: 1}, (0, 1))
        changed = RemoveEdgeOperator((0, 1)).apply(world)
        self.assertEqual(CriticalBridgeCheck().evaluate(changed, {}, {})['status'], 'passed')

    def test_not_evaluated_without_bridge_metadata(self):
        world = GraphWorld({0: set()}, {0: 0}, {0: 0})
        self.assertEqual(CriticalBridgeCheck().evaluate(world, {}, {})['status'], 'not_evaluated')

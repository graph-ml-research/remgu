import unittest
from remgu import GraphWorld, RemoveEdgeOperator

class TestRemoveEdgeOperator(unittest.TestCase):
    def test_removes_edge_without_mutating_original_and_keeps_bridge_metadata(self):
        world = GraphWorld({0: {1}, 1: {0}}, {0: 0, 1: 1}, {0: 0, 1: 1}, (0, 1))
        changed = RemoveEdgeOperator((0, 1)).apply(world)
        self.assertFalse(changed.has_edge(0, 1))
        self.assertTrue(world.has_edge(0, 1))
        self.assertEqual(changed.critical_bridge, (0, 1))

    def test_missing_edge_is_rejected(self):
        world = GraphWorld({0: set()}, {0: 0}, {0: 0})
        with self.assertRaises(ValueError):
            RemoveEdgeOperator((0, 1)).apply(world)

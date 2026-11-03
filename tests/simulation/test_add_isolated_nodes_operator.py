import unittest
from remgu import AddIsolatedNodesOperator, GraphWorld

class TestAddIsolatedNodesOperator(unittest.TestCase):
    def test_adds_isolated_nodes_and_preserves_original(self):
        world = GraphWorld({0: set()}, {0: 1}, {0: 0})
        changed = AddIsolatedNodesOperator(2, feature=0.5).apply(world)
        self.assertEqual(changed.node_ids, (0, 1, 2))
        self.assertEqual(changed.adjacency[1], set())
        self.assertEqual(world.node_ids, (0,))

    def test_negative_count_is_rejected(self):
        with self.assertRaises(ValueError):
            AddIsolatedNodesOperator(-1)

import unittest
from remgu import GraphWorld

class TestGraphWorld(unittest.TestCase):
    def setUp(self):
        self.world = GraphWorld({0: {1}, 1: {0}}, {0: 0, 1: 1}, {0: 0, 1: 1}, (0, 1))

    def test_reachability_and_edges(self):
        self.assertTrue(self.world.reachable(0, 1))
        self.assertEqual(self.world.edges, ((0, 1),))

    def test_copy_is_independent(self):
        clone = self.world.copy()
        clone.adjacency[0].clear()
        self.assertTrue(self.world.has_edge(0, 1))

    def test_ascii_output_can_be_truncated(self):
        output = self.world.to_ascii(max_nodes=1)
        self.assertIn("Nodes:", output)
        self.assertIn("truncated 1 node", output)

    def test_rejects_asymmetric_adjacency(self):
        with self.assertRaises(ValueError):
            GraphWorld({0: {1}, 1: set()}, {0: 0, 1: 1}, {0: 0, 1: 1})

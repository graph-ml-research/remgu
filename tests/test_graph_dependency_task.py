import unittest
from remgu import GraphDependencyTask, GraphWorld

class TestGraphDependencyTask(unittest.TestCase):
    def test_labels_are_derived_from_source_feature(self):
        world = GraphWorld({0: {1}, 1: {0}}, {0: 0.0, 1: 1.0}, {0: 0, 1: 1}, (0, 1))
        self.assertEqual(GraphDependencyTask(source_node=1, target_nodes=(0,)).labels(world), {0: 1})

    def test_unknown_source_is_rejected(self):
        world = GraphWorld({0: set()}, {0: 0}, {0: 0})
        with self.assertRaises(ValueError):
            GraphDependencyTask(source_node=4).labels(world)

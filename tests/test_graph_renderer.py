import unittest
from remgu import GraphRenderer, GraphWorld

class TestGraphRenderer(unittest.TestCase):
    def test_outputs_dot_edge_list_and_svg(self):
        world = GraphWorld({0: {1}, 1: {0}}, {0: 1, 1: 2}, {0: 0, 1: 1}, (0, 1))
        renderer = GraphRenderer()
        self.assertIn('graph RemguGraph', renderer.to_dot(world))
        self.assertIn('0 -- 1', renderer.to_edge_list(world))
        self.assertIn('<svg', renderer.to_svg(world))

    def test_graph_renderer_inherits_renderer_base(self):
        from remgu import Renderer
        self.assertIsInstance(GraphRenderer(), Renderer)

import unittest
from remgu import DotSvgRenderer

class TestDotSvgRenderer(unittest.TestCase):
    def test_renders_supported_dot_as_svg(self):
        svg = DotSvgRenderer().render('digraph G {\na [label="A < B"];\na -> b;\n}')
        self.assertIn('<svg', svg)
        self.assertIn('A &lt; B', svg)

    def test_rejects_empty_and_large_graphs(self):
        with self.assertRaises(ValueError): DotSvgRenderer().render('digraph G {}')
        with self.assertRaises(ValueError): DotSvgRenderer().render('graph G { a -- b; }', max_nodes=1)

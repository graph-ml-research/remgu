import unittest
from remgu import EmbeddingRenderer

class TestEmbeddingRenderer(unittest.TestCase):
    def test_renders_projected_points_and_escapes_labels(self):
        svg = EmbeddingRenderer().render([{'x': 0, 'y': 1, 'label': '<script>'}, {'x': 1, 'y': 0}])
        self.assertIn('<svg', svg)
        self.assertIn('&lt;script&gt;', svg)

    def test_requires_coordinates(self):
        with self.assertRaises(ValueError): EmbeddingRenderer().render([{'label': 'missing'}])

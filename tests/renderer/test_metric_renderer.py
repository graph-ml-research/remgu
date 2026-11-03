import unittest
from remgu import MetricRenderer

class TestMetricRenderer(unittest.TestCase):
    def test_renders_chart_and_empty_state(self):
        renderer = MetricRenderer()
        self.assertIn('<svg', renderer.render({'accuracy': [0.4, 0.7, 0.9]}))
        self.assertIn('No metric measurements', renderer.render({'accuracy': [None]}))

    def test_rejects_small_dimensions(self):
        with self.assertRaises(ValueError): MetricRenderer().render({'x': [1]}, width=10)

import unittest
from remgu import ImageRenderer

class TestImageRenderer(unittest.TestCase):
    def test_escapes_alt_text(self):
        self.assertIn('&quot;', ImageRenderer().render('assets/chart.png', 'a "chart"'))

    def test_rejects_remote_and_parent_paths(self):
        with self.assertRaises(ValueError): ImageRenderer().render('https://example.com/a.png', 'x')
        with self.assertRaises(ValueError): ImageRenderer().render('../secret.png', 'x')

import unittest
from remgu import TextRenderer

class TestTextRenderer(unittest.TestCase):
    def test_escapes_markup(self):
        rendered = TextRenderer().render('<script>alert("x")</script>')
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

import unittest
from remgu import TableRenderer

class TestTableRenderer(unittest.TestCase):
    def test_escapes_cells_and_preserves_columns(self):
        rendered = TableRenderer().render([{"name": '<img src=x>', "score": 1}], ["name", "score"])
        self.assertIn('&lt;img src=x&gt;', rendered)
        self.assertNotIn('<img src=x>', rendered)
        self.assertIn('<th>score</th>', rendered)

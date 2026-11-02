import json
import tempfile
import unittest
from pathlib import Path
from remgu import StaticHtmlReport

class TestStaticHtmlReport(unittest.TestCase):
    def test_report_selects_and_bounds_examples_in_raw_result(self):
        data = {"experiment_id": "selection", "status": "completed", "metrics": {},
                "examples": [{"id": index, "correct": index != 0} for index in range(500)]}
        with tempfile.TemporaryDirectory() as directory:
            path = StaticHtmlReport().render(data, Path(directory) / "report.html")
            html = path.read_text(encoding="utf-8")
        self.assertIn('&quot;source_count&quot;: 500', html)
        self.assertIn('&quot;selected_count&quot;: 100', html)
        self.assertNotIn('&quot;id&quot;: 499', html)
        self.assertIn('examples-page-status', html)

    def test_writes_offline_report_and_escapes_untrusted_text(self):
        data = {'experiment_id': '<script>bad</script>', 'status': 'completed', 'metrics': {'accuracy': 0.8},
                'config': {'note': '<img src=x>'}, 'world': {}, 'checks': []}
        with tempfile.TemporaryDirectory() as directory:
            path = StaticHtmlReport().render(data, Path(directory) / 'report.html', events=[{'type': 'probe', 'message': '<script>x</script>'}])
            html = path.read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;bad', html)
        self.assertNotIn('<script>bad</script>', html)
        self.assertIn('Peak process RAM', html)
        self.assertIn('not measured', html)
        self.assertIn('&lt;script&gt;x', html)
        self.assertIn('examples-page-status', html)

import tempfile
import unittest
from pathlib import Path
from remgu.research_cli import ResearchCli

class TestCliSimulation(unittest.TestCase):
    def test_run_and_report_commands_create_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / 'result.json'
            report = Path(directory) / 'report.html'
            cli = ResearchCli()
            self.assertEqual(cli.main(['simulation', 'run', '--seed', '5', '--nodes-per-community', '3', '--output', str(result)]), 0)
            self.assertTrue(result.is_file())
            self.assertEqual(cli.main(['simulation', 'report', str(result), '--output', str(report)]), 0)
            self.assertIn('ReMgu experiment report', report.read_text(encoding='utf-8'))

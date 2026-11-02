import unittest
from remgu import SimulationConfig, SimulationExperiment

class TestSimulationExperiment(unittest.TestCase):
    def test_public_facade_runs_default_scenario(self):
        result = SimulationExperiment(SimulationConfig(seed=3)).run()
        self.assertEqual(result.status, 'completed')
        self.assertIn('accuracy', result.metrics)

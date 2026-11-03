import unittest
from remgu import CriticalBridgeCheck, RemoveEdgeOperator, SimulationConfig, SimulationRunner

class TestSimulationRunner(unittest.TestCase):
    def test_end_to_end_run_and_bridge_intervention(self):
        config = SimulationConfig(seed=5, community_sizes=(3, 3), edge_probability=0.0)
        runner = SimulationRunner(checks=[CriticalBridgeCheck()])
        baseline = runner.run(config)
        intervened = runner.run(config, [RemoveEdgeOperator((2, 3))])
        self.assertEqual(baseline.status, 'completed')
        self.assertEqual(intervened.status, 'completed')
        self.assertEqual(intervened.checks[0]['status'], 'passed')
        self.assertGreaterEqual(baseline.metrics['accuracy'], intervened.metrics['accuracy'])

    def test_failed_configuration_returns_failed_result(self):
        config = SimulationConfig(seed=1)
        result = SimulationRunner().run(config, [RemoveEdgeOperator((100, 101))])
        self.assertEqual(result.status, 'failed')
        self.assertEqual(result.error['type'], 'ValueError')

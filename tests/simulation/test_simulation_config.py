import unittest
from remgu import SimulationConfig

class TestSimulationConfig(unittest.TestCase):
    def test_config_serializes(self):
        config = SimulationConfig(seed=7)
        self.assertEqual(config.to_dict()['seed'], 7)

    def test_param_types_accept_only_supported_categories(self):
        config = SimulationConfig(param_types={"learning_rate": "hot", "depth": "structural", "filter": "view"})
        self.assertEqual(config.to_dict()["param_types"]["learning_rate"], "hot")
        with self.assertRaises(ValueError):
            SimulationConfig(param_types={"bad": "runtime"})

    def test_invalid_sizes_are_rejected(self):
        with self.assertRaises(ValueError):
            SimulationConfig(community_sizes=(2, 0))

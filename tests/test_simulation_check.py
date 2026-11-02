import unittest
from remgu import SimulationCheck

class TestSimulationCheck(unittest.TestCase):
    def test_base_class_is_abstract(self):
        with self.assertRaises(TypeError):
            SimulationCheck()

import unittest
from remgu import GraphWorldGenerator, RandomSource

class TestGraphWorldGenerator(unittest.TestCase):
    def test_generation_is_reproducible(self):
        generator = GraphWorldGenerator()
        first = generator.generate(RandomSource(9))
        second = generator.generate(RandomSource(9))
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_critical_bridge_connects_communities(self):
        world = GraphWorldGenerator().generate(RandomSource(2), (3, 4), 0.0, True)
        self.assertEqual(world.critical_bridge, (2, 3))
        self.assertTrue(world.has_edge(2, 3))

    def test_invalid_probability_is_rejected(self):
        with self.assertRaises(ValueError):
            GraphWorldGenerator().generate(RandomSource(1), edge_probability=1.2)

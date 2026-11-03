import unittest
from remgu import SyntheticExampleGenerator

class TestSyntheticExampleGenerator(unittest.TestCase):
    def test_generation_is_reproducible_and_in_memory(self):
        generator = SyntheticExampleGenerator()
        self.assertEqual(generator.generate(3, seed=7), generator.generate(3, seed=7))
        self.assertTrue(all(item['synthetic'] for item in generator.generate(3)))

    def test_validates_count(self):
        with self.assertRaises(ValueError): SyntheticExampleGenerator().generate(-1)

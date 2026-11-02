import unittest
from remgu import RandomSource

class TestRandomSource(unittest.TestCase):
    def test_same_seed_reproduces_sequence(self):
        self.assertEqual([RandomSource(4).randint(0, 10) for _ in range(1)], [RandomSource(4).randint(0, 10)])
        left, right = RandomSource(12), RandomSource(12)
        self.assertEqual([left.random() for _ in range(5)], [right.random() for _ in range(5)])

    def test_choice_rejects_empty_sequence(self):
        with self.assertRaises(ValueError):
            RandomSource(1).choice([])

import unittest
from remgu import NumericNoiseTransform, RandomSource

class TestNumericNoiseTransform(unittest.TestCase):
    def test_noise_is_reproducible_and_does_not_mutate_input(self):
        record = {'x': 1.0}
        transform = NumericNoiseTransform('x', 0.2)
        first = transform.apply(record, RandomSource(2))
        second = transform.apply(record, RandomSource(2))
        self.assertEqual(first, second)
        self.assertEqual(record, {'x': 1.0})
        self.assertLessEqual(abs(first['x'] - 1.0), 0.2)

    def test_missing_field_is_rejected(self):
        with self.assertRaises(ValueError):
            NumericNoiseTransform('x', 1).apply({}, RandomSource(1))

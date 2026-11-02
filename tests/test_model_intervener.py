import unittest
from remgu import ModelIntervener

class TestModelIntervener(unittest.TestCase):
    def test_apply_and_restore(self):
        class Model:
            threshold = 0.5
        model = Model()
        intervener = ModelIntervener()
        record = intervener.apply(model, 'threshold', 0.1)
        self.assertEqual(model.threshold, 0.1)
        intervener.restore(model, record)
        self.assertEqual(model.threshold, 0.5)

    def test_unknown_attribute_is_rejected(self):
        with self.assertRaises(ValueError):
            ModelIntervener().apply(object(), 'weight', 0)

import unittest
from remgu import Transform

class TestTransform(unittest.TestCase):
    def test_base_class_is_abstract(self):
        with self.assertRaises(TypeError):
            Transform()

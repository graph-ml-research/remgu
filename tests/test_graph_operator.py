import unittest
from remgu import GraphOperator

class TestGraphOperator(unittest.TestCase):
    def test_base_class_is_abstract(self):
        with self.assertRaises(TypeError):
            GraphOperator()

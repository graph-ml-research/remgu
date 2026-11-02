import unittest
from unittest.mock import Mock
from remgu import ArchitectureAdapter

class TestArchitectureAdapter(unittest.TestCase):
    def test_returns_dot_text(self):
        model = Mock()
        model.get_architecture_dot.return_value = 'digraph M { a -> b; }'
        self.assertEqual(ArchitectureAdapter().get_architecture_dot(model), 'digraph M { a -> b; }')

    def test_missing_contract_is_unavailable(self):
        self.assertIsNone(ArchitectureAdapter().get_architecture_dot(object()))

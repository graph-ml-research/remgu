import unittest
from remgu import KerasArchitectureAdapter

class FakeLayer:
    def __init__(self, name): self.name = name

class FakeModel:
    layers = [FakeLayer('input'), FakeLayer('encoder'), FakeLayer('head')]

class TestKerasArchitectureAdapter(unittest.TestCase):
    def test_builds_sequential_layer_view(self):
        dot = KerasArchitectureAdapter().get_architecture_dot(FakeModel())
        self.assertIn('layer0 -> layer1', dot)
        self.assertIn('encoder', dot)

    def test_returns_none_without_layers(self):
        self.assertIsNone(KerasArchitectureAdapter().get_architecture_dot(object()))

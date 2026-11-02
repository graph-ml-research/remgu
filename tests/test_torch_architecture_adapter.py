import unittest
from remgu import TorchArchitectureAdapter

class FakeModule:
    def named_modules(self):
        return [('', self), ('encoder', FakeLayer()), ('encoder.projection', FakeLayer())]

class FakeLayer:
    pass

class TestTorchArchitectureAdapter(unittest.TestCase):
    def test_builds_module_hierarchy_without_torch_dependency(self):
        dot = TorchArchitectureAdapter().get_architecture_dot(FakeModule())
        self.assertIn('digraph PyTorchModules', dot)
        self.assertIn('m1 -> m2', dot)

    def test_returns_none_without_named_modules(self):
        self.assertIsNone(TorchArchitectureAdapter().get_architecture_dot(object()))

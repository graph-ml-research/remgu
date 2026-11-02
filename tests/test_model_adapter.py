import sys
import types
import unittest
from unittest.mock import Mock, patch
from remgu import ArchitectureAdapter, ModelAdapter


class TestModelAdapter(unittest.TestCase):
    def test_contract_defaults_to_unavailable(self):
        self.assertIsNone(ModelAdapter().get_architecture_dot())

    def test_custom_model_contract_is_used(self):
        model = Mock()
        model.get_architecture_dot.return_value = 'digraph Model { a -> b; }'
        self.assertEqual(ArchitectureAdapter().get_architecture_dot(model), 'digraph Model { a -> b; }')

    def test_loaded_torch_module_is_detected_without_importing_framework(self):
        class Module:
            def named_modules(self):
                return [('', self), ('layer', object())]
        fake_torch = types.SimpleNamespace(nn=types.SimpleNamespace(Module=Module))
        with patch.dict(sys.modules, {"torch": fake_torch}):
            result = ArchitectureAdapter().get_architecture_dot(Module())
        self.assertIn('digraph PyTorchModules', result)


    def test_loaded_tensorflow_keras_model_uses_model_to_dot(self):
        class KerasModel:
            pass
        graph = Mock()
        graph.to_string.return_value = 'digraph Keras { input -> output; }'
        utils = types.SimpleNamespace(model_to_dot=Mock(return_value=graph))
        keras = types.SimpleNamespace(Model=KerasModel, utils=utils)
        tensorflow = types.SimpleNamespace(keras=keras)
        with patch.dict(sys.modules, {"tensorflow": tensorflow}):
            result = ArchitectureAdapter().get_architecture_dot(KerasModel())
        self.assertEqual(result, 'digraph Keras { input -> output; }')
        utils.model_to_dot.assert_called_once()

    def test_unknown_model_returns_none(self):
        self.assertIsNone(ArchitectureAdapter().get_architecture_dot(object()))

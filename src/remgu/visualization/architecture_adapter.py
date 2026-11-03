# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Framework-neutral model architecture introspection and automatic adapter registry."""
from __future__ import annotations

import sys
from typing import Any


class ModelAdapter:
    """Common contract for objects that can describe their model architecture.

    A model can implement ``get_architecture_dot()`` without depending on ReMgu's
    framework-specific adapters. ``ArchitectureAdapter`` uses the same contract
    while discovering a representation for an arbitrary model object.
    """

    def get_architecture_dot(self, model: object | None = None) -> str | None:
        """Return an optional Graphviz DOT description, or ``None`` if unavailable."""
        del model
        return None


class ArchitectureAdapter(ModelAdapter):
    """Discover an architecture description from a model or loaded framework.

    Frameworks are detected only through ``sys.modules``: introspection never imports
    a potentially large ML framework just to draw a diagram. All adapter failures degrade
    to ``None`` because architecture visualization is optional.
    """

    def get_architecture_dot(self, model: object) -> str | None:
        """Return a DOT string when a known adapter can describe ``model``; otherwise None."""
        try:
            getter = getattr(model, "get_architecture_dot", None)
            if callable(getter):
                result = getter()
                if isinstance(result, str) and result.strip() and "graph" in result:
                    return result
                if result is None:
                    return None

            # Specific adapters share this base class; each uses duck typing and
            # only inspects metadata already available on the supplied object.
            from remgu.visualization.catboost_architecture_adapter import CatBoostArchitectureAdapter
            from remgu.visualization.keras_architecture_adapter import KerasArchitectureAdapter
            from remgu.visualization.spacy_architecture_adapter import SpacyPipelineArchitectureAdapter
            from remgu.visualization.torch_architecture_adapter import TorchArchitectureAdapter
            from remgu.visualization.word2vec_architecture_adapter import Word2VecArchitectureAdapter
            for adapter in (TorchArchitectureAdapter(), KerasArchitectureAdapter(),
                            CatBoostArchitectureAdapter(), SpacyPipelineArchitectureAdapter(),
                            Word2VecArchitectureAdapter()):
                if type(self) is not ArchitectureAdapter and isinstance(adapter, type(self)):
                    continue
                result = adapter.get_architecture_dot(model)
                if isinstance(result, str) and result.strip():
                    return result
            tensorflow = sys.modules.get("tensorflow")
            if tensorflow is not None:
                keras = getattr(tensorflow, "keras", None)
                utils = getattr(keras, "utils", None)
                model_to_dot = getattr(utils, "model_to_dot", None)
                if callable(model_to_dot) and self._is_keras_model(model, keras):
                    graph = model_to_dot(model, show_shapes=True, show_layer_names=True)
                    to_string = getattr(graph, "to_string", None)
                    if callable(to_string):
                        result = to_string()
                        if isinstance(result, str) and result.strip():
                            return result
            return None
        except Exception:
            # Model tracing and optional framework metadata are not reliable for every model.
            return None

    def _is_keras_model(self, model: object, keras: Any) -> bool:
        """Check the loaded Keras Model type without importing optional packages."""
        models = getattr(keras, "Model", None)
        if isinstance(models, type) and isinstance(model, models):
            return True
        models_module = getattr(keras, "models", None)
        model_type = getattr(models_module, "Model", None)
        return isinstance(model_type, type) and isinstance(model, model_type)

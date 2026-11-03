# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Check architecture adapters share the common model adapter contract."""
import unittest

from remgu import (ArchitectureAdapter, CatBoostArchitectureAdapter, KerasArchitectureAdapter,
                   ModelAdapter, SpacyPipelineArchitectureAdapter, TorchArchitectureAdapter,
                   Word2VecArchitectureAdapter)


class TestArchitectureInheritance(unittest.TestCase):
    """Ensure framework adapters share a stable base type."""

    def test_architecture_adapter_inherits_model_adapter(self):
        self.assertTrue(issubclass(ArchitectureAdapter, ModelAdapter))

    def test_framework_adapters_inherit_architecture_adapter(self):
        for adapter_type in (CatBoostArchitectureAdapter, KerasArchitectureAdapter,
                             SpacyPipelineArchitectureAdapter, TorchArchitectureAdapter,
                             Word2VecArchitectureAdapter):
            with self.subTest(adapter=adapter_type.__name__):
                self.assertTrue(issubclass(adapter_type, ArchitectureAdapter))
